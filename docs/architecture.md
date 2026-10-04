# Local intake architecture

```text
HTTP routes -> IntakeService -> domain models + ports
                    ^                   ^
                 bootstrap -> local extraction / SQLite adapters
```

- `api/app.py` composes the HTTP application; `api/inputs.py` contains thin routes.
- `api/uploads.py` bounds each upload read; `api/body_limit.py` bounds the complete
  actual request before JSON or multipart parsing, including chunked uploads.
- `api/schemas.py` exposes only the deliberate preview fields;
  `api/errors.py` translates domain errors into actionable HTTP responses.
- `application/intake.py` validates the complete triple before extraction and
  stores only after all three inputs have succeeded.
- `domain/inputs.py` defines immutable values and limits; `domain/errors.py`
  defines failures independently of the HTTP framework.
- `ports.py` defines extraction and repository interfaces.
- `infrastructure/text_extractors.py` selects a format adapter.
  DOCX and PDF parsing have their own modules under `infrastructure/formats/`.
- `infrastructure/sqlite_repository.py` stores comparison metadata, extracted
  text and original bytes in one transaction in `JUDGE_DATA_DIR/comparisons.sqlite3`.
- `bootstrap.py` wires the local implementations. No platform package, provider
  client, billing service or platform database is imported.

`sha256` identifies extracted UTF-8 text, which later range selections will
address. `file_sha256` identifies the exact original upload. UTF-8 BOM removal
affects text extraction only; original bytes are retained. Other TXT/MD spacing
and line endings are preserved. There are no update/delete endpoints in this
milestone.

The next stages add confirmed ranges, the assessment protocol, run manifests,
session access, cost admission and the jury UI. This intake milestone is intended
for a single local operator and is not ready for public hosting.
