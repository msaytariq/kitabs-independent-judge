# Independent Judge: agreed direction and handoff

Date: 2026-10-05. Owner requested this handoff and continuation in a new chat.
This document records requirements and evidence. It does not claim delivery of pending features.

## Goal

Compare two English translations against the same Arabic source.
Show which text needs less work to reach the same publication standard.
Evaluate source fidelity, terminology, readability, and scholarly apparatus.
Use a transparent 100-point scale and source-linked evidence.
KITABS.AI is a book-production platform. Its scientific apparatus is a central demonstration feature.
A future international standard is an ambition, not a validated status of this prototype.

## User flow

1. Load an Arabic source fragment of at most 10 pages.
2. Load English Text A by file, pasted text, or URL.
3. Load English Text B by the same methods, or select “Обработать на Kitabs.ai”.
4. For KITABS processing, select automatic or manual mode before starting.
5. In manual mode, review suggestions from audit, editor, and proofreader stages.
6. Compare the final A and B texts against the same source fragment.
7. Read one comparison table and a short evidence-based conclusion.

A and B may come from any vendor or a human translator.
Existing KITABS output can be loaded directly as B.
Manual pipeline output is the primary demonstration. Autopilot output is a secondary case.
Do not start comparison before B exists as a completed artifact.
Keep sources, methodology, stage history, and individual findings in expandable details.
Do not add a separate dashboard of configuration options to the main flow.

## Result contract

The table has two result columns: Text A and Text B.
Include overall quality, source fidelity, terminology, readability, and scholarly apparatus scores on a 0–100 scale.
Include accepted/rejected human decisions when event records exist.
Include estimated decision time and remaining correction candidates as separate values.
Use “not assessed” when required evidence is missing. Missing evidence is not a zero score.
Explain strengths and weaknesses with exact excerpts from the compared texts and source.
Allow A to win, B to win, or a tie. Do not require a promotional conclusion.
Hide producer/model labels from the judging input. Record model and rubric versions for reproducibility.
Do not claim model-family independence unless production and judge provenance confirms it.

The platform currently has a 0–10 rating: accuracy 70%, apparatus 30%.
Its apparatus score counts notes, glossary entries, and narrator notes.
This measures structural provision, not scholarly correctness or hadith authenticity.
Preserve that distinction when extracting the rating into the standalone repository.
Multiplying an existing rating by 10 changes its scale only.
Separate terminology/readability ratings need explicit versioned rules and tests.
Select the final rubric after inspecting the existing specification; do not invent approved weights.
Do not reward irrelevant added notes or treat apparatus quantity as verified quality.

## Human effort

The owner proposes 5 seconds per accept/reject decision.
Estimated decision time = unique human decisions × 5 seconds.
Label this number “estimate, assuming 5 seconds per decision”.
Do not call this measured editing time or total publication time.
Count prior human work within KITABS as well as remaining work when claiming an end-to-end comparison.
Show prior actions separately from remaining correction candidates. Avoid double counting.
An AI finding is a candidate; it is not a confirmed required correction.
Unknown historical work for either side stays unknown, not zero.
Do not request manual minute entry. Automatic event timing may supplement the estimate where implemented.
Reading, research, and writing time are not covered by the 5-second assumption.

## Reference libraries

The owner asked us to select and prepare reference sources.
The chosen interim source is https://github.com/fawazahmed0/hadith-api.
Standalone source matching exists for Arabic Bukhari and Muslim records.
This library is not integrated into the platform audit pipeline.
No contest claim of proven takhrij accuracy is permitted on that basis.
Preserve source URL, collection, numbering, retrieved text, timestamp, and hash.
No match does not mean an inauthentic hadith. A match does not verify the English translation.
Sunnah access request: https://github.com/sunnah-com/api/issues/4016.
No API access was confirmed in the preceding work. Recheck only if required for the task.

## Repository and authorization boundaries

Work only in `/Users/marat/Documents/KitabAI-v2/standalone/independent-judge`.
This is a separate Git repository, branch `codex/judge-local-comparison`.
Treat `/Users/marat/Documents/KitabAI-v2` platform code as read-only reference.
Do not edit other worktrees, platform databases, or live services.
Read the root AGENTS.md. Inspect current status before changes.
The owner authorizes local improvements and TDD, plus this new-chat handoff.
Keep changes in focused local commits with verification in commit bodies.
Public GitHub and https://app.kitabs.ai/judge are delivery targets.
They are not evidence of a deployed standalone version.
Preserve the owner's earlier gate: local review and approval before publication or jury demonstration.
Push, deployment, platform changes, and paid processing need appropriately scoped authorization.
Do not block offline implementation while waiting for deployment approval.

The comparison must build and accept uploaded A/B without access to private platform code.
The optional KITABS button can use an existing authenticated API/workflow through an adapter.
First inspect that public-facing contract. Do not invent endpoints or pretend a mock is live integration.
If the contract cannot support this flow without platform changes, report the specific boundary.
Prepare the standalone adapter and tests locally; keep imported B as the working path.

## Verified starting point

Latest implementation commit at handoff: `bd0745f`.
Earlier commits: `c8a3744` effort forecast, `30af922` hadith source verification.
Local stand supports file/paste intake, confirmed source ranges, saved comparison evidence,
background judge execution with budget gates, source matching, and a compact result screen.
URL intake, a 100-point rubric/table, and the KITABS processing button remain to implement here.
The existing relative effort forecast uses uncalibrated category weights. It is not a measured time saving.
The current 18,000-character source cap represents ten 1,800-character units, not ten physical PDF pages.
Define page handling explicitly. Never silently truncate source or mislabel character units as physical pages.
Prior verification reported 146 Python tests, 14 frontend tests, and TypeScript passing.
These historical results are not a substitute for fresh checks after changes.
Live model accuracy and the production `/judge` deployment were not established by those checks.

Existing unrelated changes to preserve:

- Modified `README.md` and `frontend/src/features/comparison/ComparisonScreen.tsx`.
- Untracked `docs/first-editorial-measurement-2026-10-04.md`.
- Untracked `frontend/src/features/comparison/useComparisonReveal.ts`.

Local start/check instructions: `docs/local-comparison.md`.
Last preview ports: frontend 3015, backend 8775, loopback only; recheck process state.
Private `.judge-data` examples are not included in a clean clone.
Prepare licensed or synthetic offline fixtures for public reproducibility.
The production model remains disabled by default. Never publish keys or private books.

## Existing code to inspect

Standalone: `domain/comparison_summary.py`, `domain/effort_forecast.py`, `domain/scope.py`,
`application/comparison_view.py`, `application/local_evaluation.py`, and `runtime_evaluation.py`
under `backend/src/independent_judge/`.
UI: `frontend/src/features/comparison/{JudgeScreen,OwnMaterials,ComparisonResult,EffortSummary}.tsx`.

Platform reference only:

- `backend/src/kitabai/domain/quality_protocol/rating.py` and `apparatus_inventory.py`.
- `docs/discrepancy-protocol/spec.md` for the existing agreed rating contract.
- `frontend/src/features/compare/intake/SideUpload.tsx` for file/URL intake behavior.
- `frontend/src/shared/api/{qualityProtocolApi,documentsApi,pipelineApi,pipelineStreamApi}.ts`.
- `frontend/src/features/compare/result/ResultInstrument.tsx` for stage/model provenance.
- Corresponding backend routes and application services for actual integration contracts.

## Communication and method

Use short Russian progress updates. Use plain English for competition reports.
Apply ASD-STE100 principles: stable terms, short sentences, one action per instruction.
Do not claim formal STE compliance without a complete terminology and rule review.
STE guides explanations and requirements. It does not establish translation quality.
Use TDD: failing behavioral test, minimal implementation, passing checks, then refactor and commit.
See `superpowers/plans/2026-10-05-judge-competition.md` for the implementation order.

Sources: https://www.asd-ste100.org/STE_faq.html and https://islamicaich.org/terms.
Competition terms permit pre-existing projects with a disclosed baseline and documented new work.
Record authentic commit history. Do not backdate progress or present baseline features as new work.
