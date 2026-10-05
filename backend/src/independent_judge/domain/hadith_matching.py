"""Conservative retrieval of hadith quotations in Arabic collections; not a religious ruling."""
from collections import Counter
from difflib import SequenceMatcher
from independent_judge.domain.arabic_text import folded, normalized

NEGATIONS = {'لا', 'ليس', 'لم', 'لن', 'ما'}
FOUND = ('exact', 'normalized', 'fragment', 'ambiguous', 'review')
_RANK = {'exact': 0, 'normalized': 1, 'fragment': 2, 'review': 3}


class HadithIndex:
    """Records are folded once; each quotation is compared with every record."""

    FUZZY_LIMIT = 30

    def __init__(self, records: list[dict]):
        self.entries = []
        frequency = Counter()
        for record in records:
            text = folded(record['text'])
            words = set(text.split())
            frequency.update(words)
            self.entries.append((record, text, ' ' + text + ' ', words))
        # Words in more than 3% of records (isnad formulas, particles) do not select candidates.
        self.common = {w for w, n in frequency.items() if n > max(3, .03 * len(records))}

    @staticmethod
    def _correspondence(quote: str, record: dict, text: str, padded: str, words: set, qwords: list) -> tuple[str, float]:
        if quote == record['text']:
            return 'exact', 1.0
        if normalized(quote) == normalized(record['text']):
            return 'normalized', 1.0
        q = ' '.join(qwords)
        at = padded.find(' ' + q + ' ')
        if at >= 0:
            preceding = padded[:at].split()
            if preceding and preceding[-1] in NEGATIONS:
                return 'review', .99
            return 'fragment', 1.0
        if len(set(qwords) & words) / len(set(qwords)) < .65:
            return 'not_found', 0
        twords = text.split()
        block = SequenceMatcher(None, qwords, twords, autojunk=False).find_longest_match()
        start = max(0, block.b - block.a)
        score = max(SequenceMatcher(None, qwords, twords[max(0, start + d):start + len(qwords) + 2],
                                    autojunk=False).ratio() for d in (-2, -1, 0))
        return ('review', score) if score >= .65 else ('not_found', 0)

    def match(self, quote: str) -> dict:
        qwords = folded(quote).split()
        if not qwords:
            return {'status': 'not_found', 'candidate_count': 0, 'candidates': []}
        q = ' ' + ' '.join(qwords) + ' '
        selective = set(qwords) - self.common or set(qwords)
        candidates, fuzzy = [], []
        for record, text, padded, words in self.entries:
            if q in padded or quote == record['text']:
                state, score = self._correspondence(quote, record, text, padded, words, qwords)
                candidates.append(record | {'match': state, 'similarity': round(score, 3)})
            else:
                overlap = len(selective & words) / len(selective)
                if overlap >= .65:
                    fuzzy.append((overlap, record, text, padded, words))
        fuzzy.sort(key=lambda f: -f[0])
        for _, record, text, padded, words in fuzzy[:self.FUZZY_LIMIT]:
            state, score = self._correspondence(quote, record, text, padded, words, qwords)
            if state != 'not_found':
                candidates.append(record | {'match': state, 'similarity': round(score, 3)})
        candidates.sort(key=lambda c: (_RANK[c['match']], -c['similarity'], str(c['id'])))
        exact = [c for c in candidates if c['match'] in ('exact', 'normalized', 'fragment')]
        status = ('ambiguous' if len(exact) > 1 else exact[0]['match'] if exact else
                  'review' if candidates else 'not_found')
        return {'status': status, 'candidate_count': len(candidates), 'candidates': (exact or candidates)[:3]}

def correspondence(quote: str, text: str) -> tuple[str, float]:
    """Compare one quotation with one known text (used for official API records)."""
    folded_text = folded(text)
    return HadithIndex._correspondence(quote, {'text': text}, folded_text, ' ' + folded_text + ' ',
                                       set(folded_text.split()), folded(quote).split())
