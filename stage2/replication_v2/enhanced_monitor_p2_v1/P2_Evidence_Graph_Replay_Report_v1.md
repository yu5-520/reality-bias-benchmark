# Stage-II P2 Offline Evidence Graph Replay Result v1

Status: **P2 OFFLINE REPLAY COMPLETE**

## Execution boundary

- population: G2-G5 frozen Natural A, 84/84 trajectories;
- natural reruns: 0;
- provider/model calls: 0;
- evaluator calls: 0;
- repair calls: 0;
- semantic audit used to build the graph: NO;
- CPR labels used to select graph candidates: NO.

## Graph replay

- normalized structural events: **1092**;
- graph nodes: **2243**;
- graph edges: **2348**;
- direct provenance/query edges: **2286**;
- explicitly UNKNOWN reuse/dependency edges: **62**;
- multi-version observed objects: **62**;
- supported edges without evidence refs: **0**;
- semantic dependency edges invented without semantic review: **0**.

Repeated visibility or reuse is represented as UNKNOWN when a dependency cannot be established from direct evidence. This keeps the graph useful for inspection without converting temporal proximity into causality.

## Old monitor versus enhanced graph inspection load

- frozen old monitor candidate records: **996**;
- frozen old monitor unique warning IDs: **955**;
- old monitor unique object refs summed within cells: **996**;
- enhanced graph inspection candidate objects: **62**.

The enhanced candidate count is an inspection-object count, not an alert-accuracy estimate.

## Separate localization proxy

Only after each graph and candidate set was fixed, the frozen full-context review was read as a separate evaluation layer. Targeted chronology-review status changes were applied only to their exact reviewed event keys.

- positive reference events in the available full-context reference: **33**;
- relevant object resolvable somewhere in the graph: **25 / 33**;
- old frozen monitor object localized: **20 / 33**;
- enhanced graph candidate object localized: **12 / 33**.

This is an object-reference localization proxy, not a replacement for the sealed primary 84-cell monitor benchmark.

## Priority route maps

Written for: G2-X3-T2, G2-X5-T2, G3-X1-T3, G3-X4-T2, G4-X3-T2, G5-X6-T3.

These route maps expose observed provenance, version history and unresolved reuse edges. No node receives mutation authority from graph visibility.

## P2 boundary

P2 is complete as an offline graph/inspection comparison. It does not authorize P3/P4 repair runs. A later repair candidate still requires a verified same-parent checkpoint, frozen authorization scope, and separate execution approval.
