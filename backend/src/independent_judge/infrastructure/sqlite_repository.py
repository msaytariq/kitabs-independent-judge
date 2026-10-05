"""Persist drafts and original bytes together in a dedicated SQLite database."""
from contextlib import closing
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from uuid import uuid4

from independent_judge.domain.inputs import Comparison, InputTriple, MaterialInput


class SqliteComparisonRepository:
    def __init__(self, data_dir: Path):
        data_dir.mkdir(parents=True, exist_ok=True)
        self.path = data_dir / "comparisons.sqlite3"
        with closing(self._connect()) as db, db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS comparisons (
                    id TEXT PRIMARY KEY, source_language TEXT NOT NULL,
                    target_language TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS materials (
                    id TEXT PRIMARY KEY, comparison_id TEXT NOT NULL REFERENCES comparisons(id),
                    role TEXT NOT NULL CHECK(role IN ('source', 'a', 'b')),
                    text TEXT NOT NULL, sha256 TEXT NOT NULL, filename TEXT NOT NULL,
                    file_sha256 TEXT NOT NULL, content_type TEXT NOT NULL, content BLOB NOT NULL,
                    warnings TEXT NOT NULL, UNIQUE(comparison_id, role)
                );
            """)
            columns = {r[1] for r in db.execute("PRAGMA table_info(materials)")}
            if "metadata" not in columns:
                db.execute("ALTER TABLE materials ADD COLUMN metadata TEXT NOT NULL DEFAULT '{}'")

    def _connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        return db

    def create(self, inputs: InputTriple) -> str:
        comparison_id = uuid4().hex
        with closing(self._connect()) as db, db:
            db.execute("INSERT INTO comparisons VALUES (?, ?, ?, ?)", (
                comparison_id, inputs.source_language, inputs.target_language,
                datetime.now(timezone.utc).isoformat(),
            ))
            for m in inputs.materials:
                db.execute("INSERT INTO materials VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (
                    m.id, comparison_id, m.role, m.text, m.sha256, m.filename,
                    m.file_sha256, m.content_type, m.content, json.dumps(m.warnings),
                    json.dumps({"page_count": m.page_count, "provenance": m.provenance}),
                ))
        return comparison_id

    def get(self, comparison_id: str) -> Comparison | None:
        with closing(self._connect()) as db:
            row = db.execute("SELECT * FROM comparisons WHERE id = ?", (comparison_id,)).fetchone()
            if row is None:
                return None
            items = db.execute("SELECT * FROM materials WHERE comparison_id = ?", (comparison_id,)).fetchall()
        materials = {}
        for item in items:
            values = dict(item)
            values.pop("comparison_id")
            values["warnings"] = tuple(json.loads(values["warnings"]))
            values.update(json.loads(values.pop("metadata")))
            materials[item["role"]] = MaterialInput(**values)
        return Comparison(
            id=row["id"], created_at=row["created_at"],
            inputs=InputTriple(**materials, source_language=row["source_language"],
                               target_language=row["target_language"]),
        )
