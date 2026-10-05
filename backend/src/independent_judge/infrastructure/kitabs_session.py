"""The operator's Kitabs refresh token, kept in a private file and replaced after each rotation."""
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

    def save(self, token: str):
        temporary = self.path.with_suffix('.tmp')
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(descriptor, 'w') as handle:
            json.dump({'refreshToken': token}, handle)
        os.replace(temporary, self.path)
