# Stage-II forward execution binding + live common subject readiness — R Plan v7.10

Date: 2026-09-25. Status: **LIVE HANDSHAKE PREPARED; ALL 21 NATURAL CELLS STILL CLOSED**.

v7.10 does not alter T1–T3, the nine Software Engineering roles, any X-native scheduling/communication mechanism, or the frozen DeepSeek scientific subject parameters. It strengthens the boundary between a paid provider-readiness check and later cell authorization.

## 1. A readiness receipt binds executable content, not a mutable control commit

A reviewed promotion must edit registry/control metadata after the provider receipt exists. Therefore the Git commit that records `SUBJECT_READY` cannot be byte-identical to the earlier readiness commit.

`stage2/native_v7/execution_binding.py` resolves that provenance problem. For each X it hashes the exact local execution files, frozen task/role/subject files, model/provider adapter files, checkout fixture tree and the selected immutable upstream refs/launch command. Control fields such as `collection_state` and `subject_readiness` are deliberately excluded.

The live preflight records a separate `execution_surface_sha256` for every probe eligible for promotion. `collect.py` recomputes the selected probe digest before reserving a cell and fails closed on any mismatch.

Thus a later reviewed registry commit may authorize a cell, but it cannot silently change the runner, provider adapter, prompt/task inputs, checkout fixture, protocol/source ref or probe launch surface covered by the readiness receipt.

## 2. One live provider handshake remains non-scientific

The live request is still one common DeepSeek connectivity/readiness call:

- no T1–T3 content;
- no checkout;
- no multi-Agent run;
- no evaluator;
- one provider call maximum;
- 32 completion-token readiness cap;
- explicit spending ceiling;
- raw response preserved before success is judged.

This call tests the common frozen subject route only. X-specific runtime behavior remains supported by the already-passed native engineering smokes.

## 3. Promotion geometry

If the common handshake succeeds, X1–X5 may be promoted by a later reviewed metadata commit only when their recorded `execution_surface_sha256` still matches current executable content.

X6 and X7 remain blocked even after the common handshake until their real study embedding/checkpoint manifests are frozen and verified. Their tiny engineering assets remain invalid for natural collection.

No workflow in this phase invokes `stage2.native_v7.collect`. Natural trajectory count remains **0 / 21**.
