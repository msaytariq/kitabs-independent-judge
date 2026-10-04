"""Append-only local scope snapshots, independent of original input storage."""
from contextlib import closing
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from uuid import uuid4


class SqliteScopeRepository:
    def __init__(self, directory: Path):
        directory.mkdir(parents=True, exist_ok=True)
        self.path = directory / 'scopes.sqlite3'
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('CREATE TABLE IF NOT EXISTS scopes (id TEXT PRIMARY KEY, snapshot TEXT NOT NULL)')

    def create(self, snapshot: dict) -> dict:
        result = {**snapshot, 'id': uuid4().hex, 'created_at': datetime.now(timezone.utc).isoformat()}
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('INSERT INTO scopes VALUES (?, ?)', (result['id'], json.dumps(result, ensure_ascii=False)))
        return result

    def get(self, scope_id: str) -> dict | None:
        with closing(sqlite3.connect(self.path)) as db:
            row = db.execute('SELECT snapshot FROM scopes WHERE id = ?', (scope_id,)).fetchone()
        return json.loads(row[0]) if row else None
