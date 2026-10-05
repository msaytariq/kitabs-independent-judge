"""Official Sunnah records need key, exact identity and attributed grades."""
import httpx
import pytest
from test_hadith_verification import QUOTE


def response(number='13'):
    return {'collection':'bukhari','bookNumber':'2','chapterId':'6','hadithNumber':number,
            'hadith':[{'lang':'ar','urn':13,'body':f'<p>{QUOTE}</p>','grades':[]},
                      {'lang':'en','urn':14,'body':'<p>None of you believes until…</p>',
                       'grades':[{'graded_by':'Named scholar','grade':'Sahih'}]}]}


def test_official_record_keeps_both_languages_and_grading_attribution():
    from independent_judge.infrastructure.sunnah_source import SunnahSource
    def handler(request):
        assert str(request.url)=='https://api.sunnah.com/v1/collections/bukhari/hadiths/13'
        assert request.headers['x-api-key']=='test-only'
        return httpx.Response(200,json=response())
    record=SunnahSource('test-only',transport=httpx.MockTransport(handler)).lookup('bukhari','13')
    assert record['text']==QUOTE
    assert record['english_text']=='None of you believes until…'
    assert record['grade']=='Named scholar: Sahih'
    assert record['url']=='https://sunnah.com/bukhari:13'
    assert len(record['snapshot_sha256'])==64


def test_wrong_number_or_unavailable_key_never_confirms_source():
    from independent_judge.infrastructure.sunnah_source import SunnahSource
    from independent_judge.reference_ports import LibraryUnavailable
    source=SunnahSource('private',transport=httpx.MockTransport(lambda r:httpx.Response(200,json=response('14'))))
    with pytest.raises(LibraryUnavailable):source.lookup('bukhari','13')
    with pytest.raises(LibraryUnavailable):SunnahSource('').lookup('bukhari','13')


def test_source_http_failure_never_echoes_key_or_response_body():
    from independent_judge.infrastructure.sunnah_source import SunnahSource
    from independent_judge.reference_ports import LibraryUnavailable
    source=SunnahSource('private',transport=httpx.MockTransport(lambda r:httpx.Response(401,text='private')))
    with pytest.raises(LibraryUnavailable) as exc:source.lookup('bukhari','13')
    assert 'private' not in str(exc.value)


def test_portable_report_includes_official_source_and_its_qualification():
    from independent_judge.application.comparison_view import _view
    from independent_judge.infrastructure.comparison_report import comparison_html
    from test_comparison_summary import record
    data = record() | {'hadith': {'status': 'checked',
        'quran': {'found': 0, 'total': 0, 'label_differs': 0, 'items': []},
        'hadith': {'found': 0, 'total': 0, 'by_collection': {}, 'items': []}, 'official': {'source': 'Sunnah.com', 'status': 'checked', 'records': [
            {'quote': QUOTE, 'status': 'review', 'record': {
                'text': '<script>bad</script>', 'english_text': 'Reference translation',
                'grade': 'Named scholar: Sahih', 'url': 'https://sunnah.com/bukhari:13',
                'snapshot_sha256': 'a'*64, 'retrieved_at': '2026-10-04'}}]}}}
    html = comparison_html(_view(data))
    assert 'https://sunnah.com/bukhari:13' in html
    assert 'Named scholar: Sahih' in html
    assert 'Близкий текст с расхождениями' in html
    assert '<script>bad</script>' not in html


def test_official_lookup_does_not_confirm_matching_number_with_different_text():
    from independent_judge.application.sunnah_verification import verify_official
    class Source:
        def lookup(self, collection, number):
            return {'text': 'هذا نص مختلف تماما لا يشبه النص المطلوب'}
    result = verify_official([{'quote': QUOTE, 'candidates': [{'id': 'bukhari:13'}]}], Source())
    assert result['records'][0]['status'] == 'not_found'


def test_official_outage_and_truncated_lookup_are_visible():
    from independent_judge.application.sunnah_verification import verify_official
    from independent_judge.reference_ports import LibraryUnavailable
    class Source:
        def lookup(self, collection, number): raise LibraryUnavailable('offline')
    result = verify_official([{'quote': QUOTE, 'candidates': [
        {'id': f'bukhari:{n}'} for n in range(12)]}], Source())
    assert result['status'] == 'unavailable'
    assert result['limit_reached'] is True
    assert result['lookups'] == 10
