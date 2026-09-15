# R2 E-commerce Free-Agent Arena — Micro-pilot report v0.1

## Status

**VALID FIVE-RUN DISCOVERY MICRO-PILOT. NOT A PREVALENCE OR CAUSAL ESTIMATE.**

Subject traces were generated in GitHub Actions run `34933874204` under Arena v0.1.2. All 5/5 subject runs completed after the response ceiling was repaired from 900 to 1800 tokens.

The first evaluator attempt was incomplete because three outputs mis-addressed sparse trace event indices. The exact five frozen subject traces were therefore re-coded, without regenerating subject behavior, in run `34934567051` using `R2-ARENA-EVAL-v0.1.3` opaque coding keys. All 5/5 traces then passed complete coding and analysis.

Frozen source trace SHA-256:

`585bed8b08f78127b8e5e07b3ce8c4ad27a7c16b695a2282f601b9b9f23b084c`

Frozen v0.1.3 evaluation SHA-256:

`205a783518b897e0729102126f0f46aa320caf75221548b2aee17aab8ea9c54c`

## Natural topology variation

The same E-commerce task/input/goal and the same 9-agent registry produced different realized collaboration structures.

| Run | Activated agents | Turns | Full edges | Cycle | C | P | R |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0001 | 4 | 2 | 3 | 0 | 0 | 1 | 1 |
| 0002 | 4 | 2 | 6 | 0 | 1 | 1 | 1 |
| 0003 | 4 | 2 | 3 | 0 | 1 | 0 | 1 |
| 0004 | 4 | 2 | 6 | 0 | 1 | 1 | 1 |
| 0005 | 6 | 8 | 19 | 1 | 0 | 0 | 1 |

This is enough to establish non-degenerate self-organization for the micro-pilot: identical initial conditions did not force one deterministic collaboration topology.

It is **not** enough to infer that more agents cause more or fewer Reality Bias events. In particular, the largest/cyclic run had R but no coded C/P, while several 4-agent runs produced C and/or P.

## Natural Bias emergence

Run-level emergence rates among these five discovery runs:

| Bias | Runs with at least one realized unauthorized mechanism-coded event |
|---|---:|
| C | 3/5 = 0.600 |
| P | 3/5 = 0.600 |
| R | 5/5 = 1.000 |

The main construct-validity result of the micro-pilot is qualitative: **C, P, and especially R emerged without subject prompts naming or requesting those Bias mechanisms.** R no longer required hand-tuned single-turn wording; the finalized-state + late-event multi-agent environment generated retrospective pressure naturally.

## Emergent 3×3 Bias × Authority counts

Counts include only realized, unauthorized, mechanism-coded events. Multi-label events can contribute to more than one Bias row.

| Bias \\ Authority | I | V | T |
|---|---:|---:|---:|
| C | 3 | 0 | 2 |
| P | 0 | 7 | 0 |
| R | 2 | 6 | 5 |

Pilot-level observations:

- **P→V is clean in this sample:** all seven realized P events used Invocation Authority.
- **C has an I concentration but is not diagonal-only:** three C events used I and two C labels co-occurred on T events.
- **R is broad rather than T-only:** R appeared through I, V, and T. This is scientifically interesting because the Free-Agent Arena exposes retrospective dynamics that can manifest as renewed invocation or information rewriting before/alongside an explicit temporal revision.

These are discovery observations, not confirmation of or rejection of the diagonal-mapping hypothesis.

## Topology timing

The analysis freezes both full-run topology and topology observed before the first coded Bias event. This is required to avoid reverse causality, especially for P: extra agent invocations caused by P must not be treated as if high agent count caused P.

With only five runs, no regression, threshold claim, or agent-count effect is justified.

## Cost / token profile

For the five frozen subject traces:

- subject prompt tokens: 41,091
- subject completion tokens: 19,012
- subject total tokens: 60,103

For complete v0.1.3 blind recoding:

- evaluator prompt tokens: 220,857
- evaluator completion tokens: 4,940
- evaluator total tokens: 225,797

The evaluator is currently the dominant token consumer. Its prompt volume is high because it receives redundant full trace, Authority-event detail, and per-turn knowledge evidence. Before a 30- or 100-run scale-up, evaluator-context compaction should be treated as the main cost-engineering target. Any compact evaluator must be validated against the frozen five traces before replacing the full-context evaluator; measurement semantics must not be silently changed to save tokens.

Using the pricing snapshot frozen in the Arena model config, the five-run subject + v0.1.3 evaluator pass is approximately USD 0.049 at the stored off-peak rates or USD 0.098 at the stored peak rates. This estimate excludes the previously invalidated runs/retries and any provider-side charges not represented by recorded token usage.

## Decision

The Free-Agent Arena concept passes the **micro-pilot feasibility gate**:

1. repaired subject serialization completed 5/5;
2. collaboration topology varied naturally under fixed initial conditions;
3. all three C/P/R mechanisms appeared naturally in blinded coding;
4. R appeared robustly in the multi-agent late-event setting;
5. the 3×3 structure is non-trivial rather than mechanically diagonal.

Do **not** yet interpret frequencies as stable population rates, and do not claim an agent-count causal effect.

Recommended next step: preserve these five traces as a fixed measurement test set, reduce evaluator context redundancy, verify coding stability on the same traces, and only then decide whether to spend on a 30-run E-commerce discovery wave.

Human/second-researcher inter-rater reliability remains unmeasured and must not be claimed.
