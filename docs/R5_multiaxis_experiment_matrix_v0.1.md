# R5 Multi-Axis Experiment Matrix v0.1

Date: 2026-09-16  
Status: FORWARD CANDIDATE / NOT A REAL-RUN AUTHORIZATION

This matrix separates where an experimental variable acts from what outcome is measured.

| Stage | Variable family | Example variable | Anchor class | Primary outcomes |
| --- | --- | --- | --- | --- |
| PRE | tension antecedent | goal conflict | ANTECEDENT_ANCHOR | Jump incidence/location/type |
| PRE | tension antecedent | evidence conflict | ANTECEDENT_ANCHOR | epistemic Jump candidates |
| PRE | tension antecedent | context competition | ANTECEDENT_ANCHOR | focus/scope Jump candidates |
| MID | containment | epistemic status downgrade | TRANSITION_ANCHOR | descendants / operational crossings / inertia |
| MID | containment | authority edge block | TRANSITION/PENETRATION_ANCHOR | penetration / descendants |
| MID | containment | routing edge block | TRANSITION/PENETRATION_ANCHOR | propagation topology / affected actors |
| POST | stabilization | challenge delay | CHALLENGE_RECOVERY_ANCHOR | persistence / R / recovery distance |
| POST | stabilization | provenance restore | CHALLENGE_RECOVERY_ANCHOR | recovery / residual descendants |
| STRUCTURE | system structure | free vs structured routing | experiment-level condition | Jump location / propagation / penetration / inertia |

## Design rule

Each confirmatory experiment changes one named variable family at a time where practicable and freezes:

- parent/history condition;
- target boundary;
- control/manipulation level;
- held constants;
- primary outcome family;
- failure/censoring treatment;
- registry/code/config hashes.

## Interpretation rule

Do not collapse these questions:

1. Did Jump generation change?
2. Did operational realization change?
3. Did downstream propagation change?
4. Did persistence/recovery change?

An intervention may affect only one of these layers.

## First-paper priority

The first paper should prioritize a narrow MID path plus recovery, using PRE variables mainly as theory-grounded future experiments unless a small low-cost PRE pilot is explicitly preregistered later.