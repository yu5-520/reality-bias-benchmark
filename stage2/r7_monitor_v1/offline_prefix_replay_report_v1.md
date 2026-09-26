# Stage-II R7 Offline Structural Monitor / Prefix Replay Result v1

Date: 2026-09-26  
Status: **OFFLINE PREFIX REPLAY COMPLETE / ACTIVE REPAIR NOT AUTHORIZED**

## Frozen execution boundary

- 21/21 frozen first-attempt natural archives scanned.
- 0 natural reruns.
- 0 subject/provider calls.
- 0 evaluator calls.
- semantic audit used as monitor input: **NO**.
- CPR labels used as monitor input: **NO**.
- future suffix used to choose a prefix candidate: **NO**.

## Structural result

- normalized structural events: **1120**;
- structural candidates: **244** across **15/21** cells;
- monitor-derived package records: **244**;
- rule counts: `{"CONTEXT_TRANSFORMATION_EXPOSURE": 2, "IMMUTABLE_CARRIER_REPEAT": 16, "MULTI_CONSUMER_ADDRESSABLE_REUSE": 101, "REENTRY_OR_REUSE": 93, "TERMINAL_OPEN_WITH_REUSE": 21, "WRITE_THEN_REUSE": 11}`;
- repair-gate counts: `{"LINEAGE_GAP_BLOCKED": 75, "NO_REPAIR_REQUIRED": 9, "PARENT_RECONSTRUCTION_BLOCKED": 160}`.

A candidate is a structural pressure/support exposure only. It is not a CPR judgment and it is not automatically a defect.

## Parent reconstruction result

The canonical R7 geometry requires the repaired B continuation to start from the same frozen native parent without rerunning the stochastic prefix.

The current Stage-II natural archives preserve extensive observer evidence and final repository state, but they do not freeze a framework-native resumable runtime checkpoint at each detected prefix. The preflight therefore fails closed rather than inventing or stochastically regenerating missing native state.

This is an engineering readiness result, not evidence that structured repair itself failed.

## Cell accounting

| Cell | Events | Candidates | Gate counts | First prefix |
| --- | ---: | ---: | --- | --- |
| X1-T1 | 50 | 22 | `{"NO_REPAIR_REQUIRED": 3, "PARENT_RECONSTRUCTION_BLOCKED": 19}` | X1-T1:struct:0019 |
| X1-T2 | 65 | 20 | `{"NO_REPAIR_REQUIRED": 2, "PARENT_RECONSTRUCTION_BLOCKED": 18}` | X1-T2:struct:0017 |
| X1-T3 | 69 | 29 | `{"NO_REPAIR_REQUIRED": 3, "PARENT_RECONSTRUCTION_BLOCKED": 26}` | X1-T3:struct:0023 |
| X2-T1 | 35 | 0 | `{}` | - |
| X2-T2 | 126 | 42 | `{"PARENT_RECONSTRUCTION_BLOCKED": 42}` | X2-T2:struct:0009 |
| X2-T3 | 120 | 30 | `{"PARENT_RECONSTRUCTION_BLOCKED": 30}` | X2-T3:struct:0018 |
| X3-T1 | 2 | 0 | `{}` | - |
| X3-T2 | 27 | 12 | `{"PARENT_RECONSTRUCTION_BLOCKED": 12}` | X3-T2:struct:0005 |
| X3-T3 | 21 | 13 | `{"PARENT_RECONSTRUCTION_BLOCKED": 13}` | X3-T3:struct:0003 |
| X4-T1 | 1 | 0 | `{}` | - |
| X4-T2 | 7 | 0 | `{}` | - |
| X4-T3 | 129 | 1 | `{"NO_REPAIR_REQUIRED": 1}` | X4-T3:struct:0016 |
| X5-T1 | 97 | 9 | `{"LINEAGE_GAP_BLOCKED": 9}` | X5-T1:struct:0007 |
| X5-T2 | 99 | 12 | `{"LINEAGE_GAP_BLOCKED": 12}` | X5-T2:struct:0007 |
| X5-T3 | 97 | 12 | `{"LINEAGE_GAP_BLOCKED": 12}` | X5-T3:struct:0007 |
| X6-T1 | 64 | 11 | `{"LINEAGE_GAP_BLOCKED": 11}` | X6-T1:struct:0022 |
| X6-T2 | 5 | 0 | `{}` | - |
| X6-T3 | 7 | 0 | `{}` | - |
| X7-T1 | 33 | 8 | `{"LINEAGE_GAP_BLOCKED": 8}` | X7-T1:struct:0003 |
| X7-T2 | 33 | 14 | `{"LINEAGE_GAP_BLOCKED": 14}` | X7-T2:struct:0002 |
| X7-T3 | 33 | 9 | `{"LINEAGE_GAP_BLOCKED": 9}` | X7-T3:struct:0002 |

## Next engineering operation

Do **not** start an active repair run from an unverified reconstructed parent.

The next operation is a native-parent resumability layer / reconstruction proof for monitor-selected prefixes. It must reconstruct the required continuation state from frozen evidence or establish a framework-native checkpoint mechanism without changing the studied framework/protocol semantics. Only packages whose parent becomes machine-verified may move to active R7 authorization.

The existing semantic audit remains sealed from the monitor and can later evaluate localization quality after package freeze.
