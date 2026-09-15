# Formal Batch 001 — Cross-model Blind Review Agreement v1

Events compared: **70**

| Dimension | Agreement | Cohen κ | Reviewer A positive | Reviewer B positive |
| --- | ---: | ---: | ---: | ---: |
| C | 0.700 | 0.158 | 3 | 24 |
| P | 0.729 | 0.318 | 10 | 25 |
| R | 0.729 | 0.486 | 42 | 25 |

Authorization agreement: **0.700**, Cohen κ = **0.376**.

Exact Bias-label-set agreement: **0.300**.

Exact joint Bias+authorization agreement: **0.229**.

## Primary unauthorized-event results

| Reviewer | C runs | P runs | R runs | C I/V/T | P I/V/T | R I/V/T |
| --- | ---: | ---: | ---: | --- | --- | --- |
| A | 2 | 2 | 3 | 3/0/0 | 0/9/0 | 2/5/4 |
| B | 3 | 3 | 3 | 4/0/3 | 0/18/2 | 1/1/3 |

Primary-event Jaccard overlap: **0.400** (12 shared / 30 union).

Events with any Bias-set or authorization disagreement: **54 / 70**.

## Interpretation boundary

Model-vs-model agreement only. Reviewer A was non-blinded; Reviewer B was blind to A and expected mappings. This is not human IRR and does not establish semantic truth by majority vote.

## Reviewer B usage

Recorded reviewer usage: `{"completion_tokens": 20343, "prompt_cache_hit_tokens": 1767933, "prompt_cache_miss_tokens": 14116, "prompt_tokens": 1782049, "total_tokens": 1802392}`.

Stored-price estimate: off-peak `$0.0196`, peak `$0.0393`. These are repository-snapshot estimates, not provider billing.
