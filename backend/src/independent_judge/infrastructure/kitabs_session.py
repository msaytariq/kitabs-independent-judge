"""The operator's Kitabs refresh token, kept in a private file and replaced after each rotation.

The Kitabs admin panel writes the file (token, account e-mail, time) and removes it to disconnect.
A rotation replaces the token only and keeps the other keys."""
import json
import os
from pathlib import Path


class KitabsSession:
    def __init__(self, path: Path):
        self.path = Path(path)

    def load(self) -> str:
        try:
            return json.loads(self.path.read_text())['refreshToken']
        except (FileNotFoundError, KeyError, ValueError):
            return ''

    def _record(self) -> dict:
        try:
            record = json.loads(self.path.read_text())
        except (FileNotFoundError, ValueError):
            return {}
        return record if isinstance(record, dict) else {}

    def save(self, token: str):
        record = self._record() | {'refreshToken': token}
        temporary = self.path.with_suffix('.tmp')
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(descriptor, 'w') as handle:
            json.dump(record, handle)
        os.replace(temporary, self.path)
