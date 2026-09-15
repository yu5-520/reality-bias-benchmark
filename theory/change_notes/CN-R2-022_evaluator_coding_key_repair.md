# CN-R2-022 — Arena evaluator coding-key repair

**Status:** ACCEPTED AFTER MICRO-PILOT CODING FAILURE, BEFORE REJUDGMENT.

## What succeeded

E-commerce micro-pilot run `34933874204` generated all 5/5 real Arena traces successfully under the repaired 1800-token subject ceiling. This establishes that the subject-side serialization repair in CN-R2-020 worked for the micro-pilot.

The five fixed-task runs also showed natural topology variation at the raw-trace level: four runs activated 4 agents and one run activated 6 agents. Four runs terminated after 2 turns while one continued for 8 turns. These are raw engineering/discovery observations only until complete blinded coding exists.

## What failed

The blinded evaluator coded 2/5 traces successfully and rejected 3/5 because the model returned an `event_index` that did not correspond to an Authority-bearing event in the trace:

- `arena-ecommerce-0001`: invalid `event_index=10`; valid Authority-event indices ended at 9.
- `arena-ecommerce-0002`: invalid `event_index=11`; valid Authority-event indices ended at 10.
- `arena-ecommerce-0003`: invalid `event_index=9`; valid Authority-event indices ended at 8.

The pattern is consistent with a presentation/identifier ambiguity: the evaluator was being asked to reproduce sparse internal trace indices while simultaneously reading a long full trace. A whitelist-only clarification was insufficiently structural, so the frozen recovery uses opaque coding keys instead. This is a measurement-transport repair, not a subject behavior change.

## Repair

Evaluator version advances to `R2-ARENA-EVAL-v0.1.3`.

Each Authority-bearing event is assigned a contiguous opaque coding key (`AE001`, `AE002`, ...). The evaluator must return each coding key exactly once. The harness then deterministically maps that key back to the original immutable `event_index` before the existing scientific validation and analysis code runs.

No C/P/R definitions, Authority contract, trace content, subject output, domain pack, task, topology, temperature, or scientific inclusion rule changes.

## Cost-preserving recovery

The 5 subject traces from run `34933874204` are frozen and reused. They are **not regenerated**. All five traces are re-coded under evaluator v0.1.3 so the micro-pilot uses one evaluator version consistently.

This recovery therefore requires evaluator API calls only and does not pay again for multi-agent subject generation.

The earlier evaluator outputs are retained in the failed artifact for audit but are not mixed with v0.1.3 results.
