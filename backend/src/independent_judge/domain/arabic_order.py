"""Repair of an Arabic PDF text layer that stores each lam-alef pair in reverse order.

Some PDF producers draw lam-alef as one glyph and store its letters in visual order: "الأول"
reads "األول", "لا" reads "ال", "الصلاة" reads "الصالة", "لله" reads "هلل". Such a text has
almost no lam before an alef. A pair of an alef and a lam can be a reversed lam-alef or a real
alef-lam ("قال", the article), so a word changes only when a word list of correct Arabic
(the Quran and the hadith collections) knows the repaired word and does not know the word as it
stands. A frequent word decides; a hamza alef after an alef cannot occur in a correct word.
"""
from itertools import combinations
import re
from typing import Callable
from independent_judge.domain.arabic_text import folded

_REVERSED = re.compile(r'[اأإآ]ل')
_CORRECT = re.compile(r'ل[اأإآ]')
_IMPOSSIBLE = re.compile(r'ا[أإآ]')
_ARTICLE = re.compile(r'ا([أإآ])ل')
_LILLAH = re.compile(r'[وف]?هلل')
_WORD = re.compile(r'[ء-ي]+')
MIN_PAIRS = 50          # enough Arabic to judge the whole text
MAX_CORRECT_SHARE = 0.02
MIN_FREQUENCY = 10      # a rarer word in the list does not replace a word of the text


def reversed_lam_alef(text: str) -> bool:
    text = text.replace('هللا', ' ')  # the reversed Allah ligature ends in lam-alef; it is not a correct pair
    reversed_pairs, correct = len(_REVERSED.findall(text)), len(_CORRECT.findall(text))
    return reversed_pairs >= MIN_PAIRS and correct <= MAX_CORRECT_SHARE * reversed_pairs


def _candidates(word: str):
    word = word.replace('هلل', 'لله')
    spots = [m.start() for m in _REVERSED.finditer(word)]
    yield word
    for size in range(1, len(spots) + 1):
        for chosen in combinations(spots, size):
            letters = list(word)
            for i in chosen:
                letters[i], letters[i + 1] = letters[i + 1], letters[i]
            yield ''.join(letters)


def _repair_word(word: str, known: Callable[[str], int]) -> str:
    if word == 'ال':
        return 'لا'  # the article never stands alone
    word = word.replace('هللا', 'الله')  # the Allah ligature, as the Kitabs intake repairs it
    if _LILLAH.fullmatch(word):
        return word[:-3] + 'لله'  # "الحمد هلل": in a reversed text the rare verb "هلّل" yields to "لله"
    if known(word):
        return word
    found = [c for c in _candidates(word) if c != word and known(c)]
    if found:
        best = max(found, key=known)
        if _IMPOSSIBLE.search(word) or known(best) >= MIN_FREQUENCY:
            return best
    # An alef before a hamza alef and lam is always the article with a reversed lam-alef.
    return _ARTICLE.sub(r'ال\1', word)


def repair_lam_alef(text: str, known: Callable[[str], int]) -> str:
    """known(word) -> how often a list of correct Arabic has the word (0 when absent)."""
    if not reversed_lam_alef(text):
        return text
    return _WORD.sub(lambda m: _repair_word(m.group(), known), text)
