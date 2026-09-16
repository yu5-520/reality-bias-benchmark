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
- Pair order: counterbalanced by trial (`FREE_THEN_STRUCTURED` for odd trials; `STRUCTURED_THEN_FREE` for even trials).
- Automatic paid evaluator: `false`
- Semantic review: deferred / append-only

## 2. Frozen implementation candidates

- Base Arena: `arena/config/arena_v0.3.json`
- Structured policy: `arena/config/structured_ecommerce_v0.1.json`
- Pair-manifest builder: `arena/build_orchestration_manifest.py`
- Structured runtime: `arena/structured_routing.py`
- Comparison adapter: `arena/orchestration_compare.py`
- Guarded real runner: `arena/run_orchestration_real.py`
- Budget guard: `arena/cost_budget.py`
- Provider factory: `arena/providers.py`
- Real-run workflow: `.github/workflows/r7-orchestration-paired-real.yml`
- Measurement: `docs/trajectory_dynamics_measurement_plan_v3.md`
- R7 protocol: `docs/R7_orchestration_protocol_v0.1.md`

Evidence interfaces:

- `schemas/orchestration_comparison_v0.1.schema.json`
- `schemas/paid_subject_authorization_v0.1.schema.json`
- `schemas/r7_paired_run_summary_v0.1.schema.json`

All file hashes and the exact code commit must be re-bound in the final run manifest at execution time.

## 3. Unresolved fields — MUST freeze before real provider calls

- `provider`: **UNRESOLVED**
- `model`: **UNRESOLVED**
- `model configuration`: **UNRESOLVED**
- `paired trial count`: **UNRESOLVED**
- `maximum subject-call budget`: **UNRESOLVED**
- `explicit spending ceiling`: **UNRESOLVED**
- `currency for spending ceiling`: **UNRESOLVED**
- `run-start commit SHA`: **UNRESOLVED**
- `final manifest hash`: **UNRESOLVED**
- `final analysis-primary metrics`: must point to a frozen metric set/version

The current guarded runner is sequential by manifest order. It therefore honors the counterbalanced pair order rather than introducing an additional worker/concurrency variable.

No default value in an old workflow or model config fills these unresolved fields automatically for R7.

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
- structured-policy hash as comparison metadata;
- logical seed identity where recorded.

The structured row activates the structured policy; the free row records the same policy hash for comparison identity but does not activate it.

The manifest also freezes `pair_execution_order` and `pair_order_pattern`.

## 5. Run-status handling

Every attempted run is preserved.

- `RUN_COMPLETE` — valid completed trajectory;
- `BUDGET_CENSORED` — prefix-scoped observation, never silently treated as negative;
- `RUN_INCOMPLETE` — preserved and reported;
- `RUN_FAILED` — preserved and reported;
- provider/transport failures — reported separately and never regenerated away merely to balance pairs;
- budget-guard stop — remaining runs are explicitly recorded as unattempted rather than silently dropped.

A paired comparison may mark a pair as incomplete when one side fails/censors/is not attempted, but neither existing side is deleted.

## 6. Proposal / realization evidence

For both conditions record subject proposals and realized system actions.

For structured routing specifically preserve:

- original subject envelope;
- blocked actions and reason;
- passed actions;
- realized Arena events.

A blocked `invoke_agent` proposal is still a proposal-level observation. It is not a realized invocation.

Completed real pairs produce `RB-ORCHESTRATION-COMPARISON-v0.1` records with:

`scientific_status = SUBJECT_EVIDENCE_PENDING_SEMANTIC_REVIEW`

This means the structural subject evidence is frozen; it does not mean C/P/R semantics have already been adjudicated.

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

- exact authorization phrase `CALL_REAL_R7_API`;
- named provider;
- named model/config;
- exact paired trial count;
- explicit maximum subject-call count;
- explicit spending ceiling;
- currency matching the chosen model-config pricing snapshot;
- final manifest binding and run-start code SHA.

Generic instructions such as “执行”, “继续”, or repository-update approval do **not** satisfy this paid-run authorization gate.

The workflow defaults to `PREPARE_ONLY`; its provider defaults to `UNRESOLVED`; its spending ceiling and subject-call cap default to zero. These defaults cannot start a paid run.

## 9. Financial guard

`arena/cost_budget.py` adds two independent operational checks:

1. a maximum subject-call cap;
2. a pre-call monetary reservation check against the explicit spending ceiling.

For the configured pricing snapshot, the guard reserves the next call using:

- UTF-8 byte length of the serialized model input as a conservative input proxy;
- configured subject `max_tokens` as the output reservation;
- configured peak/list input and output prices.

After a successful provider response, estimated spend is recomputed from provider-reported usage. If the boundary is reached, no later call may start.

This is an engineering stop guard, **not** a provider invoice guarantee. The provider's final billing record remains authoritative for actual cost.

## 10. Evidence freeze

The guarded runner writes:

- `authorization_record.json`;
- immutable manifest binding;
- raw paired traces;
- per-run journals under the standard evidence-compatible journal path;
- `errors.jsonl` plus frozen `errors.json` array;
- pair-comparison records;
- paired-run summary with attempted/unattempted identities;
- cumulative budget/accounting records.

The workflow then runs the existing standard `arena.evidence` freeze over any preserved traces. Semantic review remains separate and no paid evaluator is called automatically.

## 11. Provider support boundary

The provider factory currently supports:

- DeepSeek subject config;
- Bailian subject config **only when the selected config contains an explicit `subject` section**.

Reviewer-only Bailian configs are intentionally rejected for subject collection rather than silently reusing evaluator parameters.

This keeps provider/model selection an explicit experiment decision.

## 12. Current status

Offline scripted/mock comparison, budget-guard tests, paired-manifest preparation, provider/config binding and authorization-record construction may all be validated without API calls.

The guarded real-run workflow exists but has not been dispatched by this repository update.

This template itself authorizes zero provider calls and zero paid evaluator calls.
