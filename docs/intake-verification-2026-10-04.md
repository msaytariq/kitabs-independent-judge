# Intake milestone verification — 4 October 2026

Scope: independent upload/paste, extraction and SQLite persistence. This is not
verification of translation scoring, hosted access or the final contest product.

## Test-first evidence

- Initial intake checks: 20 failed against an empty API, then 20 passed.
- Additional boundary checks: 5 failed before implementation, then the complete
  suite passed with 25 tests in the standalone environment.
- Dependency warnings: five PyMuPDF SWIG deprecations and one Starlette TestClient
  httpx deprecation; no dependency upgrade was performed to suppress them.

## Commands

```sh
.venv/bin/python -m pytest -q -p no:cacheprovider
git diff --check
```

Covered behaviors: upload/paste, persistence after restart, original byte storage,
UTF-8 and hashes, separate data directory, no outbound connection during intake,
invalid formats, empty input, missing original, oversized file/request, corrupt
DOCX, DOCX archive expansion and pending revisions, footnotes/endnotes, PDF text
extraction and missing text pages, filename metadata, atomic failure.

## Independent installation

Copied only the standalone backend, tests and pytest configuration into a new
temporary directory. Created a fresh Python 3.12.12 environment, installed the
25 pinned dependencies and a built standalone package without dependency access
to the parent project. All 26 installed distributions passed the package
compatibility check. Python isolated mode confirmed that `kitabai` is absent and
`independent_judge` is imported from the new environment's site-packages.

The entire test suite passed there: **25 passed, 6 dependency warnings**.

## Real local HTTP

Started the installed package with Uvicorn on a loopback socket and a new data
directory. `GET /health` returned intake mode with live disabled.
`POST /api/comparisons/text` returned 201; `GET` by comparison ID returned the
same draft, preserving the Arabic input. The test server was stopped afterward.
Only loopback traffic was used; no model request was made.

## Limits of this checkpoint

The code received a local author review. No separate agent review was requested.
This verifies intake, not the assessment protocol. Public hosting still requires
session access, run admission and the later release checks.
