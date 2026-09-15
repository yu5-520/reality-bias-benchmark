# CN-R2-020 — E-commerce Wave 1 infrastructure invalidation and response-cap repair

**Status:** ACCEPTED. Infrastructure correction only; no R0/R1 theory change and no Arena hypothesis change.

## Invalid real attempt

The first E-commerce Free-Agent Arena Wave 1 execution was GitHub Actions run `34932966766`, commit `ccfd53bae5bf30f6f84a425e1ed4b9277846797a`.

The frozen v0.1.1 environment and regression tests passed, and the workflow built the planned 30-run E-commerce manifest. The real subject stage did not complete scientifically:

- 2/30 Arena runs produced raw traces;
- 28/30 failed before a complete wave existed;
- most early failures were malformed/truncated JSON after three identical-request format retries;
- later failures were provider HTTP 402 `Insufficient Balance`;
- blinded event coding, analysis, and freeze-metadata stages were skipped.

Therefore the entire attempt, including the two successful traces, is **excluded from all scientific estimates**. Selecting only the two survivors would create severe response-validity selection bias.

## Root cause 1 — subject response ceiling

The Arena model config allowed only 900 subject completion tokens. Failure logs repeatedly show JSON terminating mid-string or mid-object around the previous response ceiling. The multi-agent action envelope can legitimately require a longer structured response than the earlier single-turn benchmark.

Repair:

- subject `max_tokens`: 900 → 1800;
- subject temperature remains 0.7;
- thinking remains disabled;
- provider/model alias unchanged;
- JSON format retry count unchanged;
- Agent prompts, domain inputs, Arena mechanics, Authority contract, evaluator, and analysis are unchanged.

Because no complete Wave 1 dataset existed and no scientific result was inspected, this is classified as an infrastructure response-cap correction rather than item or hypothesis tuning.

## Root cause 2 — provider balance

The final eight manifest entries returned HTTP 402 `Insufficient Balance`. This is an external provider/account condition and cannot be repaired in the repository.

A new real run is prohibited until the account balance is restored.

## New freeze

`R2-FREE-AGENT-ARENA-v0.1.2-PRE-API` supersedes v0.1.1 for future real execution. It must pass offline validation before any rerun.

The next valid E-commerce Wave 1 must start fresh with all 30 repeats; it must not merge traces from run `34932966766`.
