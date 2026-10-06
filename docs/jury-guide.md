# Independent Judge: guide for the jury

Independent Judge compares two English translations of the same Arabic source.
It gives each translation points from 0 to 100, shows the errors it found with
quotations, and calculates how much editing work each translation needs before
publication.

Link: <https://app.kitabs.ai/judge>

## Use a saved example (no upload, no cost)

1. Open the link. Click **Example**.
2. Select an example. Click **Show comparison**.
3. Read the table from top to bottom (see "What the screen shows").

Each example has an Arabic source of about 5 to 7 pages with Quran verses and
hadith. Translation B comes from the Kitabs.ai pipeline (Autopilot, no manual
edits). Translation A comes from a general chat model (example 1) or from a
published competitor translation (example 2).

| Example | Source | A | Total A | Total B | Winner (judge 1 / judge 2) |
|---|---|---|---:|---:|---|
| 1 | Islamic child education, chapter 5 | Gemini | 31 | 78 | B / B |
| 2 | Abu Talib al-Makki, *Qut al-Qulub*, night prayers | nadwa.ai | 41 | 92 | B / B |

Example 2 takes the Arabic text and translation A from the same pages (104–120)
of the public nadwa.ai EPUB of *Qut al-Qulub*. In this passage nadwa.ai gives 12
verse references; the code finds 10 of them wrong, for example "Adh-Duha (92): 2"
for 93:2 and "Surah Al-'Aaliyah (1): 1" for 87:1. The edition itself prints most
verse numbers with swapped digits ("الإسراء: 97" for 17:79); nadwa.ai copies them,
and the section **Sources in the original** shows each one.

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
| Text accuracy | Rows **Quran verses in the translation**, **Hadith in the translation** and **Takhrij**, the section **Takhrij check** and the section **Sources in the original** |
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
When the source gives a wrong reference, the screen shows it.

### Takhrij check

The code reads each reference in A and B: a Quran verse such as (30:21), a hadith
collection such as "Narrated by Muslim", or a hadith number such as "al-Nasa'i
(3053)". No model takes part.

- The source gives the references to deliver: each verse that it quotes, each
  collection that it names and each hadith number that it gives.
- A reference is correct when the translation gives the same reference.
- A reference is wrong when the source does not quote that verse or when the
  hadith under that number is not in the source.
- A collection that the source does not name is correct only when the code finds
  a hadith of the source in it. Otherwise it stays unchecked: a source can retell
  a hadith in its own words, and the code cannot prove such a reference wrong.
- The code opens each hadith number in the library and compares the hadith text
  with the source. A number from a collection that no open library has (for
  example Musnad Ahmad) stays unchecked.

Row points = (correct references − wrong references) / references in the source.

In the saved example, A (Gemini) gives no hadith collection at all and lists the
verse references in a summary instead of translating the verses. B keeps all
collections and verse references but loses three hadith numbers of the source.

### Editing to publication

Edits that remain = errors with quotations + missing verses and hadith +
missing or wrong references.
We assume 3 minutes for one edit by an editor. For B we also count 5 seconds to
accept each edit that the Kitabs pipeline has already applied. These numbers are
assumptions, not a time measurement of a human editor.

### Second judge

Judge 1 is Gemini 3.8 Flash (Google). Judge 2 is Grok 4.1 Fast (xAI). The
translations B use Anthropic, OpenAI and DeepSeek models, so neither judge
family made translation B. Both judges receive the texts as "A" and "B",
without vendor or model names. In the saved example, both judges selected the
same winner.

## Limits

- The grades are a machine assessment. An expert review is still necessary.
- The takhrij check opens hadith numbers in seven collections only (see "Sources
  in the original"). Books often use another numbering; the code accepts both
  numbers that the library gives for each hadith.
- Model answers can change from run to run. Each saved example shows its run
  ID, model, cost and Git commit under **Method and provenance**.

## Code

Repository: <https://github.com/msaytariq/kitabs-independent-judge>.
Each change is a Git commit with a test. Run the tests:

```sh
.venv/bin/python -m pytest -q
cd frontend && npm test
```
