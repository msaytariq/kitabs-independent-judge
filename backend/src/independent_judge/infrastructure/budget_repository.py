"""Atomic persistent budget reservations, settled usage and fail-closed uncertainty."""
from contextlib import closing
from decimal import Decimal
from pathlib import Path
import sqlite3
import re
from independent_judge.domain.budget import micros, usd
from independent_judge.domain.evaluation import EvaluationError


class BudgetLedger:
    def __init__(self, directory: Path, *, total_usd: Decimal, per_run_usd: Decimal):
        self.total, self.per_run = micros(total_usd), micros(per_run_usd)
        if not 0 < self.per_run <= self.total:
            raise EvaluationError('invalid_budget','Explicit positive total and run limits are required.')
        directory.mkdir(parents=True,exist_ok=True)
        self.path=directory/'budget.sqlite3'
        with closing(self.connect()) as db, db:
            db.executescript('''CREATE TABLE IF NOT EXISTS policy (id INTEGER PRIMARY KEY CHECK(id=1), total INTEGER, per_run INTEGER, halted INTEGER DEFAULT 0);
                CREATE TABLE IF NOT EXISTS calls (run_id TEXT, call_id TEXT, reserved INTEGER, actual INTEGER, PRIMARY KEY(run_id,call_id));
                CREATE TABLE IF NOT EXISTS reconciliations (run_id TEXT, call_id TEXT, actual INTEGER, receipt_hash TEXT NOT NULL, PRIMARY KEY(run_id,call_id));''')
            db.execute('INSERT OR IGNORE INTO policy(id,total,per_run) VALUES(1,?,?)',(self.total,self.per_run))
            row=db.execute('SELECT total,per_run FROM policy').fetchone()
            if tuple(row)!=(self.total,self.per_run):
                raise EvaluationError('budget_policy_mismatch','Existing budget cannot be reset by restarting.')

    def connect(self):
        return sqlite3.connect(self.path,timeout=15)

    def reserve(self, run_id: str, call_id: str, estimate: Decimal):
        value=micros(estimate)
        if not value or not run_id or not call_id:
            raise EvaluationError('invalid_budget','Positive reservation and stable identifiers required.')
        with closing(self.connect()) as db, db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute('SELECT halted FROM policy').fetchone()[0]:
                raise EvaluationError('budget_halted','Usage exceeded its reservation; review required.')
            if db.execute('SELECT 1 FROM calls WHERE run_id=? AND call_id=?',(run_id,call_id)).fetchone():
                raise EvaluationError('duplicate_call','This call was already admitted; automatic retries are disabled.')
            usage = '''SELECT COALESCE(SUM(COALESCE(r.actual,c.actual,c.reserved)),0)
                       FROM calls c LEFT JOIN reconciliations r USING(run_id,call_id)'''
            total=db.execute(usage).fetchone()[0]
            run=db.execute(usage+' WHERE c.run_id=?',(run_id,)).fetchone()[0]
            if total+value>self.total or run+value>self.per_run:
                raise EvaluationError('budget_exceeded','The next call would exceed the total or per-run limit.')
            db.execute('INSERT INTO calls VALUES(?,?,?,NULL)',(run_id,call_id,value))

    def settle(self, run_id: str, call_id: str, actual: Decimal):
        value=micros(actual); over=False
        with closing(self.connect()) as db, db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT reserved,actual FROM calls WHERE run_id=? AND call_id=?',(run_id,call_id)).fetchone()
            if row is None or row[1] is not None:
                raise EvaluationError('invalid_settlement','Missing or already settled reservation.')
            db.execute('UPDATE calls SET actual=? WHERE run_id=? AND call_id=?',(value,run_id,call_id))
            over=value>row[0]
            if over: db.execute('UPDATE policy SET halted=1')
        if over: raise EvaluationError('budget_halted','Reported usage exceeded the conservative reservation.')

    def reconcile(self, run_id: str, call_id: str, actual: Decimal, receipt_hash: str):
        """Append a verified receipt total while preserving the original settlement."""
        value=micros(actual)
        if not re.fullmatch('[0-9a-f]{64}',receipt_hash):
            raise EvaluationError('invalid_reconciliation','A saved receipt hash is required.')
        over=False
        with closing(self.connect()) as db, db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT reserved,actual FROM calls WHERE run_id=? AND call_id=?',(run_id,call_id)).fetchone()
            if row is None or row[1] is None or value < row[1]:
                raise EvaluationError('invalid_reconciliation','A reconciliation must preserve settled spend.')
            previous=db.execute('SELECT actual,receipt_hash FROM reconciliations WHERE run_id=? AND call_id=?',(run_id,call_id)).fetchone()
            if previous is not None:
                if tuple(previous)!=(value,receipt_hash):
                    raise EvaluationError('immutable_reconciliation','Receipt reconciliation already recorded.')
                return
            db.execute('INSERT INTO reconciliations VALUES(?,?,?,?)',(run_id,call_id,value,receipt_hash))
            over=value>row[0]
            if over: db.execute('UPDATE policy SET halted=1')
        if over: raise EvaluationError('budget_halted','Reconciled spend exceeded its reservation.')

    def summary(self, run_id: str | None = None) -> dict:
        where=' WHERE c.run_id=?' if run_id else ''; args=(run_id,) if run_id else ()
        with closing(self.connect()) as db:
            rows=db.execute('''SELECT c.reserved,COALESCE(r.actual,c.actual)
                FROM calls c LEFT JOIN reconciliations r USING(run_id,call_id)'''+where,args).fetchall()
        return {'reported_usd':usd(sum(a or 0 for _,a in rows)),
                'unresolved_reserved_usd':usd(sum(r for r,a in rows if a is None)),
                'committed_usd':usd(sum(r if a is None else a for r,a in rows)),
                'calls':len(rows),'total_limit_usd':usd(self.total),'per_run_limit_usd':usd(self.per_run)}
