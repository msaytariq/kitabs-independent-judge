"""Bounded local snapshots of explicitly named electronic Arabic editions."""
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from pathlib import Path
from threading import Lock
import httpx
from independent_judge.reference_ports import LibraryUnavailable

BASE = 'https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions'
COLLECTIONS = {'bukhari': 'Sahih al-Bukhari', 'muslim': 'Sahih Muslim'}
MAX_BYTES = 64 * 1024 * 1024


class HadithLibrary:
    def __init__(self, directory: Path, *, collections=('bukhari', 'muslim'), transport=None):
        if not collections or any(c not in COLLECTIONS for c in collections):
            raise ValueError('Unsupported collection')
        self.directory = directory / 'reference-cache'
        self.collections, self.transport = collections, transport
        self.lock = Lock()

    def records(self) -> list[dict]:
        with self.lock:
            try:
                return [record for collection in self.collections for record in self._collection(collection)]
            except (httpx.HTTPError, OSError, ValueError, TypeError, KeyError) as exc:
                raise LibraryUnavailable('Reference collection unavailable or invalid') from exc

    def _collection(self, collection: str) -> list[dict]:
        path = self.directory / f'ara-{collection}.json'
        snapshot = None
        if path.is_file():
            if path.stat().st_size > MAX_BYTES * 2: raise ValueError('Oversized cache')
            snapshot = json.loads(path.read_text())
            age = (datetime.now(timezone.utc) - datetime.fromisoformat(snapshot['retrieved_at'])).total_seconds()
            if not 0 <= age < 7 * 86400: snapshot = None
        downloaded = snapshot is None
        if downloaded:
            with httpx.Client(timeout=30, follow_redirects=False, transport=self.transport) as client:
                with client.stream('GET', f'{BASE}/ara-{collection}.json') as response:
                    response.raise_for_status()
                    raw = bytearray()
                    for chunk in response.iter_bytes():
                        raw.extend(chunk)
                        if len(raw) > MAX_BYTES: raise ValueError('Oversized library')
            snapshot = {'raw': bytes(raw).decode('utf-8'), 'snapshot_sha256': sha256(raw).hexdigest(),
                        'retrieved_at': datetime.now(timezone.utc).isoformat()}
        if sha256(snapshot['raw'].encode()).hexdigest() != snapshot['snapshot_sha256']:
            raise ValueError('Changed cache')
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
            self.directory.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix('.tmp')
            temporary.write_text(json.dumps(snapshot, ensure_ascii=False), encoding='utf-8')
            temporary.replace(path)
        return records
