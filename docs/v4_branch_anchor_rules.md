# v4 Branch Anchor Rules

Date: 2026-09-16

Forward conceptual anchor classes:

- `ANTECEDENT_ANCHOR`
- `TRANSITION_ANCHOR`
- `PENETRATION_ANCHOR`
- `CHALLENGE_RECOVERY_ANCHOR`

A class is not automatically executable. A runtime-specific selector must prove branchability.

For current Arena continuation work, branchability requires a recorded restorable snapshot and pending executable work where the scheduler requires it.

The existing `r5r6_anchor_rule_v0.2.json` remains the concrete selector for the first MID epistemic-status experiment.