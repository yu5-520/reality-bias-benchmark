# R7 Execution Status — 2026-09-17

## Current state
R7 has entered implementation as a three-arm structural-control experiment contract. No paid subject run has been launched from this branch.

Implemented on branch `r7-structural-inertia-control`:
- R7 execution plan;
- formal three-arm protocol schema;
- frozen-parent/J0 matched fixture;
- offline fail-closed validator;
- pull-request CI gate that does not require provider credentials.

## Arms
- `C1_ONE_SHOT`: bounded one-shot exposure followed by free continuation.
- `C2_PERSISTENT_FIELD`: the same semantic payload is continuously propagated into eligible downstream turns without mutating the frozen parent.
- `C3_ALR`: Authority-Localized Recovery using earliest authority-violating ancestor, registered dependency closure, unaffected-node preservation, revision lineage, and localized subgraph reopen/re-execution.

## Frozen source binding
The current example fixture is bound to the existing formal R5-MID source:
- source run: `35132777581`;
- frozen parent state: `aca000a63106a393efe35dad4e0051e09f0e0cf0d6ced09640f6f9fd2eb2a47c`;
- source execution SHA: `8a33444741c9f9e016ffbd72aa5955a6da81187d`;
- selected Jump: `J0`, source event `E32`;
- target field: `shared_state_metadata.inventory_stockout_assessment_v1.status`;
- matched semantic transform: `fact → unconfirmed`;
- measurement ontology: `RB-PROCESS-REALITY-MECHANISM-MEASUREMENT-v0.4`.

## Integrity constraints now encoded
The fixture/validator fail closed unless:
1. all three arms exist and no extra arm is silently added;
2. the parent, J0 target, semantic payload, and measurement ontology are explicit;
3. C1 has exactly one exposure and no persistent parent mutation;
4. C2 is persistent propagation of the same field and no persistent parent mutation;
5. C3 uses ALR authority anchoring + dependency closure + preservation + revision lineage;
6. the experiment asserts equal semantic payload, same parent, same Jump, same horizon, and fail-closed execution.

## Next implementation boundary
The next code change should reuse the repository's existing arena/branch execution machinery. Do not introduce a parallel R7 runtime unless an existing interface is demonstrably insufficient.

The runtime integration must emit, for every arm:
- exposure events and consumption state;
- lineage/dependency edges;
- affected and preserved node sets;
- revision identifier for ALR;
- reopened nodes/subgraph boundaries;
- downstream process events in the existing measurement format;
- terminal outcome only as a secondary endpoint.

No real-model R7 call should occur until the offline contract gate passes on the PR head and the runtime adapter can reproduce the three arm semantics from the same frozen parent/J0.
