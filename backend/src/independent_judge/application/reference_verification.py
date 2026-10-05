"""Count Quran verses and hadith of the source that the reference texts contain."""
import re
from independent_judge.domain.hadith_matching import HadithIndex, FOUND
from independent_judge.domain.quran_matching import QuranIndex, label_check
from independent_judge.domain.reference_detection import detect_references
from independent_judge.reference_ports import LibraryUnavailable

LIMIT = 40


def verify_references(texts: dict[str, str], quran_library, hadith_library, *, quran_index=None, hadith_index=None) -> dict:
    source = texts['source']
    detected = detect_references(source)[:LIMIT]
    base = {'detected_count': len(detected), 'translation_accuracy': 'not_assessed',
            'authenticity': 'not_adjudicated', 'limit_reached': len(detect_references(source)) > LIMIT}
    try:
        quran = quran_index or QuranIndex(quran_library.verses())
        hadith = hadith_index or HadithIndex(hadith_library.records())
    except LibraryUnavailable:
        return base | {'status': 'unavailable', 'quran': None, 'hadith': None}
    ayat, reports = [], []
    for item in detected:
        unmarked_verse = item['kind'] == 'quran' and not item['marked']
        located = quran.locate(item['quote'], anchored=unmarked_verse)
        if unmarked_verse and not located:
            continue  # the formula was not followed by a verse
        is_quran = item['kind'] == 'quran' or (
            item['kind'] == 'quoted' and located
            and (located['matched_words'] == located['quote_words']
                 or (located['matched_words'] >= 4 and located['matched_words'] >= .8 * located['quote_words'])))
        if is_quran:
            if unmarked_verse:  # keep only the words that are the verse, not the rest of the sentence
                tokens = [m for m in re.finditer(r'\S*[\u0621-\u064a]\S*', item['quote'])]
                last = tokens[min(len(tokens), located['first_word'] + located['matched_words']) - 1]
                item = item | {'quote': item['quote'][:last.end()], 'end': item['start'] + last.end()}
            entry = {k: item[k] for k in ('quote', 'start', 'end')} | {
                'status': 'found' if located else 'not_found', **(located or {})}
            ayat.append(entry | label_check(source, item['end'], located))
        else:
            reports.append({k: item[k] for k in ('quote', 'start', 'end')} | hadith.match(item['quote']))
    found = [r for r in reports if r['status'] in FOUND]
    by_collection = {}
    for report in found:
        name = report['candidates'][0].get('collection', '')
        by_collection[name] = by_collection.get(name, 0) + 1
    return base | {'status': 'checked',
                   'quran': {'found': sum(a['status'] == 'found' for a in ayat), 'total': len(ayat), 'items': ayat,
                             'label_differs': sum(a['label_status'] == 'label_differs' for a in ayat)},
                   'hadith': {'found': len(found), 'total': len(reports), 'items': reports, 'by_collection': by_collection}}
