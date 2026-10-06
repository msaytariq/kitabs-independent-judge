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
| 1 | Islamic child education, chapter 5 | Gemini | 37 | 84 | B / B |
| 2 | Abu Talib al-Makki, *Qut al-Qulub*, night prayers | nadwa.ai | 47 | 98 | B / B |

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
4. For translation B, keep the input **Kitabs.ai autopilot** and click **Start
   the autopilot on Kitabs.ai**, or select file, text or URL for a completed B.
   The autopilot sends the source file to the Kitabs intake (the same as on
   the Kitabs desk), translates, audits, edits and assembles it, and returns
   B with the Kitabs reading of the source. A bar shows the finished steps.
   The number of Kitabs launches for the demonstration is limited.
5. Click **Continue to comparison**, then **Compare**.

## What the screen shows

The four rows below answer the four measures that our mentor asked for.

| Measure | Where on the screen |
|---|---|
| Effort reduction | **Editing to publication**: edits that remain, editor minutes for A and B, and the saving in percent |
| Text accuracy | Rows **Quran verses in the translation**, **Hadith in the translation**, **Hadith takhrij** and **Verse references**, the sections **Hadith takhrij check**, **Verse reference check** and **Sources in the original** |
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

### Scholarly apparatus

The judge grades the apparatus as a scholarly edition. The same rule applies to
A and B, and the judge does not know which system made each translation.

- Level 5 needs all notes of the source, separate from the author's text as
  anchored notes, each note at the correct place.
- When the source gives references, a translation without anchored notes gets
  0 points. The code counts the notes; no model takes part. The same rule
  applies to the first and the second judge.
- Notes that stay inside the author's text get level 3 or lower. A note that
  interrupts an author's sentence is also a readability defect.
- Takhrij and editor notes that the source prints inside the text are notes,
  not author text.
- An added note, glossary or person index is a strength only when it is
  correct. A wrong or invented added note is a defect. Length alone gives no
  points.

### Sources in the original

The code finds each Quran verse of the source in the Quran text
(fawazahmed0/quran-api, edition ara-quransimple) and gives the surah and verse.
It also finds each hadith in seven collections (fawazahmed0/hadith-api:
al-Bukhari, Muslim, Abu Dawud, at-Tirmidhi, an-Nasa'i, Ibn Majah, Malik).
When the source gives a wrong reference, the screen shows it. A verse that the
source quotes without brackets is found by six or more words in Quran order;
the basmala is not counted as a quotation.

Some PDF text layers store each lam-alef pair in reverse order ("األول" for
"الأول", "ال" for "لا"). The code repairs such a text with a word list of the
Quran and the hadith collections: a word changes only when the list knows the
repaired word and not the word as it stands.

### Seams

A long text is translated in fragments, and the fragments join at paragraph
breaks. The judge grades **Seamless assembly** (levels 1–5). The code also
checks each join of two prose paragraphs in A and B with the same rule; no
model takes part:

- A join is broken when the first paragraph does not end a sentence or the
  next paragraph starts in lowercase.
- Headings, quotations, lists, notes, page numbers and the apparatus sections
  are not prose and are not counted.

Row points = joins without a break / all joins. In example 2, nadwa.ai breaks
2 sentences of 28 joins, for example "…from the end of the night," followed
by a new paragraph "And if he reads…". Kitabs has no break in 30 joins. The
Kitabs pipeline joins its fragments at assembly and bridges each seam.

### Hadith takhrij check

Takhrij tells where a hadith is recorded: the collection and the hadith number.
The code reads each hadith reference in A and B: a collection such as "Narrated
by Muslim" or a hadith number such as "al-Nasa'i (3053)". No model takes part.

- The source gives the references to deliver: each collection that it names and
  each hadith number that it gives.
- A reference is correct when the translation gives the same reference.
- A hadith number is wrong when the hadith under that number is not in the
  source. The code opens each hadith number in the library and compares the
  hadith text with the source. A number from a collection that no open library
  has (for example Musnad Ahmad) stays unchecked.
- A collection that the source does not name is correct only when the code finds
  a hadith of the source in it. Otherwise it stays unchecked: a source can retell
  a hadith in its own words, and the code cannot prove such a reference wrong.

### Verse reference check

Verse references are not takhrij, and the screen shows them in a separate
section and row. The code reads each surah and verse number in A and B, for
example (30:21), and compares it with the verses that the source quotes. A verse
reference is wrong when the source does not quote that verse.

Row points for both rows = (correct references − wrong references) / references
in the source.

In example 1, A (Gemini) gives no hadith collection at all (0 of 12); B gives 9
of 12 and loses three hadith numbers of the source. In example 2, nadwa.ai gives
10 wrong verse references of 12; B gives all 13 verse references of the source.

### Editing to publication

Edits that remain = errors with quotations + missing verses and hadith +
missing or wrong references.
We assume 3 minutes for one edit by an editor. For B we also count 5 seconds to
accept each edit that the Kitabs pipeline has already applied. These numbers are
assumptions, not a time measurement of a human editor.

The jury table has the row **Editing**: the applied audit and editor edits as a
part of all edits, done and still needed. Points = done / (done + remaining).
A text that needs no edit gets 100 points. The row is shown when a translation
has applied edits with receipts. In the saved examples: example 1, A 0 (0 done,
41 remaining), B 92 (69 done, 6 remaining); example 2, A 0 (0 done, 25
remaining), B 100 (135 done, 0 remaining).

The section also shows the editing work that the pipeline has already done:
the applied audit and editor edits, times 3 minutes. Each edit has a receipt
with the text before and after (section **Processing time**). The judge grades
the text after these edits. In the saved examples B has 69 and 135 applied
edits (207 and 405 minutes); A has none.

### Readiness for publication

A separate block, not part of the quality total. For A and B the code counts
the anchored notes, glossary entries and person entries; for B the block adds
the typeset book (PDF) that Kitabs.ai makes after the autopilot, with a download
button, and the applied audit and editor edits. The block has its own score of
4 checks.

### Second judge

Judge 1 is Gemini 3.8 Flash (Google). Judge 2 is Grok 4.1 Fast (xAI); it also
grades your own comparisons, after judge 1. The
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
