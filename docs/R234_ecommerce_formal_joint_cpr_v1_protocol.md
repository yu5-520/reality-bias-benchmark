# R2–R4 E-commerce Formal Joint C/P/R Experiment v1

## Status

**FROZEN BEFORE FIRST FORMAL SUBJECT BATCH.**

This is the first preregistered formal discovery batch under the evidence-first Arena architecture. It is not a pilot, smoke test, transport test, or evaluator calibration run.

The experiment studies one domain — **E-commerce** — while observing all three Reality Bias mechanisms **C / P / R together** on the same natural multi-Agent traces.

C, P and R are outcomes to be adjudicated later. They are **not three separate subject conditions** and are not exposed to subject Agents.

## 1. Research question

Under one fixed Free-Agent Arena environment, do Completion, Perfection and Retrospective Reality Bias emerge naturally, through which Authority routes do realized events pass, and what downstream exposure / inheritance / structural-feedback evidence is present in the same traces?

The experiment therefore uses one subject evidence stream for three audit scales:

- **R2 event layer:** C/P/R event adjudication and I/V/T route;
- **R3 relation layer:** downstream exposure, reading, inheritance and later semantic-dependency review;
- **R4 structural layer:** neutral structural feedback rounds and later loop/self-reinforcement review.

R2/R3/R4 are analysis views over the same subject behavior, not three sequential subject experiments.

## 2. Subject condition

Domain: `ecommerce`  
Arena runtime: `R2-FREE-AGENT-ARENA-v0.3.2`  
Arena config: `arena/config/arena_v0.3.json`  
Observation horizon: 32 turns  
Invocation safety cap: 64  
Pending-message safety cap: 128  
Termination policy: `observe_until_quiescent`  
Automatic paid evaluator: **disabled**

The subject Agents receive only the domain task, role/private information, current runtime state and uniform action protocol. They do not receive C/P/R labels, I/V/T labels, expected mappings, R2/R3/R4 hypotheses, or evaluator decisions.

“Labels are not exposed” does not mean the environment contains no experimental structure. The domain, roles, Authority contract, late-event schedule, action interface and safety limits are fixed experimental conditions. The claim is only that C/P/R are not directly prompted as target behaviors.

## 3. First formal batch size

The first frozen formal batch contains **3 independent subject runs** under the same E-commerce Base condition.

This N=3 batch is formal discovery data because its protocol is frozen before collection, but it is deliberately small. It is **not** a prevalence estimate, stable effect-size estimate, or confirmatory test of population frequency.

No run is regenerated merely because it is inconvenient, censored, semantically negative, or difficult to review.

## 4. Evidence inclusion and objective status

Every attempted formal run is preserved according to its actual objective state:

- `RUN_COMPLETE` — naturally completed recorded episode;
- `BUDGET_CENSORED` — fixed observation/safety boundary reached with unfinished work;
- `RUN_INCOMPLETE` — stopped without a final state under a non-budget natural stop;
- `RUN_FAILED` — provider/transport/parse failure interrupted execution.

A failed or censored run remains part of the formal audit record. Its permitted scientific use is determined by evidence completeness and estimand, not by whether the behavior looks useful.

The run records contemporaneous inputs, raw provider outputs, parsed actions, message/invocation/execution ledgers, shared-state versions, FINAL/revision state, termination reason, pending queue, failures and actual usage where available.

## 5. Joint C/P/R review

Semantic review is deferred until after the raw evidence is frozen.

For every applicable event, later reviewers may independently record:

- C / P / R labels;
- authorization judgment;
- rationale;
- confidence;
- uncertainty;
- evidence references.

A run may contain none, one, two or all three Bias mechanisms. The protocol does not require all three to appear.

The first formal semantic outputs are:

- run-level observed C occurrence;
- run-level observed P occurrence;
- run-level observed R occurrence;
- event-level C/P/R annotations;
- event-level authorization judgments.

Until such review exists, semantic outputs remain `NOT_ADJUDICATED`; they are never converted to zero.

## 6. Authority and structural outputs

The system may deterministically export objective facts including:

- I/V/T action route by action type;
- actual activation / execution / return participation;
- message and invocation edges;
- state writes and final-state revisions;
- read/visibility relations supported by recorded runtime input;
- semantic-blind structural feedback rounds.

These facts do not decide C/P/R by themselves.

The later Bias × Authority 3×3 table is an event summary after semantic adjudication. It does not prove a fixed diagonal mapping and does not establish a temporal C→P→R propagation order.

## 7. R3/R4 claim boundary

Exposure is not semantic dependency. Temporal order is not causal influence. A communication cycle is not automatically an Authority loop. A structural feedback round is not automatically Reality Bias or self-reinforcement.

For censored runs, absence is scoped to the recorded prefix. For natural complete runs, whole-recorded-episode statements may be made only within the evidence actually captured.

Causal self-reinforcement remains an intervention-level claim and is not established by this Base batch.

## 8. Base before K upper-bound experiment

This formal batch is **Base only**. It does not activate K=2 or K=4.

The Base experiment answers what emerges under a common 32-turn observation condition. A later K=2 experiment is a distinct upper-bound condition designed to test persistence / expansion / amplification under a controlled structural-feedback budget.

K=4 remains unavailable until a real K=2 batch is frozen and its deferred review passes the preregistered continuation gate.

No Base run that happens to contain two or more structural feedback rounds is retroactively relabeled as a K-controlled arm.

## 9. Multiplicity and reviewer agreement

C/P/R are jointly observed dimensions. This first formal discovery batch does not claim family-wise confirmatory significance across the three dimensions.

Human inter-rater reliability and multi-model agreement are not yet measured. Later reviewers must bind their records to the same frozen evidence batch and append disagreement / adjudication records without overwriting original opinions.

## 10. Formal-data boundary

Only subject data generated after the formal design freeze and through the formal workflow belong to this first formal discovery batch.

Historical micro-pilots, structural smoke runs, failed infrastructure attempts, scripted validations and frozen Base re-derivations retain their original historical status and are not silently promoted into this formal corpus.

The formal workflow stops after evidence freeze, deterministic objective statistics and review-material export. It performs **zero automatic paid evaluator calls**.
