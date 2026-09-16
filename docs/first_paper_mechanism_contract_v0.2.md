# First-paper mechanism refinement v0.2

Status: frozen before new v4 subject evidence. This forward contract refines the R5-MID experiment without rewriting v0.1 files or historical evidence.

## Scope and estimand

The intervention remains exactly one epistemic-status downgrade from the same frozen parent. The structural endpoint remains anchor-downstream operational crossings. Forward reporting groups complete pair deltas by parent-state hash, then gives each observed parent equal weight. All planned pairs, censoring and missingness remain visible.

Within-parent repeats measure conditional run variability, not independent scenarios. Distinct parents from the same baseline are also not automatically independent: multi-batch output preserves source-trace clusters. v0.2 produces descriptive estimates without an inferential interval because independent-parent sampling and its uncertainty design have not been frozen. The old v0.1 eight-pair bootstrap threshold is not the forward criterion. No new runs are launched to meet a threshold.

Before a future paid collection, freeze parent selection, baseline/parent counts, repeats, order, call cap and budget prospectively. Do not select parents or repeat counts after inspecting branch effects. The present change does not authorize paid collection or choose its budget.

## Outcome-blind anchor classification

`branch_plan` now exports `anchor_source_packets_v0.2.jsonl` before provider execution. A packet contains the selected parent value/metadata and at most 12,000 characters of the producing call's recorded input, located by its event-index interval. It never includes later baseline calls, branch outputs or reviewer conclusions. Missing and truncated inputs are explicit.

Source packets are hashed into the prepared v4 binding and verified when loading it. Reviewers classify SUPPORTED_CALIBRATED, UNSUPPORTED_OR_OVERSTATED or INSUFFICIENT_EVIDENCE using only source evidence. Missing/truncated input cannot support a determinate class in this version. Classification is asynchronous and never changes mechanical anchor selection or pair inclusion. Two distinct independent reviewers must agree for a determinate result; independence/outcome blindness are declared provenance conditions, not facts proven by differing IDs. Disagreement remains unresolved.

## Auxiliary observations

Each continuation exports Agent-turn count, realized-action count, total operational crossings, anchor-reachable crossings, crossings not reached by recorded anchor lineage, and anchor-visible turns. The last complement is not proof of semantic unrelatedness. Visibility is not attention, reading or adoption.

Same-key writes and high-certainty rewrites are exported as candidates with event references. They do not establish semantic inheritance, recertification or R; a changed value may represent a different claim.

Bounded downstream review packets ask about task completion, adoption, verification, correction, inheritance, recertification and challenge presence. RUN_COMPLETE is natural execution termination, not successful task completion. If the bounded evidence lacks the task, outcome, challenge or relevant provenance, use INSUFFICIENT_EVIDENCE or NOT_OBSERVED. These packets do not reconstruct full trajectories or hidden reasoning. No composite success score or automatic R label is produced.

These observations distinguish selective containment from generalized inactivity without conditioning the primary endpoint on post-treatment activity. Auxiliary counts are descriptive and do not replace the primary endpoint.

## Execution and analysis

The existing Phase-B workflow automatically exports:

- `first_paper_mechanism_analysis_v0.2.json`
- `mechanism_observations_v0.2.jsonl`
- `mechanism_review_packets_v0.2.jsonl`

The forward workflow uses v0.2; v0.1 analysis remains available for its historical contract and regression tests, not a second competing forward primary analysis.

Combine separately frozen batches without losing baseline clusters:

```bash
python -m arena.first_paper_mechanism --analyses batch_a/first_paper_mechanism_analysis_v0.2.json batch_b/first_paper_mechanism_analysis_v0.2.json --out mechanism_parent_summary.json
```

Import optional append-only reviews and emit resolutions:

```bash
python -m arena.first_paper_mechanism --packets packets.jsonl --reviews new_reviews.jsonl --ledger reviews.jsonl --out review_resolution_001.json
```

Each review binds `packet_hash`, `reviewer_id`, `independent: true`, `evidence_sufficiency`, valid `evidence_refs`, and `review_hash` (canonical content hash excluding that field). Source reviews additionally require `outcome_blind: true` and `anchor_class`. Downstream reviews require all seven `judgments` fields from the contract. YES/NO requires sufficient cited evidence. Uncertainty, disagreement and absence are never resolved as NO. Additional imports must include the packets referenced by existing ledger records.

R9 cross-model robustness remains supplementary. Neither source classification nor local semantic review triggers an automatic evaluator or reruns subject evidence.
