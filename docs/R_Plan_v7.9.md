# Stage-II subject-readiness gate — R Plan v7.9

Date: 2026-09-25. Status: **READINESS GATE IMPLEMENTED; NO LIVE RECEIPT; ALL 21 NATURAL CELLS CLOSED**.

v7.9 begins only after the X1–X7 native-runner phase has closed. It does not modify any native X runtime, T1–T3, the nine Software Engineering roles, the checkout fixture, or the frozen DeepSeek subject profile.

## 1. Readiness is not another experiment

The next question is narrower than scientific collection: can the exact frozen subject binding still be reached with the configured credential/endpoint on the exact execution commit?

All seven X conditions share `stage2/subject.json` and `arena/config/model_deepseek_v0.2.json`. Repeating the same paid connectivity request seven times would add cost without adding seven independent scientific observations. v7.9 therefore freezes one **common provider handshake**.

The handshake uses no T1–T3 task, no checkout, no multi-agent collaboration, no CPR audit and no evaluator. It is explicitly non-scientific infrastructure evidence.

## 2. Manual one-call gate

The only live entrypoint is `.github/workflows/stage2-native-v7-subject-readiness.yml`, launched manually with:

- the exact dispatched execution SHA;
- the exact phrase `CALL_REAL_STAGE2_SUBJECT_READINESS_API`;
- `max_subject_calls=1`;
- an explicit USD spending ceiling no greater than 0.05.

Before the credential is exposed, the workflow reruns the frozen v7 matrix and all native-v7 unit tests, verifies the SHA and authorization phrase, verifies that every X already has a native runner, and writes a preflight artifact.

The live step then makes exactly one DeepSeek subject request with transport retries forced to one and a 32-token completion cap. It records raw provider response bytes/JSON, provider usage, the observed response model string, the frozen expected model version, subject/model-config hashes and peak-price accounting. No automatic evaluator can run.

## 3. A receipt cannot open a cell

A successful live call has status:

`COMMON_PROVIDER_HANDSHAKE_RECORDED_NOT_SUBJECT_READY`

The workflow has read-only repository permissions. It cannot edit `registry.json`, change a cell state, or invoke `stage2.native_v7.collect`.

Promotion is deliberately a separate reviewed repository commit. `policy.py` now rejects any `SUBJECT_READY` entry unless the probe contains frozen readiness evidence identifying the execution SHA, common receipt hash, subject/model config hashes and workflow run.

This separation prevents “provider reachable” from silently becoming “scientific trajectory authorized.”

## 4. X6/X7 remain additionally blocked

The common subject handshake is necessary but not sufficient for X6 or X7.

- X6 requires `study_embedding.state == FROZEN_MANIFEST_VERIFIED` with a real study embedding checkpoint and exact file hashes.
- X7 requires `study_checkpoint.state == FROZEN_MANIFEST_VERIFIED` with a real LongLLMLingua compressor checkpoint and exact file hashes.

Their deterministic tiny smoke assets remain engineering-only and are explicitly invalid for natural collection.

Therefore, before a live common handshake is even run, the current preflight reports X1–X5 as eligible for later reviewed promotion and X6/X7 as asset-blocked.

## 5. What remains unchanged

All X1–X7 remain `NATIVE_RUNNER_VERIFIED_SUBJECT_PENDING`.

The 21-cell matrix remains unopened and its trajectory count remains **0 / 21**. The next paid action, if authorized, is one common provider handshake—not a Stage-II natural trajectory.
