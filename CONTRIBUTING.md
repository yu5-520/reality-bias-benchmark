# Contributing

Contributions are welcome.

This repository is intended to support an open research programme, not a closed implementation controlled by a single laboratory.

Useful contributions include:

- independent replications;
- new domain experiments;
- new model or provider adapters;
- alternative semantic-audit methods;
- new lineage representations;
- monitor / repair implementations;
- validation and conformance tests;
- bug fixes;
- documentation improvements;
- evidence-integrity tools;
- negative or contradictory findings;
- links to downstream studies for `ECOSYSTEM.md`.

## 1. Preserve frozen evidence

Do not rewrite frozen historical evidence to make it match a later interpretation.

Corrections should be appended as a new version, with a clear explanation of:

- what changed;
- why it changed;
- what historical object remains frozen;
- whether scientific conclusions change;
- which hashes, manifests, or identifiers are affected.

## 2. Separate execution from interpretation

A new analysis does not imply a new subject run.

A new semantic interpretation does not authorize rewriting raw evidence.

Where relevant, distinguish:

- subject/provider execution;
- structural derivation;
- semantic audit;
- theory synthesis;
- engineering demonstration;
- publication packaging.

## 3. State scientific status clearly

Please label work according to what it actually supports.

Examples:

- exploratory;
- retrospective;
- prospective;
- replicated;
- censored;
- engineering-only;
- hypothesis-generating;
- application outlook;
- externally validated.

Avoid upgrading an observation into a universal claim merely because the repository makes the result easy to reproduce.

## 4. Independent work does not need to be merged upstream

A downstream laboratory or project may remain fully independent.

If the work is scientifically relevant, it can still be linked from `ECOSYSTEM.md`.

Upstream inclusion is not required for legitimacy, and upstream inclusion does not imply endorsement.

## 5. Credit and authorship

Contributors retain credit for their contributions.

A code, documentation, data, or analysis contribution does not automatically create authorship on an unrelated paper.

Paper authorship should reflect substantial intellectual and research contribution to that specific work.

Likewise, independent downstream work does not need to include the upstream maintainer as an author merely because it uses or extends the repository. Appropriate scholarly citation is the normal mechanism for preserving research lineage.

## 6. Contribution licensing

By submitting a contribution, you confirm that you have the right to contribute it.

Unless explicitly stated otherwise:

- original software contributions are submitted under the repository's MIT licence;
- original non-code research material is submitted under CC BY 4.0;
- third-party material must retain its own licence and provenance.

No copyright assignment or contributor licence agreement is required by default.

## 7. Pull-request notes

A substantial pull request should explain:

- the problem or research question;
- the changed files;
- whether frozen evidence is touched;
- whether any provider/model execution occurred;
- whether any semantic adjudication changed;
- validation performed;
- compatibility implications;
- relevant upstream or downstream provenance.

## 8. Research disagreement is welcome

Replication failures, alternative explanations, contradictory evidence, and boundary-setting results are scientifically useful.

The goal is not to keep every later result consistent with the original theory.

The goal is to keep the evidence and lineage clear enough that disagreement can be inspected.
