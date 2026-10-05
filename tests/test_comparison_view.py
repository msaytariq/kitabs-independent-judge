"""The local comparison surface reuses saved evidence and never starts a run."""
from copy import deepcopy
import json
from fastapi.testclient import TestClient
from independent_judge.api.app import create_app
from independent_judge.domain.scope import text_hash
from test_comparison_summary import record


def catalog(tmp_path):
    folder = tmp_path / 'comparison-catalog'
    folder.mkdir()
    data = record() | {'title': '<script>unsafe()</script>', 'description': 'Локальный пример',
                      'provenance': {'a': 'Перевод A', 'b': 'Перевод B'},
                      'apparatus': {'a': [], 'b': []}, 'boundary_review': {'note_ru': 'Проверены границы.'}}
    path = folder / 'example.json'
    path.write_text(json.dumps(data), encoding='utf-8')
    return data, path


def test_catalog_report_and_exact_uploaded_match_are_read_only(tmp_path):
    data, path = catalog(tmp_path)
    original = path.read_bytes()
    with TestClient(create_app(tmp_path)) as client:
        response = client.get('/api/examples')
        assert response.status_code == 200
        assert response.json()[0]['id'] == 'example'
        view = client.get('/api/examples/example').json()
        assert view['summary']['sides']['a']['candidates'] == 2
        assert view['run']['id'] == 'saved'
        assert 'passes' not in view['run']
        exported = client.get('/api/examples/example/report.html')
        assert exported.status_code == 200
        assert '<script>unsafe' not in exported.text
        assert '&lt;script&gt;unsafe' in exported.text
        assert 'First claim.' in exported.text
        assert 'не установлено' in exported.text
        scope = data['scope']
        draft = client.post('/api/comparisons/text', json=scope['texts'] | {
            'source_language': 'en', 'target_language': 'en'}).json()
        prepared = client.post(f"/api/comparisons/{draft['id']}/scopes", json={
            'confirmed': True, 'profile': 'general', 'ranges': {k: {
                'start': 0, 'end': len(v['text']), 'text_sha256': v['sha256']}
                for k, v in draft['materials'].items()}}).json()
        matched = client.get(f"/api/scopes/{prepared['id']}/comparison").json()
        assert matched['run']['id'] == 'saved'
        assert matched['matched_example_id'] == 'example'
    assert path.read_bytes() == original
    assert not (tmp_path / 'runs.sqlite3').exists()
    assert not (tmp_path / 'budget.sqlite3').exists()


def test_new_materials_and_unconfirmed_scope_have_no_invented_score(tmp_path):
    with TestClient(create_app(tmp_path)) as client:
        draft = client.post('/api/comparisons/text', json={
            'source': 'Source.', 'a': 'One.', 'b': 'Two.', 'source_language': 'en', 'target_language': 'en'}).json()
        prepared = client.post(f"/api/comparisons/{draft['id']}/scopes", json={
            'confirmed': False, 'ranges': {k: {'start': 0, 'end': len(v['text']), 'text_sha256': v['sha256']}
                                         for k, v in draft['materials'].items()}}).json()
        view = client.get(f"/api/scopes/{prepared['id']}/comparison").json()
        assert view['ratings']['sides']['a']['total'] is None
        assert view['run'] is None
        assert view['summary']['sides']['a']['candidates'] is None
        assert view['scope']['status'] == 'needs_review'
        assert client.get(f"/api/scopes/{prepared['id']}/report.html").status_code == 200


def test_catalog_rejects_stale_report_and_unknown_id(tmp_path):
    data, path = catalog(tmp_path)
    data['run']['manifest']['scope']['texts']['source'] += ' wrong source'
    path.write_text(json.dumps(data))
    with TestClient(create_app(tmp_path)) as client:
        assert client.get('/api/examples/example').status_code == 422
        assert client.get('/api/examples/unknown').status_code == 404


def test_generated_apparatus_is_positive_evidence_without_changing_findings(tmp_path):
    data, path = catalog(tmp_path)
    source = data['scope']['texts']['b']
    note = '[1] Generated explanation.'
    full = source + '\n\n' + note
    folder = tmp_path / 'apparatus-evidence'
    folder.mkdir()
    evidence = {'artifact_text':full, 'artifact_sha256':text_hash(full),
        'scope_hashes':data['scope']['hashes'], 'translation_range':{'start':0,'end':len(source)},
        'label_ru':'Сохранённый результат', 'scope_label_ru':'Весь сохранённый результат',
        'groups':[{'id':'notes', 'title_ru':'Примечания', 'purpose_ru':'Пояснения читателю',
                   'sample_indices':[0], 'items':[{'start':len(source)+2,'end':len(full),
                                                  'text':note,'sha256':text_hash(note)}]}]}
    sidecar = folder / 'example.json'
    sidecar.write_text(json.dumps(evidence))
    original = path.read_bytes()
    with TestClient(create_app(tmp_path)) as client:
        view = client.get('/api/examples/example').json()
        assert view['generated_apparatus']['groups'][0]['count'] == 1
        assert view['summary']['sides']['a']['candidates'] == 2
        assert 'Научный аппарат, созданный Kitabs' in client.get('/api/examples/example/report.html').text
        assert note in client.get('/api/examples/example/report.html').text
        evidence['artifact_text'] += ' changed'
        sidecar.write_text(json.dumps(evidence))
        assert client.get('/api/examples/example').status_code == 422
    assert path.read_bytes() == original
