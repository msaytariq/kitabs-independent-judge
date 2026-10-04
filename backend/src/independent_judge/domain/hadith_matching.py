"""Conservative local retrieval of Arabic quotations; not a religious ruling."""
from difflib import SequenceMatcher
import re
import unicodedata

NEGATIONS = {'لا', 'ليس', 'لم', 'لن', 'ما'}


def normalized(text: str) -> str:
    chars = []
    for char in unicodedata.normalize('NFC', text):
        if char == 'ـ' or (unicodedata.category(char) == 'Mn' and 'ARABIC' in unicodedata.name(char, '')):
            continue
        chars.append(' ' if unicodedata.category(char).startswith('P') else char)
    return ' '.join(''.join(chars).split())


def quotations(source: str) -> list[dict]:
    # Quran brackets are deliberately excluded. Unmarked prose is not silently
    # claimed to have been fully scanned for hadiths.
    results = []
    for match in re.finditer(r'«([^«»]{10,2000})»|“([^“”]{10,2000})”|"([^"\n]{10,2000})"|\(([^()]{10,2000})\)', source):
        group = next(i for i in (1, 2, 3, 4) if match.group(i) is not None)
        quote = match.group(group)
        if re.search(r'[\u0621-\u064a]', quote) and len(normalized(quote).split()) >= 3:
            results.append({'quote': quote, 'start': match.start(group), 'end': match.end(group)})
    return results


def correspondence(quote: str, text: str) -> tuple[str, float]:
    q, t = normalized(quote), normalized(text)
    if quote == text: return 'exact', 1.0
    if q == t: return 'normalized', 1.0
    at = (' ' + t + ' ').find(' ' + q + ' ')
    if at >= 0:
        preceding = t[:at].split()
        if preceding and preceding[-1] in NEGATIONS:
            return 'review', .99
        return 'fragment', 1.0
    qwords, twords = q.split(), t.split()
    if not qwords or len(set(qwords) & set(twords)) / len(set(qwords)) < .65:
        return 'not_found', 0
    # Compare a local window, not an entire isnad + matn against a short quote.
    block = SequenceMatcher(None, qwords, twords, autojunk=False).find_longest_match()
    start = max(0, block.b - block.a)
    score = max(SequenceMatcher(None, qwords, twords[max(0, start+d):start+len(qwords)+2],
                                autojunk=False).ratio() for d in (-2, -1, 0))
    return ('review', score) if score >= .65 else ('not_found', 0)


def match_hadiths(source: str, records: list[dict]) -> list[dict]:
    result = []
    for quote in quotations(source)[:30]:
        candidates = []
        for record in records:
            state, score = correspondence(quote['quote'], record['text'])
            if state != 'not_found':
                candidates.append(record | {'match': state, 'similarity': round(score, 3)})
        candidates.sort(key=lambda c: (-c['similarity'], c['id']))
        exact = [c for c in candidates if c['match'] in ('exact', 'normalized', 'fragment')]
        status = ('ambiguous' if len(exact) > 1 else exact[0]['match'] if exact else
                  'review' if candidates else 'not_found')
        result.append(quote | {'status': status, 'candidate_count': len(candidates),
                              'candidates': (exact or candidates)[:3]})
    return result
