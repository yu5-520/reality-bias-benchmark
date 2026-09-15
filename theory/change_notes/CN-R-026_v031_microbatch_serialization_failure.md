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

Arena advances from `R2-FREE-AGENT-ARENA-v0.3.1` to `R2-FREE-AGENT-ARENA-v0.3.2` with a serialization-only subject-prompt correction.

The prompt now requires:

- exactly one top-level object with `decision_summary` and `actions`;
- exact field layouts per action type;
- `write_state.value`, `basis`, and `status` as sibling fields;
- `revise_final_state.patch` and `reason` as sibling fields;
- explicit object closure, comma placement and string escaping checks;
- concise values to reduce syntax risk.

Unchanged:

- E-commerce task and domain pack;
- agent identities/responsibilities/private information;
- free routing and collaboration rights;
- Authority contract;
- late-event schedule;
- observe-until-quiescent scheduler;
- turn/invocation/queue budgets;
- DeepSeek model alias and subject temperature;
- evidence-first and deferred-adjudication policy.

## Gate

The next paid subject action is limited to **one** v0.3.2 E-commerce episode. It is an infrastructure/feasibility gate, not a prevalence sample.

If it succeeds, later small-batch expansion may resume. If it fails again on non-truncation JSON syntax, real API expansion stops and the subject transport must be redesigned before further spending.
