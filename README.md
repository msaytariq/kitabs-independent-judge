# Independent Judge

Independent Judge compares two English translations of the same Arabic source.
It gives each translation points from 0 to 100 on the same criteria, shows the
errors it found with quotations, checks the Quran verses and hadith of the
source against public reference texts, and calculates how much editing work
each translation needs before publication.

- Live demonstration: <https://app.kitabs.ai/judge>
- Guide for the jury: [docs/jury-guide.md](docs/jury-guide.md)
- License: [MIT](LICENSE)

Independent Judge is the competition entry of [Kitabs.ai](https://kitabs.ai).
It is a separate, standalone module: it does not import the Kitabs.ai code and
it does not use the Kitabs.ai database. Translation B can come from any vendor,
or the user can start the Kitabs.ai pipeline from the Judge screen.

## What the screen shows

| Measure | Screen section |
|---|---|
| Quality | A table of six criteria (accuracy, completeness, terminology, readability, seamless assembly, scholarly apparatus) and the rows for quotations, references, seams and editing, with points 0–100 for A and B, a total and a winner |
| Text accuracy | Rows "Quran verses in the translation", "Hadith in the translation", "Hadith takhrij" and "Verse references"; the sections "Hadith takhrij check", "Verse reference check" and "Sources in the original" |
| Effort reduction | "Editing to publication": edits that remain, editor minutes and the saving in percent |
| Bias mitigation | "Second judge": a model of a different family grades the same criteria |
| Case study | "What the judge caught": source quote, translation quote and explanation |

The judge receives the texts as "A" and "B", without vendor or model names.
A quoted error counts only when the code finds the exact quotation in the text.

## Saved examples

| Example | Translation A | Total A | Total B (Kitabs.ai) | Winner, judge 1 / judge 2 |
|---|---|---:|---:|---|
| Islamic child education, chapter 5 | Gemini | 37 | 84 | B / B |
| Abu Talib al-Makki, *Qut al-Qulub*, night prayers | nadwa.ai (published translation) | 47 | 98 | B / B |

Judge 1: Gemini 3.8 Flash. Judge 2: Grok 4.1 Fast.

## Run it locally

Python 3.12 or later:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.lock.txt
.venv/bin/python -m pip install --no-build-isolation --no-deps -e backend
JUDGE_DATA_DIR="$PWD/.judge-data/local" .venv/bin/python -m uvicorn \
  independent_judge.api.app:create_app --factory --host 127.0.0.1 --port 8766
```

In a second terminal, Node.js 22 or later:

```sh
cd frontend
npm ci --ignore-scripts
JUDGE_API_ORIGIN=http://127.0.0.1:8766 npm run dev
```

Open <http://127.0.0.1:3005>. Without operator settings the stand makes no
model calls. A clean clone has no saved examples: the corpus is not part of
the repository.

To let the stand call the judge model, set `JUDGE_ENABLE_LIVE=1`,
`JUDGE_CONFIG_PATH` (for example `config/judge-gemini-3.8-flash.json`),
`AI_GATEWAY_API_KEY`, `JUDGE_BUDGET_TOTAL_USD` and `JUDGE_BUDGET_RUN_USD`.
Each call is reserved in a budget ledger before it starts.

## Public deployment

- `scripts/build_public_frontend.sh /judge <out>` builds the screen as static
  files under a path prefix, from a commit (never from uncommitted work).
- `JUDGE_PUBLIC_HOSTS` names the public host names. Other hosts and cross-site
  writes are refused.
- `JUDGE_PIPELINE_MAX_REQUESTS` limits Kitabs.ai launches paid by the operator.

## Architecture

```text
api/            HTTP routes and request limits
application/    use cases: intake, scope, judge runs, reference checks, views
domain/         rules: rubric, points, coverage, Quran and hadith matching
infrastructure/ adapters: gateway, SQLite, file formats, reference libraries, reports
frontend/       Next.js screen
```

All model calls go through the Vercel AI Gateway. Reference texts:
[fawazahmed0/quran-api](https://github.com/fawazahmed0/quran-api) (edition
ara-quransimple) and [fawazahmed0/hadith-api](https://github.com/fawazahmed0/hadith-api)
(al-Bukhari, Muslim, Abu Dawud, at-Tirmidhi, an-Nasa'i, Ibn Majah, Malik).

More: [architecture](docs/architecture.md), [evaluation protocol](docs/evaluation-protocol.md),
[rating method](docs/rating-method.md), [reference sources](docs/reference-sources.md).

## Tests

```sh
.venv/bin/python -m pytest -q
cd frontend && npm test && npm run typecheck
```

Each change in the Git history is one commit with its tests.

## Limits

- The grades are a machine assessment. An expert review is still necessary.
- The editing time uses assumptions (3 minutes for one edit by an editor,
  5 seconds to accept one edit that Kitabs.ai has already applied), not a
  measurement of a human editor.
- The takhrij check opens hadith numbers in seven open collections only; other numbers stay unchecked.

## Competition timeline

The module was built for the islamicaich.org competition in four days. Every step is a commit in this repository; GitHub shows the date and time of each commit on the [commits page](https://github.com/msaytariq/kitabs-independent-judge/commits/main), and the server time of each push on the [activity page](https://github.com/msaytariq/kitabs-independent-judge/activity). On the live screen, the block "Method and provenance" shows the Git hash of the code that graded each example, so a reader can open that commit here. The tag [`competition-2026-10-06`](https://github.com/msaytariq/kitabs-independent-judge/releases/tag/competition-2026-10-06) marks the state at the end of the competition.

**3 October** — repository created ([`bfeab77`](https://github.com/msaytariq/kitabs-independent-judge/commit/bfeab77)).

**4 October** (12 commits) — document intake and isolated storage ([`01e42e5`](https://github.com/msaytariq/kitabs-independent-judge/commit/01e42e5)); symmetric confirmed text scopes; a bounded judge pilot with evidence quotes and immutable receipts ([`af8460c`](https://github.com/msaytariq/kitabs-independent-judge/commit/af8460c)); strict response schemas and full Gateway charge reconciliation; the editorial effort workbench; source-grounded reviews; hadith quotations verified with traceable source records ([`30af922`](https://github.com/msaytariq/kitabs-independent-judge/commit/30af922)).

**5 October** (38 commits) — 100-point comparison indices and the bilingual jury table ([`5dfa72f`](https://github.com/msaytariq/kitabs-independent-judge/commit/5dfa72f), [`ce4e70e`](https://github.com/msaytariq/kitabs-independent-judge/commit/ce4e70e)); URL intake and PDF page limits; the verified Kitabs result bridge; a reproducible offline demo; reviewed judge configurations (Gemini Flash, Kimi K3); a shared budget guard and continuation from paid receipts; the paired source-grounded protocol, then one definite rubric pass ([`e540d84`](https://github.com/msaytariq/kitabs-independent-judge/commit/e540d84)); the embedded Kitabs autopilot launch ([`c00e0f7`](https://github.com/msaytariq/kitabs-independent-judge/commit/c00e0f7)); verified processing time and the applied-edit journal; Quran verses and hadith of the source located across the reference collections and counted in each translation ([`6c70774`](https://github.com/msaytariq/kitabs-independent-judge/commit/6c70774), [`68d0ecc`](https://github.com/msaytariq/kitabs-independent-judge/commit/68d0ecc)).

**6 October** (54 commits) — points 0–100 with the editing time that remains ([`f1e9463`](https://github.com/msaytariq/kitabs-independent-judge/commit/f1e9463)); a second judge of another model family ([`53ef7ca`](https://github.com/msaytariq/kitabs-independent-judge/commit/53ef7ca)); the public screen as static files with a launch limit ([`e187bea`](https://github.com/msaytariq/kitabs-independent-judge/commit/e187bea), [`676193e`](https://github.com/msaytariq/kitabs-independent-judge/commit/676193e)); the MIT license, the English README and the Arabic interface ([`f15f00a`](https://github.com/msaytariq/kitabs-independent-judge/commit/f15f00a)); the takhrij check of each translation ([`3d73392`](https://github.com/msaytariq/kitabs-independent-judge/commit/3d73392)); the scholarly apparatus graded as an edition form ([`962734c`](https://github.com/msaytariq/kitabs-independent-judge/commit/962734c)); the editing and seams rows; the Kitabs.ai autopilot as the input of translation B, with PDF and DOCX sent to the Kitabs intake and a progress bar ([`68383e2`](https://github.com/msaytariq/kitabs-independent-judge/commit/68383e2), [`c770c93`](https://github.com/msaytariq/kitabs-independent-judge/commit/c770c93)); the typeset book B and the edition block ([`ff1dcea`](https://github.com/msaytariq/kitabs-independent-judge/commit/ff1dcea)); the second judge on live comparisons ([`cc87e66`](https://github.com/msaytariq/kitabs-independent-judge/commit/cc87e66)); the critical errors row ([`5e5f786`](https://github.com/msaytariq/kitabs-independent-judge/commit/5e5f786)); quotes found across line breaks ([`65e421d`](https://github.com/msaytariq/kitabs-independent-judge/commit/65e421d)); the provenance of each example on the public screen in the interface language ([`eb6200f`](https://github.com/msaytariq/kitabs-independent-judge/commit/eb6200f), [`76eed55`](https://github.com/msaytariq/kitabs-independent-judge/commit/76eed55)); the source check in plain words ([`ed99fba`](https://github.com/msaytariq/kitabs-independent-judge/commit/ed99fba)). The same day the Kitabs.ai engine (a separate repository) received five footnote rules found with this judge, and both saved examples were produced again through the production server.
