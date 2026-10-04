# Independent Judge

Compare two translations or edited versions against their source, using the same
assessment rules for both. Materials may come from KITABS.AI or external sources.

**Current milestone — 4 October 2026:** a runnable local intake API. It accepts
three documents or pasted texts, extracts preview text and stores an immutable
draft with original bytes and SHA-256 hashes in its own SQLite database.
Evaluation, the jury interface, session access and the public demo are subsequent
milestones. This version makes no model calls and does not score translations.

## Local setup

Python 3.12 or newer is required. Run from this repository's root:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.lock.txt
.venv/bin/python -m pip install --no-build-isolation --no-deps -e backend
JUDGE_DATA_DIR="$PWD/.judge-data" .venv/bin/python -m uvicorn independent_judge.api.app:create_app --factory --host 127.0.0.1 --port 8765
```

Open `http://127.0.0.1:8765/docs` for the interactive upload API.
`GET /health` reports `stage: intake` and `live_enabled: false`.
Bind only to loopback: this milestone has no session authorization and must not
be exposed on a public host. Use a new data directory, never a platform database.
Environment variables are read from the process; `.env.example` is a reference,
not an automatically loaded configuration file.

## Try three documents

```sh
curl --fail-with-body http://127.0.0.1:8765/api/comparisons \
  -F 'source=@original.txt' \
  -F 'a=@version-a.txt' \
  -F 'b=@version-b.txt' \
  -F 'source_language=ar' \
  -F 'target_language=en'
```

The response contains an ID, `draft` status and extracted text for each role.
Retrieve it with `GET /api/comparisons/{id}`. Pasted text uses
`POST /api/comparisons/text` with JSON fields `source`, `a`, `b`,
`source_language` and `target_language`.

Supported inputs: UTF-8 TXT/MD, DOCX and PDF with a selectable text layer.
Each input is limited to 20 MiB; the entire HTTP request is limited to 61 MiB.
No OCR, translation or external network request is triggered by upload.

Always inspect the extracted text. PDF layout/reading order can differ from the
page. A PDF page without text requires manual review; even an intentionally blank
page needs handling before this version accepts the PDF. DOCX paragraphs, table
paragraphs, footnotes and endnotes are supported; headers, footers, comments and
text inside images are excluded and reported as extraction warnings. Resolve
tracked text revisions before uploading DOCX. Expanded DOCX size is limited to
80 MiB.

## Verify

```sh
.venv/bin/python -m pytest -q
git diff --check
```

The tests cover persistence across restarts, original byte/text hashes, parser
errors, size limits, notes, missing PDF text pages and intake with outbound
connections disabled. Test fixtures are engineering controls, not a showcase
or evidence of translation quality.

See [architecture](docs/architecture.md), [baseline](BASELINE.md) and the
[milestone verification](docs/intake-verification-2026-10-04.md).
