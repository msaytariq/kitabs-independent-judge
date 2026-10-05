import pytest
from independent_judge.domain.errors import InputError


def fetcher(responses, *, addresses=('93.184.216.34',)):
    from independent_judge.infrastructure.url_retrieval import UrlRetriever
    visited = []
    def request(url, address, limit, timeout):
        visited.append((url, address))
        response = responses.pop(0)
        if isinstance(response, Exception): raise response
        return response
    return UrlRetriever(resolve=lambda host: addresses, request=request), visited


def test_public_document_preserves_bytes_hash_and_retrieval_provenance():
    retriever, visited = fetcher([(200, {'content-type':'text/plain'}, b'Full translation.\n[1] Note.')])
    result = retriever.fetch('https://example.org/translation.txt')
    assert result.content == b'Full translation.\n[1] Note.'
    assert result.filename == 'translation.txt'
    assert len(result.provenance['sha256']) == 64
    assert result.provenance['source_url'] == 'https://example.org/translation.txt'
    assert result.provenance['retrieved_at']
    assert visited[0][1] == '93.184.216.34'


@pytest.mark.parametrize('url,addresses', [
    ('http://localhost/test', ('127.0.0.1',)),
    ('https://private.test/a', ('10.0.0.1',)),
    ('https://private.test/a', ('::1',)),
    ('https://mixed.test/a', ('93.184.216.34','192.168.1.1')),
    ('file:///etc/passwd', ()),
    ('https://user:password@example.org/a', ('93.184.216.34',)),
])
def test_private_destinations_and_credentials_are_rejected(url, addresses):
    retriever, visited = fetcher([], addresses=addresses)
    with pytest.raises(InputError): retriever.fetch(url)
    assert not visited


def test_redirect_target_is_revalidated_before_any_private_connection():
    retriever, visited = fetcher([(302, {'location':'http://127.0.0.1/private'}, b'')])
    retriever.resolve = lambda host: ('127.0.0.1',) if host == '127.0.0.1' else ('93.184.216.34',)
    with pytest.raises(InputError): retriever.fetch('https://example.org/a')
    assert len(visited) == 1


@pytest.mark.parametrize('response,code', [
    ((200, {'content-type':'image/png'}, b'png'), 'unsupported_url_content'),
    ((200, {'content-type':'text/plain'}, b'x' * (20*1024*1024+1)), 'file_too_large'),
    (TimeoutError(), 'url_unavailable'),
    ((403, {}, b'blocked'), 'url_unavailable'),
])
def test_fetch_failures_are_explicit(response, code):
    retriever, _ = fetcher([response])
    with pytest.raises(InputError) as caught: retriever.fetch('https://example.org/a')
    assert caught.value.code == code


def test_html_extracts_readable_content_without_scripts_and_keeps_notes():
    from independent_judge.infrastructure.text_extractors import LocalTextExtractor
    text = LocalTextExtractor().extract(b'<html><script>bad()</script><h1>Translation</h1><p>Claim.</p><p>[1] Note.</p></html>', 'page.html', 'text/html').text
    assert 'bad()' not in text
    assert 'Claim.' in text and '[1] Note.' in text


def test_mixed_intake_saves_url_provenance_and_rejects_partial_triples(tmp_path):
    from fastapi.testclient import TestClient
    from independent_judge.api.app import create_app
    retriever, _ = fetcher([(200, {'content-type':'text/plain'}, b'Translation A.')])
    with TestClient(create_app(tmp_path, retriever=retriever)) as client:
        result = client.post('/api/comparisons/mixed', data={
            'source_kind':'text', 'source_value':'Arabic source.',
            'a_kind':'url', 'a_value':'https://example.org/a.txt', 'b_kind':'file',
            'source_language':'ar', 'target_language':'en'},
            files={'b':('b.txt',b'Translation B.','text/plain')})
        assert result.status_code == 201, result.text
        saved = client.get('/api/comparisons/' + result.json()['id']).json()
        assert saved['materials']['a']['provenance']['final_url'] == 'https://example.org/a.txt'
        assert saved['materials']['b']['text'] == 'Translation B.'
        assert client.post('/api/comparisons/mixed', data={'source_kind':'text'}).status_code == 422
