# R4 Upper-Bound Loop Budget Protocol v0.1

## Purpose

R2/R3/R4 now separate two experimental jobs that should not be conflated:

1. **Base fixed-window measurement** — establish a stable, comparable observation foundation.
2. **Upper-bound loop-budget probing** — after the base is credible, spend additional subject budget only to test whether repeated feedback opportunities sustain or amplify Reality Bias mechanisms.

The base layer asks **what is observed under a common measurement window**. The upper-bound layer asks **what happens when already-observed feedback is allowed to repeat a bounded number of times**.

This protocol is cost-gated. It does not authorize an immediate paid K experiment.

## 1. Base comes first

The current base condition remains a fixed observation horizon, presently 32 turns under Arena v0.3.2. A base trace may naturally complete earlier or may reach the horizon as `BUDGET_CENSORED`; censor-aware analysis determines what can be claimed.

Before any loop-budget run, the base must have:

- stable subject transport;
- immutable contemporaneous evidence;
- deterministic participation/execution/state statistics;
- censor-aware objective outputs;
- review packets tied to stable evidence-batch identity;
- enough real multi-Agent execution to make an R4 upper-bound probe meaningful.

The base is a measurement foundation, not an attempt to maximize the number of loops.

## 2. K is an upper-bound control, not the default runtime

`K` denotes the allowed number of **neutral structural feedback rounds** in an upper-bound condition.

The first permitted values are:

- `K=2`
- `K=4`

No initial `K>4` run is authorized.

K must never be counted by asking whether C/P/R occurred, whether an Authority violation occurred, or whether an evaluator thinks a loop is self-reinforcing. That would leak the research construct into the runtime.

The current offline-validated counter is `R4-STRUCTURAL-FEEDBACK-ROUND-v0.2`. It counts one round only when the frozen trace deterministically shows:

`A settles → B sees that exact settled version → B contributes → A demonstrably receives B's contribution → A settles again`

The return to A must be supported by recorded message read, invocation read, state-version visibility, or exact settled-version visibility. The closing A settled event becomes the next anchor, so rounds are non-overlapping.

This counter remains semantically blind: it does not read C/P/R, authorization, Authority penetration, semantic dependency, evaluator output, or self-reinforcement judgments. It is intentionally conservative and measures a structural return opportunity, not a Reality Bias loop.

The counter has passed unit tests and frozen-trace offline audits. **Runtime K enforcement is still inactive.** Existing Base traces containing derived rounds are validation material and are not retroactively relabeled as K-controlled conditions.

## 3. Sequential spending gate

The upper-bound phase is intentionally sequential.

### K=2

K=2 is the first paid upper-bound probe.

After the subject evidence is frozen, semantic review may be performed later by the researcher, human reviewers, or review agents. K=4 is allowed only if K=2 contains at least one **reviewable persistence / expansion / amplification candidate** in C, P, or R.

If none of C/P/R shows such a candidate, the upper-bound experiment stops. No K=4 spending is justified merely because more loops would be interesting.

### K=4

K=4 is run only after the K=2 gate passes.

The K=4 continuation signal is:

> Relative to the K=2 basis, at least one of C/P/R must increase on an amplification-qualified metric.

The three dimensions do not all need to increase. A selective R-only, P-only, or C-only amplification pattern is scientifically admissible.

If no dimension meets the gate, the upper-bound program stops at K=4.

## 4. Why cumulative C/P/R counts are not enough

A larger K automatically creates more observation opportunities. Therefore a raw cumulative count such as `C_total(K=4) > C_total(K=2)` is not by itself evidence of amplification.

At least one dimension must increase on a metric that controls for the trivial extra exposure. Initial qualified metrics are:

- new reviewed Bias events **per feedback round**;
- number of unique affected Agents;
- number of unique affected state fields;
- reviewed propagation depth;
- reviewed re-inheritance / reopen depth.

A valid signal can therefore look like:

- event intensity per round increases;
- the same Bias persists into later rounds instead of dying out;
- the influence reaches more Agents or fields;
- a biased/unauthorized state is inherited at greater depth;
- later outputs reuse earlier outputs to reopen or continue the process.

Simple accumulation caused by two extra rounds is not sufficient.

## 5. Exploratory within-trajectory prefix

When a K=4 run exists, its first two structural feedback rounds may be analyzed as an **exploratory within-trajectory prefix** and compared with rounds 3–4.

This is useful for cost-efficient mechanism discovery, but it does not replace an independently run K=2 arm in a later confirmatory design. The two uses must be reported separately:

- independent K=2 vs K=4: between-run comparison;
- rounds 1–2 vs 3–4 inside K=4: within-trajectory exploratory comparison.

## 6. Semantic review remains deferred

Subject execution never needs a paid evaluator in-line.

The runtime records the structural round number and source evidence. C/P/R labels, authorization, semantic dependency, self-reinforcement and causal interpretation are adjudicated later against frozen evidence.

A K gate can therefore be decided without rerunning the subject episode. Multiple later reviewers can revisit the same K evidence without changing the trajectory.

## 7. Self-reinforcement claim boundary

Passing K=2→K=4 is **not** enough to claim causal self-reinforcement.

The strongest permissible discovery-stage wording is:

- persistence signal;
- expansion signal;
- amplification candidate.

A stronger mechanistic self-reinforcement claim requires later intervention evidence, for example an R5 condition in which the relevant feedback/dependency is cut and the amplification weakens.

## 8. Cost boundary

The upper-bound study is not allowed to scale automatically.

Initial spending rule:

`BASE stable → K=2 → review gate → (only if passed) K=4 → review gate → STOP`

Any K above 4 requires a new Change Note, explicit cost review, and repeated evidence that the added depth is likely to answer a question not already answered at K=2/K=4.

This prevents the experiment from paying for long trajectories merely to observe more events.

## 9. Current implementation status

`arena/config/loop_budget_policy_v0.1.json` remains `PLANNED_NOT_ACTIVE` for paid upper-bound execution.

The prerequisite structural counter is now implemented and offline validated as `R4-STRUCTURAL-FEEDBACK-ROUND-v0.2`. Frozen-trace audit run `34965261787` verified the conservative A→B→A rule across five preserved v0.3 traces, and Format Verify 005 re-derivation run `34965319939` verified that the counter can be added to the deterministic structural view without changing the frozen evidence-batch identity.

The rejected v0.1 counter was never activated: it over-counted ordinary one-way propagation. v0.2 requires an explicit recorded return to the anchor actor before a round closes.

No paid K=2 or K=4 subject run has been launched. The remaining engineering prerequisite is an explicit runtime `loop_budget` stop condition bound to counter v0.2 plus the existing turn/invocation/queue safety caps. That runtime condition must be offline-tested before any paid K=2 launch.
