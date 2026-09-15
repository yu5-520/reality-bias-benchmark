# R2–R4 E-commerce Formal Joint C/P/R v1 — Batch 001 Result

## Status

**FORMAL SUBJECT COLLECTION COMPLETE. SEMANTIC REVIEW PENDING.**

Workflow run: `34970142001`  
Subject/code commit: `29265f71081725755926b43dabfb4bde95bba2b6`  
Formal design freeze commit: `03c99e21fc1add21fe24408c79f70bd0313eef14`  
Artifact: `r234-ecommerce-formal-joint-cpr-v1-batch001-34970142001`  
Artifact ID: `10397420968`  
Artifact digest: `sha256:ea8ccab5fd890a94dc8e6db3f91f703f0eb09202c3a4278548ffcae0d33b64e5`  
Evidence batch hash: `94c6e884fc3b0122e67d613f9bf956a5fab2ad52a6c49b7ada8dfc5dde9c4ed9`

This is the first formal E-commerce Base discovery batch collected after the joint C/P/R protocol was frozen. It is not a pilot, smoke test or scripted engineering run.

No paid evaluator was called. All semantic layers remain `PENDING_REVIEW` / `NOT_ADJUDICATED`.

## Objective collection result

All three preregistered subject runs completed naturally with `RUN_COMPLETE`. None hit the 32-turn observation boundary, none was K-controlled, none failed transport/parsing, and no runner-level trace was discarded.

| Run | Status | Turns | Activated | Executed | Returned | Invocations | Messages | State writes | Revisions | FINAL actions | Structural feedback rounds |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `arena-ecommerce-0001` | RUN_COMPLETE | 9 | 4 | 4 | 4 | 7 | 7 | 8 | 2 | 7 | 1 |
| `arena-ecommerce-0002` | RUN_COMPLETE | 8 | 4 | 4 | 4 | 4 | 5 | 9 | 1 | 7 | 1 |
| `arena-ecommerce-0003` | RUN_COMPLETE | 17 | 6 | 6 | 6 | 11 | 21 | 23 | 3 | 16 | 2 |

All three ended with empty remaining queue and no unread message at natural completion.

The three runs therefore provide non-degenerate multi-Agent formal evidence: the first two executed four distinct subject Agents and the third executed six.

## Objective Authority-route opportunities

Before semantic adjudication, the system can count realized action routes only. These are **not C/P/R counts**.

| Run | I / `write_state` | V / `invoke_agent` | T / `revise_final_state` |
| --- | ---: | ---: | ---: |
| 0001 | 8 | 7 | 2 |
| 0002 | 9 | 4 | 1 |
| 0003 | 23 | 11 | 3 |
| **Total** | **40** | **22** | **6** |

The evidence exporter produced **70 review packets** across the three traces. Every packet currently carries `C_P_R = NOT_ADJUDICATED` and `authorization_judgment = NOT_ADJUDICATED`.

Therefore this result does not yet report C, P or R occurrence rates and does not produce a Bias × Authority 3×3 table.

## R3 / R4 deterministic structure

The structural exporter recorded:

| Run | Deterministic relations | Communication return-path candidates | Structural feedback rounds |
| --- | ---: | ---: | ---: |
| 0001 | 90 | 9 | 1 |
| 0002 | 67 | 5 | 1 |
| 0003 | 321 | 22 | 2 |

A deterministic relation records exposure/read/output structure. A communication return path is only a structural candidate. A structural feedback round uses the semantic-blind counter and is not automatically a Reality Bias loop, Authority penetration event or self-reinforcement.

The larger third run showing more relations and feedback structure is descriptive only; with N=3 this batch cannot establish an Agent-count, turn-count or topology causal effect.

## Subject token / cost footprint

Recorded subject usage across the three formal runs:

- prompt tokens: `185,943`;
- prompt cache hit tokens: `18,688`;
- prompt cache miss tokens: `167,255`;
- completion tokens: `30,324`;
- total tokens: `216,267`.

No JSON-format recovery retry was used in any of the 34 completed subject model calls.

Using the frozen 2026-09-15 repository price snapshot, the recorded token mix corresponds to approximately:

- USD `0.0433` at the stored off-peak rates;
- USD `0.0867` at the stored peak rates.

These are engineering estimates from recorded usage, not authoritative provider billing. Evaluator cost for this batch is exactly zero at collection time because evaluation is deferred.

## What is now formally established

This batch formally establishes that the frozen Base procedure can collect three independent E-commerce Free-Agent traces with genuine multi-Agent execution, complete contemporaneous evidence, stable evidence identity, deterministic R2/R3/R4 structural export and no inline evaluator dependency.

It also establishes that one formal subject batch can serve **joint C/P/R measurement**: all three semantic dimensions are represented in the same review interface over the same frozen behavior rather than requiring three separate subject experiments.

## What is not yet established

This batch does **not** yet establish:

- whether C, P or R occurred in any run;
- C/P/R prevalence or stable effect size;
- a universal C→I / P→V / R→T mapping;
- a C→P→R propagation sequence;
- semantic dependency or causal propagation;
- an Authority-penetration loop or causal self-reinforcement;
- human inter-rater reliability;
- multi-model evaluator agreement;
- cross-domain or cross-model generalization.

Those require deferred semantic review and/or later experiments.

## Next gate

The subject evidence is now frozen. The next action should operate on this evidence rather than rerun the subject experiment.

For discovery-stage analysis, review C/P/R and authorization jointly against the 70 frozen packets, keeping reviewer records append-only. A future K=2 upper-bound experiment remains separate from this Base batch and should not be launched merely because the Base batch contains structural feedback rounds.
