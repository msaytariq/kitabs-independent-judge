"""A public deployment keeps its Kitabs session alive and records the processing journal of B."""
import json
from datetime import datetime, timezone
import httpx
import pytest
from independent_judge.domain.errors import InputError
from independent_judge.domain.scope import text_hash
from test_pipeline_b import packets


def pipeline(handle, store):
    from independent_judge.infrastructure.kitabs_pipeline import KitabsPipeline
    return KitabsPipeline('https://platform.example/api', '', transport=httpx.MockTransport(handle), session=store)


def test_expired_access_token_is_renewed_once_with_the_rotated_refresh_token(tmp_path):
    from independent_judge.infrastructure.kitabs_session import KitabsSession
    store = KitabsSession(tmp_path / 'session.json')
    store.save('refresh-1')
    seen = []
    def handle(request):
        seen.append((request.url.path, request.headers.get('authorization')))
        if request.url.path == '/api/auth/refresh':
            assert json.loads(request.content) == {'refreshToken': 'refresh-1'}
            return httpx.Response(200, json={'accessToken': 'access-2', 'refreshToken': 'refresh-2'})
        if request.headers.get('authorization') != 'Bearer access-2':
            return httpx.Response(401, json={'detail': 'expired'})
        return httpx.Response(200, json={'job': {'id': 'j', 'status': 'running'}})
    assert pipeline(handle, store).status('j')['status'] == 'running'
    assert store.load() == 'refresh-2'  # The rotated token replaces the used one.
    assert (tmp_path / 'session.json').stat().st_mode & 0o077 == 0
    assert [p for p, _ in seen].count('/api/auth/refresh') == 1


def test_a_refused_refresh_reports_missing_authorization(tmp_path):
    from independent_judge.infrastructure.kitabs_session import KitabsSession
    store = KitabsSession(tmp_path / 'session.json')
    store.save('refresh-1')
    handle = lambda request: httpx.Response(401, json={})
    with pytest.raises(InputError) as error:
        pipeline(handle, store).status('j')
    assert error.value.code == 'pipeline_auth_required'


def journal_packets():
    data = packets()
    data['/api/pipeline/jobs/j/assembly']['artifacts'][-1]['createdAt'] = '2026-10-06T10:05:00+00:00'
    data['/api/pipeline/jobs/j/artifacts'] = {'jobId': 'j', 'artifacts': [
        {'id': 'a1', 'jobId': 'j', 'kind': 'audit_report', 'chunkId': 'c1', 'hash': 'h1',
         'payload': {'translatedText': 'He came and be with us.', 'issues': [
             {'currentText': 'came and be with us', 'revisedText': 'came to us'}]}},
        {'id': 'e1', 'jobId': 'j', 'kind': 'edited_chunk', 'chunkId': 'c1', 'hash': 'h2',
         'payload': {'inputText': 'He came to us.', 'issues': []}},
        {'id': 'p1', 'jobId': 'j', 'kind': 'proofread_chunk', 'chunkId': 'c1', 'hash': 'h3',
         'payload': {'inputText': 'He came to us.'}}]}
    return data


def test_completed_b_carries_the_processing_journal_from_platform_records():
    data = journal_packets()
    def handle(request):
        if request.url.path.endswith('/audit-reviews'):
            stage = request.url.params['stageId']
            assert request.url.params['chunkId'] == 'c1'
            statuses = [{'issueIndex': 0, 'status': 'accepted'}] if stage == 'audit' else []
            return httpx.Response(200, json={'jobId': 'j', 'stageId': stage, 'chunkId': 'c1', 'statuses': statuses})
        return httpx.Response(200, json=data[request.url.path])
    from independent_judge.infrastructure.kitabs_pipeline import KitabsPipeline
    port = KitabsPipeline('https://platform.example/api', 'token', transport=httpx.MockTransport(handle))
    started = datetime(2026, 10, 6, 10, 0, tzinfo=timezone.utc).timestamp()
    result = port.completed('j', text_hash('source'), started_at=started)
    journal = result['processing']
    assert journal['intervals'] == [{'start': started, 'end': started + 300}]
    assert journal['operations_complete'] is True
    assert [(o['stage'], o['status'], o['before'], o['after']) for o in journal['operations']] == [
        ('audit', 'applied', 'came and be with us', 'came to us')]
    assert journal['text_sha256'] == text_hash('Translation B.')
    # Without a known start the time stays unknown; the edits are still recorded.
    assert port.completed('j', text_hash('source'))['processing']['timing_complete'] is False


def test_renewal_keeps_who_connected_the_session(tmp_path):
    from independent_judge.infrastructure.kitabs_session import KitabsSession
    path = tmp_path / 'session.json'
    path.write_text(json.dumps({'refreshToken': 'refresh-1', 'email': 'admin@kitabs.ai', 'userId': 'u1'}))
    KitabsSession(path).save('refresh-2')
    assert json.loads(path.read_text()) == {'refreshToken': 'refresh-2', 'email': 'admin@kitabs.ai', 'userId': 'u1'}


def test_a_disconnected_operator_stops_launches_at_once(tmp_path):
    """The admin removes the session file: a cached access token must not keep working."""
    from independent_judge.infrastructure.kitabs_session import KitabsSession
    store = KitabsSession(tmp_path / 'session.json')
    store.save('refresh-1')
    calls = []
    def handle(request):
        calls.append(request.url.path)
        if request.url.path == '/api/auth/refresh':
            return httpx.Response(200, json={'accessToken': 'access-2', 'refreshToken': 'refresh-2'})
        return httpx.Response(200, json={'job': {'id': 'j', 'status': 'running'}})
    port = pipeline(handle, store)
    assert port.ready() is True
    port.status('j')
    (tmp_path / 'session.json').unlink()
    assert port.ready() is False
    with pytest.raises(InputError) as error:
        port.status('j')
    assert error.value.code == 'pipeline_auth_required'
    assert calls == ['/api/auth/refresh', '/api/pipeline/jobs/j']


def test_a_new_operator_session_replaces_the_cached_access_token(tmp_path):
    from independent_judge.infrastructure.kitabs_session import KitabsSession
    store = KitabsSession(tmp_path / 'session.json')
    store.save('refresh-1')
    seen = []
    def handle(request):
        seen.append(request.headers.get('authorization'))
        if request.url.path == '/api/auth/refresh':
            old = json.loads(request.content)['refreshToken'] == 'refresh-1'
            pair = ('access-1', 'refresh-1b') if old else ('access-new', 'refresh-new-b')
            return httpx.Response(200, json={'accessToken': pair[0], 'refreshToken': pair[1]})
        return httpx.Response(200, json={'job': {'id': 'j', 'status': 'running'}})
    port = pipeline(handle, store)
    port.status('j')
    store.save('refresh-new')  # The admin connected another account.
    port.status('j')
    assert seen[-1] == 'Bearer access-new'
