"""Public Quran text (simple Arabic script) for locating verses quoted in a source."""
import json
from pathlib import Path
from threading import Lock
import httpx
from independent_judge.infrastructure.reference_snapshot import load_snapshot, store_snapshot
from independent_judge.reference_ports import LibraryUnavailable

URL = 'https://cdn.jsdelivr.net/gh/fawazahmed0/quran-api@1/editions/ara-quransimple.json'
EDITION = 'ara-quransimple'
MAX_BYTES = 16 * 1024 * 1024


class QuranLibrary:
    def __init__(self, directory: Path, *, transport=None):
        self.path = directory / 'reference-cache' / f'{EDITION}.json'
        self.transport, self.lock, self.cached = transport, Lock(), None

    def verses(self) -> list[dict]:
        with self.lock:
            if self.cached is None:
                try:
                    self.cached = self._load()
                except (httpx.HTTPError, OSError, ValueError, TypeError, KeyError) as exc:
                    raise LibraryUnavailable('Quran text unavailable or invalid') from exc
            return self.cached

    def _load(self) -> list[dict]:
        snapshot, downloaded = load_snapshot(URL, self.path, transport=self.transport, max_bytes=MAX_BYTES)
        items = json.loads(snapshot['raw'])['quran']
        if not isinstance(items, list) or not 1 <= len(items) <= 7000:
            raise ValueError('Invalid Quran edition')
        verses = []
        for item in items:
            chapter, verse, text = item['chapter'], item['verse'], item['text']
            if type(chapter) is not int or type(verse) is not int or not isinstance(text, str) or not text.strip():
                raise ValueError('Invalid verse')
            verses.append({'chapter': chapter, 'verse': verse, 'text': text, 'edition': EDITION,
                           'url': f'https://quran.com/{chapter}/{verse}',
                           'snapshot_sha256': snapshot['snapshot_sha256'], 'retrieved_at': snapshot['retrieved_at']})
        if downloaded:
            store_snapshot(self.path, snapshot)
        return verses
