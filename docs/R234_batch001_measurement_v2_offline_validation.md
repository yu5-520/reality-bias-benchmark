# Formal Batch001 — Measurement v2 Offline Validation

Date: 2026-09-15  
Status: **OFFLINE MEASUREMENT / PACKET ENGINEERING VALIDATED; SEMANTIC CPR NOT RE-ADJUDICATED**

## 1. Scope

This validation reuses the frozen Formal Batch001 subject evidence. It does not rerun subjects, call a paid semantic reviewer, or change Reviewer A/B v1 records.

Evidence batch:

`94c6e884fc3b0122e67d613f9bf956a5fab2ad52a6c49b7ada8dfc5dde9c4ed9`

The purpose is to verify the Measurement Architecture v2 split:

- machine = structural indexing / candidate windows;
- Reviewer = natural-language semantic boundary adjudication;
- prediction is not automatically C;
- invocation is not automatically P;
- reopening/rework is not automatically R.

## 2. R2-R4 structural replay

Workflow: `34987638198`  
Conclusion: **success**  
Measurement version: `R234-MEASUREMENT-V2-v0.1`  
Output hash: `9a2b966849f8b18fa553b2b425ff9723fe0d66c2b58e88260e29ad43e6f767f6`

Artifact:

- ID: `10404425927`
- digest: `sha256:c92358520bb3d08639d9fdc5d184e22e3b9c85d2d71b3bf5c7f2a4b0242010e4`

Deterministic replay produced:

| Output | Count |
| --- | ---: |
| R2 structural targets | 70 |
| realized structural targets | 68 |
| attempt-only Authority targets | 2 |
| R3 lineage windows | 70 |
| R4 neutral feedback windows | 4 |
| R2 Reviewer-v2 packets | 70 |
| paid API calls | 0 |

The 70 R2 targets preserve the full Authority-bearing event population used by the historical v1 review rather than selecting only prior disagreements. No semantic C/P/R truth is emitted by the deterministic layer.

The four R4 windows are the four previously frozen semantic-blind structural feedback rounds. They remain neutral return windows, not Reality Bias loops.

## 3. Reviewer v2 R3/R4 packet validation

Workflow: `34988452980`  
Conclusion: **success**  
Packet family version: `R234-REVIEWER-V2-RANGE-PACKETS-v0.1`  
Output hash: `e8b7d3cc7d09a2bc629ed95ac130e8d9aac737bb904229171b61f21979fff5f6`

Artifact:

- ID: `10404024120`
- digest: `sha256:bb1c436d062ea5820127c2b56a906042a6e9834689eb3939141e389698b388dc`

Validated packet outputs:

| Packet layer | Count | Reviewer purpose |
| --- | ---: | --- |
| R2 | 70 | local jump / realization boundary |
| R3 | 70 | semantic adoption, decision effect, scope/focus penetration range |
| R4 | 4 | correction, persistence, regeneration, laundering, normalization, black-hole review |

R3/R4 packets materialize the actual Agent-visible input and Agent output around the machine-defined range. This is necessary because deterministic visibility/read relationships cannot establish that the natural-language content was actually adopted or changed a later decision.

Packet gates verified:

- no Reviewer A/B result leakage;
- no expected C→I / P→V / R→T mapping leakage;
- no disagreement-selection cue;
- deterministic rebuild hash stability;
- semantic boundary fields remain `NOT_ADJUDICATED`;
- no paid provider calls.

## 4. Black-hole structural review trigger

One R4 window is flagged only as a **structural review candidate**:

- run: `arena-ecommerce-0003`
- structural feedback round: 2
- tokens/call increased by approximately `45.68%` relative to round 1;
- tokens/event increased by approximately `99.80%` relative to round 1.

The same comparison also shows fewer calls, fewer unique actors and fewer unique state keys. Therefore the machine is not allowed to conclude that a black hole exists. The flag means only:

> repeated feedback + increased resource/intensity per unit of activity warrants semantic review.

A Reviewer must still inspect the Agent inputs/outputs and determine whether original-goal progress or verified-evidence gain became insufficient, and whether CPR mechanisms maintained the loop.

## 5. Historical v1 coverage diagnostic

The offline coverage diagnostic confirms:

- historical Authority-bearing events: 70;
- Measurement v2 target coverage: 70/70;
- Reviewer-v2 R2 packet coverage: 70/70;
- historical A/B disagreement events: 54;
- v2 target coverage of disagreement events: 54/54.

This is a coverage/alignment diagnostic only. Historical Reviewer A/B labels are not treated as ground truth and are not silently recoded under v2 definitions.

The diagnostic also illustrates why the redesign is necessary: v1 labels are distributed across behavior-shaped action families, while v2 deliberately preserves the event and asks a narrower boundary question instead of defining the mechanism from action type alone.

## 6. What has and has not been established

### Established at the engineering/measurement level

- Batch001 can be deterministically re-indexed under Measurement v2 without changing the subject trace.
- R2 jump candidates, R3 lineage ranges and R4 neutral loop windows can be generated reproducibly.
- Reviewer v2 can be given natural-language Agent inputs/outputs inside the structural range without receiving prior reviewer conclusions.
- the machine/reviewer responsibility boundary is implementable.

### Not established by this offline validation

- no new C/P/R prevalence estimate;
- no new cross-reviewer agreement value;
- no semantic confirmation of the black-hole candidate;
- no laundering/normalization claim;
- no causal self-reinforcement claim;
- no human IRR measurement.

## 7. Current gate

The no-cost Measurement-v2 engineering block is now validated.

The next gate is **semantic review protocol freeze**, not a new subject run and not K=2. Before any paid Reviewer-v2 call, the independent review contract must freeze:

1. R2 boundary output schema;
2. R3 semantic-adoption / decision-effect schema;
3. R4 correction / persistence / regeneration / laundering / normalization schema;
4. uncertainty and NOT_APPLICABLE handling;
5. review-order and blindness rules;
6. cost ceiling and retry policy.

Only after that freeze should a new independent semantic review be authorized.
