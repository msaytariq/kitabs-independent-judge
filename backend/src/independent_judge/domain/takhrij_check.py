"""Takhrij accuracy: do the references of a translation agree with the source and the libraries?

The source gives the units: each Quran verse that it quotes, each hadith collection that it names
and each numbered hadith reference. A translation delivers a unit when it gives the same reference.
A reference that the source does not support is wrong: a verse that the source does not quote, a
hadith number whose text is not in the source, or a collection that the source does not name.
No model takes part; a reference that no library can open stays unchecked.
"""
import re
import unicodedata
from independent_judge.domain.arabic_text import folded
from independent_judge.domain.hadith_matching import correspondence
from independent_judge.domain.reference_detection import detect_references

VERSION = 'takhrij-v1'
NAMES = {'bukhari': 'Sahih al-Bukhari', 'muslim': 'Sahih Muslim', 'abudawud': 'Sunan Abi Dawud',
         'tirmidhi': "Jami' at-Tirmidhi", 'nasai': "Sunan an-Nasa'i", 'ibnmajah': 'Sunan Ibn Majah',
         'malik': 'Muwatta Malik', 'ahmad': 'Musnad Ahmad', 'hakim': 'al-Mustadrak of al-Hakim',
         'bayhaqi': 'al-Bayhaqi', 'tabarani': 'at-Tabarani', 'ibnhibban': 'Sahih Ibn Hibban',
         'darimi': 'Sunan ad-Darimi', 'daraqutni': 'Sunan ad-Daraqutni'}
_FOUND = ('exact', 'normalized', 'fragment', 'review')

# Arabic: folded word sequences after an attribution verb.
_AR_NAMES = {('البخاري',): 'bukhari', ('مسلم',): 'muslim', ('ابو', 'داود'): 'abudawud', ('ابي', 'داود'): 'abudawud',
             ('الترمذي',): 'tirmidhi', ('النسائي',): 'nasai', ('ابن', 'ماجه'): 'ibnmajah', ('مالك',): 'malik',
             ('الموطا',): 'malik', ('احمد',): 'ahmad', ('الحاكم',): 'hakim', ('المستدرك',): 'hakim',
             ('البيهقي',): 'bayhaqi', ('الطبراني',): 'tabarani', ('ابن', 'حبان'): 'ibnhibban',
             ('الدارمي',): 'darimi', ('الدارقطني',): 'daraqutni'}
_AR_TRIGGERS = {'رواه', 'اخرجه', 'روي', 'اخرج', 'رواهما', 'مسند', 'سنن', 'صحيح'}
_AR_STOP = {'عن', 'قال', 'حدثنا', 'اخبرنا'}
_AR_BREAK = re.compile(r'[.\n«»"“”﴿﴾]')

# English: ASCII-folded, lower case.
_EN_NAMES = [('bukhari', r'bukhari'), ('muslim', r'\bmuslim\b'), ('abudawud', r'\babu da(?:w|u)u?d\b'),
             ('tirmidhi', r'tirmidhi'), ('nasai', r'nasa-?i\b'), ('ibnmajah', r'\bibn majah?\b'),
             ('malik', r'(?<!ibn )(?<!bin )\bmalik\b|muwatta'), ('ahmad', r'\bahmad\b'),
             ('hakim', r'\bhakim\b|mustadrak'), ('bayhaqi', r'ba[yi]haqi'), ('tabarani', r'tabarani'),
             ('ibnhibban', r'\bibn hibban\b'), ('darimi', r'\bdarimi\b'), ('daraqutni', r'daraqutni')]
_EN_NAME = re.compile('|'.join(f'(?P<{key}>{pattern})' for key, pattern in _EN_NAMES))
_EN_TRIGGER = re.compile(r'\b(?:narrated|reported|recorded|related|transmitted|collected|cited|included|compiled|'
                         r'authenticated)\b(?:\s+it)?\s+(?:by|in)\b|\b(?:sahih|sunan|musnad|jami|agreed upon|muttafaq)\b')
_EN_AFTER = re.compile(r'\s+(?:also\s+)?(?:narrated|reported|recorded|related|transmitted)\b')
_EN_NUMBER = re.compile(r'(?:\bno\.|[^.\n\d]){0,40}?(\d{1,5})\b')
_EN_WINDOW_END = re.compile(r'[:"“\n]|\.(?:\s|$)')
_APPARATUS = re.compile(r'^\s*#{1,6}\s*(?:persons|people|glossary|index|biograph|names)', re.I | re.M)
_QURAN_CONTEXT = re.compile(r"(?:qur-?an|surah?|surat|ayah?|verse|\bq\b)[^\d\n]{0,40}$")
_QURAN_REF = re.compile(r'\b(\d{1,3})\s*:\s*(\d{1,3})(?:\s*[-–]\s*(\d{1,3}))?\b')
MAX_RANGE = 40
_QURAN_NAMED = re.compile(r'\((\d{1,3})\)\s*[:,]?\s*(?:ayah|ayat|verse)s?\s*(\d{1,3})')


def _ascii(text: str) -> str:
    plain = ''.join(c for c in unicodedata.normalize('NFKD', text) if not unicodedata.combining(c))
    return re.sub(r"[ʿʾ'’‘`]", '', plain).lower()


def _number(token: str) -> int | None:
    return int(token) if token.isdecimal() and len(token) <= 5 else None


def source_takhrij(source: str) -> dict:
    collections, numbered = set(), []
    for segment in _AR_BREAK.split(source):
        words = [w[1:] if w.startswith('و') and len(w) > 2 and w[1:] in _AR_TRIGGERS | {n[0] for n in _AR_NAMES}
                 else w for w in folded(segment).split()]
        active, i, last = False, 0, None
        while i < len(words):
            word = words[i]
            if word in _AR_TRIGGERS or (word == 'متفق' and words[i + 1:i + 2] == ['عليه']):
                active = True
                if word == 'متفق':
                    collections.update(('bukhari', 'muslim'))
            elif active and word in _AR_STOP:
                active = False
            elif active:
                name = next(((key, len(seq)) for seq, key in _AR_NAMES.items() if tuple(words[i:i + len(seq)]) == seq), None)
                if name:
                    last = (name[0], i + name[1] + 4)
                    collections.add(name[0])
                    i += name[1]
                    continue
                if last and i < last[1] and _number(word):
                    numbered.append((last[0], _number(word)))
                    last = None
            i += 1
    return {'collections': sorted(collections), 'numbered': list(dict.fromkeys(numbered))}


def translation_takhrij(text: str) -> dict:
    cut = _APPARATUS.search(text)
    plain = _ascii(text[:cut.start()] if cut else text)
    collections, numbered = set(), []
    for match in _EN_NAME.finditer(plain):
        key = match.lastgroup
        before = plain[max(0, match.start() - 160):match.start()]
        trigger = list(_EN_TRIGGER.finditer(before))
        attributed = bool(trigger) and not _EN_WINDOW_END.search(before[trigger[-1].end():])
        attributed = attributed or bool(_EN_AFTER.match(plain, match.end()))
        number = _EN_NUMBER.match(plain, match.end())
        between = plain[match.end():number.start(1)] if number else ''
        if number and not re.search(r'\bvol|\bbook\b', between) and not _EN_NAME.search(between):
            numbered.append({'collection': key, 'number': int(number.group(1)),
                             'quote': plain[match.start():number.end()]})
            collections.add(key)
        elif attributed:
            collections.add(key)
    if any(m for m in re.finditer(r'agreed upon|muttafaq', plain)):
        collections.update(('bukhari', 'muslim'))
    quran = []
    for match in _QURAN_REF.finditer(plain):
        opened = plain.rfind('(', 0, match.start()) > plain.rfind(')', 0, match.start()) or \
            plain.rfind('[', 0, match.start()) > plain.rfind(']', 0, match.start())
        if opened or _QURAN_CONTEXT.search(plain[max(0, match.start() - 50):match.start()]):
            first, last = int(match.group(2)), int(match.group(3) or match.group(2))
            last = last if first <= last <= first + MAX_RANGE else first  # (31:13-19) cites seven verses
            quran += [(int(match.group(1)), ayah, match.group(0), match.start()) for ayah in range(first, last + 1)]
    for match in _QURAN_NAMED.finditer(plain):
        quran.append((int(match.group(1)), int(match.group(2)), match.group(0), match.start()))
    refs = sorted({(s, a): (s, a, q, at) for s, a, q, at in quran if 1 <= s <= 114 and a >= 1}.values(),
                  key=lambda r: (r[3], r[1]))
    return {'collections': sorted(collections), 'numbered': numbered,
            'quran': [{'surah': s, 'ayah': a, 'quote': q} for s, a, q, _ in refs]}


def _verse_units(verses: list[str]) -> list[tuple[int, int, int, str]]:
    units = []
    for ayah in verses:
        chapter, rest = ayah.split(':', 1)
        if '–' in rest:  # a span over two surahs: keep the first one
            rest = rest.split('–')[0]
        first, _, last = rest.partition('-')
        units.append((int(chapter), int(first), int(last or first), ayah))
    return list(dict.fromkeys(units))


def _side(source_refs: dict, verses: list, quotes: list[str], text: str, lookup, quoted) -> dict:
    found = translation_takhrij(text)
    items, delivered, wrong = [], 0, 0
    cited = [(r['surah'], r['ayah']) for r in found['quran']]
    for chapter, first, last, label in verses:
        hit = any(s == chapter and first <= a <= last for s, a in cited)
        delivered += hit
        items.append({'kind': 'quran', 'reference': f'Quran {label}', 'status': 'correct' if hit else 'missing'})
    for s, a in cited:
        if not any(s == c and f <= a <= l for c, f, l, _ in verses) and not quoted(s, a):
            wrong += 1
            items.append({'kind': 'quran', 'reference': f'Quran {s}:{a}', 'status': 'wrong'})
    def verified(key):
        texts = lookup(*key)
        return texts, texts is not None and any(correspondence(q, t)[0] in _FOUND for q in quotes for t in texts)

    source_numbers, judged, seen = set(source_refs['numbered']), set(), set()
    for ref in found['numbered']:
        key = (ref['collection'], ref['number'])
        if key in seen or key in source_numbers:
            seen.add(key)
            continue
        seen.add(key)
        judged.add(key[0])  # a numbered reference judges its collection; it is not counted twice
        texts, matches = verified(key)
        status = 'unchecked' if texts is None else 'correct' if matches else 'wrong'
        wrong += status == 'wrong'
        items.append({'kind': 'hadith', 'reference': f'{NAMES[key[0]]} {key[1]}', 'status': status})
    for key in source_refs['numbered']:
        status = 'missing'
        if key in seen:
            delivered += 1
            status = 'correct' if verified(key)[1] else 'as_in_source'
        items.append({'kind': 'hadith', 'reference': f'{NAMES[key[0]]} {key[1]}', 'status': status})
    for key in source_refs['collections']:
        hit = key in found['collections']
        delivered += hit
        items.append({'kind': 'collection', 'reference': NAMES[key], 'status': 'correct' if hit else 'missing'})
    for key in found['collections']:
        if key not in source_refs['collections'] and key not in judged:
            wrong += 1
            items.append({'kind': 'collection', 'reference': NAMES[key], 'status': 'wrong'})
    return {'delivered': delivered, 'wrong': wrong, 'items': items}


def takhrij_check(source: str, translations: dict[str, str], verses: list[str], lookup, quoted=None) -> dict | None:
    """lookup(collection, number) -> Arabic texts of that hadith, [] if absent, None if no library has it.

    verses are the verses that the code located in the source; quoted(surah, ayah) tells whether the
    source quotes a verse that the location missed, such as the rest of a passage (12:84-87)."""
    quoted = quoted or (lambda surah, ayah: False)
    source_refs = source_takhrij(source)
    units = _verse_units(verses)
    total = len(units) + len(source_refs['collections']) + len(source_refs['numbered'])
    if not total:
        return None
    quotes = [r['quote'] for r in detect_references(source) if r['kind'] != 'quran']
    return {'version': VERSION, 'total': total,
            **{side: _side(source_refs, units, quotes, translations.get(side, ''), lookup, quoted) for side in ('a', 'b')}}
