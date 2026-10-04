"""Source reviews stay bound to their actual texts, notes, and evidence."""
from copy import deepcopy
from hashlib import sha256
import json

import pytest
from fastapi.testclient import TestClient
from independent_judge.api.app import create_app
from test_comparison_view import catalog


def digest(value):
    return sha256(value.encode()).hexdigest()


def review_fixture(tmp_path):
    record, path = catalog(tmp_path)
    record['run'] = None
    record['apparatus']['b'] = [{'number': 2, 'text': 'An explanatory note.'}]
    path.write_text(json.dumps(record))
    review = {
        'version': 1, 'id': 'source-check', 'checked_on': '2026-10-04',
        'scope_hashes': record['scope']['hashes'],
        'apparatus_hashes': {'a': [], 'b': [{'number': 2, 'sha256': digest('An explanatory note.')}]},
        'summary_ru': 'Сноска подготовлена; нужна ссылка на источник.',
        'sources': [{'id': 'ref', 'label': 'Primary source', 'url': 'https://example.org/reference',
                     'summary_ru': 'Текст источника сверен.'}],
        'evidence': [{'id': 'note', 'role': 'note_b', 'number': 2, 'start': 0, 'end': 20,
                      'text': 'An explanatory note.', 'sha256': digest('An explanatory note.')}],
        'benefits': [{'title_ru': 'Подготовлена сноска', 'detail_ru': 'Доступна для проверки.',
                      'evidence_ids': ['note']}],
        'checks': [{'id': 'check', 'title_ru': 'Источники', 'a_ru': 'Нет примечаний.',
                    'b_ru': 'Есть сноска.', 'conclusion_ru': 'Проверить атрибуцию.',
                    'evidence_ids': ['note'], 'source_ids': ['ref']}],
        'tasks': [{'id': 'task', 'side': 'b', 'title_ru': 'Дополнить источник',
                   'reason_ru': 'Не указан сборник.', 'draft_ru': '<script>alert(1)</script>',
                   'evidence_ids': ['note'], 'source_ids': ['ref']}],
        'limitations_ru': ['Разбор Codex, без решения эксперта.'],
    }
    directory = tmp_path / 'source-reviews'
    directory.mkdir()
    sidecar = directory / 'example.json'
    sidecar.write_text(json.dumps(review))
    return record, path, review, sidecar


def test_source_review_is_available_in_api_and_export_without_inventing_score(tmp_path):
    record, path, review, sidecar = review_fixture(tmp_path)
    original = path.read_bytes(), sidecar.read_bytes()
    with TestClient(create_app(tmp_path)) as client:
        response = client.get('/api/examples/example')
        assert response.status_code == 200
        view = response.json()
        assert view.get('source_review') is not None
        assert view['source_review']['status'] == 'desk_review'
        assert view['source_review']['evidence'][0]['text'] == 'An explanatory note.'
        assert view['summary']['sides']['b']['necessary_edits'] is None
        assert view['summary']['sides']['b']['candidates'] is None
        assert view['run'] is None
        report = client.get('/api/examples/example/report.html').text
        assert 'An explanatory note.' in report
        assert 'https://example.org/reference' in report
        assert '<script>alert' not in report
        assert '&lt;script&gt;alert' in report
        assert client.get('/api/examples').json()[0]['has_source_review'] is True
    assert original == (path.read_bytes(), sidecar.read_bytes())
    assert not (tmp_path / 'budget.sqlite3').exists()


@pytest.mark.parametrize('damage', ['source', 'note', 'quote', 'range', 'unknown_evidence', 'unknown_source', 'url', 'duplicate'])
def test_invalid_or_stale_source_review_is_rejected(tmp_path, damage):
    record, path, review, sidecar = review_fixture(tmp_path)
    if damage == 'source': record['scope']['texts']['source'] += ' changed'
    elif damage == 'note': record['apparatus']['b'][0]['text'] += ' changed'
    elif damage == 'quote': review['evidence'][0]['text'] = 'Invented quote.'
    elif damage == 'range': review['evidence'][0]['start'] = -1
    elif damage == 'unknown_evidence': review['tasks'][0]['evidence_ids'] = ['missing']
    elif damage == 'unknown_source': review['tasks'][0]['source_ids'] = ['missing']
    elif damage == 'url': review['sources'][0]['url'] = 'javascript:alert(1)'
    elif damage == 'duplicate': review['evidence'].append(deepcopy(review['evidence'][0]))
    path.write_text(json.dumps(record))
    sidecar.write_text(json.dumps(review))
    with TestClient(create_app(tmp_path)) as client:
        assert client.get('/api/examples/example').status_code == 422


def test_saved_run_match_does_not_copy_source_review_to_user_materials(tmp_path):
    record, path, review, sidecar = review_fixture(tmp_path)
    from test_comparison_summary import record as pilot
    record['run'] = pilot()['run']
    path.write_text(json.dumps(record))
    with TestClient(create_app(tmp_path)) as client:
        draft = client.post('/api/comparisons/text', json=record['scope']['texts'] | {
            'source_language': 'en', 'target_language': 'en'}).json()
        scope = client.post(f"/api/comparisons/{draft['id']}/scopes", json={
            'confirmed': True, 'profile': 'general', 'ranges': {k: {
                'start': 0, 'end': len(v['text']), 'text_sha256': v['sha256']}
                for k, v in draft['materials'].items()}}).json()
        view = client.get(f"/api/scopes/{scope['id']}/comparison").json()
        assert view['run']['id'] == 'saved'
        assert view.get('source_review') is None


@pytest.mark.parametrize('changed', [False, True])
def test_full_artifact_evidence_is_bound_to_the_original_output(tmp_path, changed):
    from independent_judge.domain.source_review import source_review
    from independent_judge.domain.errors import InputError
    record, _, review, _ = review_fixture(tmp_path)
    full = record['scope']['texts']['b'] + '\nGlossary entry.'
    original_hash = digest(full)
    record['source_review'] = review
    record['capability_evidence'] = {
        'artifact_text': full + (' changed' if changed else ''), 'artifact_sha256': original_hash,
        'scope_hashes': record['scope']['hashes'], 'translation_range': {'start': 0, 'end': 34}}
    review['evidence'].append({'id': 'glossary', 'role': 'artifact_b', 'start': 35, 'end': 50,
        'text': 'Glossary entry.', 'sha256': digest('Glossary entry.'), 'artifact_sha256': original_hash})
    if changed:
        with pytest.raises(InputError): source_review(record)
    else:
        result = source_review(record)
        assert result['evidence'][-1]['text'] == 'Glossary entry.'
