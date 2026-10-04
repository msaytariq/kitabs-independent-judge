# Evaluation pilot, version 1 — 4 October 2026

## Protocol and responsibilities

1. An operator confirms three corresponding ranges. The original and selected
   hashes, Unicode code-point ranges, languages and profile are retained.
2. `application/judge_runner.py` coordinates three stateless assessments of each
   translation. `domain/judge_prompt.py` sends the source and one translation;
   filenames, platform labels and translator metadata are not sent. Content can
   itself reveal an author; masking metadata does not guarantee perfect blindness.
3. `domain/evidence.py` locates exact quotes. Missing and repeated/ambiguous quotes
   remain visible and unconfirmed. `domain/consensus.py` counts two distinct passes
   with identical source/translation quotes. This conservative rule can miss
   semantically equivalent allegations anchored with different quotes.
4. `application/critical_review.py` appeals K findings; rejected claims remain in
   original passes and appeal decisions. `application/cross_check.py` tests each
   side for defects reported on the other. Cross-check additions have only one
   review and are shown separately, not silently added to majority counts.
5. `application/completeness.py` builds one shared source-only inventory (up to
   16 nonoverlapping, exact-anchored units) and evaluates each translation twice.
   Disagreement or missing evidence requires review. Character coverage of the
   inventory is reported. Unit coverage is not a guarantee that every meaning in
   a whole book was checked. No ungrounded overall score or winner is assigned.
6. `domain/run_manifest.py` identifies code, inputs, ranges, prompt templates,
   model configuration and protocol. Each actual prompt/response is retained in
   private receipts; prompt hashes, usage, actual model IDs and costs are in the
   report. Final reports cannot be overwritten. Raw reasoning, if returned by a
   provider, is private diagnostic data, not a public report explanation.

All prompts in `domain/judge_prompt.py`, `critical_review_prompt.py`,
`cross_check_prompt.py` and `completeness.py`, plus `profiles.py`, are standalone
assessment prompts intended for this repository's reviewed publication scope.
They do not contain platform translation/production prompts. Public publication
still needs the repository owner's final scope/license decision.

## Gateway and budget

`infrastructure/gateway.py` calls only Vercel AI Gateway, pins the Anthropic route,
and currently permits only `anthropic/claude-sonnet-5.5`. No direct-provider key,
model fallback or automatic retry is implemented. Temperature/top-p/top-k are
omitted; reasoning effort is medium, output cap 4096 tokens including reasoning.
Prices checked 4 October: $2/M input and $10/M output. Admission reserves input
at $2.50/M (cache-write allowance), UTF-8 bytes plus 2048 framing tokens, and a
25% buffer. Requests above the reviewed pilot size are blocked. Prices and
reported usage are checked; a cost above reservation halts further admissions.

`application/run_admission.py` reserves before calling. `budget_repository.py`
uses atomic SQLite transactions and persistent limits. A priced failed response
still counts; missing reported cost keeps the full reservation held. A timeout is
not proof of zero spend. The ledger is the local application's cost record,
not an independent reconciliation of the Vercel account invoice. Other platform
activity is outside this stand ledger. Keep one ledger for the approved budget.

Sources: [Sonnet 5.5](https://vercel.com/ai-gateway/models/claude-sonnet-5.5),
[Gateway routing](https://vercel.com/docs/ai-gateway/models-and-providers/provider-options),
[Chat API](https://vercel.com/docs/ai-gateway/sdks-and-apis/openai-chat-completions).

## Verification and remaining limits

58 offline tests cover upload/extraction, symmetric scopes, three-pass voting,
exact/ambiguous evidence, malformed/truncated responses, appeals, cross-checks,
coverage disagreement, manifest identity, immutable reports, swapped A/B,
concurrent reservations, persistent caps and Gateway request fields.
Fixed provider responses are engineering controls, not quality evidence. The
prompt-injection test verifies system/data separation only, not model immunity.

This is a local operator pilot. Session authorization, web UI for ranges/runs,
PDF output, independent-model adjudication, hadith libraries and public deployment
are not implemented. A Sonnet-generated translation reviewed by Sonnet is marked
same-vendor. Expert Arabic/English review remains required for quality claims.
