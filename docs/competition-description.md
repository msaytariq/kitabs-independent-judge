# Independent Judge — competition description

Independent Judge is module 38 of the Kitabs.ai ecosystem. Kitabs.ai is an intelligent multi-agent system. It processes long multilingual documents. It keeps the meaning, the terminology and the structure consistent across the full work. The platform prepares Islamic texts for publication. It does OCR, translation, scholarly apparatus in footnotes, editing, layout and covers.

## Problem

Many translators now use LLMs. Some of them publish the LLM output without a human check. The reader gets a distorted text and cannot see it. For Islamic texts this is a serious problem. The Sharia requires accuracy when a person transmits the Quran, the hadith and religious knowledge. Today only one check exists: an expert reads the full translation against the source. This is slow and expensive. We did not find a tool that measures the quality of an LLM translation and points to its errors.

## Our solution

Independent Judge is this tool. It measures a translation against its source: six criteria, points from 0 to 100, and each error with a quote from the source and a quote from the translation. The expert reads the errors that the Judge found, not the full text. The Judge always grades two translations of the same text by the same criteria, so the user sees which one is nearer to the source and better for publication. The second translation can come from another vendor, or the user starts the Kitabs.ai pipeline from the Judge screen and gets it in minutes.

## What the module does

1. It compares two translations of the same source. In the competition examples the source is Arabic and the translations are English. Translation B can come from any vendor, or the user starts the Kitabs.ai pipeline from the Judge screen. The Judge then sends the source to the Kitabs.ai production server and receives the translation, the editing receipts and the typeset book (PDF).
2. An AI judge gives points from 0 to 100 on six criteria: accuracy, completeness, terminology, readability, seamless assembly and scholarly apparatus. The code adds rows that it counts without a model: Quran verses and hadith found in the translation, hadith references, verse references, paragraph seams and editing done. The total is the mean of all rows. The module shows a winner.
3. It counts critical errors in A and in B: reversed meaning, invented content, omitted text, a changed verse or hadith, a wrong attribution or reference. It counts an error only when it finds the exact quote in the source and in the translation. The count is not part of the total.
4. It shows each error with a quote from the source and a quote from the translation.
5. It checks Quran verses and hadith against public reference texts: the Quran and seven hadith collections (al-Bukhari, Muslim, Abu Dawud, at-Tirmidhi, an-Nasa'i, Ibn Majah, Malik). It also checks the references printed in the source edition and shows where the edition prints a verse number with an error.
6. It calculates the editing work before publication: the edits that remain, the editor minutes and the time saving in percent.
7. It counts the apparatus of each translation (footnotes, glossary, persons) and typesets translation B as a book PDF.
8. It shows where each text comes from: the vendor of A, and for B the production server, the date and the number of chunks.

## Bias control

The judge gets the texts as "A" and "B", without vendor or model names. A second judge from a different model family grades the same criteria and counts the critical errors. The screen shows both judges and says if they selected the same winner.

## Results

Translation B in both examples comes from the Kitabs.ai pipeline on the production server (6 October 2026), with no manual edits.

- Islamic child education: love and patience in upbringing. Translation A: the Gemini chat. Gemini 36 points, Kitabs.ai 94 points. Critical errors: Gemini 2, Kitabs.ai 0.
- Abu Talib al-Makki, Qut al-Qulub, pages 104–120. Translation A: the published nadwa.ai translation (public EPUB). nadwa.ai 42 points, Kitabs.ai 100 points. Critical errors: nadwa.ai 2, Kitabs.ai 0. The code found 10 wrong Quran verse references out of 13 in the nadwa.ai text. Kitabs.ai gave 13 of 13.

Both judges selected Kitabs.ai as the winner in both examples.

In the short time of the competition, we got important results. More work is necessary to make the module an international standard tool.

## Value for editors and publishers

The module helps to select a translation vendor. The editor compares translations of the same text: from an LLM chat, from a translation service or from Kitabs.ai. The judge shows which translation is more accurate, how many critical errors it has and how many edits it needs before publication. In Kitabs.ai a person corrects each critical error: the audit and the editor propose an edit, and the person accepts or rejects it. Chat and other AI translation services that work without a person do not have this step. The editor selects the best translation, uses less time for proofreading and publishes a high-quality book.

## Limits

The grades are a machine assessment. A human expert makes the final decision. The judge grades the selected excerpt only.

- Live: <https://app.kitabs.ai/judge>
- Code: <https://github.com/msaytariq/kitabs-independent-judge>
- Product: <https://kitabs.ai>
