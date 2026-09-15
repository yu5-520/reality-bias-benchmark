# CN-R-026 — v0.3.1 microbatch serialization failure and v0.3.2 correction

**Status:** ACCEPTED AFTER MICRO-BATCH 003, BEFORE ANY v0.3.2 SUBJECT DATA.

## Trigger

E-commerce structural micro-batch run `34960602410` attempted three fresh subject episodes under Arena v0.3.1.

- one episode completed;
- two episodes preserved substantial multi-agent traces but terminated on malformed subject JSON;
- both malformed responses ended with provider `finish_reason=stop` and completion lengths far below the 4,096-token cap;
- no paid evaluator was called.

Therefore this is not another truncation problem and not a semantic R2/R3/R4 finding.

## Scientific treatment

The evidence batch remains immutable and auditable. The two failed episodes are partial execution records, not complete subject runs. They are not repaired in place and are not counted as completed episodes.

No semantic zero is inferred from the absence of adjudication. R2/R3/R4 remain pending review.

## Correction

Arena advances from `R2-FREE-AGENT-ARENA-v0.3.1` to `R2-FREE-AGENT-ARENA-v0.3.2`. The correction is limited to subject-output serialization/transport handling; task semantics and social conditions are unchanged.

The prompt now requires:

- exactly one top-level object with `decision_summary` and `actions`;
- exact field layouts per action type;
- `write_state.value`, `basis`, and `status` as sibling fields;
- `revise_final_state.patch` and `reason` as sibling fields;
- explicit object closure, comma placement and string escaping checks;
- concise values to reduce syntax risk.

Model transport config advances to `R234-ARENA-DEEPSEEK-v0.2.1`: `json_format_retries` changes from 1 to 2, meaning at most one additional identical-request attempt after malformed JSON. This is bounded infrastructure recovery, not an evaluator. Every malformed provider response is retained, retry count is exposed in the provider response, and token/latency usage is aggregated rather than hidden. No retry is permitted merely because a syntactically valid answer is scientifically inconvenient.

Unchanged:

- E-commerce task and domain pack;
- agent identities/responsibilities/private information;
- free routing and collaboration rights;
- Authority contract;
- late-event schedule;
- observe-until-quiescent scheduler;
- turn/invocation/queue budgets;
- DeepSeek model alias, thinking setting, subject temperature and 4,096-token cap;
- evidence-first and deferred-adjudication policy.

## Gate

The next paid subject action is limited to **one** v0.3.2 E-commerce episode. It is an infrastructure/feasibility gate, not a prevalence sample.

The gate asks whether the subject episode can finish with auditable JSON transport under the bounded recovery policy. If a retry is used, the episode remains identifiable as format-recovered rather than silently equivalent to a first-attempt-valid response.

If the episode succeeds, later small-batch expansion may resume. If it still fails on non-truncation JSON syntax after the bounded retry, real API expansion stops and the subject transport must be redesigned before further spending.
