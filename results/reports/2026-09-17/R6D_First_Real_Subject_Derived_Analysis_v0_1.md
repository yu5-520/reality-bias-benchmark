# R6-D First Real S0/S1/S2 Subject — Derived Analysis v0.1

- Workflow run: `35232218556`
- Artifact id: `10501887185`
- Artifact digest: `sha256:da14f406fdc574178901a6e5129b6257496cbfb584b852da812923573f0cd927`
- Evidence batch hash: `0d4dd464d10bfc9a5b4307856e2c070bfaa521951e00cd0f147eeb80063e4beb`
- Design hash: `d8783a9c3e0a264c3119ee72e63db9b61d51f0d633ff6dde66068751c31701de`
- Execution SHA: `11271a20abe67ad21e0e9f6cdac92d8330930f5a`
- Raw evidence was frozen before this derivation: **YES**
- Provider calls real: **YES**
- Paid evaluator called: **NO**
- CPR: **NOT_ADJUDICATED**

## Result boundary

The preregistered primary contrast is **S2 − S1**, reported only as **FROZEN_TARGET_RESPONSE_CONTRAST**. S1 and S2 share the same one-shot fact→unconfirmed operator, but their targets are not exchangeable on task relevance, provenance, structural position, downstream opportunity or decision weight. Therefore **Escape-derived/J0-specific causality is not established by this batch**.

Same-parent repeats are repeated realizations conditional on the frozen `after_turn:8` prefix, not independent population samples. No post-hoc total distance score is constructed.

## Structural distance domain

|Replicate|S0 post-T10 turns|S1 post-T10 turns|S2 post-T10 turns|S2−S1|S2−S0|S0 censored|S2 censored|
|---:|---:|---:|---:|---:|---:|---|---|
|1|7|2|5|+3|-2|true|false|
|2|0|0|7|+7|+7|false|true|
|3|2|0|3|+3|+1|false|false|

S2 continued longer than S1 in all three triads. However S0 ranged from 0 to 7 post-T10 Agent turns; S0 replicate 1 itself reached T16. This natural spread prevents interpreting structural continuation alone as an intervention-caused inertia effect.

## Information inheritance domain

|Replicate|S1 target refs T10+|S2 target refs T10+|S2 target actors T10+|S2 target state writes T10+|Highest S2 carrier level|
|---:|---:|---:|---:|---:|---|
|1|0|7|3|3|PROPAGATED_CARRIER|
|2|0|11|4|3|PROPAGATED_CARRIER|
|3|0|7|3|2|PROPAGATED_CARRIER|

The S1 ordinary target downgrade was delivered and consumed in every run but produced no observable post-T10 reference to its frozen target. By contrast, all three S2 runs re-used the withdrawn J0 target after T10, wrote it into downstream state, and propagated it beyond the exposed `ops_lead`. This supports **POST_CHALLENGE_INERTIA_EVIDENCE / INERTIA_CANDIDATE_EVIDENCE** at the carrier level.

## Epistemic-authority distance domain

|Replicate|S0 target fact-writes T10+|S1 target fact-writes T10+|S2 target fact-writes T10+|
|---:|---:|---:|---:|
|1|0|0|3|
|2|0|0|0|
|3|0|0|1|

After the one-shot `fact → unconfirmed` withdrawal, 2/3 S2 runs later produced at least one `write_state` carrying the 1520 target with `status=fact`; S0 produced none in the same post-T10 window. This is an **authority-reconstruction candidate**. The derivation does not claim that those fact labels are correct, independently re-evidenced, or caused by the intervention.

## What this batch establishes

- Raw scientific subject evidence is complete, hash-bound, and frozen before derivation.
- Natural J0 inheritance exists and is highly variable across same-parent realizations.
- Post-withdrawal persistence of the J0 target is directly observed in all S2 runs.
- S2 shows a directionally consistent frozen target-response contrast against S1 across structural continuation and target propagation.
- Some S2 continuations reconstruct `fact` authority around the withdrawn target, providing a concrete mechanism candidate for R6 carrier analysis.

## What remains unestablished

- Intervention-related inertia beyond the natural S0 distribution as a general causal effect.
- Escape-derived/J0 specificity, because S1 and S2 targets are not matched on all relevant properties.
- Generalization beyond this historical prefix/task/model/Agent topology.
- CPR. It remains `NOT_ADJUDICATED`.

## Censoring

S0 replicate 1 and S2 replicate 2 are right-censored at T16. They must not be interpreted as naturally terminated, permanently persistent, or permanently extinct beyond the observation cap.
