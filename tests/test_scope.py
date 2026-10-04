"""Manual scope is explicit, symmetric, immutable and bound to original text."""
from fastapi.testclient import TestClient
import pytest
from independent_judge.api.app import create_app


def draft(c, swap=False):
    return c.post('/api/comparisons/text', json={
        'source': 'مقدمة\n\nالنص الأصلي\n\nنهاية',
        'a': 'Intro.\n\nSame passage.\n\nSame passage.',
        'b': 'Opening.\n\nOther passage.\n\nEnd.',
        'source_language': 'ar', 'target_language': 'en',
    } | ({'a': 'Opening.\n\nOther passage.\n\nEnd.',
          'b': 'Intro.\n\nSame passage.\n\nSame passage.'} if swap else {})).json()


def selection(d):
    return {'profile': 'islamic-scholarly', 'confirmed': True, 'ranges': {
        role: {'start': 0, 'end': len(m['text']), 'text_sha256': m['sha256']}
        for role, m in d['materials'].items()}}


def test_scope_preview_persists_and_swaps_symmetrically(tmp_path):
    with TestClient(create_app(tmp_path)) as c:
        d, swapped = draft(c), draft(c, True)
        x = c.post(f"/api/comparisons/{d['id']}/scopes", json=selection(d))
        assert x.status_code == 201, x.text
        x = x.json()
        y = c.post(f"/api/comparisons/{swapped['id']}/scopes", json=selection(swapped)).json()
        assert x['status'] == y['status'] == 'ready'
        assert x['texts']['a'] == y['texts']['b']
        assert x['hashes']['a'] == y['hashes']['b']
        assert x['texts']['source'] == d['materials']['source']['text']
        assert x['profile'] == 'islamic-scholarly'
        assert x['sampling_version'] == 'manual-codepoints-v1'
    with TestClient(create_app(tmp_path)) as c:
        assert c.get(f"/api/scopes/{x['id']}").json() == x


@pytest.mark.parametrize('field,value', [('text_sha256', '0'*64), ('start', -1), ('end', 99999), ('start', True)])
def test_stale_or_invalid_range_is_blocked(tmp_path, field, value):
    with TestClient(create_app(tmp_path)) as c:
        d = draft(c)
        request = selection(d)
        request['ranges']['b'][field] = value
        assert c.post(f"/api/comparisons/{d['id']}/scopes", json=request).status_code == 422


def test_unconfirmed_alignment_needs_review_even_with_repeated_text(tmp_path):
    with TestClient(create_app(tmp_path)) as c:
        d = draft(c)
        request = selection(d) | {'confirmed': False}
        response = c.post(f"/api/comparisons/{d['id']}/scopes", json=request)
        assert response.status_code == 201
        assert response.json()['status'] == 'needs_review'
        # A repeated phrase is selected by its exact offset, never by a guessed match.
        request['confirmed'] = True
        request['ranges']['a'].update(start=8, end=21)
        confirmed = c.post(f"/api/comparisons/{d['id']}/scopes", json=request).json()
        assert confirmed['texts']['a'] == 'Same passage.'
        assert confirmed['ranges']['a']['start'] == 8


def test_unknown_profile_and_oversized_source_rejected(tmp_path):
    with TestClient(create_app(tmp_path)) as c:
        d = draft(c)
        assert c.post(f"/api/comparisons/{d['id']}/scopes", json=selection(d) | {'profile': 'brand-wins'}).status_code == 422
        d = c.post('/api/comparisons/text', json={'source':'x'*18001, 'a':'one', 'b':'two', 'source_language':'en','target_language':'en'}).json()
        assert c.post(f"/api/comparisons/{d['id']}/scopes", json=selection(d)).status_code == 422
