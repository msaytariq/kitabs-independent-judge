# Independent Judge: guide for the jury

Independent Judge compares two English translations of the same Arabic source.
It gives each translation points from 0 to 100, shows the errors it found with
quotations, and calculates how much editing work each translation needs before
publication.

Link: <https://app.kitabs.ai/judge>

## Use a saved example (no upload, no cost)

1. Open the link. Click **Example**.
2. Select one of the three examples. Click **Show comparison**.
3. Read the table from top to bottom (see "What the screen shows").

Each example has an Arabic source of about 5 pages with Quran verses and hadith.
Translation A comes from a general chat model. Translation B comes from the
Kitabs.ai pipeline (Autopilot, no manual edits).

| Example | Source | A | Total A | Total B | Winner (judge 1 / judge 2) |
|---|---|---|---:|---:|---|
| 1 | an-Nawawi, *Riyad as-Salihin*, chapter on patience | ChatGPT | 91 | 91 | tie / tie |
| 2 | Islamic child education, chapter 5 | Gemini | 28 | 77 | B / B |
| 3 | al-Ghazali, *Ihya*, Book of Death, chapter 8 | Claude | 100 | 66 | A / A |

Example 3 shows that the judge does not favour Kitabs.ai: the judge found that
the Kitabs pipeline moved a paragraph of the author into footnote [4].

## Use your own texts

1. Click **Your materials**.
2. Supply the Arabic source (up to 18,000 characters, about 10 pages): file
   (TXT, MD, DOCX, HTML, PDF with a text layer), pasted text or URL.
3. Supply translation A: file, text or URL.
4. Supply translation B, or click **Start processing on Kitabs.ai (Autopilot)**.
   Kitabs.ai translates and edits the source and returns B to this page.
   The number of Kitabs launches for the demonstration is limited.
5. Click **Check materials**, then start the comparison.

## What the screen shows

The four rows below answer the four measures that our mentor asked for.

| Measure | Where on the screen |
|---|---|
| Effort reduction | **Editing to publication**: edits that remain, editor minutes for A and B, and the saving in percent |
| Text accuracy | Rows **Quran verses in the translation** and **Hadith in the translation**, and the section **Sources in the original** |
| Bias mitigation | **Second judge: bias check**: a second model of a different family grades the same criteria |
| Live case study | **What the judge caught**: source quote, translation quote and explanation for each error |

### Points

The AI judge grades six criteria with levels 1 to 5. Each level has a written
definition. The screen shows the levels as points:

| Level | Points | Meaning |
|---:|---:|---|
| 5 | 100 | No defects |
| 4 | 75 | Small local defects |
| 3 | 50 | Notable defects |
| 2 | 25 | Many substantive errors |
| 1 | 0 | Meaning is systematically distorted |

The verse and hadith rows show the part of the source quotations that the
translation contains. A quotation counts only when the judge gives the exact
sentence and the code finds this sentence in the translation. The total is the
mean of all rows.

### Sources in the original

The code finds each Quran verse of the source in the Quran text
(fawazahmed0/quran-api, edition ara-quransimple) and gives the surah and verse.
It also finds each hadith in seven collections (fawazahmed0/hadith-api:
al-Bukhari, Muslim, Abu Dawud, at-Tirmidhi, an-Nasa'i, Ibn Majah, Malik).
When the source gives a wrong reference, the screen shows it. Example 1 has one:
the source gives "Muhammad: 31", the Quran has 2:153.

### Editing to publication

Edits that remain = errors with quotations + missing verses and hadith.
We assume 3 minutes for one edit by an editor. For B we also count 5 seconds to
accept each edit that the Kitabs pipeline has already applied. These numbers are
assumptions, not a time measurement of a human editor.

### Second judge

Judge 1 is Gemini 3.8 Flash (Google). Judge 2 is Grok 4.1 Fast (xAI). The
translations B use Anthropic, OpenAI and DeepSeek models, so neither judge
family made translation B. Both judges receive the texts as "A" and "B",
without vendor or model names. In the three examples, both judges selected the
same winner.

## Limits

- The grades are a machine assessment. An expert review is still necessary.
- The judge does not check the takhrij in the footnotes of B (collection and
  number of each hadith). The code checks the hadith of the source only.
- Model answers can change from run to run. Each saved example shows its run
  ID, model, cost and Git commit under **Method and provenance**.

## Code

Repository: <https://github.com/msaytariq/kitabs-independent-judge>.
Each change is a Git commit with a test. Run the tests:

```sh
.venv/bin/python -m pytest -q
cd frontend && npm test
```
