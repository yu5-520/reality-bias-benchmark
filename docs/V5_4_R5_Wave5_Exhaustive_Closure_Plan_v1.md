# V5.4 R5 Wave5 exhaustive closure plan

Date: 2026-09-19

## Purpose

Wave5 is not another sampled observation wave. It is the **exhaustive closure batch** for the already-frozen Pass-1 R5-eligible set.

The scientific population for this step was fixed before Wave3-Wave4 execution:

- localized semantic-audit Pass 1: 29 cases eligible for the existing `fact -> unconfirmed` atomic probe;
- canonical R5-R6 pool after Waves 1-4: 20 of those 29 cases;
- remaining set: exactly 9 cases.

Wave5 therefore executes the exact set difference:

`Wave5 = Pass1Eligible29 - CanonicalCompleted20`

No random sampling, ranking, per-wave quota, replacement, or discretionary case selection is allowed.

## Geometry

Each remaining case preserves the v5.4 canonical geometry:

`existing N0 frozen natural reference + exactly one new R5-I continuation`

- cases: 9
- new provider trajectories: 9
- synthetic controls: 0
- natural reruns: 0
- canonical replicate count: 1
- R6: passive, 0 provider trajectories
- R7: not authorized
- R8 / CPR: not adjudicated

After successful Wave5 completion, canonical R5 coverage of the Pass-1 eligible set is planned to be **29/29**, with **0 eligible cases left unexecuted**.

## Anti-selection audit

The execution workflow must fail closed unless:

1. the repository Pass-1 review manifest contains exactly 29 reviewed case hashes;
2. the 20 previously canonical case hashes and the 9 Wave5 hashes are disjoint;
3. their union equals the complete 29-case Pass-1 reviewed set;
4. all nine source cases bind to the exact frozen natural artifacts, source events, parent snapshots and next actors;
5. the plan produces exactly nine canonical R5-I branches.

This makes Wave5 an exhaustive coverage completion step rather than a new sampling decision.
