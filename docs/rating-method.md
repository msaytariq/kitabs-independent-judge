# Rating method: judge-100-70-30-v1

This is a provisional machine index for one comparison, not an expert grade.
It cannot establish whole-book quality, vendor superiority, or hadith authenticity.
The owner confirmed the 70/30 allocation on 5 October 2026.

## Formulas

P = exact source character count / 1800. Never use rounded display pages.
K, T, S count unique final critical, terminology and style candidates.
Only exact, unambiguous, undisputed quote pairs enter these counts.
Excluded findings remain visible. These candidates are not confirmed defects.

Accuracy = max(0, 10 − (3K + T + 0.5S)/P), rounded to one decimal, then ×10.
Terminology = max(0, 10 − T/P), rounded to one decimal, then ×10.
Readability = max(0, 10 − 0.5S/P), rounded to one decimal, then ×10.
The latter two are diagnostic indices extracted from the same findings.
They are already represented in accuracy. Do not average them into the total again.
A score of 100 means no included penalties, not proof of flawless prose.

Structural apparatus = notes (up to 50, proportional to source notes; 50 for
any notes when the source has none) + glossary present (30) + persons/narrator
notes present (20). The standalone English parser counts explicit note entries,
not orphan reference markers. Its inventory version differs from the platform's
multilingual parser; unsupported layouts require review. Source notes must be
preserved during extraction. No entry count can prove relevance or correctness.

Total = 0.7 × accuracy + 0.3 × structural apparatus, with rounding on the
platform's original 0–10 scale before multiplying by ten. This preserves its
allocation and rounding. It is explicitly a structural compatibility index:
irrelevant notes must not be presented as evidence of scholarly merit.
Scientific correctness and relevance remain **not assessed**; no bonus for
verified quality is claimed. Apparatus findings remain available as evidence.

Missing run, failed run, zero source length or unknown protocol → not assessed.
Supported protocol: blind-3pass-exact-consensus-v1. Recompute only from the
exact saved source, translation and final findings. Never infer scores from
unsupported legacy totals or partial provider replies. Save model identifiers,
prompt hashes and code SHA in the run; report this rubric version on projection.
A/B labels and producer identities do not enter the judging prompt.

Equal displayed totals produce a tie. Swapping sides swaps scores.
The score leader is provisional. Evidence and exclusions accompany the table.

## Effort and scope

Five seconds per unique accept/reject decision is an assumption, not measured
editing time. Prior human decisions and remaining correction candidates are
separate. Unknown history is not zero. Reading, research and writing are excluded.
The primary contest example is autopilot output; no manual review is planned.
Do not manufacture human decision records from automatic stage completion.

PDF source: at most ten physical pages, including blank pages. Text/MD/DOCX:
at most 18,000 source characters, described as ten 1,800-character units, not
physical pages. Preserve full inputs and never silently truncate. An additional
18,000-character selected-source cap bounds judging cost for every format.
