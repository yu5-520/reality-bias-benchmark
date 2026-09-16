# R7 Real-Model Orchestration Run Freeze Template v0.1

Date: 2026-09-16  
Status: TEMPLATE / NOT AUTHORIZED / NOT A FORMAL SUBJECT FREEZE

This document is intentionally incomplete. A real R7 subject batch must not start until every unresolved field below is frozen and the API authorization fields are explicitly supplied.

## 1. Experiment identity

- Experiment family: `R7-ORCHESTRATION-BOUNDARY-v0.1`
- Domain: `ecommerce`
- Condition A: `EMERGENT_FREE_ROUTING`
- Condition B: `STRUCTURED_SYSTEM_OWNED_ROUTING`
- Pairing: same task/domain/Agent registry/model config/code version and paired logical seed per trial where the provider permits meaningful seed recording.
- Automatic paid evaluator: `false`
- Semantic review: deferred / append-only

## 2. Frozen implementation candidates

- Base Arena: `arena/config/arena_v0.3.json`
- Structured policy: `arena/config/structured_ecommerce_v0.1.json`
- Pair-manifest builder: `arena/build_orchestration_manifest.py`
- Structured runtime: `arena/structured_routing.py`
- Comparison adapter: `arena/orchestration_compare.py`
- Measurement: `docs/trajectory_dynamics_measurement_plan_v3.md`
- R7 protocol: `docs/R7_orchestration_protocol_v0.1.md`

All file hashes and the exact code commit must be re-bound in the final run manifest at execution time.

## 3. Unresolved fields — MUST freeze before real provider calls

- `provider`: **UNRESOLVED**
- `model`: **UNRESOLVED**
- `model configuration`: **UNRESOLVED**
- `paired trial count`: **UNRESOLVED**
- `worker/concurrency limit`: **UNRESOLVED**
- `maximum subject-call budget`: **UNRESOLVED**
- `explicit spending ceiling`: **UNRESOLVED**
- `currency for spending ceiling`: **UNRESOLVED**
- `run-start commit SHA`: **UNRESOLVED**
- `final manifest hash`: **UNRESOLVED**
- `final analysis-primary metrics`: must point to a frozen metric set/version

No default value in an old workflow or model config fills these fields automatically for R7.

## 4. Pair manifest rule

The prepared manifest must contain exactly two rows per `pair_id`:

- one `EMERGENT_FREE_ROUTING` row;
- one `STRUCTURED_SYSTEM_OWNED_ROUTING` row.

Within a pair, the following bindings must match:

- domain hash;
- task hash;
- Agent-pool hash;
- Arena-config hash;
- model-config hash;
- logical seed identity where recorded.

The structured row additionally binds the structured-policy hash. The free row retains the same policy hash as comparison metadata but does not activate the policy.

## 5. Run-status handling

Every attempted run is preserved.

- `RUN_COMPLETE` — valid completed trajectory;
- `BUDGET_CENSORED` — prefix-scoped observation, never silently treated as negative;
- `RUN_INCOMPLETE` — preserved and reported;
- `RUN_FAILED` — preserved and reported;
- provider/transport failures — reported separately and never regenerated away merely to balance pairs.

A paired comparison may mark a pair as incomplete when one side fails/censors, but neither side is deleted.

## 6. Proposal / realization evidence

For both conditions record subject proposals and realized system actions.

For structured routing specifically preserve:

- original subject envelope;
- blocked actions and reason;
- passed actions;
- realized Arena events.

A blocked `invoke_agent` proposal is still a proposal-level observation. It is not a realized invocation.

## 7. Primary structural outcomes

Before the real run, freeze which of the following are primary versus secondary:

- first Jump candidate location/type;
- proposal invocation expansion;
- realized invocation expansion;
- first operational commit;
- propagation/lineage depth;
- Authority Penetration depth;
- affected descendants/Agents;
- post-Jump persistence/inertia;
- feedback-return structure;
- recovery distance/cost when linked to R6;
- calls / turns / tokens.

No architecture-level winner/ranking is a permitted output. The experiment estimates structural differences under the frozen conditions.

## 8. API authorization gate

A real run requires all of the following in one explicit authorization record:

- named provider;
- named model/config;
- exact or bounded run count;
- explicit spending ceiling;
- currency;
- explicit instruction to execute the paid subject run.

Generic instructions such as “执行”, “继续”, or repository-update approval do **not** satisfy this paid-run authorization gate.

## 9. Current status

Offline scripted/mock comparison and paired-manifest machinery may be validated without API calls.

This template itself authorizes zero provider calls and zero paid evaluator calls.
