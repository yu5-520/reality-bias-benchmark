# R7 Runtime Integration Contract

This document defines the minimum adapter boundary for wiring the validated R7 protocol into the repository's existing Arena/branch runtime.

## Principle
Do not create a second experimental engine for R7. Reuse the existing continuation/runtime path and add a small structural-control adapter that changes only how the same frozen J0 payload is exposed or recovered.

## Required runtime inputs
The adapter must receive an immutable experiment envelope containing:
- `protocol_id`;
- `arm_id`;
- frozen `parent_state_hash`;
- selected `jump_id` and `source_event`;
- semantic `payload_id` and target path;
- observation horizon;
- measurement schema id;
- code/config identity.

The adapter must not infer or silently rewrite these fields.

## C1 — one-shot adapter
Behavior:
1. expose the semantic payload to the first eligible post-J0 agent turn;
2. record exposure event;
3. mark overlay consumed immediately after delivery;
4. prevent all later experiment-origin reinjection;
5. leave persistent parent/shared-state source unchanged;
6. continue through the normal runtime.

Required evidence fields:
- `exposure_count`;
- `first_exposure_turn`;
- `overlay_consumed`;
- `reinjection_count`;
- `persistent_parent_mutation`.

Fail closed if `exposure_count != 1`, `reinjection_count != 0`, or persistent parent mutation occurs.

## C2 — persistent-field adapter
Behavior:
1. expose the same semantic payload to every eligible post-J0 turn within the declared horizon;
2. record every exposure;
3. keep the experiment field external to the frozen parent state;
4. do not convert persistent exposure into a permanent source-state rewrite;
5. continue through the normal runtime.

Required evidence fields:
- `exposure_count`;
- ordered `exposure_turns`;
- `eligible_turn_count`;
- `payload_hash` for each exposure;
- `persistent_parent_mutation`.

Fail closed if payload hashes differ across exposures or persistent parent mutation occurs.

## C3 — ALR adapter
Behavior:
1. identify the earliest relevant authority-violating ancestor using registered lineage/authority evidence;
2. compute dependency closure under the runtime's registered dependency relation;
3. partition reachable nodes into `affected` and `preserved`;
4. freeze preserved successful nodes;
5. apply the matched semantic correction to the authority/provenance condition rather than continuously injecting it as context;
6. emit a distinct revision identity;
7. reopen/re-execute only the affected closure using normal runtime execution;
8. append the revised lineage rather than overwriting the original evidence.

Required evidence fields:
- `authority_anchor_node`;
- `authority_anchor_reason`;
- `dependency_relation_version`;
- ordered `affected_nodes`;
- ordered `preserved_nodes`;
- `closure_hash`;
- `revision_hash`;
- `reopened_nodes`;
- `reexecuted_nodes`;
- `preserved_nodes_mutated`;
- `original_lineage_hash`;
- `revised_lineage_hash`.

Fail closed if:
- no authority anchor is inspectable;
- affected/preserved sets overlap;
- a preserved node is mutated;
- revision identity equals original lineage identity;
- a reopened node lies outside affected closure;
- an affected node required by dependency closure is silently omitted.

## Cross-arm invariants
Before launch, verify:
- same frozen parent;
- same J0;
- same semantic correction payload and payload hash;
- same task input;
- same agent pool/role prompts;
- same model/provider binding;
- same downstream horizon;
- same Process Reality measurement schema.

Only propagation/recovery structure is allowed to vary by arm.

## Runtime output envelope
Each arm must export a machine-readable envelope with:
```json
{
  "protocol_id": "RB-R7-STRUCTURAL-INERTIA-CONTROL-v1.0",
  "arm_id": "C1_ONE_SHOT | C2_PERSISTENT_FIELD | C3_ALR",
  "source": {
    "parent_state_hash": "...",
    "jump_id": "J0",
    "source_event": "E32",
    "payload_id": "..."
  },
  "runtime": {
    "code_sha": "...",
    "config_hash": "...",
    "model_binding": "..."
  },
  "structural_control": {},
  "raw_trace": [],
  "measurement_schema": "RB-PROCESS-REALITY-MECHANISM-MEASUREMENT-v0.4",
  "terminal_outcome": {},
  "integrity": {}
}
```

## Measurement rule
R7 does not introduce a new primary ontology. Continue using the existing Process Reality structural quantities and extend only where ALR requires explicit recovery lineage fields.

Primary derivation must remain possible from frozen raw evidence without calling a reviewer model.

## Launch gate
The formal R7 subject workflow may be added only after:
1. protocol fixture passes offline validation;
2. runtime adapter passes deterministic fixture tests for all three arms;
3. ALR dependency-closure test proves unaffected-node preservation;
4. raw evidence is frozen before any semantic interpretation layer;
5. reviewer/evaluator failure is unable to trigger a subject rerun.
