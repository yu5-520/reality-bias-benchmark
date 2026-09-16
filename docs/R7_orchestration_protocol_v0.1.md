# R7 Orchestration Boundary Protocol v0.1

Date: 2026-09-16  
Status: ENGINEERING-FROZEN CANDIDATE / NO REAL PROVIDER RUN AUTHORIZED  
Depends on:

- `docs/R_Plan_v3.2.md`
- `theory/theory_contract_v0.3.md`
- `docs/trajectory_dynamics_measurement_plan_v3.md`

## 1. Question

R7 asks whether orchestration structure changes trajectory-level Reality Bias dynamics.

It does **not** rank one architecture as universally better.

Primary comparison:

- Condition A — `EMERGENT_FREE_ROUTING`
- Condition B — `STRUCTURED_SYSTEM_OWNED_ROUTING`

The target quantities are first-Jump location/type, propagation topology, Authority Penetration, post-Jump inertia and recovery behavior.

## 2. Condition A — Emergent / Free Routing

Reference runtime:

- current Free-Agent Arena v0.3.2;
- one overall task goal;
- full registered specialist directory remains visible;
- Agents may dynamically invoke other specialists within the frozen Arena policy;
- no experimental commit/routing gate is enabled unless a separately named R5 condition says so.

This condition preserves the current natural self-organization substrate.

## 3. Condition B — Structured / System-Owned Routing

Reference implementation:

- `arena/structured_routing.py`
- `arena/config/structured_ecommerce_v0.1.json`

The same domain task, public context, late event, Agent definitions and action language remain available, but:

- stage order is externally assigned;
- stage goals are explicitly delivered by the environment;
- the system owns executable routing;
- dynamic `invoke_agent` proposals are retained as subject proposals but blocked from system realization;
- non-stage action types are filtered by deterministic stage policy;
- stage handoff occurs through recorded shared state and the system-owned queue;
- the original subject proposal is preserved under `provider_response.structured_routing.original_subject_envelope`;
- realized Arena actions remain separately recorded in the normal trace.

This provides a proposal-versus-realization distinction rather than deleting evidence that the model attempted an out-of-policy action.

## 4. Current E-commerce stage sequence

The v0.1 structured condition uses a minimal four-stage chain:

1. `S1_media` — `ads`
2. `S2_inventory` — `inventory`
3. `S3_finance` — `finance`
4. `S4_integrate` — `ops_lead`

The full domain Agent registry remains unchanged. The system-owned condition determines which actors are scheduled in this minimal chain.

The final stage may finalize and later handle the fixed late event without creating new stages.

## 5. Confound discipline

The v0.1 A/B comparison intentionally changes orchestration structure, which includes scheduling/activation and stage-goal exposure. It therefore does **not** claim to isolate one microscopic routing bit.

Hold constant where possible:

- domain task and public context;
- late-event content/timing rule;
- model/provider/config;
- base Agent role/responsibility/private context definitions;
- observation horizon and evidence policy;
- semantic-review contract;
- code version within a comparison batch.

Record explicitly:

- active/scheduled Agent differences;
- blocked proposal counts in Condition B;
- actual executed Agent counts;
- stage/handoff identity;
- calls/tokens/turns.

If the v0.1 comparison is scientifically ambiguous, the next step is not to declare a winner. It is to separate factors with a later design, potentially:

`goal fixed/staged × context continuous/reset-or-compressed`

or a narrower scheduling-only intervention.

## 6. Primary structural outcomes

For each valid run/branch:

- time/turn to first Jump candidate;
- Jump candidate type;
- first operational commit boundary;
- lineage depth;
- penetration depth;
- affected descendant count;
- affected Agent count;
- blocked-proposal count and type, where applicable;
- post-Jump persistence/inertia;
- feedback-return structure;
- recovery distance/cost if R6 is attached.

C/P/R semantic conclusions are appended later and do not replace structural records.

## 7. Proposal versus realization in Condition B

Condition B must retain both:

- **subject proposal** — what the upstream model attempted;
- **realized action set** — what the system-owned policy actually admitted.

A blocked dynamic invocation is not erased. It is evidence that a proposal occurred but did not obtain operational effect.

This enables direct comparison of:

`proposal expansion tendency`

versus

`realized graph expansion`.

## 8. No production-framework dependency

The structured condition is a small experimental policy only.

It does not import a production control plane, deployment system, business database, full queue/lease framework, frontend, or product-specific engineering architecture into the research repository.

Its purpose is to create a controllable orchestration boundary for mechanism testing.

## 9. Offline validation requirement

Before any real provider experiment:

- structured policy validation passes;
- system-owned stage queue order is deterministic;
- blocked dynamic invocation proposals remain preserved in evidence;
- no blocked invocation is realized in Arena state;
- late-event path reaches the final-stage actor correctly;
- existing Free-Agent regression suite remains green;
- experimental-control snapshot/branch tests remain green.

The current unit-test entry is:

`arena/tests/test_structured_routing.py`

## 10. Real-run gate

A real R7 provider run requires a separate run-freeze document containing:

- exact A/B configs and hashes;
- model/provider version;
- repeat count;
- valid/censored/failure handling;
- primary metrics and analysis plan;
- explicit paid API authorization;
- explicit spending ceiling.

This v0.1 protocol does not authorize any provider call.
