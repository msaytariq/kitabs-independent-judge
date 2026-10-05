from fastapi.testclient import TestClient
from independent_judge.api.app import create_app
from test_local_runs import prepare, runtime, wait_done
from test_runner import FakeJudge


def test_full_offline_pipeline_projects_scores_effort_and_evidence(tmp_path):
    judge = FakeJudge()
    with TestClient(create_app(tmp_path, evaluation=runtime(tmp_path, judge))) as client:
        scope = prepare(client)
        client.post(f'/api/scopes/{scope}/run')
        assert wait_done(client, scope)['status'] == 'completed'
        view = client.get(f'/api/scopes/{scope}/comparison').json()
        assert view['ratings']['winner'] == 'b'
        assert view['ratings']['sides']['b']['total'] == 70
        assert view['decision_effort']['sides']['a']['remaining_estimated_seconds'] == 5
        assert view['decision_effort']['sides']['a']['prior_decisions'] is None
        assert view['ratings']['sides']['a']['finding_ids'] == [view['summary']['findings'][0]['id']]
        assert view['summary']['findings'][0]['source_excerpt'] == 'الصدق فضيلة'


def test_synthetic_catalog_is_visibly_labelled(tmp_path):
    from test_comparison_view import catalog
    import json
    data, path = catalog(tmp_path)
    data['demonstration'] = True
    path.write_text(json.dumps(data))
    with TestClient(create_app(tmp_path)) as client:
        assert client.get('/api/examples/example').json()['demonstration'] is True
