# V5.3 R5 Second-Wave Balance Recovery Protocol v0.1

Date: 2026-09-19  
Status: FROZEN PRE-EXECUTION RECOVERY

This recovery exists only because the original second-wave run exhausted provider balance after wave 3.

Recovery eligibility is mechanical and pre-semantic:

- original branch terminated with `model_call_failure`;
- exactly one model call was attempted;
- that call failed;
- error contains `HTTP 402` and `Insufficient Balance`;
- zero model calls completed.

The eligible set is therefore exactly the 12 matched branches belonging to wave 4, wave 5 and wave 6.

The recovery does not select branches by scientific outcome. Wave 1 and wave 3 are not rerun because they already contain valid scientific responses.

Every recovery branch reuses the same frozen parent, condition, replicate index and logical seed, but receives a new run/branch execution identity. Original failed traces remain immutable and are never overwritten.

After recovery evidence is frozen, R6 again runs passively/offline. No paid evaluator, R7 repair or CPR adjudication is authorized.
