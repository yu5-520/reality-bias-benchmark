# CN-R-025 — Shared structural observation runtime v0.3

Date: 2026-09-15. Implements R Plan v2.0 / CN-R-024, following the user's instruction to implement and run the repository experiment.

## Changed behavior

- New `arena_v0.3.json`: 32-turn observation window, 64 invocation / 128 pending-wakeup bounds. Finalize settles a plan; an episode ends at queue quiescence. Repeated calls and revisions remain observable. Only pending wakeups for an actor are coalesced; all messages and invocation identities are preserved and consumed together. No semantic loop suppression or automatic reviewer insertion.
- Turn, invocation and capacity limits are `BUDGET_CENSORED`, including when a FINAL state exists. Natural quiescence exactly at the turn limit remains natural completion. Historical trace files are never rewritten.
- Raw calls and events are durably journaled during execution, with timestamps, hash chaining and runtime snapshots. Finished runs are appended immediately. Partial journals survive caught provider failures and can be uploaded after workflow interruption; a hard host loss can still prevent artifact upload.
- Evidence batches bind journal hashes and export event, exposure relation and actor-projected feedback candidates. Visibility is not semantic dependence; actor return paths need not be chronological causal chains. Loop absence/presence and self-enhancement remain unadjudicated.
- Independent later R2/R3/R4 review import validates batch hashes and evidence references and refuses review overwrite. No model calls or subject retries occur during import. Old event-review interface remains available.
- Real runner verifies actual domain/config/model file hashes against the manifest, refuses overwriting outputs, and retains explicit subject failure status.

## Execution and limits

The default manual subject workflow uses v0.3. A separate launch record triggers one ecommerce subject smoke episode on initial push, after offline gates. No automatic paid evaluator. This validates execution integration only, not C/P/R frequency, causality, self-enhancement or cross-domain generalization. The 32-turn cap is a predeclared observation bound, not proof that loops are impossible beyond it.

v0.1/v0.2 configurations and historical evidence remain available; default changes must not be silently pooled with prior scheduling conditions. v0.3 does not artificially keep an idle society active or inject repeated late events. R5/R6 causal interventions/recovery are separate future experiments.

## Validation

18 regression tests cover old scheduling, repeated feedback, censoring, exact-boundary completion, complete inbox delivery, journal survival and legacy missingness. Four-domain synthetic export checks three-layer review import, invalid references and overwrite rejection. Real run outcome is tracked in GitHub Actions, not asserted by this pre-run change note.
