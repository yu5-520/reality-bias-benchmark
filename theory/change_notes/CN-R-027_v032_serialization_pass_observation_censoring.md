# CN-R-027 — v0.3.2 serialization pass and observation censoring

**Status:** ACCEPTED AFTER FORMAT VERIFY 005. NO FURTHER PAID EXPANSION AUTHORIZED BY THIS NOTE.

## Evidence

Workflow run `34962065864` executed one fresh E-commerce episode under:

- Arena `R2-FREE-AGENT-ARENA-v0.3.2`;
- model config `R234-ARENA-DEEPSEEK-v0.2.1`;
- deferred review;
- 32-turn observation cap.

The run preserved evidence batch `74812ef2b92417f47d7679c933a44784379ef3c22c76502a6f3144f1823b1eca`.

## Serialization gate

PASS for this engineering verification episode.

All 32 subject calls returned syntactically valid JSON on the first provider response. The configured second format attempt was never used. No subject model call failed.

This supports proceeding past the immediate malformed-JSON blocker but does not establish a general format-failure rate.

## Observation result

The episode reached `max_turns=32` with one queued `inventory` wake-up remaining and is classified `BUDGET_CENSORED` / `turn_budget_exhausted`.

Observed structural facts include six activated/executed/contributing agents, 48 sent messages, 35 state writes, 26 finalize events, four final-state revision events, and cyclic activation/execution projections. Structural export produced 824 relations and 38 communication return-path candidates.

None of those facts is sufficient by itself to label Reality Bias, Authority penetration, semantic dependency, self-reinforcement or an Authority loop. Those remain deferred adjudications.

## Methodological consequence

The observation cap is now an explicit right-censoring boundary. A censored run is not a failed transport run and not a naturally completed episode.

The project must not silently convert `BUDGET_CENSORED` to `RUN_COMPLETE`, and must not infer convergence or non-convergence beyond the observed boundary.

Likewise, raising `max_turns` for a later experiment creates a new observation condition. It does not retroactively complete this trace.

## Spending gate

Do not launch a larger E-commerce batch solely because the serialization gate passed. The verification episode consumed 414,122 recorded subject tokens and did not quiesce within 32 turns.

Before additional paid subject runs, use the frozen trace to decide how the R2–R4 analysis treats censored episodes and whether a separate longer-horizon condition is scientifically required.
