# Stage-II R7 Offline Structural Monitor / Prefix Replay Result v1

Date: 2026-09-26  
Status: **OFFLINE PREFIX REPLAY + PACKAGE ASSEMBLY COMPLETE / ACTIVE REPAIR NOT AUTHORIZED**

## Frozen execution boundary

- 21/21 frozen first-attempt natural archives scanned.
- 0 natural reruns.
- 0 subject/provider calls.
- 0 evaluator calls.
- semantic audit used as monitor input: **NO**.
- CPR labels used as monitor input: **NO**.
- future suffix used to choose a prefix candidate: **NO**.

## Structural monitor result

- normalized structural events: **1120**;
- raw structural candidate signals retained: **244** across **15/21** cells;
- structurally assembled repair episodes/packages: **24** across **15/21** cells;
- raw candidate rule counts: `{"CONTEXT_TRANSFORMATION_EXPOSURE": 2, "IMMUTABLE_CARRIER_REPEAT": 16, "MULTI_CONSUMER_ADDRESSABLE_REUSE": 101, "REENTRY_OR_REUSE": 93, "TERMINAL_OPEN_WITH_REUSE": 21, "WRITE_THEN_REUSE": 11}`;
- final repair-gate counts: `{"LINEAGE_GAP_BLOCKED": 7, "NO_REPAIR_REQUIRED": 1, "PARENT_RECONSTRUCTION_BLOCKED": 16}`.

Raw candidate signals remain individually auditable. They are not counted as separate repair experiments. Generic structural assembly merges connected pressure/support signals into lineage-bounded package episodes without semantic labels.

## Parent reconstruction / lineage gate

- PARENT_RECONSTRUCTION_BLOCKED: **16** packages;
- LINEAGE_GAP_BLOCKED: **7** packages;
- NO_REPAIR_REQUIRED: **1** packages;
- COMPLETE_FOR_STRUCTURED_REPAIR: **0** packages.

The current frozen archives preserve rich process evidence but do not freeze framework-native resumable runtime checkpoints at the monitor-selected prefixes. Immutable RAG / MemoryBank / compression carriers are also deliberately not treated as writable repair surfaces; where a legal downstream adoption anchor is not fully bound by raw structural evidence, the package remains LINEAGE_GAP_BLOCKED.

The monitor therefore fails closed. This is an engineering readiness result, not an R7 repair-efficacy result.

## Cell accounting

| Cell | Events | Raw candidates | Packages | Package gates | First prefix |
| --- | ---: | ---: | ---: | --- | --- |
| X1-T1 | 50 | 22 | 1 | `{"PARENT_RECONSTRUCTION_BLOCKED": 1}` | X1-T1:struct:0019 |
| X1-T2 | 65 | 20 | 2 | `{"PARENT_RECONSTRUCTION_BLOCKED": 2}` | X1-T2:struct:0017 |
| X1-T3 | 69 | 29 | 2 | `{"PARENT_RECONSTRUCTION_BLOCKED": 2}` | X1-T3:struct:0023 |
| X2-T1 | 35 | 0 | 0 | `{}` | - |
| X2-T2 | 126 | 42 | 5 | `{"PARENT_RECONSTRUCTION_BLOCKED": 5}` | X2-T2:struct:0009 |
| X2-T3 | 120 | 30 | 3 | `{"PARENT_RECONSTRUCTION_BLOCKED": 3}` | X2-T3:struct:0018 |
| X3-T1 | 2 | 0 | 0 | `{}` | - |
| X3-T2 | 27 | 12 | 2 | `{"PARENT_RECONSTRUCTION_BLOCKED": 2}` | X3-T2:struct:0005 |
| X3-T3 | 21 | 13 | 1 | `{"PARENT_RECONSTRUCTION_BLOCKED": 1}` | X3-T3:struct:0003 |
| X4-T1 | 1 | 0 | 0 | `{}` | - |
| X4-T2 | 7 | 0 | 0 | `{}` | - |
| X4-T3 | 129 | 1 | 1 | `{"NO_REPAIR_REQUIRED": 1}` | X4-T3:struct:0016 |
| X5-T1 | 97 | 9 | 1 | `{"LINEAGE_GAP_BLOCKED": 1}` | X5-T1:struct:0007 |
| X5-T2 | 99 | 12 | 1 | `{"LINEAGE_GAP_BLOCKED": 1}` | X5-T2:struct:0007 |
| X5-T3 | 97 | 12 | 1 | `{"LINEAGE_GAP_BLOCKED": 1}` | X5-T3:struct:0007 |
| X6-T1 | 64 | 11 | 1 | `{"LINEAGE_GAP_BLOCKED": 1}` | X6-T1:struct:0022 |
| X6-T2 | 5 | 0 | 0 | `{}` | - |
| X6-T3 | 7 | 0 | 0 | `{}` | - |
| X7-T1 | 33 | 8 | 1 | `{"LINEAGE_GAP_BLOCKED": 1}` | X7-T1:struct:0003 |
| X7-T2 | 33 | 14 | 1 | `{"LINEAGE_GAP_BLOCKED": 1}` | X7-T2:struct:0002 |
| X7-T3 | 33 | 9 | 1 | `{"LINEAGE_GAP_BLOCKED": 1}` | X7-T3:struct:0002 |

## Next engineering operation

Do **not** start an active repair continuation from an unverified parent.

Next: build and audit framework-specific native-parent resumability/reconstruction proofs for monitor-selected prefixes, without modifying upstream framework/protocol semantics and without rerunning the stochastic natural prefix. For immutable foreign information carriers, bind the observed carrier to the nearest legal downstream application/process repair surface without mutating the foreign store.

Only machine-verified packages may later move to active R7 authorization. The existing complete semantic audit remains sealed from this engineering path until package freeze and later validation.
