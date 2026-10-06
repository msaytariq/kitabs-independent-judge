"""Locate a quotation in the Quran text and compare a source label such as (البقرة : 155)."""
from bisect import bisect_right
import re
from independent_judge.domain.arabic_text import folded

SURAHS = ('الفاتحة البقرة آل_عمران النساء المائدة الأنعام الأعراف الأنفال التوبة يونس هود يوسف الرعد إبراهيم '
          'الحجر النحل الإسراء الكهف مريم طه الأنبياء الحج المؤمنون النور الفرقان الشعراء النمل القصص العنكبوت '
          'الروم لقمان السجدة الأحزاب سبأ فاطر يس الصافات ص الزمر غافر فصلت الشورى الزخرف الدخان الجاثية '
          'الأحقاف محمد الفتح الحجرات ق الذاريات الطور النجم القمر الرحمن الواقعة الحديد المجادلة الحشر '
          'الممتحنة الصف الجمعة المنافقون التغابن الطلاق التحريم الملك القلم الحاقة المعارج نوح الجن المزمل '
          'المدثر القيامة الإنسان المرسلات النبأ النازعات عبس التكوير الانفطار المطففين الانشقاق البروج الطارق '
          'الأعلى الغاشية الفجر البلد الشمس الليل الضحى الشرح التين العلق القدر البينة الزلزلة العاديات القارعة '
          'التكاثر العصر الهمزة الفيل قريش الماعون الكوثر الكافرون النصر المسد الإخلاص الفلق الناس').split(' ')
SURAHS = [name.replace('_', ' ') for name in SURAHS]
_BY_NAME = {folded(name): number for number, name in enumerate(SURAHS, 1)}
LABEL = re.compile(r'[﴾}»"”]?\s*\(\(?\s*([^():\d]{1,30}?)\s*:\s*(\d{1,3})\s*\)\)?')
# Some editions print the label without brackets after the verse: (...) الإسراء: 79
BARE_LABEL = re.compile(r'\)?\s*\[?\s*([^():\[\]\d\s،,.]{2,20}(?:\s[^():\[\]\d\s،,.]{2,20})?)\s*:\s*([0-9٠-٩]{1,3})')
MIN_WORDS = 3
MIN_SCAN_WORDS = 6  # an unmarked passage counts as a verse only with six or more words in Quran order
_TOKEN = re.compile(r'\S+')
_BASMALA = folded('بسم الله الرحمن الرحيم').split()


class QuranIndex:
    def __init__(self, verses: list[dict]):
        parts, self.starts, self.refs, offset = [], [], [], 0
        for verse in verses:
            text = folded(verse['text'])
            if not text:
                continue
            self.starts.append(offset)
            self.refs.append(verse)
            parts.append(text)
            offset += len(text) + 1
        self.text = ' ' + ' '.join(parts) + ' '
        words = self.text.split()
        self.trigrams = {' '.join(words[i:i + 3]) for i in range(len(words) - 2)}

    def scan(self, source: str) -> list[tuple[int, int]]:
        """Spans of the source that quote the Quran without brackets or formula, six words or more."""
        tokens = [(m.start(), m.end(), folded(m.group())) for m in _TOKEN.finditer(source)]
        tokens = [t for t in tokens if t[2] and ' ' not in t[2]]
        # The basmala opens a book or a chapter; it is a formula, not a quotation.
        words = [t[2] for t in tokens]
        tokens = [t for n, t in enumerate(tokens)
                  if not any(words[k:k + 4] == _BASMALA for k in range(max(0, n - 3), n + 1))]
        spans, i = [], 0
        while i + MIN_SCAN_WORDS <= len(tokens):
            j = i
            while j + 3 <= len(tokens) and ' '.join(t[2] for t in tokens[j:j + 3]) in self.trigrams:
                j += 1
            if j - i + 2 >= MIN_SCAN_WORDS:
                located = self.locate(source[tokens[i][0]:tokens[j + 1][1]], anchored=True)
                if located and located['matched_words'] >= MIN_SCAN_WORDS:
                    first = i + located['first_word']
                    last = first + located['matched_words'] - 1
                    spans.append((tokens[first][0], tokens[last][1]))
                    i = last + 1
                    continue
            i += 1
        return spans

    def _verse_at(self, position: int) -> dict:
        return self.refs[max(0, bisect_right(self.starts, position - 1) - 1)]

    def locate(self, quote: str, *, anchored: bool = False) -> dict | None:
        """Longest contiguous run of the quotation found in the Quran (at least three words)."""
        words = folded(quote).split()
        best = None
        starts = range(min(2, len(words))) if anchored else range(len(words))
        for i in starts:
            j = i
            while j + 3 <= len(words) and ' '.join(words[j:j + 3]) in self.trigrams:
                j += 1
            for end in range(j + 2, i + MIN_WORDS - 1, -1):
                at = self.text.find(' ' + ' '.join(words[i:end]) + ' ')
                if at >= 0:
                    if not best or end - i > best[1] - best[0]:
                        best = (i, end, at)
                    break
        if not best:
            return None
        i, end, at = best
        first, last = self._verse_at(at + 1), self._verse_at(at + len(' '.join(words[i:end])))
        ayah = f"{first['chapter']}:{first['verse']}"
        if last is not first:
            ayah += f"-{last['verse']}" if last['chapter'] == first['chapter'] else f"–{last['chapter']}:{last['verse']}"
        return {'ayah': ayah, 'surah': first['chapter'], 'surah_name': SURAHS[first['chapter'] - 1],
                'matched_words': end - i, 'quote_words': len(words), 'first_word': i,
                'verse_text': first['text'] if last is first else None}


def label_check(source: str, end: int, located: dict | None) -> dict:
    """Compare an explicit (Surah : ayah) label that follows the quotation."""
    match = LABEL.match(source, end)
    if not match:
        bare = BARE_LABEL.match(source, end)
        # Without brackets only a real surah name makes a label; "رواه البخاري: 1" is not one.
        if not bare or folded(bare.group(1).strip()) not in _BY_NAME:
            return {'label': None, 'label_status': 'no_label'}
        match = bare
    name, number = match.group(1).strip(), int(match.group(2))
    label = f'{name} : {number}'
    surah = _BY_NAME.get(folded(name))
    if not located or surah is None:
        return {'label': label, 'label_status': 'label_unchecked'}
    chapter, verses = located['ayah'].split(':', 1)[0], located['ayah'].split(':', 1)[1]
    first = int(re.split(r'[-–]', verses)[0])
    same = surah == int(chapter) and number == first
    return {'label': label, 'label_status': 'label_matches' if same else 'label_differs'}


def verse_quoted(index: QuranIndex, source: str):
    """quoted(surah, ayah): does the source give at least four words in a row of this verse?"""
    texts = {(v['chapter'], v['verse']): folded(v['text']).split() for v in index.refs}
    padded = ' ' + folded(source) + ' '

    def quoted(surah: int, ayah: int) -> bool:
        words = texts.get((surah, ayah)) or []
        size = min(4, len(words))
        return bool(words) and any(' ' + ' '.join(words[i:i + size]) + ' ' in padded
                                   for i in range(len(words) - size + 1))
    return quoted


def surah_label_follows(source: str, end: int) -> bool:
    """Is the text after a bracketed quotation a surah label such as الإسراء: 79?"""
    bare = BARE_LABEL.match(source, end)
    return bool(bare) and folded(bare.group(1).strip()) in _BY_NAME
