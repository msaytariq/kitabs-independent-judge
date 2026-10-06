"""Find Quran and hadith quotations in an Arabic source; every span keeps its coordinates."""
import re
from independent_judge.domain.arabic_text import folded
from independent_judge.domain.quran_matching import surah_label_follows

_ARABIC = re.compile(r'[ء-ي]')
_PROPHET = r'(?:صلى الله عليه وسلم|ﷺ)'
# A saying: a verb of speech next to the Prophet's name or honorific, not narration around it.
_SAYING = (r'(?:(?:قال|يقول|فقال|وقال)\s+(?:رسول الله|النبي)?\s*' + _PROPHET +
           r'|' + _PROPHET + r'\s*(?:قال|يقول|فقال))')
_CONTEXT_BEFORE = re.compile(r'رسول الله|النبي|' + _PROPHET)
_CONTEXT_AFTER = re.compile(r'رواه|أخرجه|متفق|البخاري|مسلم')
# An intake that unifies alef maqsura writes "تعالي"; both forms open a verse.
_QURAN_FORMULA = r'(?:قال|وقال|قوله|يقول)\s+(?:الله\s+)?(?:تعال[ىي]|عز وجل|سبحانه(?:\s+وتعال[ىي])?)'
_ATTRIBUTION = re.compile(r'\s*(?:رواه|متفق|أخرجه|انظر|وفي رواية|وفى رواية|صحيح|سنن|مسند)')
_DIGITS = re.compile(r'[0-9٠-٩]')
_STOP = re.compile(r'[.\n]|\s(?:حديث|أخرجه|رواه|متفق)\s')
PATTERNS = [  # (kind, regex, group); earlier patterns win overlapping spans
    ('quran', re.compile(r'﴿([^﴾]{3,1500})﴾|\{([^{}]{3,1500})\}'), None),
    ('quoted', re.compile(r'«([^«»]{10,2000})»|“([^“”]{10,2000})”|"([^"\n]{10,2000})"|\(([^()]{10,2000})\)'), None),
    ('hadith', re.compile(r'حديث\s+(.{6,600}?)\s+(?:أخرجه|رواه|متفق)'), 1),
    ('quran', re.compile(_QURAN_FORMULA + r'\s*:?\s*([^.\n]{6,400})'), 1),
    ('hadith', re.compile(_SAYING + r'\s*:?\s*([^.\n]{6,600})'), 1),
]


def _span(match, group):
    if group is not None:
        return match.start(group), match.end(group)
    used = next(i for i in range(1, (match.re.groups or 0) + 1) if match.group(i) is not None)
    return match.start(used), match.end(used)


def detect_references(source: str) -> list[dict]:
    taken, found, seen = [], [], set()
    for kind, pattern, group in PATTERNS:
        for match in pattern.finditer(source):
            start, end = _span(match, group)
            stop = _STOP.search(source, start, end) if group is not None else None
            if stop:
                end = stop.start()
            while end > start and source[end - 1] in ' ،,:;':
                end -= 1
            quote = source[start:end]
            if sum(bool(_ARABIC.search(w)) for w in quote.split()) < 3 or _ATTRIBUTION.match(quote):
                continue
            if _DIGITS.search(quote) and len(quote.split()) < 8:
                continue  # a citation such as (صحيح البخاري: ٣١٠٤)
            sentence = max(source.rfind('\n', 0, start), source.rfind('.', 0, start), start - 120, -1) + 1
            if kind == 'quoted' and not (_CONTEXT_BEFORE.search(source, sentence, start)
                                         or _CONTEXT_AFTER.search(source, end, end + 60)
                                         or surah_label_follows(source, end)
                                         or re.search(r'تعال[ىي]|عز وجل|سبحانه', source[max(0, start - 60):start])):
                continue  # an ordinary quotation, neither attributed to the Prophet nor to the Quran
            if any(s <= start < e for s, e in taken):
                continue
            later = [s for s, e in taken if start < s < end]
            if later:  # an unmarked quotation stops where an already found one begins
                end = min(later)
                while end > start and source[end - 1] in ' ،,:;':
                    end -= 1
                quote = source[start:end]
                if sum(bool(_ARABIC.search(w)) for w in quote.split()) < 3:
                    continue
            taken.append((start, end))
            # A takhrij note often repeats the hadith it follows; one quotation counts once.
            if folded(quote) in seen:
                continue
            seen.add(folded(quote))
            found.append({'kind': kind, 'quote': quote, 'start': start, 'end': end,
                          'marked': group is None})
    return sorted(found, key=lambda r: r['start'])
