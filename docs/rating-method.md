# How the Judge makes the points

Method versions: rubric `paired-rubric-v3`, points `points-v1`. These versions grade
the saved examples on <https://app.kitabs.ai/judge>.

The result table has one row for each measure. Each row gives points from 0 to 100
for translation A and for translation B. There are two kinds of rows:

- **Judge rows.** An AI judge gives a level from 1 to 5. Each level has a written
  definition (section 1).
- **Code rows.** The code counts verses, hadith, references, seams and edits
  (section 2).

The judge receives the texts as "A" and "B", without vendor or model names. The same
definitions apply to A and to B.

## 1. Judge rows: six criteria

The judge reads the source and the two translations in one request. For each
criterion it gives a level and quotes from the source and from the translation. The
code shows a quote only when it finds that exact quote in the text.

Level to points: **1 = 0, 2 = 25, 3 = 50, 4 = 75, 5 = 100.**

Level 5 needs positive evidence. The absence of defects alone does not give level 5.

The definitions below are the exact text that the judge receives
(`backend/src/independent_judge/domain/paired_rubric.py`).

### Accuracy

| Level | Definition |
|---|---|
| 1 | Systematic meaning reversals or invention. |
| 2 | Many substantive errors. |
| 3 | Usable meaning with notable errors. |
| 4 | Only small localized meaning defects. |
| 5 | All applicable meanings, negations, conditions, numbers and agents checked against source with positive evidence. |

### Completeness

| Level | Definition |
|---|---|
| 1 | Substantial sections lost. |
| 2 | Many important source units missing. |
| 3 | Most content conveyed with notable partial/missing units. |
| 4 | Only small local omissions. |
| 5 | All meaningful units in the selected source are accounted for with positive correspondence evidence. |

### Terminology

| Level | Definition |
|---|---|
| 1 | Core concepts systematically mistranslated. |
| 2 | Frequent consequential term errors. |
| 3 | Usable but notably inconsistent or inaccurate terminology. |
| 4 | Minor local term defects. |
| 5 | Applicable key terms are accurate and consistent throughout; demonstrate correspondence. |

### Readability

| Level | Definition |
|---|---|
| 1 | Largely unreadable. |
| 2 | Frequent grammar or coherence failures. |
| 3 | Readable with noticeable objective problems. |
| 4 | Fluent with small local defects. |
| 5 | Grammar, naturalness and coherence demonstrated throughout, and notes do not interrupt the author's sentences; do not penalize legitimate style choices. |

### Seamless assembly

| Level | Definition |
|---|---|
| 1 | Assembly loses or duplicates major sections. |
| 2 | Frequent breaks, repetition or ordering defects. |
| 3 | Usable continuity with notable local disruptions. |
| 4 | Only minor transition defects. |
| 5 | Order, continuity and transitions match source across the observed range; unknown vendor chunk boundaries remain unknown. |

Code limit: the code counts the sentences that break at a paragraph join (the
"Seams" row). With 1 broken sentence the level is 4 or lower; with 2 or 3, 3 or
lower; with more, 2 or lower.

### Scholarly apparatus

| Level | Definition |
|---|---|
| 1 | Apparatus systematically corrupts attribution or meaning. |
| 2 | Many consequential attachment or citation defects. |
| 3 | Notes are kept but stay inside the author's text, or useful apparatus has notable defects. |
| 4 | Notes are separate from the author's text with only small local defects. |
| 5 | All applicable notes and attributions are preserved, separate from the author's text as anchored notes, and attached to the correct place, with positive evidence. External sources remain unchecked. |

Code limit: when the source gives references and a translation has no anchored
notes, no glossary and no person index, that translation gets level 1 (0 points).
The code counts these parts; no model takes part.

## 2. Code rows

| Row | What the code does | Points |
|---|---|---|
| Quran verses in the translation | The code finds each verse that the source quotes. A model shows where the translation gives it and copies a quote. The code counts the verse only when it finds that quote in the translation. | verses found ÷ verses in the source × 100 |
| Hadith in the translation | The same for each hadith that the source quotes. | hadith found ÷ hadith in the source × 100 |
| Hadith takhrij: collections and hadith numbers | The code reads each collection and hadith number in A and B and compares it with the source. It opens each hadith number in the library and compares the hadith text with the source. | (correct − wrong) ÷ references in the source × 100, not below 0 |
| Verse references: surah and verse numbers | The code reads each surah and verse number and compares it with the verses that the source quotes. | (correct − wrong) ÷ references in the source × 100, not below 0 |
| Seams: paragraph joins without a broken sentence | The code reads each join of two prose paragraphs. A join is broken when the first paragraph does not end a sentence or the next one starts in lowercase. | joins without a break ÷ all joins × 100 |
| Editing: the part of the editing work that is done | Done: applied audit and editor edits, each with a receipt (text before and after). Remaining: errors with quotations, missing verses and hadith, missing or wrong references. | done ÷ (done + remaining) × 100 |

A wrong reference cancels a correct one: a reader cannot know which reference to
trust. A row appears only when the source has units for it (for example, no hadith
row when the source quotes no hadith).

## 3. Total and winner

**Total = the mean of all rows that have points for both A and B**, rounded half up
(62.5 → 63). All rows have the same weight.

The translation with the higher total wins. Equal totals give a tie.

## 4. Critical errors (not part of the total)

The judge lists each critical error once. A critical error has one of five classes:

| Class | Definition |
|---|---|
| Meaning reversed | The translation reverses a negation, a condition, a number or the agent of the source. |
| Invented content | The translation adds a statement that the source does not give. |
| Omitted text | The translation omits a sentence, a ruling, a quotation or a reference of the source. |
| Verse or hadith changed | The translation changes the words or the meaning of a Quran verse or a hadith. |
| Wrong attribution or reference | The translation gives a statement, a hadith or a reference to a wrong person, collection, surah or verse. |

Style, word choice, transliteration, punctuation and small local defects are not
critical errors. The code counts an error only when it finds both quotes (source and
translation). The table shows the count; it is not part of the total.

## 5. Second judge

A model of a different family grades the same six criteria and the critical errors
with the same instructions. For the saved examples, the first judge is
`google/gemini-3.8-flash` and the second judge is
`spacexai/grok-4.1-fast-reasoning`. The second judge did not make a translation.
The screen shows both tables and tells if the winners agree. The code rows are not
repeated for the second judge.

## 6. Blocks outside the total

| Block | What it shows |
|---|---|
| Readiness for publication | Notes moved out of the author text, glossary entries and person index entries (the code counts them), and the typeset book B (PDF). |
| Editing to publication | Edits that remain. Assumption: 3 minutes for one edit by an editor, 5 seconds to accept one edit that Kitabs.ai has already applied. |
| Processing time | Pipeline time and applied edits with their receipts. |
| Sources in the original | Verses and hadith of the source, found in the public Quran text and the Arabic editions of Bukhari, Muslim, Abu Dawud, Tirmidhi, Nasa'i, Ibn Majah and Malik. |

## 7. Limits

- This is a machine assessment of the selected passage. It is not an expert verdict
  and not a grade of a whole book.
- A text match in a hadith collection is not a ruling on authenticity.
- An AI judge can give a different level in a different run. The second judge shows
  this variation.

This file replaces the earlier 70/30 index (`judge-100-70-30-v1`). The Judge has not
used that index since 5 October 2026.
