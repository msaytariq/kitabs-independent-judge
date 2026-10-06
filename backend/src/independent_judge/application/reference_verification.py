"""Count Quran verses and hadith of the source that the reference texts contain."""
import re
from independent_judge.domain.hadith_matching import HadithIndex, FOUND
from independent_judge.domain.quran_matching import QuranIndex, label_check, verse_quoted
from independent_judge.domain.takhrij_check import takhrij_check
from independent_judge.domain.reference_detection import detect_references
from independent_judge.reference_ports import LibraryUnavailable

LIMIT = 40


def verify_references(texts: dict[str, str], quran_library, hadith_library, *, quran_index=None, hadith_index=None) -> dict:
    source = texts['source']
    detected = detect_references(source)
    try:
        quran = quran_index or QuranIndex(quran_library.verses())
        hadith = hadith_index or HadithIndex(hadith_library.records())
    except LibraryUnavailable:
        detected = detected[:LIMIT]
        return {'detected_count': len(detected), 'translation_accuracy': 'not_assessed',
                'authenticity': 'not_adjudicated', 'limit_reached': False,
                'status': 'unavailable', 'quran': None, 'hadith': None}
    # A verse quoted without brackets or formula is found by its words in Quran order.
    taken = [(d['start'], d['end']) for d in detected]
    detected += [{'kind': 'quran', 'marked': True, 'quote': source[s:e], 'start': s, 'end': e}
                 for s, e in quran.scan(source) if not any(s < te and ts < e for ts, te in taken)]
    detected.sort(key=lambda d: d['start'])
    base = {'detected_count': min(len(detected), LIMIT), 'translation_accuracy': 'not_assessed',
            'authenticity': 'not_adjudicated', 'limit_reached': len(detected) > LIMIT}
    detected = detected[:LIMIT]
    ayat, reports = [], []
    previous = None  # (end in the source, verse) of the last verse found
    for item in detected:
        unmarked_verse = item['kind'] == 'quran' and not item['marked']
        near = previous if previous and item['start'] - previous[0] <= 30 else None
        located = quran.locate(item['quote'], anchored=unmarked_verse, prefer=near and near[1])
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
            if located and located.get('verse_text'):
                previous = (item['end'], {'chapter': located['surah'], 'verse': int(located['ayah'].split(':')[1]),
                                          'text': located['verse_text']})
        else:
            reports.append({k: item[k] for k in ('quote', 'start', 'end')} | hadith.match(item['quote']))
    found = [r for r in reports if r['status'] in FOUND]
    found_in = {c['id'].split(':', 1)[0] for r in found for c in r['candidates'] if ':' in str(c.get('id'))}
    takhrij = takhrij_check(source, texts, [a['ayah'] for a in ayat if a['status'] == 'found'],
                            _lookup(hadith_library), verse_quoted(quran, source), found_in=found_in)
    by_collection = {}
    for report in found:
        name = report['candidates'][0].get('collection', '')
        by_collection[name] = by_collection.get(name, 0) + 1
    return base | {'status': 'checked',
                   'quran': {'found': sum(a['status'] == 'found' for a in ayat), 'total': len(ayat), 'items': ayat,
                             'label_differs': sum(a['label_status'] == 'label_differs' for a in ayat)},
                   'hadith': {'found': len(found), 'total': len(reports), 'items': reports, 'by_collection': by_collection},
                   'takhrij': takhrij}


def _lookup(library):
    """A library that cannot open a number leaves the reference unchecked, never wrong."""
    def lookup(collection, number):
        try:
            return library.lookup(collection, number) if hasattr(library, 'lookup') else None
        except LibraryUnavailable:
            return None
    return lookup
