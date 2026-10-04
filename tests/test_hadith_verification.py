"""Automatic source matching is evidence retrieval, never an authenticity verdict."""
import httpx
import pytest

QUOTE = 'لا يؤمن أحدكم حتى يحب لأخيه ما يحب لنفسه'


def test_quote_detection_and_matching_preserve_negation_and_source_coordinates():
    from independent_judge.domain.hadith_matching import match_hadiths
    text = f'قال رسول الله ﷺ: «{QUOTE}».'
    records = [{'id': 'bukhari:13', 'text': QUOTE, 'url': 'https://example.org/13'}]
    result = match_hadiths(text, records)
    assert len(result) == 1
    item = result[0]
    assert text[item['start']:item['end']] == QUOTE
    assert item['status'] == 'exact'
    changed = match_hadiths(text.replace('لا ', ''), records)[0]
    assert changed['status'] == 'review'
    assert changed['candidates'][0]['id'] == 'bukhari:13'


def test_diacritics_are_normalized_but_partial_and_ambiguous_matches_stay_explicit():
    from independent_judge.domain.hadith_matching import match_hadiths
    records = [{'id': 'one', 'text': QUOTE}]
    assert match_hadiths(f'«لَا يؤمن أحدكم حتى يحب لأخيه ما يحب لنفسه»', records)[0]['status'] == 'normalized'
    assert match_hadiths('«حتى يحب لأخيه ما يحب لنفسه»', records)[0]['status'] == 'fragment'
    records.append({'id': 'two', 'text': QUOTE})
    assert match_hadiths(f'«{QUOTE}»', records)[0]['status'] == 'ambiguous'
    assert match_hadiths('«من جد وجد ومن زرع حصد»', records)[0]['status'] == 'not_found'
    assert match_hadiths('﴿قل هو الله أحد﴾', records) == []


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
    from independent_judge.application.hadith_verification import verify_hadiths
    from independent_judge.infrastructure.hadith_library import HadithLibrary
    library = HadithLibrary(tmp_path, collections=('bukhari',), transport=httpx.MockTransport(
        lambda request: httpx.Response(503)))
    result = verify_hadiths({'source': f'«{QUOTE}»', 'a': 'Translation A', 'b': 'Translation B'}, library)
    assert result['status'] == 'unavailable'
    assert result['verified_count'] is None
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
def test_parenthesized_arabic_citations_are_candidates_but_quran_brackets_are_not():
    from independent_judge.domain.hadith_matching import quotations
    source = f'وقال صلى الله عليه وسلم ({QUOTE}) ثم قال ﴿قل هو الله أحد﴾'
    detected = quotations(source)
    assert len(detected) == 1
    assert detected[0]['quote'] == QUOTE
    assert source[detected[0]['start']:detected[0]['end']] == QUOTE
