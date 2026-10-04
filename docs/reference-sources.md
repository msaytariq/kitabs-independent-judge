# Sources for local hadith checks

The module checks textual correspondence, not hadith authenticity, theological
correctness or translation adequacy. It never invents a scholar's grading.

| Source | Role | Access and limits |
|---|---|---|
| [Sunnah.com](https://sunnah.com/developers) | Primary direct record verification, Arabic and available English text, attributed grading | Official API key required. Adapter implemented and tested with recorded-shape fixtures; live access pending. API covers part of the library; no assumption that every record has a grading. |
| [HadeethEnc official API](https://github.com/islamhouse-dev/hadith-api) | Additional institutional text/translation source for a future verified connector | Public read-only probe returned HTTP 403 on 2026-10-04. Not integrated or silently simulated. |
| [Hadith API](https://github.com/fawazahmed0/hadith-api) | Implemented electronic Arabic Bukhari/Muslim collections; identify candidates and quote exact records | Community-maintained electronic editions, not institutional certification. Repository declares Unlicense; underlying [source inventory](https://github.com/fawazahmed0/hadith-api/blob/1/References.md) must accompany publication review. Data stays in private cache, not Git. |
| [Dorar search widget](https://dorar.net/article/2107/نافذة-البحث-في-الموسوعة-الحديثية-لأصحاب-المواقع) | Human scholarly cross-check reference | No automated scraping or unsupported API assumptions. Not integrated. |

[HadeethEnc/IslamHouse content policy](https://github.com/IslamHouse-API/multilingual-quran-hadith-islamic-content-database-api-hub)
allows indexing/offline integration with attribution and intact original texts;
this does not make an unreachable API a working connector.

Implemented retrieval: detect marked Arabic quotations («…», “…” or straight
double quotes, or round parentheses); compare locally against two named Arabic collections. Up to 30
quotations per scope; show truncation. Unmarked prose and Quran brackets are not
covered by this detector. A quotation is a candidate, not necessarily a hadith.
No corpus text is sent to a library. Only fixed edition URLs are downloaded.
Snapshots retain full original text, retrieval timestamp and SHA-256; refresh
after seven days. Normalization is used for matching only. Reports preserve
original source text and URLs. Record numbers are edition-specific.

Exact and diacritic-normalized full matches are distinguished from fragments,
near matches, ambiguity, no match within these collections and library failure.
No match does not mean fabricated/weak hadith. The search is not exhaustive
takhrij. Both compared translations share this source evidence; their semantic
accuracy remains a separate judge/expert task.

## Sunnah.com contract

Use `SUNNAH_API_KEY` only on the backend. Request access through the
[official issue template](https://github.com/sunnah-com/api/issues/new?template=request-for-api-access.md).
Website scraping and bulk republication are excluded; see the
[site policy](https://sunnah.com/about). Clarify allowed local retention and
commercial use with the maintainers before publication.

The official [API source](https://github.com/sunnah-com/api) describes individual
record lookup. The adapter uses `api.sunnah.com/v1/collections/{collection}/hadiths/{number}`
and the issued `x-api-key`. Live header/schema compatibility remains to be verified
when access is granted. At most ten unique Bukhari/Muslim candidate identities are
looked up per check. Apply the granted account rate limits before enabling live
access; the adapter does not yet enforce a daily quota.

Candidate identities come from the separate electronic index. Numbering schemes
can differ: a returned Sunnah record is compared to the actual Arabic quotation,
and its existence alone never confirms correspondence. Fractional edition numbers
may return no Sunnah record. The API is not a full-text search fallback; no index
candidate means no automatic Sunnah lookup. Missing key, outage, truncated checks,
no record and textual differences remain distinct.

The Arabic record, available English translation, original HTML record, attributed
grading, retrieval timestamp and response SHA-256 are preserved. The English
reference is shown as evidence; automatic semantic equivalence with the uploaded
translation is not implemented. Quran source validation is not part of this adapter.
