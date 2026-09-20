# R8-A Dynamic CPR Semantic Event Reconstruction Result v1

Date: 2026-09-20  
Status: **FROZEN DERIVATIVE RESULT / R8-A COMPLETE / CPR NOT ADJUDICATED**

## 1. Purpose

R8-A converts the completed first-round frozen R2-R7 evidence into a semantic-event ledger and case-bound permission-review packets for later Dynamic CPR adjudication.

This pass performs **semantic event reconstruction only**.

It does not assign positive C/P/R labels, does not rerun subject Agents, and does not mutate any frozen evidence.

## 2. Frozen source binding

The materialization used the exact frozen bytes of four prior evidence artifacts:

| Evidence layer | Artifact ID | Frozen digest |
| --- | ---: | --- |
| R2-R6 complete-route semantic re-audit | 10588404740 | `sha256:14fb11da98fae0afb5e82152c101fc5be937e43259f445b25ad10796b1801182` |
| R6 lineage-completeness package | 10586243376 | `sha256:1a13ad31f0eef2dc0bb9181340a4e581c1738bab947dbfd0f5989d54cd9c5b6d` |
| R7 dual structural comparison | 10586267940 | `sha256:242498dac7ad07e764e56d0e69c606256ac5b8d0294fcedd92b2e150b7385bee` |
| R7 dual semantic audit | 10587430720 | `sha256:dbe8d38c3105f0a645eeaf902ff1fb7dfa4acfd8dc0680d4b63371d441924acf` |

Theory binding:

- `docs/R_Plan_v5.5.md`
- `theory/theory_contract_v0.16.md`
- `docs/R8_Dynamic_CPR_Permission_Penetration_Protocol_v0.3.md`
- `configs/cpr_definition_contract_v0.3.json`
- `configs/cpr_adjudication_contract_v0.3.json`

## 3. Materialized first-round R8-A result

| Item | Result |
| --- | ---: |
| Complete-route audits | 32 |
| Natural R2-R4 complete routes | 3 |
| Canonical R5-R6 complete routes | 29 |
| Actual route-node ledger events | 908 |
| Semantic-edge ledger events | 194 |
| R5 bounded-authority challenge events | 29 |
| R6 semantic-lineage closure overlays | 4 |
| R7 control overlays | 8 |
| Total semantic-event ledger records | **1,175** |
| Dynamic CPR permission-review packets | **29** |
| CPR-positive adjudications | **0** |

Packet domain distribution:

- finance: 5;
- supply_chain: 16;
- software_engineering: 8.

CPR remains:

`NOT_ADJUDICATED`.

## 4. Information-permission substrate

The frozen complete-route semantic layer contains:

- 32 `SOURCE_OBSERVATION` nodes;
- 21 `INDEPENDENT_EVIDENCE_REANCHOR` nodes;
- 4 `NEW_DESCENDANT_CARRIER` nodes;
- 4 `READ_OR_ADOPTION` nodes;
- 162 `ACTION_APPLICATION` nodes;
- 2 `REAFFIRMATION` nodes;
- 1 `TRANSFORMATION` node.

This creates an explicit R8-B substrate for separating:

`independent evidential support`

from:

`lineage-derived semantic support`.

The 21 independent-reanchoring nodes are especially important as healthy comparator material. Their presence must not be converted into a generic CPR-negative label without case-level adjudication; they show that persistence can be reconstructed from independent evidence rather than inherited authority.

## 5. Four high-priority descendant-carrier cases

The four complete-route cases containing `NEW_DESCENDANT_CARRIER` are exactly the four previously identified stronger System Inertia candidates:

1. `wave-3-56ee79f97f54`
2. `wave-4-8b1731b57396`
3. `wave-4-cf726639de1d`
4. `wave-6-7c7e526e4d91`

This alignment is structurally important because the new Dynamic CPR theory asks whether information permission can migrate through semantic descendants.

However:

> **new descendant carrier + System Inertia candidate != C, P or R by itself.**

These four cases are therefore high-priority R8-B adjudication packets, not positive CPR findings.

## 6. Collaboration / execution permission substrate

For all 29 canonical R5-R6 cases, R8-A preserves the complete realized Agent route and derives review surfaces for:

- Agent invocation activity;
- role re-entry;
- baseline task premise;
- actual role sequence;
- later comparison of user-visible/task-visible target with realized process/action scope.

These are P review surfaces only.

`extra Agent call != P`

`role re-entry != P`

R8-B must determine whether the collaboration or execution boundary actually exceeded the supported or authorized task closure.

## 7. Temporal permission substrate

Each canonical R5-R6 packet now binds:

- the one-shot R5 challenge boundary;
- the direct-stimulus end;
- the post-stimulus route window;
- historical System Inertia classification;
- R6 lineage closure where available;
- R7-P / R7-S overlays for the four repair-ready cases.

The R7 layer contributes eight explicit temporal-control overlays:

- 4 persistent semantic-correction arms;
- 4 structured lineage-repair arms.

These make it possible for R8-B to separately test:

- `LINEAGE_PRESERVING_R`;
- `RETROSPECTIVE_GENERATIVE_R`.

But:

`reopen / recompute / repair != R`

and:

`System Inertia != R`.

## 8. Dynamic coupling remains unadjudicated

R8-A does not yet create semantic edges such as:

- `C_DRIVES_P`;
- `P_REINFORCES_C`;
- `R_GENERATES_NEW_C`;
- `R_GENERATES_NEW_P`.

It creates the evidence objects required to judge those transitions later.

This prevents the new Dynamic CPR theory from becoming a post-hoc narrative imposed on the frozen trajectories.

## 9. Frozen derivative outputs

Full derivative package outputs:

| Output | SHA256 | Size |
| --- | --- | ---: |
| `case_index.jsonl` | `cf4208d9de14a345304abad0195c78f9e19d9077fe61d5a51f2109b11ccac96d` | 29,392 B |
| `permission_review_packets.jsonl` | `cdd79fb745ef7b096703332bbc5a2b82047c57d88f6f76e80787ad01c7a3b882` | 120,049 B |
| `semantic_event_ledger.jsonl` | `717a9948516845cc1d4edf4c0efc25e64216bee819907b8c0a8ac67638cad013` | 3,336,982 B |
| `summary.json` | `b24d30d00472bdae1a6f15027d387a4395828912fe35dbc2ffd3f3ffa1aaa1eb` | 1,958 B |
| frozen ZIP package | `8d5894a531523663737a0d06934258977cc7fa142d266a8e9db90dfd016503ac` | 417,796 B |

The large ledger remains a derivative artifact rather than being committed inline into source history. Its exact hash is frozen in the result manifest and it is reproducible from the committed R8-A builder plus the four pinned source artifacts.

## 10. Control-plane note

The repository includes an issue-triggered offline materialization workflow.

Issue #142 was created through the connected GitHub application, but that connector-created issue did not emit the expected `issues` workflow event. The materialization was therefore reproduced in the chat-side container using the committed deterministic builder against the exact frozen GitHub artifact bytes.

This affected only the trigger path.

It did **not** alter:

- source evidence;
- derivation logic;
- artifact identities;
- output hashes;
- scientific interpretation boundary.

## 11. Execution boundary

- new provider calls: **0**
- new paid evaluator calls: **0**
- subject reruns: **0**
- raw evidence mutation: **NO**
- historical semantic record mutation: **NO**
- CPR adjudication: **NO**

## 12. Next gate

R8-A is complete.

The next distinct step is **R8-B — Permission-Penetration Adjudication** over the 29 frozen packets.

R8-B should begin with the strongest contrasts:

1. independent re-anchoring comparator cases;
2. the four descendant-carrier / stronger-System-Inertia cases;
3. only then broader Dynamic C/P/R and coupling adjudication.

No new subject trajectory is required for that gate.
