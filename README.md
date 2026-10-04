# Independent Judge

Compare two translations or edited versions against their source, using the same
assessment rules for both. Materials may come from KITABS.AI or external sources.

**Current milestone — 4 October 2026:** standalone intake, confirmed text ranges,
and an operator-only evaluation pilot with Claude Sonnet 5.5 through Vercel AI
Gateway. Three blind passes per translation, critical appeals, cross-checks and
shared source-unit coverage produce an immutable report and cost receipts.
The jury interface, session access, PDF export and public demo remain pending.

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

## Bounded evaluation pilot

Create a confirmed scope with `POST /api/comparisons/{id}/scopes` (see
[scope contract](docs/scope-verification-2026-10-04.md)). Offsets are Unicode code
points, not UTF-16 browser offsets. Each range includes the entire input text hash.
Check the three previews before setting `confirmed: true`.

```sh
.venv/bin/python -m independent_judge.cli --scope-id SCOPE_ID --run-id UNIQUE_RUN_ID
```

This preflight makes no model call. To run, supply `AI_GATEWAY_API_KEY`,
`JUDGE_BUDGET_TOTAL_USD` and `JUDGE_BUDGET_RUN_USD` securely in the process environment,
then add `--live`. An explicit example budget is total `3`, per-run `1` USD.
`--translator-a-vendor` / `--translator-b-vendor` record known model families;
omitted provenance remains unknown. Use the same data directory for all budgeted
runs. Changing the data directory creates a different ledger; this operator CLI
is not a multi-tenant billing boundary.

Live runs require a clean committed checkout. Failed/uncertain calls are not
silently retried; unresolved cost reservations stay held. Duplicate run IDs cannot
trigger another request. Reports and raw receipts stay in the private data
folder, never Git. An incomplete run has no final scores. See
[protocol and limitations](docs/evaluation-protocol.md).

A [real Sonnet 5.5 pilot](docs/sonnet-pilot-2026-10-04.md) completed on 4 October: 15 calls in the full protocol, status `needs_review`. All attempts cost $0.313172. Findings require review; this is not a validated platform ranking.
