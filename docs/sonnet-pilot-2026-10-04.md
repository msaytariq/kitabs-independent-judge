# Real Sonnet 5.5 pilot — 4 October 2026

The independent stand completed all 15 calls of its protocol on an unchanged
real Arabic passage and two corresponding English versions from Al-Ghazali's
Book on the Etiquette of Marriage. Output status: **needs_review**.
This confirms the live integration path; it does not validate every allegation.

Evaluation code: `6fd2efe20981bb72a2996f99f7ef4f56b88b6612`.
Run ID: `sonnet55-ghazali-20261004-02`.
Actual returned model: `anthropic/claude-sonnet-5.5`, routed through Vercel Gateway.
Scope: 794 original characters, 1576 in version A, 1470 in version B.
The first complete praise passage was fixed before observing the new outputs.

A is the [published Madelain Farah translation](https://www.ghazali.org/rrs-bk12-mfarh/).
B is historical Kitabs output translated with Claude Sonnet 4.5. The judge and
Kitabs translator share a model vendor; no vendor independence is asserted.
The [Arabic source collection](https://www.ghazali.org/ihya-arabic/) and archived
private inputs establish provenance. No literary texts or raw replies are
included in this repository.

## Reported cost, including service charges

| Attempt | Calls | USD |
|---|---:|---:|
| Initial attempt, invalid finding schema | 6 | 0.087128 |
| Full protocol | 15 | 0.226044 |
| All attempts | 21 | **0.313172** |

Remaining from the approved $3 total: $2.686828. No unresolved reservations.
Totals reconcile to the saved `usage.gateway_cost` fields. This is not an
independent account-invoice reconciliation. The failed attempt and its original
report remain preserved, together with an append-only cost correction.

## Machine output, not a validated ranking

| After consensus and appeal | A | B |
|---|---:|---:|
| K, critical | 3 | 1 |
| T, terminology | 1 | 1 |
| A, apparatus | 0 | 0 |
| S, readability | 0 | 1 |

The 16-unit coverage assessment returned A: 11 conveyed, 4 partial, 1 requiring
review; B: 15 conveyed, 1 requiring review. No missing unit was reported.
No overall winner is declared. Four non-verbatim quotes from initial assessments
were excluded from verified consensus: two whitespace differences and two altered
Arabic source quotes. Exact anchoring verifies location, not semantic truth.

Preliminary contextual review found useful lexical/meaning discrepancies, but
also a likely false critical allegation about a pronoun antecedent in B. Both
coverage passes separately classified that same meaning unit as conveyed.
Some metaphor-preservation preferences were also classified as errors. The
separate review notes do not overwrite or selectively remove model findings.
An independent Arabic/English expert has not adjudicated this pilot.

## Engineering verification and next work

The first attempt exposed two integration problems: missing severity fields and
inference-only cost accounting. Required JSON schemas and full Gateway cost
handling corrected those problems; see [contract fixes](pilot-contract-fixes.md).
63 offline tests pass locally and in a clean non-editable installation with the
platform package absent. The clean environment contains 26 compatible packages.
The complete second live protocol finished in approximately 166 seconds.

Sonnet is usable as an auditable candidate assessor with review. This small,
same-vendor pilot is insufficient for an unqualified final arbiter or a claim
of whole-book/platform superiority. Remaining product work includes jury UI,
session authorization, review decisions, exports and a separate public demo.
Hadith-reference integration is not enabled.
