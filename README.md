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
| Quality | A table of six criteria (accuracy, completeness, terminology, readability, assembly integrity, scholarly apparatus) with points 0–100 for A and B, a total and a winner |
| Text accuracy | Rows "Quran verses in the translation", "Hadith in the translation" and "Takhrij"; the sections "Takhrij check" and "Sources in the original" |
| Effort reduction | "Editing to publication": edits that remain, editor minutes and the saving in percent |
| Bias mitigation | "Second judge": a model of a different family grades the same criteria |
| Case study | "What the judge caught": source quote, translation quote and explanation |

The judge receives the texts as "A" and "B", without vendor or model names.
A quoted error counts only when the code finds the exact quotation in the text.

## Saved examples

| Example | Translation A | Total A | Total B (Kitabs.ai) | Winner, judge 1 / judge 2 |
|---|---|---:|---:|---|
| Islamic child education, chapter 5 | Gemini | 31 | 78 | B / B |
| Abu Talib al-Makki, *Qut al-Qulub*, night prayers | nadwa.ai (published translation) | 41 | 92 | B / B |

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
