"""Automatic source matching is evidence retrieval, never an authenticity verdict."""
import httpx
import pytest

QUOTE = 'لا يؤمن أحدكم حتى يحب لأخيه ما يحب لنفسه'


def test_quote_detection_and_matching_preserve_negation_and_source_coordinates():
    from independent_judge.domain.hadith_matching import HadithIndex
    from independent_judge.domain.reference_detection import detect_references
    text = f'قال رسول الله ﷺ: «{QUOTE}».'
    found = detect_references(text)
    assert len(found) == 1 and text[found[0]['start']:found[0]['end']] == QUOTE
    index = HadithIndex([{'id': 'bukhari:13', 'text': QUOTE, 'url': 'https://example.org/13'}])
    assert index.match(QUOTE)['status'] == 'exact'
    changed = index.match(QUOTE.replace('لا ', ''))
    assert changed['status'] == 'review'
    assert changed['candidates'][0]['id'] == 'bukhari:13'


def test_diacritics_are_normalized_but_partial_and_ambiguous_matches_stay_explicit():
    from independent_judge.domain.hadith_matching import HadithIndex
    from independent_judge.domain.reference_detection import detect_references
    one = HadithIndex([{'id': 'one', 'text': QUOTE}])
    assert one.match('لَا يؤمن أحدكم حتى يحب لأخيه ما يحب لنفسه')['status'] == 'normalized'
    assert one.match('حتى يحب لأخيه ما يحب لنفسه')['status'] == 'fragment'
    assert HadithIndex([{'id': 'one', 'text': QUOTE}, {'id': 'two', 'text': QUOTE}]).match(QUOTE)['status'] == 'ambiguous'
    assert one.match('من جد وجد ومن زرع حصد')['status'] == 'not_found'
    assert [r['kind'] for r in detect_references('﴿قل هو الله أحد﴾')] == ['quran']


def test_adapter_fetches_fixed_editions_without_sending_private_text_and_caches(tmp_path):
    from independent_judge.infrastructure.hadith_library import HadithLibrary
    calls = []
    def respond(request):
        calls.append(str(request.url))
        return httpx.Response(200, json={'metadata': {'name': 'Sahih al Bukhari'}, 'hadiths': [
            {'hadithnumber': 13, 'text': QUOTE, 'grades': [], 'reference': {'book': 2, 'hadith': 6}}]})
    library = HadithLibrary(tmp_path, collections=('bukhari',), transport=httpx.MockTransport(respond))
    records = library.records()
    assert records[0]['id'] == 'bukhari:13'
    assert records[0]['text'] == QUOTE
    assert records[0]['url'].endswith('/ara-bukhari/13.json')
    assert len(records[0]['snapshot_sha256']) == 64
    assert records[0]['retrieved_at']
    assert library.records() == records
    assert len(calls) == 1
    assert calls[0].endswith('/editions/ara-bukhari.json')


@pytest.mark.parametrize('body', [{'hadiths': []}, {'hadiths': [{'hadithnumber': 1, 'text': ''}]}, {'oops': 1}])
def test_adapter_rejects_invalid_records_without_writing_success_cache(tmp_path, body):
    from independent_judge.infrastructure.hadith_library import HadithLibrary
    from independent_judge.reference_ports import LibraryUnavailable
    library = HadithLibrary(tmp_path, collections=('bukhari',), transport=httpx.MockTransport(
        lambda request: httpx.Response(200, json=body)))
    with pytest.raises(LibraryUnavailable): library.records()
    assert not list(tmp_path.rglob('*.json'))


def test_library_outage_is_not_a_negative_hadith_verdict(tmp_path):
    from independent_judge.application.reference_verification import verify_references
    from independent_judge.infrastructure.hadith_library import HadithLibrary
    library = HadithLibrary(tmp_path, collections=('bukhari',), transport=httpx.MockTransport(
        lambda request: httpx.Response(503)))
    class Quran:
        def verses(self): return [{'chapter': 1, 'verse': 1, 'text': 'بسم الله الرحمن الرحيم'}]
    result = verify_references({'source': f'«{QUOTE}»', 'a': 'Translation A', 'b': 'Translation B'}, Quran(), library)
    assert result['status'] == 'unavailable'
    assert result['hadith'] is None
    assert result['translation_accuracy'] == 'not_assessed'


def test_fractional_edition_ids_and_empty_records_are_reported_not_renumbered(tmp_path):
    from independent_judge.infrastructure.hadith_library import HadithLibrary
    library = HadithLibrary(tmp_path, collections=('bukhari',), transport=httpx.MockTransport(
        lambda request: httpx.Response(200, json={'hadiths': [
            {'hadithnumber': 402.2, 'text': QUOTE}, {'hadithnumber': 403, 'text': ''}]})))
    rows = library.records()
    assert len(rows) == 1
    assert rows[0]['id'] == 'bukhari:402.2'
    assert rows[0]['url'].endswith('/402.2.json')
    assert rows[0]['omitted_empty_records'] == 1
def test_parenthesized_arabic_citations_are_candidates_and_quran_brackets_are_quran():
    from independent_judge.domain.reference_detection import detect_references
    source = f'وقال صلى الله عليه وسلم ({QUOTE}) ثم قال ﴿قل هو الله أحد﴾ ((رواه مسلم والترمذي وقال حديث حسن))'
    detected = detect_references(source)
    assert [(r['kind'], r['quote']) for r in detected] == [('quoted', QUOTE), ('quran', 'قل هو الله أحد')]
    assert source[detected[0]['start']:detected[0]['end']] == QUOTE
