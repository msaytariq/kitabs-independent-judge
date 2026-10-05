# Independent Judge: local release candidate

## Scope

A standalone Arabic-source / English-A / English-B comparison. The jury screen
supports English and Russian. Inputs can independently use text, file or public
URL. Results show one 0–100 table, provisional index leader, correction candidates
and the five-second decision hypothesis. Exact excerpts and limitations expand
on request. Optional B processing opens the existing KITABS workspace.

The underlying KITABS comparison methodology predates this contest; see
[BASELINE](../BASELINE.md). Development before this continuation ends at bd0745f;
the user-requested handoff is a990d85. New work on 5 October 2026:

- 5dfa72f: versioned 100-point indices, preserving the 70/30 allocation.
- 2ecf843: prior decisions separated from remaining five-second estimates.
- 891c836: bounded URL intake, provenance and physical PDF page limits.
- c9717fd: verified read-only KITABS result contract and external workspace flow.
- ce4e70e: bilingual jury table, mixed inputs and expandable evidence.
- f610b9a: bilingual error handling.

The authentic Git history is the development record. Do not backdate it or
present pre-existing features as contest-period invention.

## Reproduce locally without private data

Use Python 3.12+ and Node.js 22+. From the standalone repository root:

```sh
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.lock.txt
.venv/bin/pip install --no-deps -e backend
npm --prefix frontend ci
.venv/bin/python -m pytest -q
npm --prefix frontend test
npm --prefix frontend run typecheck
.venv/bin/python tools/prepare_demo.py --data-dir .judge-data/demo
JUDGE_DATA_DIR=.judge-data/demo JUDGE_ENABLE_LIVE=0 .venv/bin/python -m uvicorn independent_judge.api.app:create_app --factory --host 127.0.0.1 --port 8786
```

In a second terminal:

```sh
cd frontend
JUDGE_API_ORIGIN=http://127.0.0.1:8786 npm run build
JUDGE_API_ORIGIN=http://127.0.0.1:8786 npm run start -- --port 3026
```

Open http://127.0.0.1:3026. Select Example → Show comparison, or paste the three
synthetic fixture sentences without trailing newlines and choose the General
profile. Exact matching can reuse the labelled saved fixture. Other materials
are accepted and saved but never receive synthetic scores. New live evaluations
remain disabled until model configuration and budget are approved.

The fixture command imports a test-only provider and runs the real orchestration.
Its reported model is fixture/offline-no-model and its cost is zero. It does not
verify the accuracy of a live judge. Existing catalog entries are not overwritten.

## Review and publication boundary

Local functionality and offline protocol tests are separate from live-model
accuracy and production readiness. The primary real example is Madelain Farah's
human translation of al-Ghazali's Book XII, *Book on the Etiquette of Marriage*,
against a future KITABS Autopilot result. The translator and title are confirmed
on [ghazali.org](https://www.ghazali.org/rrs-bk12-mfarh/), matching the existing
H-01/H-02 catalog provenance. The [Arabic catalog](https://www.ghazali.org/ihya-arabic/)
links the [Book XII Word original](https://www.ghazali.org/ihya/arabic/j2-k02.doc).
The name is Farah, not Farahi; the verified domain is ghazali.org, not ghazali.com.
The exact matching fragment and note boundaries still need selection before
pricing or running B. No manual
review is planned. Five seconds per remaining candidate is a hypothesis, not
measured editing time or a claim of end-to-end savings.

No push, public repository publication, deployment, platform edit or paid run is
authorized by this document. Obtain the owner's approval after local review.
Before a live run, verify the configured model/prices, exact fragment, rights and
spending cap. Do not infer permission from an old pilot configuration.

## Hosting target: app.kitabs.ai/judge

This is a target, not a verified deployment. The current servers intentionally
accept loopback access only. Do not simply remove the host guard or expose the
operator's private data directory or credentials.

Proposed deployment contract for owner review:

1. Build this separate repository and deploy separate frontend/backend services.
2. Mount both UI assets and API under /judge; current absolute /api clients need
   a verified base-path configuration before mounting beside the platform.
3. Use an isolated Judge data directory. Publish only permitted synthetic/licensed
   examples; never deploy .judge-data, keys, private books or platform source.
4. For a public read-only demo, disable upload/run routes. For public personal
   uploads and paid runs, add owner-scoped sessions, quotas and authorized budget
   admission. The current local API has no public multi-user isolation.
5. Configure the reverse proxy only after comparing and backing up the named
   target. Confirm asset paths, locale switching, request limits, HTTPS and
   isolation from the platform API. Preserve the separate rollback build.

A public upload-and-judge deployment still needs the public access contract above;
the local build alone does not meet that contract. The existing platform remains
read-only throughout this task. The workspace handoff is usable without platform
changes; a seamless return requires delegated authorization/callback support.

Dependency limitation: the current locked frontend installs and builds, but
`npm audit` reports two affected packages (Next.js/PostCSS: one moderate, one high).
The report includes PostCSS source-map file disclosure advisories. Resolve and
revalidate the dependency contract before public release; the audit's proposed
automatic fix is a major Next.js upgrade and was not applied in this iteration.

See [rating method](rating-method.md), [KITABS bridge](kitabs-bridge.md), and
[synthetic fixture](../examples/synthetic/README.md). No claim of verified takhrij,
formal STE certification, model-family independence or measured savings is made.
