# Standalone architecture

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

Confirmed scopes, the operator assessment protocol and cost ledger are implemented
in separate domain/application/infrastructure modules. The local editorial
workbench is a second, provider-free use case:

```text
React components -> editorial hook -> shared/api/editorial.ts
  -> API editorial router -> EditorialService -> domain editorial rules
                                          -> EditorialRepository port
bootstrap -> SqliteEditorialRepository (separate editorial.sqlite3)
```

The domain separates sessions, versions/decisions and metrics. An immutable scope
and rubric define the review. Text snapshots and an append-only command log retain
history; one atomic transaction updates the current state, revision and editor lock.
The store enforces one running timer per self-declared actor across reviews.

Frontend components render and collect input; the hook owns requests and current
state. Only `src/shared/api` performs HTTP calls. The API and browser proxy both
check loopback Host headers. No credentials or provider client are in the browser.

Public session authentication, reference attachment/import and hosted jury access
remain pending. Local labels are not authenticated identities, and version/hash
history is not a cryptographic attestation against a local database administrator.
