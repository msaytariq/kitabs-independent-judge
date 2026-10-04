# Editorial workbench verification — 4 October 2026

## Delivered and checked

A separate local Next.js workbench now connects confirmed three-text scopes to
human editorial work. It preserves original versions, exact task anchors, decisions,
server-timestamped intervals, declared prior work and final acceptance. It does not
invoke the judge or import its findings automatically.

- Backend: **84 passed**, six existing dependency deprecation warnings (SWIG and
  Starlette/httpx). New rules were checked failing before implementation.
- Frontend: **4 passed**; TypeScript and production build pass without warnings.
- Clean frontend copy: `npm ci --offline --ignore-scripts` installs the locked 29
  packages, all four tests pass, and a production build succeeds independently of
  the platform. Python runtime dependencies were unchanged from the verified lock.
- Browser engineering control: create comparison, start/pause/stop timer, save a
  second version, reload paused state, anchor a task, resolve it, verify, accept A,
  export JSON. Export revision 9 has 10 events and two A snapshots. Unknown history
  correctly leaves savings unavailable. No browser console errors were observed.
- Responsive inspection: observed CSS widths 325 and 1200 pixels have no page-level
  horizontal overflow. Tables may scroll within their own panels on narrow screens.
- Real HTTP: local frontend/backend return 200; a nonlocal Host returns 403 for
  both the HTML entry point and the frontend API proxy.
- Three private real-text workspaces were prepared from the existing hashed
  Al-Ghazali packet. Input hashes match. All have zero sessions, unknown prior
  effort and no acceptance. They are prepared materials, not new evaluation results.

## Verification commands

```sh
.venv/bin/python -m pytest -q
npm --prefix frontend test
npm --prefix frontend run typecheck
NEXT_TELEMETRY_DISABLED=1 npm --prefix frontend run build
git diff --check
```

The clean-copy installation also used `npm ci --offline --ignore-scripts` with a
populated temporary npm cache. Fresh users can use `npm ci --ignore-scripts` online.
The current owner's local instance uses API port 8766 and browser port 3005; the
portable README defaults to API port 8765. Set `JUDGE_API_ORIGIN` during the build
when changing the API port.

## Responsibilities and changed files

Backend routes/schemas expose a typed envelope. The service coordinates confirmed
scopes and a repository port. Domain files separately own validation, versions and
decisions, session intervals and metrics. The SQLite adapter owns transactions,
revision conflicts, idempotency, persistence and editor locks. Bootstrap composes
these parts; HTTP middleware is limited to local access checks.

Frontend `shared/api` is the HTTP client, `shared/types` describes the contract and
`shared/server` validates the proxy host. `useEditorialReview` owns loading/errors/
commands. Components each render one workflow responsibility: entry, session,
prior work, tasks, version editing, metrics and page composition. Helpers own
Unicode offsets and time presentation. App files compose layout/styles, and
middleware protects the local proxy. Package and lock files pin the runtime.

Documentation states behavior, operator steps and limitations. Tests cover the
boundaries and calculations rather than claiming scholarly quality.

Modified files:

- `.gitignore`
- `README.md`
- `backend/src/independent_judge/api/app.py`
- `backend/src/independent_judge/api/errors.py`
- `backend/src/independent_judge/bootstrap.py`
- `docs/architecture.md`
- `tests/test_intake.py`

Created files:

- `backend/src/independent_judge/api/editorial_review.py`
- `backend/src/independent_judge/api/editorial_schemas.py`
- `backend/src/independent_judge/api/local_access.py`
- `backend/src/independent_judge/application/editorial_review.py`
- `backend/src/independent_judge/domain/editorial_metrics.py`
- `backend/src/independent_judge/domain/editorial_sessions.py`
- `backend/src/independent_judge/domain/editorial_validation.py`
- `backend/src/independent_judge/domain/editorial_work.py`
- `backend/src/independent_judge/editorial_ports.py`
- `backend/src/independent_judge/infrastructure/editorial_repository.py`
- `docs/editorial-operator-checklist.md`
- `docs/editorial-verification-2026-10-04.md`
- `docs/editorial-workbench-contract.md`
- `frontend/app/layout.tsx`
- `frontend/app/page.tsx`
- `frontend/app/styles.css`
- `frontend/middleware.ts`
- `frontend/next-env.d.ts`
- `frontend/next.config.mjs`
- `frontend/package-lock.json`
- `frontend/package.json`
- `frontend/src/features/editorial/EditorialWorkbench.tsx`
- `frontend/src/features/editorial/PriorWork.tsx`
- `frontend/src/features/editorial/SessionControls.tsx`
- `frontend/src/features/editorial/StartReview.tsx`
- `frontend/src/features/editorial/TaskList.tsx`
- `frontend/src/features/editorial/TimeSummary.tsx`
- `frontend/src/features/editorial/VersionEditor.tsx`
- `frontend/src/features/editorial/helpers.mjs`
- `frontend/src/features/editorial/useEditorialReview.ts`
- `frontend/src/shared/api/editorial.ts`
- `frontend/src/shared/server/local-access.mjs`
- `frontend/src/shared/types/editorial.ts`
- `frontend/tests/editorial.test.mjs`
- `frontend/tests/local-access.test.mjs`
- `frontend/tsconfig.json`
- `tests/test_editorial_workbench.py`

## Limits and next work

This is a local, operator-controlled stand, not authenticated jury access. A timer
measures declared working intervals, not attention; operators must start it before
reading/research and pause during breaks. Historic effort remains unknown without
records. Human acceptance is attributed, not independently certified. SQLite logs
preserve application history but are not tamper-proof against machine administrators.

Separate Farah notes and Quran/hadith references are still in the prepared packet;
they have not been automatically attached to these workspaces or passed through a
new reference-aware judge run. Automatic pilot-finding import, public session
access, PDF reports, redistribution clearance and final public release remain open.
The Sonnet pilot shares a model family with the historical Kitabs translation, so
it must not be called a fully independent-family test. No new paid requests were
made in this milestone. Previous total spend remains $0.313172 of the $3 budget.

Main platform code, VPS, original books and existing artifacts were not changed or
deleted. Engineering timer results are excluded from the real showcase.
