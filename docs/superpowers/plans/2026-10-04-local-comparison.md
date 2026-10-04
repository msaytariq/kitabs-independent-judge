# Local Independent Judge implementation plan

**Goal:** Three corresponding documents → blind comparison → automatic effort forecast and source-linked hadith checks, in the isolated local stand.
**Approved brief:** User instructions in this chat: no manual minutes; select libraries ourselves; never modify the platform; local verification and explicit approval before publication.
**Architecture:** Reuse the standalone intake, scope and judge protocol. Pure domain calculations, dedicated source adapters, application orchestration, thin API and compact result components. No platform imports.
**Stack:** Existing Python/FastAPI/SQLite/httpx and Next/React; no dependency upgrades.

## Constraints
- Work only on `codex/judge-local-comparison` in this repository. Preserve pre-existing edits. No push/deploy, real paid calls, or public access in this iteration.
- No time entry and no fabricated measured time. Forecast uses explicitly uncalibrated relative effort weights, same for A/B, with sensitivity range. Missing assessment is unknown, never zero.
- Existing human-work tools remain available separately; they are not part of the comparison flow.
- Library checks distinguish text correspondence from authenticity and translation adequacy. Keep source text, source URL, retrieval time and hash. No invented source numbers.
- Live evaluation requires explicit operator configuration and budget; test the real orchestration with a deterministic provider at the network boundary.

## Task 1: Automatic forecast
Files: `domain/effort_forecast.py`, `application/comparison_view.py`, `infrastructure/comparison_report.py`, tests.
Interface: `forecast_effort(summary: dict) -> dict` consumes deduplicated anchored findings and measured assessment state, returns A/B counts, weighted units, reduction and sensitivity. Disputed/unlocated findings remain excluded and visible.
- [ ] RED: 40/10 same-type edits yield 75%; no assessment/zero denominator yields null; reversed roles can yield negative reduction; same weights apply to A/B; apparatus counts, duplicates do not.
- [ ] GREEN: implement pure calculation and expose identical data in API/export.
- [ ] Verify targeted tests and commit only this task.

## Task 2: Hadith sources
Files: `domain/hadith_matching.py`, `reference_ports.py`, `infrastructure/hadeethenc.py`, `application/hadith_verification.py`, API/bootstrap integration, tests, `docs/reference-sources.md`.
Interface: library provides title index + authoritative records; match candidates locally against Arabic source, retrieve selected IDs only; return exact/normalized/partial/review/unavailable states without an authenticity verdict.
- [ ] RED: diacritics vs missing negation; multiple candidates; no match; API failures and malformed/oversized content; no private full text sent; citations in both translations checked equally.
- [ ] GREEN: bounded adapter, automatic retrieval, output and export with provenance.
- [ ] Verify offline transport tests, public API read-only smoke, commit.

## Task 3: Local end-to-end flow and UI
Files: separate run service/store/config/routes, comparison view, frontend run hook/API/types and result components.
- [ ] RED: a new confirmed scope can run; disabled config spends nothing; duplicate clicks/restarts do not trigger duplicate calls; failure has no invented scores; status/result survives reload.
- [ ] GREEN: background local runs using existing budgeted protocol; auto-library check; compact forecast/library summaries, details collapsed. No provider selectors, timers or minute fields in main UI.
- [ ] Verify full backend/frontend tests, typecheck, production build, browser upload/result and mobile layout; review changed code and commit.

## Review focus
Unicode quote boundaries, stale results after changing inputs, ambiguous reference identity, failure/reload idempotency, uncertainty hidden by an attractive percentage. Test these at the owning boundaries.

Live model accuracy and time savings remain unvalidated until separately authorized model runs and expert evaluation. Local implementation and offline tests do not establish comparative product superiority.
