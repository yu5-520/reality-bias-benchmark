# V5.3 Cross-Domain R5 Second-Wave Effective Evidence Contract v0.1

Date: 2026-09-19  
Status: APPEND-ONLY DERIVED EVIDENCE

The second R5 wave contains two immutable evidence sources:

1. original workflow `35436694271`;
2. balance-recovery workflow `35438000140`.

The derived effective view does not overwrite either source.

Selection rule:

- wave 1 and wave 3 branches use their original continuations;
- the 12 wave 4/5/6 branches that failed on the first provider call with HTTP 402 and produced zero scientific responses use their append-only recovery continuations;
- the original 12 failed traces remain preserved in provenance.

A separate wave-3 control branch failed with HTTP 402 only after 25 successful model calls. It is **not** replaced or rerun, because doing so from the frozen parent would create a new stochastic control path rather than recover the already-realized trajectory. Its late truncation remains explicit control-context quality metadata.

The effective scientific intervention set contains 10 intervention continuations across five cases. Every intervention continuation has a completed direct-exposure response and is eligible for passive R6 structural derivation subject to the normal structural evidence checks.

This derived layer makes no new provider call and does not estimate domain probability.
