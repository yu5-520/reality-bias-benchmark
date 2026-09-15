# R2-R4 v2 Execution Gate

Date: 2026-09-15

## Current gate

No new paid subject run and no new paid Reviewer v2 call is authorized by this planning update.

The next executable block is no-cost/offline and uses only frozen Batch001 evidence:

1. build a structural candidate index for R2;
2. expand candidate lineages for R3;
3. map existing semantic-blind feedback rounds into R4 review windows;
4. export Reviewer v2 packets with target-local attribution;
5. run deterministic leakage/schema/reference checks;
6. compare packet coverage against v1 annotations without treating v1 labels as ground truth.

## Success criteria before paid re-review

- every v2 packet has a single target and resolvable source refs;
- no Reviewer A/B v1 output leaks into independent packets;
- no expected mechanism-to-authority mapping appears in independent packets;
- C packet generation does not treat prediction itself as C;
- P packet generation does not treat invocation count itself as P;
- R packet generation does not treat reopening itself as R;
- R3 distinguishes exposure/read from semantic adoption;
- R4 keeps structural loop detection semantic-blind;
- packet hashes are stable under deterministic rebuild;
- missing historical fields remain explicit rather than reconstructed as fact.

Only after these gates pass should a new blinded semantic review be considered.
