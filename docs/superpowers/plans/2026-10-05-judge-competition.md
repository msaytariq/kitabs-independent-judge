# Independent Judge competition implementation plan

**Goal:** Deliver a standalone A/B comparison with 100-point results and optional KITABS processing for B.
**Architecture:** Domain rules own scores and effort calculations. Application services coordinate intake and pipeline jobs. Adapters handle network and storage. React renders results through typed API clients.
**Tech stack:** Existing Python/FastAPI backend and Next.js/React frontend. Reuse the current Gateway port and test environment.
**Spec:** `docs/2026-10-05-judge-handoff.md`.
**Boundary:** All edits stay in this nested repository. Platform code is read-only. Publish only after owner approval.

## 1. Inspect the baseline and freeze the rating contract

Read the current repository status and existing standalone tests.
Read the platform rating specification and API contracts listed in the handoff.
Document the chosen 0–100 mapping, criterion formulas, missing-data rules, and rubric version in `docs/rating-method.md`.
Keep the existing 70/30 total semantics unless a justified rubric revision is explicitly identified.
Explain how separate criterion scores relate to that total; do not average overlapping metrics by accident.
Define structural apparatus coverage separately from correctness.
Identify the existing KITABS authenticated launch, status, human decisions, and final-artifact contracts.
Resolve the ten-page rule for PDF and text inputs without silent clipping.
Inspect extraction responsibilities before choosing exact URL intake changes.
This task must not mutate platform configuration or run paid models.

## 2. Implement scores with TDD

Create `tests/test_ratings.py` and `backend/src/independent_judge/domain/ratings.py`.
Write failing tests for 0/100 bounds, ties, missing assessments, identical texts, and scaling legacy scores.
Test that swapping A/B evidence swaps deterministic results without changing their values.
Test that irrelevant apparatus and missing source notes cannot create unsupported correctness claims.
Test that disputed/unlocated findings do not silently become confirmed penalties.
Implement the smallest deterministic scoring module consistent with Task 1.
Extend `application/comparison_view.py` and `frontend/src/shared/types/comparison.ts` for versioned ratings.
Add projection tests to `tests/test_comparison_view.py`; do not invent ratings for unsupported saved reports.
Run targeted tests, inspect staged diff, and commit only this iteration.

## 3. Implement explicit effort estimates with TDD

Create `tests/test_decision_effort.py` and `backend/src/independent_judge/domain/decision_effort.py`.
Test 12 unique decisions → 60 estimated seconds under the five-second assumption.
Test that accept and reject events count once; retries/reloads do not duplicate events.
Test separation of prior KITABS work from final correction candidates.
Test unknown historical work, zero denominators, and cases where B needs more work.
Keep forecasts separate from measured durations and confirmed necessary edits.
Extend the comparison projection and `EffortSummary.tsx`; remove no unrelated legacy flow.
Add frontend assertions for the estimate label and absence of manual minute inputs in the main flow.
Run targeted checks and create a focused commit.

## 4. Complete input parity with TDD

Extend `OwnMaterials.tsx` and the existing intake application/API modules after inspecting their contracts.
Keep file, paste, and URL methods in the same compact input component.
Create a dedicated URL retrieval adapter; do not put network calls in domain or React rendering code.
Add URL tests in `tests/test_url_intake.py`: valid document, unsupported content, timeout, oversize response,
private/loopback address rejection, and redirect revalidation.
Extend `tests/test_scope.py` for page limits, source bounds, and unmatched translation fragments.
Preserve source text, footnotes, extraction provenance, and artifact hashes.
Use deterministic HTTP fixtures. Do not fetch private books into the public repository.
Run targeted checks and commit.

## 5. Add the optional KITABS bridge with TDD

Create a pipeline port, an application use case, and an adapter to the verified existing contract.
Suggested modules: `pipeline_ports.py`, `application/pipeline_b.py`, `infrastructure/kitabs_pipeline.py`.
Create `tests/test_pipeline_b.py` before implementing behavior.
Test automatic/manual selection, missing authorization, job failure, and an unfinished B artifact.
Test duplicate start prevention, reconnect behavior, and final source/artifact hash matching.
Test that manual-mode provenance requires actual human event records.
The standalone backend must never access the platform database directly.
Add the “Обработать на Kitabs.ai” action inside B's input area with a compact status display.
Reuse the platform's existing review workflow where its contract permits it.
Preserve the upload-B path when KITABS credentials are absent.
Offline adapter tests prove the contract handling, not a live end-to-end run.
If an existing API is insufficient, document the exact blocker without changing platform code.
Run targeted checks and commit.

## 6. Present one clear result and verify the complete flow

Create `QualityTable.tsx` and a small pure view-model helper under the comparison feature.
Update `ComparisonResult.tsx` to show A/B criterion scores, total, work estimates, and a short conclusion.
Keep finding excerpts and source details expandable. Preserve accessible headings and Arabic direction.
Add frontend tests for A winning, B winning, ties, incomplete evidence, and swapped sides.
Use source-linked findings for the conclusion; do not make another paid call just for promotional prose.
Test the full offline flow with a deterministic provider fixture and visibly label demonstration data.
Inspect the browser at desktop and narrow widths, including errors and the optional processing state.
Run `.venv/bin/python -m pytest -q`, frontend test/typecheck/build, and `git diff --check`.
Inspect final outputs and staged changes before the local commit.

## 7. Prepare a reviewable release

Add only permitted synthetic/licensed examples and reproducible setup instructions.
Verify a clean clone can build and compare uploaded A/B without private platform source.
Record baseline and development commit hashes in the release description with accurate dates.
Report separately: implemented, locally tested, live-tested, and awaiting approval.
Prepare the public-repository diff and `/judge` hosting plan for owner review.
Do not expose platform source, secrets, local book data, or unrelated changes.
Do not claim deployment, proven time savings, model independence, or takhrij accuracy without evidence.
Request the remaining publication/live-test approval only after the local deliverable is concrete.
