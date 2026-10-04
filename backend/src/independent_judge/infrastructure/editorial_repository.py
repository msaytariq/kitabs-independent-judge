"""Atomic local snapshots plus append-only command history and editor locks."""
from contextlib import closing
from hashlib import sha256
import json
import sqlite3
from independent_judge.domain.editorial_validation import require


def encode(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)


def fingerprint(command):
    try:
        return sha256(encode(command).encode()).hexdigest()
    except (TypeError,ValueError):
        require(False,'Commands must contain valid finite JSON values.')


class SqliteEditorialRepository:
    def __init__(self,directory):
        directory.mkdir(parents=True,exist_ok=True)
        self.path=directory/'editorial.sqlite3'
        with closing(sqlite3.connect(self.path)) as db,db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS reviews(id TEXT PRIMARY KEY,revision INTEGER NOT NULL,state TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS editorial_events(review_id TEXT,revision INTEGER,command_id TEXT,
              fingerprint TEXT NOT NULL,event TEXT NOT NULL,PRIMARY KEY(review_id,revision),UNIQUE(review_id,command_id));
            CREATE TABLE IF NOT EXISTS active_editors(actor TEXT PRIMARY KEY,review_id TEXT);
            ''')

    def create(self,state,command):
        with closing(sqlite3.connect(self.path)) as db,db:
            db.execute('INSERT INTO reviews VALUES(?,?,?)',(state['id'],0,encode(state)))
            self._event(db,state,command)
        return state

    def get(self,ident):
        with closing(sqlite3.connect(self.path)) as db:
            row=db.execute('SELECT state FROM reviews WHERE id=?',(ident,)).fetchone()
        return json.loads(row[0]) if row else None

    def _previous(self,db,ident,command):
        row=db.execute('SELECT fingerprint FROM editorial_events WHERE review_id=? AND command_id=?',
                       (ident,command['command_id'])).fetchone()
        if not row: return None
        require(row[0]==fingerprint(command),'Command ID already used with different content.','editorial_conflict')
        return json.loads(db.execute('SELECT state FROM reviews WHERE id=?',(ident,)).fetchone()[0])

    def previous_command(self,ident,command):
        with closing(sqlite3.connect(self.path)) as db:
            return self._previous(db,ident,command)

    def append(self,state,expected_revision,command):
        with closing(sqlite3.connect(self.path,timeout=10)) as db,db:
            db.execute('BEGIN IMMEDIATE')
            previous=self._previous(db,state['id'],command)
            if previous is not None: return previous
            changed=db.execute('UPDATE reviews SET revision=?,state=? WHERE id=? AND revision=?',
                (state['revision'],encode(state),state['id'],expected_revision)).rowcount
            require(changed==1,'Review changed in another tab. Reload before continuing.','editorial_conflict')
            db.execute('UPDATE active_editors SET review_id=NULL WHERE review_id=?',(state['id'],))
            for s in state['sessions']:
                if s['status']!='running': continue
                actor=s['actor'].casefold()
                owner=db.execute('SELECT review_id FROM active_editors WHERE actor=?',(actor,)).fetchone()
                require(owner is None or owner[0] is None or owner[0]==state['id'],
                        'This editor already has a running timer in another review.','editorial_conflict')
                db.execute('INSERT INTO active_editors VALUES(?,?) ON CONFLICT(actor) DO UPDATE SET review_id=excluded.review_id',
                           (actor,state['id']))
            self._event(db,state,command)
        return state

    def _event(self,db,state,command):
        event={'revision':state['revision'],'at_ms':state['updated_at_ms'],'command':command}
        db.execute('INSERT INTO editorial_events VALUES(?,?,?,?,?)',
            (state['id'],state['revision'],command['command_id'],fingerprint(command),encode(event)))

    def events(self,ident):
        with closing(sqlite3.connect(self.path)) as db:
            rows=db.execute('SELECT event FROM editorial_events WHERE review_id=? ORDER BY revision',(ident,)).fetchall()
        return [json.loads(row[0]) for row in rows]
