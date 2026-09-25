# Stage-II forward execution binding + common subject readiness — R Plan v7.10

Date: 2026-09-25. Status: **COMMON PROVIDER HANDSHAKE RECORDED; X1–X5 SUBJECT READY; X6/X7 STUDY-ASSET BLOCKED; ZERO NATURAL TRAJECTORIES**.

v7.10 does not alter T1–T3, the nine Software Engineering roles, any X-native scheduling/communication mechanism, or the frozen DeepSeek scientific subject parameters. It closes the provider-readiness phase while keeping scientific collection separate.

## 1. The readiness receipt binds executable content, not a mutable control commit

The paid readiness request ran against exact execution commit `57263f4b2913eab041c1737fdce62e1bd2ab5242`. A later reviewed promotion necessarily changes registry/control metadata, so the promotion commit itself cannot be byte-identical to that execution commit.

`stage2/native_v7/execution_binding.py` resolves that provenance problem. For each X it hashes the local execution files, frozen task/role/subject files, DeepSeek model/provider adapter files, checkout fixture tree and immutable X source/SDK refs plus launch command. Control fields such as `collection_state` and `subject_readiness` are excluded.

The readiness receipt recorded separate execution-surface SHA-256 values for X1–X5. `collect.py` recomputes the selected probe digest before returning an executable request and therefore before a natural cell directory can be reserved. Any drift in covered executable science fails closed.

## 2. One live provider handshake was executed

Workflow `36145131256` made exactly one non-scientific DeepSeek request.

It used no T1–T3 content, no checkout, no multi-Agent run and no evaluator. Completion was capped at 32 tokens and the explicit spending ceiling was USD 0.01.

The provider returned:

- requested model alias: `deepseek-flash`;
- recorded response model string: `deepseek-flash`;
- expected frozen model-version label: `DeepSeek-V4.1-Flash`;
- finish reason: `stop`;
- usage: 31 prompt tokens + 2 completion tokens = 33 total tokens;
- estimated peak-price cost: USD `0.0000117`;
- receipt SHA-256: `93f06cb677b7da3997bcbf38a09cdd10fed650f2e05139e4ac82645a23228464`;
- raw response SHA-256: `e43dbdbb54c5d5fba137ac5561be47e807047b8afbfd2b396b31f000c58f64c9`.

The response model string is preserved as provider evidence; it is not rewritten into the separately frozen expected-version label.

The workflow artifact is `stage2-v710-readiness-36145131256`, artifact id `10869108698`, with artifact digest `sha256:c59c3673d89d4376808cfd3143d99a51376023815de4b5e65e134cc90a15e7d2`.

## 3. Reviewed promotion after the receipt

X1 AutoGen, X2 MetaGPT, X3 A2A, X4 MCP and X5 RAG are promoted to `SUBJECT_READY` only by the reviewed repository state that cites the receipt and each probe-specific execution-surface hash.

This promotion does not execute a task and does not occupy a cell.

X6 MemoryBank remains `NATIVE_RUNNER_VERIFIED_SUBJECT_PENDING` until its real study embedding checkpoint plus exact manifest is frozen and verified.

X7 LongLLMLingua remains `NATIVE_RUNNER_VERIFIED_SUBJECT_PENDING` until its real LongLLMLingua study checkpoint plus exact manifest is frozen and verified. The earlier LLMLingua-2 engineering checkpoint remains a different method and cannot be reused.

## 4. The one-call gate is closed again

After recording the successful common receipt, `subject_readiness.py` rejects a second paid readiness preflight. The temporary branch-only push trigger is removed after use. The standing manual gate also fails closed because the registry now records `COMMON_PROVIDER_HANDSHAKE_RECORDED`.

This prevents repeated connectivity testing from becoming an accidental resampling process.

## 5. Scientific collection remains untouched

No invocation of `stage2.native_v7.collect` occurred in this phase.

All 21 Stage-II cells still have `subject_trajectory_count = 0`. X1–X5 are technically eligible for later one-shot natural collection after this reviewed state is merged; X6/X7 remain asset-blocked.

Stage-II natural trajectory count remains **0 / 21**.
