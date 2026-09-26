# Stage-II G2-G5 84-Cell Natural Block Preflight Report v1.0

Date: 2026-09-26  
Status: **FROZEN READY / ZERO SCIENTIFIC SUBJECT CALLS / ACTIVE EXECUTION NOT YET AUTHORIZED**  
Canonical plan predecessor: `docs/R_Plan_v7.45.md`  
Freeze record: `configs/stage2_g2_g5_natural_block_preflight_freeze_v1.json`

## 1. Purpose

This report closes the pre-execution engineering gate required before G2-G5 prospective natural collection.

The gate had four questions:

1. Is the exact four-group natural population frozen before any scientific subject call?
2. Can all seven heterogeneous wrappers honor one 64-logical-model-decision ceiling without rewriting native framework/protocol semantics?
3. Can raw evidence for the independent full semantic audit be separated from prospective monitor outputs at collection time?
4. Does the new prospective path preserve the historical G1 default path rather than silently rewriting it?

All four gates passed.

No scientific subject/provider call, paid evaluator call, or active repair was used.

---

## 2. Exact natural population

The canonical launch contract is:

`configs/stage2_g2_g5_84_cell_natural_block_launch_contract_v1.json`.

It contains exactly:

- G2: 21 cells;
- G3: 21 cells;
- G4: 21 cells;
- G5: 21 cells.

Total:

`4 × 21 = 84 prospective natural first attempts`.

Every cell is uniquely bound to:

- group ID;
- X condition;
- task ID;
- first-attempt index = 1;
- runner module;
- 64 logical-decision ceiling;
- natural output root;
- audit-raw bundle manifest;
- monitor-runtime bundle manifest.

No B is admitted before all 84 A cells are sealed.

---

## 3. What “64 logical decisions” means

The common unit is not a synthetic scheduler turn.

It is:

> **one actual model/provider decision consumed by the studied execution path.**

Framework-native scheduler, round, message, protocol-call, handoff, and carrier counts remain separately observable.

Mappings:

| X | Common logical-decision counter | Native structure preserved |
| --- | --- | --- |
| X1 AutoGen | model-client create calls | Swarm scheduling/handoffs/tools |
| X2 MetaGPT | RuntimeState/provider decisions | Environment/Role/message-buffer scheduling |
| X3 A2A | accumulated role-service model turns | official A2A role-service calls and JSON-RPC protocol |
| X4 MCP | passive provider-tap decisions | MCP resource/tool boundary + software host |
| X5 RAG | passive provider-tap decisions | retrieval carrier + software host |
| X6 MemoryBank | passive provider-tap decisions | persistent memory carrier + software host |
| X7 LongLLMLingua | passive provider-tap decisions | compression carrier + software host |

The frozen subject/model configuration remains `stage2/subject.json`.

The prospective change is the observation horizon only:

- historical G1 default: 32;
- G2-G5: exactly 64.

A cell cannot receive 63, 65, or a result-conditioned extension.

---

## 4. Full-horizon proof

Workflow:

`Stage-II G2-G5 Natural Block Preflight`

Run:

`36237462819`.

The preflight used scripted/non-study providers only.

### Full 64-decision paths

- X1: **64 / 64** AutoGen model-client decisions — PASS.
- X2: **64 / 64** MetaGPT provider decisions — PASS.
- X3: **64 / 64** A2A role-service model decisions — PASS.
- X4: **64 / 64** shared software-host provider decisions through the MCP condition — PASS.

### Shared-host capability admission

X5-X7 use the same prospective software-host decision loop proven to 64 by X4.

Each was additionally launched with horizon=64 on its own native capability binding:

- X5 RAG: capability smoke PASS;
- X6 MemoryBank: capability smoke PASS;
- X7 LongLLMLingua: capability smoke PASS.

These three short capability smokes are not claimed as independent 64-step endurance trials. Their 64-step host-loop property is inherited from the same tested host implementation; their condition-specific purpose is to verify that the capability binding remains admissible under the 64-decision contract.

---

## 5. Evidence-channel separation

Each prospective natural cell now seals two separate manifests.

### Audit raw bundle

`audit_raw_bundle_manifest.json`

Role:

`MONITOR_BLIND_SEMANTIC_AUDIT_INPUT`.

It may contain raw/native route evidence, checkout/state evidence, protocol traffic, carrier evidence, checkpoint metadata needed for route reconstruction, termination evidence, and hashes.

It rejects monitor-derived artifacts including:

- monitor warnings/evidence;
- monitor candidate labels;
- repair packages;
- runtime structural bridge products;
- native-event/wire monitor indexes used as monitor-derived summaries;
- CPR predictions;
- semantic-reference material.

### Monitor runtime bundle

`monitor_runtime_bundle_manifest.json`

Role:

`PROSPECTIVE_MONITOR_OUTPUT`.

It may contain prospective warnings, structural candidates, package candidates, runtime bridge/index products, and coverage evidence.

It rejects post-hoc semantic-audit material.

All seven conditions passed the channel-separation checks.

The monitor and audit channels may be joined only after the v7.45 independent reference-set gate.

---

## 6. Non-study evidence accounting

The successful preflight produced the following evidence-volume checks:

| X | Decision count | Audit-bundle entries | Monitor-bundle entries | Result |
| --- | ---: | ---: | ---: | --- |
| X1 | 64 | 292 | 4 | PASS |
| X2 | 64 | 1,058 | 4 | PASS |
| X3 | 64 | 83 | 4 | PASS |
| X4 | 64 | 992 | 4 | PASS |
| X5 | 1 | 51 | 4 | PASS |
| X6 | 1 | 53 | 4 | PASS |
| X7 | 1 | 51 | 4 | PASS |

These counts belong to non-study preflight fixtures. They are implementation evidence, not scientific results.

---

## 7. Native-preservation correction

During preflight development, an initial implementation parameterized the frozen X3 native A2A service source directly.

That implementation was rejected before merge because the native-v7 freeze correctly detected a source-hash change.

The final implementation restores the frozen native A2A service unchanged.

The 64-decision prospective horizon is instead applied only inside the experiment-owned prospective sidecar subprocess.

Therefore:

- frozen native A2A source remains unchanged;
- A2A protocol/SDK bindings remain unchanged;
- G1 default path remains 32;
- G2-G5 sidecar path receives 64;
- no private runtime state is synthesized.

This is the intended native-preservation boundary.

---

## 8. Historical G1 regression

Legacy workflow:

`Stage-II R7 G1 Execution Readiness Preflight`

Run:

`36237462711`.

Result:

**X1-X7 = 7/7 PASS.**

Additional historical validations on the final preflight head also passed:

- Stage-II R7 G1 Execution Readiness Validate;
- Stage-II R7 Parent Resumability Validate;
- Stage-II R7 G1 Contract Validate;
- Stage-II R7 G1 Native Event Integration Validate;
- Stage-II Day-1 offline conformance;
- Process Reality v5 offline validation;
- NMI P9D Evidence Accounting Validate.

The new prospective horizon path therefore does not replace the historical G1 default behavior.

---

## 9. Scientific interpretation boundary

This preflight establishes engineering readiness only.

It does not establish:

- any CPR occurrence;
- monitor recall/precision;
- framework reliability;
- task success rate;
- cross-group recurrence;
- repair effectiveness.

Those questions require the prospective natural evidence defined by v7.45.

---

## 10. Current gate

Engineering-ready now:

- exact 84-cell first-attempt natural block;
- 64 logical-decision common horizon;
- seven wrapper bindings;
- passive monitor/checkpoint infrastructure;
- monitor-blind audit raw bundles;
- prospective monitor-runtime bundles;
- zero-repair natural A path;
- G1 backward-compatible default path.

Still gated:

- real G2-G5 scientific subject/provider calls;
- active B;
- paid evaluator calls.

Next scientific operation after explicit authorization:

> **execute the prospective natural block, beginning with G2 21A, while retaining the frozen G2-G5 monitor version and zero-repair rule.**
