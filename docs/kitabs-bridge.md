# KITABS bridge contract

Verified against platform checkout c2ae2c4b, read only, 5 October 2026.
No production request or paid processing was performed for this integration.

## Supported contest flow

Judge opens https://app.kitabs.ai/workspace in a separate tab. Sign in there.
Upload the same Arabic fragment, select English and Autopilot, and review the
platform's price before Start. When processing and assembly finish, export the
complete result with its apparatus. Return to Judge and load it as B. Confirm
that A and B cover the same source boundaries before comparison.

The button is a workspace handoff. It does not upload a source, select a mode,
start a job or automatically return B. Repeated clicks cannot duplicate a paid
API launch because Judge makes no launch request. Keep the original tab open;
file selections and pasted materials remain in its state. A page reload requires
selecting unsaved files again. The primary example uses Autopilot, no manual review.

## Existing authenticated API

- POST /api/documents: source/target languages, rightsConfirmed and file with
  fileName, contentType, dataBase64. Requires platform authorization for ownership.
- POST /api/documents/{id}/session: get or create the document's session.
- POST /api/pipeline/jobs/{id}/prepare: preparation; can invoke paid analysis.
- POST /api/pipeline/jobs/{id}/start-stream: automatic run; step=true plus
  after_stage/after_chunk enables the existing manual step workflow.
- GET /api/pipeline/jobs/{id}: status inside job, not the legacy outer mock_ready label.
- GET/PUT /api/pipeline/jobs/{id}/audit-reviews: chunkId, stageId
  (audit/editor/proofreader), issueIndex and status. This is the latest decision
  snapshot. It has no actor/timestamp/event ID and does not prove elapsed time.
- GET/POST /api/revisions: revision text anchored to baseArtifactId/baseArtifactHash.
- GET /api/pipeline/jobs/{id}/assembly: artifacts with kind, id, hash and camelCase payload.
- POST /api/pipeline/jobs/{id}/assemble: creates assembly; not a read-only operation.
- POST /api/exports, GET /api/exports/{id}/download/{format}: existing export flow.

The optional Python KitabsPipeline adapter only reads job and assembly.
Its API origin and token must be supplied explicitly by an operator. Neither is
inferred from another project. No token is embedded in the frontend or repository.
It verifies exact extracted-source SHA-256, complete chunk membership and input
artifact references. It records the opaque platform artifact hash and independently
hashes the returned text. These are different hashes. A changed source, partial
assembly or missing evidence blocks import. Reconnecting repeats GET only.

## Limits for a seamless public bridge

The web workspace accepts a document link (?doc=...) but has no verified external
source handoff, mode selection and return callback contract. Judge cannot reuse
another origin's bearer token. A public automatic import requires scoped delegated
authorization and a return contract; a shared operator token is not acceptable.
Do not add those contracts to platform code in this task. The tested result reader
is available for local operator use, not exposed as an unauthenticated public API.
The workspace/export/upload path remains complete without this adapter.

The API does not prove the run's historical mode or exhaustive human history.
Do not label a retrieved job “manually reviewed” or infer zero human effort from
an empty status list. Five-second estimates apply to visible candidate decisions.
Hadith library matching in Judge is not the platform audit's takhrij verification.
