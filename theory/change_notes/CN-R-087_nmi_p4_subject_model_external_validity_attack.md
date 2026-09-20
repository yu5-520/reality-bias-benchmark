# CN-R-087 — P4 Limited Subject-Model External Validity Attack

Date: 2026-09-21  
Status: **ACCEPTED / EXTERNAL-VALIDITY HARDENING**

## Attack

> Is the phenomenon merely specific to the single subject model/provider/runtime used in the study?

## Finding

The current paper has strong domain variation but narrow subject-model coverage.

Formal e-commerce, held-out cross-domain and canonical active R5/R7 subject runs use one frozen DeepSeek subject configuration.

This was useful for controlled domain comparison but does not establish model/provider invariance.

Canonical guards:

> **cross-domain != cross-model robustness**

> **cross-model review != cross-model subject replication**

## Measurement distinction

Historical cross-model reviewer disagreement informs semantic measurement reliability.

It is not subject-system replication.

## Allowed claim

> The first paper establishes mechanism evidence in the studied runtime and prepares a frozen replication programme for alternate subject models.

It does not establish model-invariant prevalence, provider robustness, topology robustness or independent external replication.

## Manuscript update

Create append-only:

`docs/submission/nmi/NMI_Manuscript_v0.10.md`

Main text before Methods: approximately 3,239 words.

Abstract: 147 words.

## Execution boundary

No new subject run, provider call, evaluator call, semantic adjudication or raw-evidence mutation.
