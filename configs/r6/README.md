# R6 configuration index

## R6-D target-specificity execution freeze

Current forward pre-execution binding:

- Design document: `docs/R6D_specificity_execution_freeze_v0.1.md`
- Design manifest: `manifests/r6d_specificity_preexecution_design_freeze_2026-09-17_v0_1.json`
- Fail-closed subject gate: `configs/r6/r6d_specificity_formal_subject_gate_v0.1.json`
- Exact-plan validator: `scripts/validate_r6d_specificity_exact_plan_v0_1.py`

Frozen design hash:

`d8783a9c3e0a264c3119ee72e63db9b61d51f0d633ff6dde66068751c31701de`

The design fixes three cyclically rotated S0/S1/S2 triads, the T9 direct-response window, the T10+ post-consumption R6 window, the T16 absolute cap, the multidimensional process-distance vector, and the fail-closed budget ceilings.

This directory contains planning/gate contracts only. No real R6-D subject runner or provider-call workflow is bound at v0.1, and no scientific provider run is authorized.
