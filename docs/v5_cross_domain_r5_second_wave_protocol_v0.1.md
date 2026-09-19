# V5.3 Cross-Domain R5 Second Wave Protocol v0.1

Date: 2026-09-19  
Status: FROZEN PRE-EXECUTION / CASE-STRUCTURE PHASE

The second R5 wave consumes already-qualified pass-1 cases. It does not add natural trajectories and does not estimate domain probability.

Selection is deterministic after excluding the six first-wave cases. For every natural wave that still has an eligible case, select the smallest tuple:

`(source_event_index, source_run_id, source_case_hash)`.

Wave 2 is explicitly `EXHAUSTED_AFTER_WAVE1`; it is not replaced by another domain or wave.

Geometry:

- 5 source-bound cases;
- 2 matched pairs per case;
- 2 conditions per pair;
- 20 branches total.

Operator remains one-shot runtime-view `fact -> unconfirmed` on the first resumed Agent only, with zero reinjection and no experiment-origin persistent mutation.

The purpose is to generate additional case-level structural evidence. After raw evidence freezes, R6 is passive/offline: it consumes the frozen R5 continuation and does not require a new subject experiment.

No paid evaluator, R7 repair, or CPR adjudication is authorized.
