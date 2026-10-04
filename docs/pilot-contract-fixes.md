# Pilot integration corrections — 4 October 2026

The first paid pilot was preserved as a failed run, without final scores. On its
sixth response the model omitted the required severity code in every finding.
The strict validator rejected the response. The code does not invent the missing
codes or reinterpret the failure as zero errors. This is a model-output contract
failure, not a proof about translation quality.

All evaluation prompts now carry a required JSON response schema derived from
the same Pydantic models used for validation. The Gateway adapter transmits this
through `response_format`. Length and evidence checks remain local. The text of
the assessment rubric and all three source materials are unchanged. Actual prompt
hashes include the schema, and the new code SHA distinguishes this attempt.

The live usage envelope exposed `cost`, `surcharge_cost`, and `gateway_cost`.
The original adapter read the inference-only `cost`. The corrected adapter uses
`gateway_cost` when present, otherwise `cost + surcharge_cost`, and never adds a
surcharge twice. Invalid totals keep the reservation held. Typed failures carry
the same total to admission, including for truncated paid responses. The request
reservation includes schema bytes and $0.001 allowance for service charges.

A separate append-only reconciliation table accounts for the six historical
receipt totals, without changing original settlements, receipts or reports.
The failed attempt cost $0.087128 including $0.000600 in service charges.
The old report states $0.086528; its separately hashed reconciliation supersedes
that cost field only. Both versions remain available in the private runtime.

Five regression tests failed before correction; the full 63-test suite passes
afterwards. Tests cover required schemas, missing-code rejection, total Gateway
cost, priced truncation and immutable reconciliation affecting future admission.
The public test data is synthetic and contains no literary excerpts.

References: [structured output](https://vercel.com/docs/ai-gateway/sdks-and-apis/openai-chat-completions/structured-outputs),
[pricing and provider allowlist charges](https://vercel.com/docs/ai-gateway/pricing).
