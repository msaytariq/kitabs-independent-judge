"""Durable idempotency and results for a single local worker process."""
from contextlib import closing
import fcntl
import json
from pathlib import Path
import sqlite3
from uuid import uuid4


class LocalJobs:
    def __init__(self, directory: Path):
        directory.mkdir(parents=True, exist_ok=True)
        self.path = directory / 'local-jobs.sqlite3'
        self.lock_path = directory / 'local-worker.lock'
        self.owner = None
        with closing(sqlite3.connect(self.path)) as db, db:
            db.executescript('''CREATE TABLE IF NOT EXISTS jobs
                (scope_id TEXT PRIMARY KEY, id TEXT UNIQUE, status TEXT, error TEXT, report TEXT);
                CREATE TABLE IF NOT EXISTS reference_checks (key TEXT PRIMARY KEY, result TEXT);''')

    def activate(self):
        self.owner = self.lock_path.open('a')
        try: fcntl.flock(self.owner, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.owner.close(); self.owner = None
            raise RuntimeError('Another local evaluation worker owns this data directory') from None
        with closing(sqlite3.connect(self.path)) as db, db:
            pending = db.execute("SELECT scope_id,id FROM jobs WHERE status IN ('queued','running','checking_references','interrupted')").fetchall()
            reports = self.path.parent / 'runs.sqlite3'
            for scope_id, run_id in pending:
                report = None
                if reports.exists():
                    with closing(sqlite3.connect(reports.as_uri() + '?mode=ro', uri=True)) as saved:
                        row = saved.execute('SELECT report FROM runs WHERE id=?', (run_id,)).fetchone()
                    if row and row[0]: report = json.loads(row[0])
                db.execute('UPDATE jobs SET status=?,error=?,report=? WHERE scope_id=?',
                    (report['status'] if report else 'interrupted',
                     report.get('error', {}).get('code') if report else 'worker_interrupted',
                     json.dumps(report, ensure_ascii=False) if report else None, scope_id))

    def close(self):
        if self.owner:
            self.owner.close(); self.owner = None

    def claim(self, scope_id: str) -> tuple[dict, bool]:
        with closing(sqlite3.connect(self.path)) as db, db:
            inserted = db.execute('INSERT OR IGNORE INTO jobs VALUES(?,?,?,NULL,NULL)',
                                  (scope_id, uuid4().hex, 'queued')).rowcount == 1
        return self.get(scope_id), inserted

    def get(self, scope_id: str) -> dict:
        with closing(sqlite3.connect(self.path)) as db:
            row = db.execute('SELECT id,status,error,report FROM jobs WHERE scope_id=?', (scope_id,)).fetchone()
        if not row: return {'id': None, 'status': 'idle', 'error': None, 'report': None}
        return {'id': row[0], 'status': row[1], 'error': row[2],
                'report': json.loads(row[3]) if row[3] else None}

    def update(self, scope_id: str, status: str, *, report=None, error=None):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('UPDATE jobs SET status=?,error=?,report=? WHERE scope_id=?',
                       (status, error, json.dumps(report, ensure_ascii=False) if report else None, scope_id))

    def reference(self, key: str) -> dict | None:
        with closing(sqlite3.connect(self.path)) as db:
            row = db.execute('SELECT result FROM reference_checks WHERE key=?', (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def save_reference(self, key: str, result: dict):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('INSERT OR REPLACE INTO reference_checks VALUES(?,?)',
                       (key, json.dumps(result, ensure_ascii=False)))
