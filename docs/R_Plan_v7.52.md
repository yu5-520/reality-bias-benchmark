# Stage-II v7.52: 84-Cell Engineering Eligibility Freeze and G2 B Gate

Date: 2026-09-27  
Status: **84-CELL ENGINEERING ELIGIBILITY SEALED; G2 ENGINEERING B IS NEXT; NO B EXECUTED.**

Predecessor: `docs/R_Plan_v7.51.md`.

## 1. What v7.52 closes

This version freezes the complete G2-G5 engineering-eligibility population after the corrected 84-cell primary monitor benchmark.

The eligibility object is independent of the post-hoc semantic layers. It reads only the prospectively frozen:

`monitor candidate -> repair package -> parent checkpoint -> legal repair surface -> preserve set -> foreign-state reconstruction check`.

It does not use Layer B, Layer C, CPR labels, or audit-discovered misses to create a repair candidate.

## 2. Frozen population

Population:

`G2-G5 = 84 Natural-A cells`.

Result:

- ELIGIBLE_FOR_ONE_B: **48**;
- NO_PROSPECTIVE_PACKAGE: **12**;
- PARENT_RECONSTRUCTION_BLOCKED: **24**.

No other top-level outcome was observed in this frozen population.

## 3. Group accounting

Each prospective group has the same eligibility geometry:

- G2: 12 eligible / 3 no package / 6 parent blocked;
- G3: 12 eligible / 3 no package / 6 parent blocked;
- G4: 12 eligible / 3 no package / 6 parent blocked;
- G5: 12 eligible / 3 no package / 6 parent blocked.

The symmetry is observed evidence, not an assumption imposed by the ledger.

## 4. System accounting

Across all four groups:

- X1 AutoGen: 0 eligible / 12 parent reconstruction blocked;
- X2 MetaGPT: 12/12 eligible;
- X3 A2A: 0 eligible / 12 no prospective package;
- X4 MCP: 12/12 eligible;
- X5 RAG: 12/12 eligible;
- X6 MemoryBank: 0 eligible / 12 parent reconstruction blocked;
- X7 LongLLMLingua: 12/12 eligible.

X1 remains fail-closed because the required legal same-parent native continuation state is not available.

X3 remains in the natural/audit/monitor population but produced no prospective repair package under the frozen generic monitor/package pipeline.

X6 contains structurally complete package candidates, but the selected same-parent checkpoint depends on mutable MemoryBank foreign state that cannot be legally reconstructed from the frozen archive under the native-preservation contract.

## 5. Task accounting

Each task family contributes:

- T1: 16 eligible / 4 no package / 8 parent blocked;
- T2: 16 eligible / 4 no package / 8 parent blocked;
- T3: 16 eligible / 4 no package / 8 parent blocked.

Eligibility therefore follows the current system/checkpoint boundary more strongly than task family in this frozen population.

## 6. Package selection

For every eligible cell, the selected package is:

`EARLIEST_COMPLETE_PACKAGE_BY_PREFIX_SEQUENCE_THEN_PACKAGE_ID`.

The selected package must satisfy:

- `repair_gate_status = COMPLETE_FOR_STRUCTURED_REPAIR`;
- package hash valid;
- parent reconstruction marked VERIFIED;
- exactly one parent checkpoint hash;
- FULL_NATIVE restore capability;
- native-state hash valid;
- model-visible-context hash valid;
- application-state hash valid;
- non-empty preserve set;
- non-empty legal repair surface;
- no semantic-audit input;
- no CPR-label input;
- no future evidence.

Mutable foreign parent state is checked again at eligibility time rather than trusted from package status alone.

## 7. Frozen G2 B subset

G2 has exactly 12 eligible cells:

- X2-T1, X2-T2, X2-T3;
- X4-T1, X4-T2, X4-T3;
- X5-T1, X5-T2, X5-T3;
- X7-T1, X7-T2, X7-T3.

G2 blocked/non-package cells:

- X1-T1/T2/T3 — parent reconstruction blocked;
- X3-T1/T2/T3 — no prospective package;
- X6-T1/T2/T3 — foreign parent-state reconstruction blocked.

The exact selected package/checkpoint bindings are frozen in:

`stage2/replication_v2/engineering_eligibility_84_v1/G2_b_selection_index.json`.

This index is an eligibility freeze, **not B authorization**.

## 8. Scientific accounting

Eligibility freeze used:

- Natural-A reruns: 0;
- new subject/provider calls: 0;
- paid evaluator calls: 0;
- semantic re-audits: 0;
- Layer-C reads for selection: 0;
- repair calls: 0;
- B executions: 0.

## 9. Evidence bindings

Eligibility ledger:

`stage2/replication_v2/engineering_eligibility_84_v1/eligibility_ledger.json`

Eligibility seal:

`stage2/replication_v2/engineering_eligibility_84_v1/eligibility_seal.json`

Group selection indexes:

`G2_b_selection_index.json` through `G5_b_selection_index.json`.

Freeze workflow:

`36305612096`.

Result:

`ENGINEERING_ELIGIBILITY_84_GATE=PASS`.

## 10. Next gate

The next operation is a separate G2 Engineering-B authorization.

That authorization may use only the 12 frozen G2 eligible rows and must preserve:

- exactly one B per eligible cell;
- same frozen parent checkpoint;
- selected frozen package;
- first B stochastic attempt only;
- no best-of-N;
- no repair retry for a preferred outcome;
- repair executor exits after one package;
- post-repair monitor remains WATCH_ONLY;
- blocked/no-package G2 cells receive zero B calls.

After G2 B is frozen:

`G2 paired audit -> G2 synthesis -> G3 authorization`.

No G3-G5 B is opened by v7.52.
