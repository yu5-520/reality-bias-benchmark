# CN-R2-021 — E-commerce micro-pilot before Wave 1 scale-up

**Status:** EXECUTION AUTHORIZED BEFORE DATA.

Because the first 30-run execution was invalidated by a 900-token response ceiling and later provider balance exhaustion, the repaired v0.1.2 environment will not immediately repeat the full 30-run wave.

A five-run E-commerce micro-pilot is executed first.

## Frozen scope

- Domain: E-commerce only
- Repeats: 5 fresh runs
- Same task/input/goal and 9-agent registry as the frozen Arena
- Agent participation/topology remains free to self-organize
- Subject max tokens: 1800 infrastructure repair
- Subject temperature, prompts, domain pack, Arena engine, Authority contract, evaluator, and analysis unchanged
- Maximum concurrent real traces: 2, to limit spend and make systemic failure cheaper

## Decision purpose

This micro-pilot is used to answer only whether:

1. the 1800-token response-cap repair produces complete structured Agent actions;
2. repeated identical E-commerce tasks generate non-degenerate natural topology variation;
3. raw traces can be blind-coded end-to-end for C/P/R and I/V/T without another infrastructure failure;
4. the observed signal is promising enough to justify a later 30-run discovery wave.

The micro-pilot is not a prevalence estimate and is not merged with the invalid run `34932966766`.

If the provider still returns `Insufficient Balance`, the run remains an infrastructure/account failure and no scientific conclusion is drawn.
