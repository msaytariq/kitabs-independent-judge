# Editorial workbench, 4 October 2026

Implementation of the owner-approved editorial-effort methodology. This is a
local operator workbench; public jury sessions and hosted deployment remain pending.

- A review binds one confirmed scope and one immutable publication rubric to A/B.
- Initial versions, subsequent text snapshots and editor decisions remain available.
- A server-timestamped, operator-controlled timer records editing and final review
  intervals. Pauses do not count. It measures declared work intervals, not attention.
- One running interval per editor across workspaces. Actor labels are self-declared
  on this local stand, not authenticated identities.
- Save requires an active editing session and matching revision/text hash. Final
  acceptance requires a completed verification of that exact version and no pending
  tasks. Later edits invalidate acceptance and earlier task decisions.
- Previous human work defaults to unknown. Explicit no-prior-work or a documented
  self-report may be recorded; self-report and timer measurements stay separate.
- Total savings are unavailable until both sides meet the same rubric, all prior
  time is known, all timers are stopped, and A's total is positive. Negative savings
  are retained. Counts of findings are never converted into predicted minutes.
- Persist append-only events and full snapshots transactionally in a separate
  editorial SQLite file; optimistic revisions and command IDs prevent lost updates
  and repeated actions. Export includes provenance, versions, events and limitations.
- A browser workspace supports pasted text or an existing scope, review tasks,
  editing, timing, explicit acceptance and JSON evidence export. No automatic LLM call.

Implementation order: boundary/API tests RED, domain/ports/storage/service GREEN,
then a focused Next.js client and browser acceptance. Keep modules by responsibility.
Tests cover stale revisions, idempotency, pause accounting, overlapping editor
sessions, unknown prior time, re-edit invalidation, attribution and negative savings.
