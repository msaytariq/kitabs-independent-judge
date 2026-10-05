"""Atomic launch claims. A missing POST response is never permission to replay."""
from contextlib import closing
import json
import sqlite3
from independent_judge.domain.errors import InputError


class PipelineJobs:
    def __init__(self, directory):
        directory.mkdir(parents=True, exist_ok=True)
        self.path = directory / 'pipeline-jobs.sqlite3'
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('CREATE TABLE IF NOT EXISTS pipeline_jobs (id TEXT PRIMARY KEY, packet TEXT NOT NULL)')

    def claim(self, request_id, packet):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT packet FROM pipeline_jobs WHERE id=?', (request_id,)).fetchone()
            if row:
                old = json.loads(row[0])
                if any(old[k] != packet[k] for k in ('source_sha256', 'source_language', 'target_language')):
                    raise InputError('pipeline_source_mismatch', 'This launch ID belongs to different material.')
                return old, False
            db.execute('INSERT INTO pipeline_jobs VALUES(?,?)', (request_id, json.dumps(packet)))
        return packet, True

    def get(self, request_id):
        with closing(sqlite3.connect(self.path)) as db:
            row = db.execute('SELECT packet FROM pipeline_jobs WHERE id=?', (request_id,)).fetchone()
        if not row:
            raise InputError('pipeline_not_found', 'Pipeline request not found.')
        return json.loads(row[0])

    def update(self, request_id, **changes):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT packet FROM pipeline_jobs WHERE id=?', (request_id,)).fetchone()
            current = json.loads(row[0])
            # A late transport exception must not undo a concurrently verified result.
            if current['status'] == 'completed' and changes.get('status') != 'completed':
                return
            packet = current | changes
            db.execute('UPDATE pipeline_jobs SET packet=? WHERE id=?', (json.dumps(packet), request_id))
