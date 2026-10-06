import httpx
import pytest
from independent_judge.domain.errors import InputError
from independent_judge.domain.scope import text_hash


def test_external_workflow_has_stable_identity_and_never_starts_a_paid_job():
    from independent_judge.application.pipeline_b import handoff
    a = handoff('source', 'autopilot', 'https://app.kitabs.ai')
    assert a == handoff('source', 'autopilot', 'https://app.kitabs.ai')
    assert a['state'] == 'external_workflow'
    assert a['workspace_url'] == 'https://app.kitabs.ai/workspace'
    assert a['job_started'] is False
    assert handoff('source','manual','https://app.kitabs.ai')['mode'] == 'manual'
    with pytest.raises(InputError): handoff('source','unknown','https://app.kitabs.ai')


def packets(status='completed'):
    return {
      '/api/pipeline/jobs/j': {'job': {'id':'j','documentId':'d','status':status}},
      '/api/pipeline/jobs/j/assembly': {'jobId':'j','artifacts':[
        {'id':'s','jobId':'j','kind':'source_text','payload':{'text':'source'}},
        {'id':'c','jobId':'j','kind':'chunks','payload':{'chunks':[{'id':'c1'}]}},
        {'id':'p','jobId':'j','kind':'proofread_chunk','stageId':'proofreader',
         'chunkId':'c1','hash':'p-hash','payload':{'chunkId':'c1'}},
        {'id':'b','jobId':'j','kind':'assembled_document','hash':'assembly-hash',
         'payload':{'jobId':'j','body':'Translation B.','inputSources':[
             {'chunkId':'c1','stageId':'proofreader','artifactId':'p',
              'artifactHash':'p-hash','sourceKind':'generated'}]}}]},
    }


def adapter(data, token='test-token'):
    from independent_judge.infrastructure.kitabs_pipeline import KitabsPipeline
    def handle(request):
        assert request.method == 'GET'
        assert request.headers['authorization'] == 'Bearer test-token'
        return httpx.Response(200,json=data[request.url.path])
    return KitabsPipeline('https://platform.example/api', token, transport=httpx.MockTransport(handle))


def test_completed_artifact_requires_exact_source_and_preserves_hashes():
    result = adapter(packets()).completed('j', text_hash('source'))
    assert result['text'] == 'Translation B.'
    assert result['sha256'] == text_hash(result['text'])
    assert result['platform_artifact_hash'] == 'assembly-hash'
    assert result['human_work'] is None
    with pytest.raises(InputError) as error: adapter(packets()).completed('j',text_hash('different'))
    assert error.value.code == 'pipeline_source_mismatch'


@pytest.mark.parametrize('status', ['running','paused','waiting_review','failed','cancelled'])
def test_unfinished_or_failed_job_never_produces_b(status):
    with pytest.raises(InputError): adapter(packets(status)).completed('j',text_hash('source'))


def test_absent_authorization_fails_before_network_access():
    with pytest.raises(InputError) as error: adapter(packets(), token='').completed('j',text_hash('source'))
    assert error.value.code == 'pipeline_auth_required'


def test_partial_or_stale_assembly_is_rejected_and_reconnect_is_read_only():
    data = packets()
    port = adapter(data)
    assert port.completed('j',text_hash('source')) == port.completed('j',text_hash('source'))
    data['/api/pipeline/jobs/j/assembly']['artifacts'][1]['payload']['chunks'].append({'id':'c2'})
    with pytest.raises(InputError): adapter(data).completed('j',text_hash('source'))
    data = packets()
    data['/api/pipeline/jobs/j/assembly']['artifacts'][-1]['payload']['inputSources'][0]['artifactHash'] = 'stale'
    with pytest.raises(InputError): adapter(data).completed('j',text_hash('source'))


@pytest.mark.parametrize('target,updates', [
    ('input', {'artifactId':'missing','artifactHash':None}),
    ('input', {'artifactId':'p','artifactHash':''}),
    ('input', {'stageId':'editor'}),
    ('input', {'sourceKind':'human_revision','revisionId':'r1'}),
    ('artifact', {'chunkId':'other'}),
    ('artifact', {'stageId':'editor'}),
    ('artifact', {'kind':'source_text'}),
    ('artifact', {'payload':{'chunkId':'other'}}),
])
def test_unproven_assembly_artifact_ownership_is_rejected(target, updates):
    data = packets()
    artifacts = data['/api/pipeline/jobs/j/assembly']['artifacts']
    item = artifacts[2] if target == 'artifact' else artifacts[-1]['payload']['inputSources'][0]
    item.update(updates)
    with pytest.raises(InputError): adapter(data).completed('j',text_hash('source'))


def test_embedded_adapter_uses_platform_upload_and_autopilot_stream():
    import json
    import base64
    from independent_judge.infrastructure.kitabs_pipeline import KitabsPipeline
    calls = []
    def handle(request):
        calls.append((request.method, request.url.path))
        assert request.headers['authorization'] == 'Bearer test-only'
        if request.url.path == '/api/documents':
            data = json.loads(request.content)
            assert base64.b64decode(data['file']['dataBase64']).decode() == 'الأصل'
            assert (data['sourceLang'], data['targetLang']) == ('ar', 'en')
            return httpx.Response(201, json={'document': {'id': 'doc'}})
        if request.url.path == '/api/pipeline/jobs':
            assert json.loads(request.content) == {'documentId': 'doc'}
            return httpx.Response(201, json={'job': {'id': 'job'}})
        if request.url.path.endswith('start-stream'):
            assert request.url.params['step'] == 'false'
            return httpx.Response(200, text='event: job_completed\ndata: {}\n\n')
        return httpx.Response(200, json={'job': {'id': 'job', 'status': 'completed'}})
    port = KitabsPipeline('https://platform.example/api', 'test-only', transport=httpx.MockTransport(handle))
    assert port.create(port.upload('الأصل', 'ar', 'en')) == 'job'
    port.start('job')
    assert port.status('job')['status'] == 'completed'
    assert len(calls) == 4


def test_a_file_source_is_sent_as_the_original_file_and_kitabs_text_is_the_source():
    import json
    import base64
    from independent_judge.infrastructure.kitabs_pipeline import KitabsPipeline
    sent = {}
    def handle(request):
        sent.update(json.loads(request.content))
        return httpx.Response(201, json={'document': {'id': 'doc'}})
    port = KitabsPipeline('https://platform.example/api', 'test-only', transport=httpx.MockTransport(handle))
    port.upload(None, 'ar', 'en', original={'filename': 'book.pdf', 'content_type': 'application/pdf',
                                            'content': b'%PDF-1.7'})
    assert sent['sourceFormat'] == 'pdf' and sent['isScannedPdf'] is False
    assert sent['file']['fileName'] == 'book.pdf' and base64.b64decode(sent['file']['dataBase64']) == b'%PDF-1.7'
    # Without a judge source, the platform source text of the job is the source of the comparison.
    result = adapter(packets()).completed('j', None)
    assert result['source'] == 'source' and result['source_sha256'] == text_hash('source')


def test_progress_reads_the_job_and_its_artifacts_without_payloads_in_the_answer():
    from independent_judge.infrastructure.kitabs_pipeline import KitabsPipeline
    def handle(request):
        if request.url.path.endswith('/artifacts'):
            return httpx.Response(200, json={'artifacts': [
                {'kind': 'chunks', 'stageId': 'chunking', 'chunkId': None, 'payload': {'chunks': [{'id': 'a'}, {'id': 'b'}]}},
                {'kind': 'translated_chunk', 'stageId': 'translator', 'chunkId': 'a', 'payload': {'text': 'long'}}]})
        return httpx.Response(200, json={'job': {'id': 'job', 'status': 'running', 'currentStage': 'audit'}})
    port = KitabsPipeline('https://platform.example/api', 'test-only', transport=httpx.MockTransport(handle))
    progress = port.progress('job')
    assert (progress['chunk'], progress['chunks'], progress['stage']) == (1, 2, 'audit')
    assert progress['percent'] == 17  # 1 preparation + 1 stage of 12 steps
