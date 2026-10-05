"""Bounded local snapshots of explicitly named electronic Arabic editions."""
import json
import math
from pathlib import Path
from threading import Lock
import httpx
from independent_judge.reference_ports import LibraryUnavailable
from independent_judge.infrastructure.reference_snapshot import load_snapshot, store_snapshot

BASE = 'https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions'
COLLECTIONS = {'bukhari': 'Sahih al-Bukhari', 'muslim': 'Sahih Muslim', 'abudawud': 'Sunan Abi Dawud',
               'tirmidhi': "Jami' at-Tirmidhi", 'nasai': "Sunan an-Nasa'i", 'ibnmajah': 'Sunan Ibn Majah',
               'malik': "Muwatta Malik"}
MAX_BYTES = 64 * 1024 * 1024


class HadithLibrary:
    def __init__(self, directory: Path, *, collections=tuple(COLLECTIONS), transport=None):
        if not collections or any(c not in COLLECTIONS for c in collections):
            raise ValueError('Unsupported collection')
        self.directory = directory / 'reference-cache'
        self.collections, self.transport = collections, transport
        self.lock = Lock()
        self.cached = None

    def records(self) -> list[dict]:
        with self.lock:
            if self.cached is not None:
                return self.cached
            try:
                self.cached = [record for collection in self.collections for record in self._collection(collection)]
                return self.cached
            except (httpx.HTTPError, OSError, ValueError, TypeError, KeyError) as exc:
                raise LibraryUnavailable('Reference collection unavailable or invalid') from exc

    def _collection(self, collection: str) -> list[dict]:
        path = self.directory / f'ara-{collection}.json'
        snapshot, downloaded = load_snapshot(f'{BASE}/ara-{collection}.json', path,
                                             transport=self.transport, max_bytes=MAX_BYTES)
        data = json.loads(snapshot['raw'])
        items = data['hadiths']
        if not isinstance(items, list) or not 1 <= len(items) <= 15000:
            raise ValueError('Invalid collection')
        records = []
        omitted = 0
        for item in items:
            number, text = item['hadithnumber'], item['text']
            if type(number) not in (int, float) or not math.isfinite(number) or number <= 0 or not isinstance(text, str):
                raise ValueError('Invalid hadith record')
            if not text.strip():
                omitted += 1
                continue
            records.append({'id': f'{collection}:{number}', 'collection': COLLECTIONS[collection],
                            'number': number, 'text': text, 'edition': f'ara-{collection}',
                            'url': f'{BASE}/ara-{collection}/{number}.json',
                            'reference': item.get('reference', {}),
                            'grades': item.get('grades', []),
                            'snapshot_sha256': snapshot['snapshot_sha256'],
                            'retrieved_at': snapshot['retrieved_at']})
        if not records: raise ValueError('Empty collection')
        for record in records: record['omitted_empty_records'] = omitted
        if downloaded:
            store_snapshot(path, snapshot)
        return records
