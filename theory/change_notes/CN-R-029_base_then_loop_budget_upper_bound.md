# CN-R-029 — Base measurement first; K=2/K=4 as gated upper-bound probes

**Status:** ACCEPTED. POLICY ONLY. NO PAID K RUN AUTHORIZED BY THIS NOTE.

## Decision

The R2–R4 program separates two jobs:

- **Base:** fixed-window measurement used to establish reliable event, relation and feedback-candidate observation under a common horizon.
- **Upper bound:** a later loop-budget experiment that allows a bounded number of neutral structural feedback rounds.

The base is the scientific foundation. The upper-bound condition is more expensive and is not part of routine sampling.

## Initial K range

The initial upper-bound search is limited to:

- `K=2`
- `K=4`

No K greater than 4 is permitted in the initial phase.

K is not a Reality Bias label. The subject runtime must not inspect C/P/R, evaluator outputs, authorization judgments, Authority-penetration labels or self-reinforcement labels to count K.

Before any K run, a deterministic and semantically blind structural-feedback-round counter must be specified, versioned and offline-tested.

## Sequential gate

The spending order is:

`BASE stable → K=2 → deferred review → optional K=4 → deferred review → STOP`

K=4 is allowed only if K=2 yields at least one reviewable persistence, expansion or amplification candidate in **at least one** of C/P/R.

If K=2 yields no such signal, upper-bound spending stops.

After K=4, the initial upper-bound program also stops unless at least one C/P/R dimension increases on an amplification-qualified metric relative to the K=2 basis. A future K>4 condition would require a new Change Note and explicit cost review.

## What counts as “increase”

A raw cumulative event count is insufficient because K=4 automatically provides more observation opportunities than K=2.

Initial amplification-qualified metrics are:

- new reviewed Bias events per feedback round;
- unique affected Agents;
- unique affected state fields;
- reviewed propagation depth;
- reviewed re-inheritance/reopen depth.

Only one C/P/R dimension needs to satisfy the gate. The protocol does not require diagonal or simultaneous growth across all three Bias types.

## Exploratory prefix use

If a K=4 trajectory is later run, rounds 1–2 may be compared with rounds 3–4 as an exploratory within-trajectory prefix analysis. This can reduce discovery cost, but it is not equivalent to an independent K=2 arm for later confirmation.

## Claim boundary

Passing a K gate supports only language such as persistence signal, expansion signal, or amplification candidate.

Causal self-reinforcement requires later intervention evidence, such as an R5 condition in which the relevant feedback dependency is disrupted and the apparent amplification weakens.

## Current state

`arena/config/loop_budget_policy_v0.1.json` and `docs/R4_loop_budget_protocol_v0.1.md` register this design. The policy remains `PLANNED_NOT_ACTIVE`.

This note does not change the current subject runtime and does not trigger any subject or evaluator API call.
