# R9 Innovation Synthesis, Prior-Art Boundary, and Outlook Protocol v1

Date: 2026-09-20
Status: FORWARD / LITERATURE-GROUNDED / NO NEW SUBJECT RUNS

## 1. Purpose

R9 closes the first paper at the contribution/innovation layer.

It does not manufacture new empirical evidence. It maps already-frozen R2-R8 evidence against the strongest adjacent literature and determines what the paper may and may not claim as contribution.

## 2. Required outputs

R9 produces four canonical outputs:

1. `Prior-Art Literature Map`;
2. `Innovation Boundary Matrix`;
3. `Contribution Ledger`;
4. `Innovation Synthesis and Outlook Report`.

## 3. Literature admission

### Tier A — peer-reviewed anchors

Prefer official proceedings from:

- NeurIPS;
- ICML/PMLR;
- ACL/EMNLP/EACL;
- IEEE/ACM archival conferences/journals.

### Tier B — high-risk frontier neighbors

Recent preprints are included when they overlap closely enough that ignoring them could lead to an inflated novelty claim.

Tier B work must be labeled `PREPRINT / NOT PEER-REVIEWED` unless publication status is independently verified.

### Tier C — surveys / synthesis

Use to map field-wide terminology and open problems, not as sole evidence for a novelty claim.

## 4. Boundary-audit template

For each proposed contribution record:

- `claim_id`;
- `our_object`;
- `nearest_prior_art`;
- `prior_art_object`;
- `overlap`;
- `exact_difference`;
- `frozen_evidence`;
- `allowed_wording`;
- `forbidden_wording`;
- `novelty_confidence`;
- `remaining_search_risk`.

## 5. Innovation dimensions

R9 separately audits:

- structural innovation;
- mechanism innovation;
- methodology innovation;
- engineering innovation.

A mechanism finding must not be presented as an engineering novelty, and vice versa.

## 6. Required high-risk comparisons

At minimum include:

- MAS failure taxonomy / fault attribution;
- communication topology / information propagation;
- shared/persistent memory;
- execution provenance;
- epistemic provenance / support status;
- rollback / recovery;
- task-scoped transactional control;
- collaborative software-engineering recovery.

## 7. Strongest-boundary rule

If a recent source overlaps more strongly than an older top-venue paper, it must be included even if it is only a preprint.

This is particularly important for:

- typed epistemic provenance;
- task-scoped semantic transactions;
- execution-provenance synthesis.

## 8. Evidence binding

Innovation claims may bind only to already-frozen repository evidence, including:

- R8 Dynamic CPR semantic closure;
- R8 150-trajectory analysis inventory;
- R5/R6 lineage findings;
- R7 process-integrity engineering evidence.

R9 itself cannot upgrade `SUPPORTED_CANDIDATE` to `SUPPORTED`.

## 9. Outlook discipline

Future directions must be labeled as:

- `EVIDENCE-ADJACENT FUTURE WORK`;
- `EXTERNAL VALIDATION`;
- or `SPECULATIVE ENGINEERING DIRECTION`.

They are not results.

## 10. Citation role

References serve two distinct functions:

1. locate the paper inside existing research;
2. constrain overclaiming by identifying what is already known.

R9 citation count is not a quality metric; boundary relevance is.

## 11. Current paper position

The first paper should be positioned as:

`mechanism-first / high-resolution / process-reality study`

rather than:

`large-scale benchmark / universal prevalence study`.

## 12. Authorization boundary

No new model/provider/evaluator experiment is authorized by R9.
