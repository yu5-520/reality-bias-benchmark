# Reality Bias System Behavior Measurement Plan v4.5.1

Date: 2026-09-17  
Status: FORWARD / R6 IDENTIFICATION / METHODOLOGICAL CLOSURE  
Predecessor: `docs/system_behavior_measurement_plan_v4.5.md`

## 1. Measurement hierarchy

`raw evidence -> local response -> normal inheritance/carrier evidence -> inertia candidate -> natural-baseline comparison -> intervention-related inertia -> frozen-target contrast -> R7 closure/control -> R8 semantics`

No layer automatically promotes to the next.

## 2. Local response

T9 remains the direct-response window for the frozen design. Immediate checking, message, write, invocation, reroute or finalization is local response unless later evidence shows inherited consequences beyond that window.

## 3. Normal inheritance versus inertia candidate

Record normal inheritance whenever information is delivered/read/reused.

Label an `INERTIA_CANDIDATE` only if evidence supports that a prior epistemic status, commitment, constraint or action tendency changes later process options, transition propensity or downstream state.

Record whether a relevant challenge/downgrade/withdrawal opportunity occurred and whether the constraint persisted afterward.

## 4. Carrier relation evidence

Each claimed carrier chain should preserve relation records with:

- source ref;
- destination ref;
- relation type;
- actor/turn;
- evidence refs;
- evidence level;
- semantic-use status where observable;
- inherited state/action refs where applicable.

Reachability alone is never upgraded to adoption.

## 5. Three-domain process distance

Report three domain vectors separately.

### `STRUCTURAL_DISTANCE`

- event/edge set;
- actor set/sequence;
- reach/depth;
- branch/merge/re-entry;
- path family;
- reconvergence.

### `INHERITANCE_DISTANCE`

- delivery/read;
- explicit reference;
- adoption/rejection/abandonment;
- inherited state/action;
- propagation/re-entry;
- source replacement.

### `EPISTEMIC_AUTHORITY_DISTANCE`

- authority/status used downstream;
- response to downgrade;
- unsupported re-confirmation;
- authority transfer/reconstruction;
- independently sufficient new evidence.

No total scalar is required for the first paper.

## 6. R6-D target contrast

Frozen conditions remain S0/S1/S2.

The primary contrast remains `S2 - S1`, but report it first as `FROZEN_TARGET_RESPONSE_CONTRAST`.

Also record pre-outcome target descriptors:

- task relevance;
- provenance class;
- structural location;
- downstream exposure opportunities;
- decision-role category where determinable.

A stronger Escape-derived specificity interpretation must state the matching/robustness evidence used.

## 7. Conditionality record

Every repeated same-parent branch must carry:

- `historical_prefix_hash`;
- task/model/agent/environment binding;
- replicate id;
- execution order position;
- `conditional_identification=true`;
- `independent_population_sample=false`.

## 8. Experiment-origin persistence semantics

For the frozen v0.2 operator:

- legacy `persistent_state_mutation=false` is interpreted as `experiment_origin_persistent_state_mutation=false`;
- `endogenous_agent_state_mutation_allowed=true`;
- endogenous writes/messages/invocations after exposure must be recorded, not filtered.

## 9. R7 closure measurements

Record separately:

- `potentially_affected_refs` and hash;
- `evidence_supported_affected_refs` and hash;
- `mechanically_required_replay_refs` and hash;
- `repair_closure_refs` and hash;
- `preserved_refs` and hash.

The repair closure must be explainable as evidence-supported affected nodes plus only frozen replay dependencies.

## 10. Hash/adoption separation

Hashes support identity, revision and lineage queries. Adoption requires explicit relation evidence. Reports must not use shared hash ancestry as a substitute for decision-premise evidence.

## 11. Censoring

Natural early termination remains right-censoring. Censored dimensions are unresolved, not zero.

## 12. Authorization

Offline validation only. No provider/evaluator/semantic-adjudication authorization.
