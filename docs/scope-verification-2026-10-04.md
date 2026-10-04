# Scope milestone — 4 October 2026

Manual selections use half-open Unicode code-point offsets in all three extracted
texts. `text_sha256` binds each range to the entire input. The response includes
selected text, its own hash, original range, profile, and sampling version.
No automatic boundary expansion is performed; the source limit is 18000 code
points. The caller must select complete corresponding passages and confirm their
alignment. Until confirmation, status is `needs_review`. Confirmation records a
human assertion; it does not prove semantic alignment.

POST `/api/comparisons/{id}/scopes`; GET `/api/scopes/{id}`.
Profiles: `general`, `islamic-scholarly`; neither needs platform metadata.
Snapshots are append-only in a separate local SQLite store. This API remains
loopback-only until session access is implemented. Frontend selection UI is pending.

Verification: 7 new tests failed with 404 before implementation; all 32 tests pass
with `.venv/bin/python -m pytest -q`. Tests cover swapped A/B previews/hashes,
stale input hashes, invalid/bool offsets, repeated text selected by explicit offset,
unconfirmed scope, unknown profiles, source size, and restart persistence.
