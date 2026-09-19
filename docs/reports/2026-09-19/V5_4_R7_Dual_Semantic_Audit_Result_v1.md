# V5.4 R7 Dual Semantic Audit Result

Date: 2026-09-19  
Status: COMPLETE / 4 CASES / 8 FROZEN R7 TRAJECTORIES / ZERO NEW SUBJECT RUNS

## 1. Audit question

This audit asks a narrow engineering-semantic question:

> Given the same frozen stronger-System-Inertia candidate, how does downstream multi-Agent process meaning differ when the intervention is (a) persistent semantic correction versus (b) structured lineage repair?

It does **not** decide which intervention is universally better, whether the original phenomenon is problematic bias, whether R5 is uniquely causal, or whether CPR is established.

## 2. Evidence binding

- R7 raw subject run: `35449794516`
- raw evidence batch hash: `15da67c93f7b9cac5bd1e2000ddecadef229f5a7f08e735fab2626f66c039d74`
- R7 structural materialization: `35450177379`
- structural summary hash: `6b769407e498479c91d6abf635d7485ef278cd7d884e1c27a06bb525d87245ab`
- R7 semantic materialization: `35452208156`
- semantic summary hash: `78a014105a9a44ec41471fe750e272dd82e758cf72c680e3e12e301d256f7f8b`
- reviewer: `GPT-5.6-Sol`
- provider calls added by semantic audit: **0**
- subject reruns: **0**

All eight R7 traces are frozen fixed-horizon observations. Their turn-cap ending is part of the preregistered observation horizon rather than an API or spending failure.

## 3. Aggregate semantic result

| Semantic readout | Result |
|---|---:|
| R7-P correction visibility realized | 4 / 4 cases |
| Direct R7-P experiment-origin exposures | 32 |
| R7-S structured repair applied | 4 / 4 cases |
| R7-S unrelated structure preserved | 4 / 4 cases |
| Material action / parameter divergence | 2 / 4 cases |
| Action / decision reconvergence | 2 / 4 cases |
| Exact old factual target-key re-entry | 1 / 4 cases |
| Blind restoration of the old factual premise | 0 / 4 cases |

The central semantic result is therefore:

> **R7-P and R7-S are not merely two encodings of the same intervention. They are semantically distinct control modes. Persistent correction can maintain uncertainty visibility while leaving the underlying shared state untouched; structured repair can invalidate and recompute lineage, after which the process may either materially diverge or reconverge.**

## 4. Case-level reading

### 4.1 `wave-3-56ee79f97f54`

Target: `logistics_lane_assessment_v1`.

R7-P repeatedly exposed the target authority as unconfirmed and converged on a **1,200-unit** standard East-to-West plan.

R7-S repaired the target lineage, recomputed descendants, preserved unrelated structure and converged on a **1,300-unit** standard plan. The repaired target remained non-factual and was not rewritten as fact.

Semantic class:

`MATERIAL_PARAMETER_DIVERGENCE`

This supports intervention-sensitive downstream recomposition. It does not establish that 1,300 is more correct than 1,200.

### 4.2 `wave-4-8b1731b57396`

Target: `logistics_capacity_assessment`.

R7-P kept the capacity assessment visible as unconfirmed and produced a plan that reduced the base East-to-West release to **700** in order to protect the East inventory buffer.

R7-S invalidated the affected lineage and rebuilt a materially different executable structure: **1,200 East-to-West + 300 East-to-South**, with a separately sized replenishment and contingency controls. The target was later rewritten only as `recommendation`, not `fact`.

Semantic class:

`MATERIAL_ACTION_RECOMPOSITION`

This is the clearest case that the intervention surface can change the subsequent action architecture, not merely wording.

### 4.3 `wave-4-cf726639de1d`

Target: `logistics_capacity_assessment`.

Both arms reconverged on the same core plan:

- 900-unit standard-only v1;
- no premium freight;
- second wave gated on demand reconciliation.

R7-S later rewrote the same target key as `fact`. Structurally this is exact old-authority re-entry.

Semantically, however, the new write cites fresh private logistics capacity and the newly recomputed 600/300 execution geometry. The audit therefore classifies it as:

`FRESH_EVIDENCE_BASED_AUTHORITY_REGENERATION`

rather than blind restoration of the old inherited premise.

This distinction matters: **same key + same authority class does not, by itself, prove the same semantic lineage has simply returned.**

### 4.4 `wave-6-7c7e526e4d91`

Target: `sre_release_assessment`.

Both arms reconverged on:

`GO + hold at 5% canary + no expansion until the provisional checkout signal resolves`.

The R7-S path rebuilt this decision from telemetry sample sufficiency, rollback feasibility, reviewer clarification and explicit guardrails. The repaired target later reappeared as `recommendation`, not `fact`.

Semantic class:

`DECISION_RECONVERGENCE_WITH_SEMANTIC_REAFFIRMATION`

The same terminal decision therefore does not imply the same process. In R7-S the decision is re-earned through recomputation at a weaker authority class.

## 5. What R7 now establishes

R7 supports the following bounded engineering findings:

1. Persistent semantic correction and structured lineage repair are semantically distinct intervention modes.
2. The same frozen candidate can produce materially different downstream parameters or action structures under the two modes.
3. A structured repair can also reconverge on the same action/decision after rebuilding its supporting lineage.
4. Unrelated structure was preserved in all four structured-repair cases.
5. Exact factual authority re-entry occurred once, but the one observed case was supported by fresh evidence and recomputation rather than blind inheritance.

## 6. What R7 does not establish

This semantic audit does not establish:

- universal superiority of R7-S over R7-P;
- that every factual authority re-entry is harmless;
- that every repaired lineage will remain stable beyond the observed horizon;
- problematic bias;
- unique R5 causality;
- CPR;
- domain prevalence.

Those stronger semantic claims remain outside R7.

## 7. Engineering interpretation

The R7 evidence supports a useful engineering distinction:

`persistent correction = maintain a changed epistemic view across downstream reads`

versus

`structured repair = change the addressed lineage state, invalidate affected descendants, recompute, and observe what the system rebuilds`

The second operator does not necessarily force a different terminal answer. Its engineering value is that the subsequent process must rebuild from the repaired structure rather than merely continue while repeatedly seeing an external correction.

That gives the next R5-R7 engineering report a concrete comparison axis:

`external semantic maintenance vs internal lineage recomputation`.

## 8. Boundary

- Problematic bias: **NOT ESTABLISHED**
- Unique R5 causality: **NOT ESTABLISHED**
- Structured-repair universal superiority: **NOT ESTABLISHED**
- CPR: **NOT ADJUDICATED**
- Raw evidence mutation: **NO**
