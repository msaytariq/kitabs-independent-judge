"""Word frequencies of correct Arabic: the Quran and the hadith collections of the reference cache.

Read once, when a text first needs the lam-alef repair; an unavailable cache leaves texts unchanged.
"""
from collections import Counter
from pathlib import Path
from threading import Lock
from independent_judge.domain.arabic_order import repair_lam_alef
from independent_judge.domain.arabic_text import folded
from independent_judge.infrastructure.hadith_library import HadithLibrary
from independent_judge.infrastructure.quran_library import QuranLibrary


class ArabicLexicon:
    def __init__(self, directory: Path):
        self.directory, self.counts, self.lock = Path(directory), None, Lock()

    def __call__(self, word: str) -> int:
        return self._counts().get(folded(word), 0)

    def repair(self, text: str) -> str:
        return repair_lam_alef(text, self)

    def _counts(self) -> Counter:
        with self.lock:
            if self.counts is None:
                counts = Counter()
                try:
                    for record in HadithLibrary(self.directory).records():
                        counts.update(folded(record['text']).split())
                    for verse in QuranLibrary(self.directory).verses():
                        counts.update(folded(verse['text']).split())
                except Exception:  # noqa: BLE001 - no word list: the text stays as extracted
                    counts = Counter()
                self.counts = counts
            return self.counts
