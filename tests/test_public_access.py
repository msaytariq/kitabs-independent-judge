"""A public deployment names its hosts; every other host and cross-site write stays blocked."""
from fastapi.testclient import TestClient
from independent_judge.api.app import create_app


def test_named_public_hosts_reach_the_comparison_api(tmp_path, monkeypatch):
    monkeypatch.setenv('JUDGE_PUBLIC_HOSTS', 'app.kitabs.ai,api.kitabs.ai')
    with TestClient(create_app(tmp_path)) as c:
        public = {'Host': 'app.kitabs.ai'}
        assert c.get('/api/examples', headers=public).status_code == 200
        same_site = public | {'Origin': 'https://app.kitabs.ai', 'Sec-Fetch-Site': 'same-origin'}
        assert c.post('/api/comparisons/text', json={}, headers=same_site).status_code != 403
        assert c.get('/api/examples', headers={'Host': 'evil.example'}).status_code == 403
        assert c.post('/api/comparisons/text', json={},
                      headers=public | {'Origin': 'https://evil.example'}).status_code == 403
        assert c.post('/api/comparisons/text', json={},
                      headers=public | {'Sec-Fetch-Site': 'cross-site'}).status_code == 403


def test_the_editorial_workbench_stays_local_only(tmp_path, monkeypatch):
    monkeypatch.setenv('JUDGE_PUBLIC_HOSTS', 'app.kitabs.ai')
    with TestClient(create_app(tmp_path)) as c:
        assert c.post('/api/editorial', json={}, headers={'Host': 'app.kitabs.ai'}).status_code == 403
        assert c.get('/api/editorial/x', headers={'Host': 'app.kitabs.ai'}).status_code == 403


def test_without_public_hosts_only_loopback_is_accepted(tmp_path, monkeypatch):
    monkeypatch.delenv('JUDGE_PUBLIC_HOSTS', raising=False)
    with TestClient(create_app(tmp_path)) as c:
        assert c.get('/api/examples', headers={'Host': 'app.kitabs.ai'}).status_code == 403
