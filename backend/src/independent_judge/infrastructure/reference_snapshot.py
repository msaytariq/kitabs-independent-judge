"""Download a public reference edition once, keep a hashed local copy for seven days."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import httpx

MAX_AGE_SECONDS = 7 * 86400


def load_snapshot(url: str, path: Path, *, transport=None, max_bytes: int) -> tuple[dict, bool]:
    """Return (snapshot, downloaded). The caller stores it only after validating the content."""
    if path.is_file():
        if path.stat().st_size > max_bytes * 2:
            raise ValueError('Oversized cache')
        snapshot = json.loads(path.read_text())
        age = (datetime.now(timezone.utc) - datetime.fromisoformat(snapshot['retrieved_at'])).total_seconds()
        if 0 <= age < MAX_AGE_SECONDS:
            if sha256(snapshot['raw'].encode()).hexdigest() != snapshot['snapshot_sha256']:
                raise ValueError('Changed cache')
            return snapshot, False
    with httpx.Client(timeout=30, follow_redirects=False, transport=transport) as client:
        with client.stream('GET', url) as response:
            response.raise_for_status()
            raw = bytearray()
            for chunk in response.iter_bytes():
                raw.extend(chunk)
                if len(raw) > max_bytes:
                    raise ValueError('Oversized library')
    return {'raw': bytes(raw).decode('utf-8'), 'snapshot_sha256': sha256(raw).hexdigest(),
            'retrieved_at': datetime.now(timezone.utc).isoformat()}, True


def store_snapshot(path: Path, snapshot: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(snapshot, ensure_ascii=False), encoding='utf-8')
    temporary.replace(path)
