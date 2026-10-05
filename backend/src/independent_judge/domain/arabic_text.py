"""Arabic comparison forms: diacritics, tatweel and letter variants do not decide a match."""
import unicodedata

_FOLD = str.maketrans({'أ': 'ا', 'إ': 'ا', 'آ': 'ا', 'ٱ': 'ا', 'ى': 'ي', 'ة': 'ه'})


def normalized(text: str) -> str:
    """Remove Arabic marks and punctuation; keep letters as written."""
    chars = []
    for char in unicodedata.normalize('NFC', text):
        if char == 'ـ' or (unicodedata.category(char) == 'Mn' and 'ARABIC' in unicodedata.name(char, '')):
            continue
        category = unicodedata.category(char)
        chars.append(char if category[0] in 'LN' else ' ')
    return ' '.join(''.join(chars).split())


def folded(text: str) -> str:
    """Normalized text with alef, ya and ta marbuta variants unified for retrieval."""
    return normalized(text).translate(_FOLD)
