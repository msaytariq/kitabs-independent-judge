"""Private immutable run request, call receipts and finalized reports."""
from contextlib import closing
import json
from pathlib import Path
import sqlite3
from independent_judge.domain.evaluation import EvaluationError


class RunRepository:
    def __init__(self,directory: Path):
        directory.mkdir(parents=True,exist_ok=True)
        self.path=directory/'runs.sqlite3'
        with closing(sqlite3.connect(self.path)) as db,db:
            db.executescript('''CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY, request TEXT NOT NULL, report TEXT);
            CREATE TABLE IF NOT EXISTS receipts(run_id TEXT,call_id TEXT,snapshot TEXT NOT NULL,PRIMARY KEY(run_id,call_id));''')

    def begin(self,run_id,request):
        try:
            with closing(sqlite3.connect(self.path)) as db,db:
                db.execute('INSERT INTO runs VALUES(?,?,NULL)',(run_id,json.dumps(request,ensure_ascii=False)))
        except sqlite3.IntegrityError:
            raise EvaluationError('duplicate_run','Run ID already exists; no automatic replay.') from None

    def receipt(self,run_id,call_id,snapshot):
        with closing(sqlite3.connect(self.path)) as db,db:
            db.execute('INSERT INTO receipts VALUES(?,?,?)',(run_id,call_id,json.dumps(snapshot,ensure_ascii=False)))

    def finish(self,run_id,report):
        with closing(sqlite3.connect(self.path)) as db,db:
            changed=db.execute('UPDATE runs SET report=? WHERE id=? AND report IS NULL',
                              (json.dumps(report,ensure_ascii=False),run_id)).rowcount
            if changed!=1: raise EvaluationError('immutable_report','Run report already finalized or missing.')

    def get(self,run_id):
        with closing(sqlite3.connect(self.path)) as db:
            row=db.execute('SELECT report FROM runs WHERE id=?',(run_id,)).fetchone()
        return json.loads(row[0]) if row and row[0] else None
