# Stage-II forward freeze and independent X readiness — R Plan v7.10

Date: 2026-09-25. Status: **IMPLEMENTED OFFLINE; NO LIVE RECEIPT; NATURAL TRAJECTORIES 0/21**.

This checkpoint continues v7.9. T1–T3, the nine roles, the checkout fixture, the seven native X implementations and the DeepSeek subject remain frozen. The 21 cells still each allow at most one natural trajectory. No scripted smoke is a scientific observation.

## Forward evidence binding

The single common, non-scientific provider handshake records the exact execution commit, its GitHub workflow run ID, the raw response hash, subject/model configuration hashes and an execution snapshot. That snapshot contains hashes of the frozen executable files and a digest of the checkout fixture. The later registry promotion commit may change `registry.json`, the derived matrix and planning prose, but any change to the execution snapshot invalidates the receipt for collection. The handshake cannot itself promote an X or reserve a cell.

After the manually dispatched v7.9 workflow has succeeded, preserve its complete artifact. Review the raw response, provider usage and receipt. A separate promotion commit may copy the receipt to `stage2/native_v7/readiness/receipt.json`, record its SHA-256 in `subject_readiness_gate`, set that gate to `COMMON_PROVIDER_HANDSHAKE_RECORDED`, and add `subject_readiness` to each independently eligible X. The latter must cite the execution commit, receipt hash, subject/model hashes and workflow run ID from the receipt. The policy verifies the receipt's bytes and fields against the current execution snapshot, rather than accepting populated strings alone. The archived raw provider response remains part of the evidence package; its digest is cited by the receipt. A reviewed promotion can open X1–X5 without waiting for X6/X7 assets.

## X6/X7 asset condition

Each of X6 and X7 separately requires a committed study manifest path and SHA-256 in its registry entry and `FROZEN_MANIFEST_VERIFIED` state. The manifest must say `purpose: STAGE2_NATURAL_STUDY`, use the corresponding probe schema and list every checkpoint file with its hash. The non-study tiny smoke manifests are invalid. Before reserving an X6/X7 cell, the collector hashes the actual local checkpoint and compares it to that committed manifest. It passes the committed manifest path to the runner, preventing an environment variable from selecting a different manifest. A missing asset blocks only its own X cells.

These checks validate identity and provenance of the assets. They do not preselect agent messages, tool use, semantic labels or outcome. Native X runtimes and the external observer continue to own their respective execution and recording boundaries. A failure before reservation leaves the natural count at zero for the cell; any attempt after reservation is preserved as an attempt.

## Current state

The repository has no provider receipt and no frozen study embedding/compressor manifests. The local execution environment has no `DEEPSEEK_API_KEY` and no GitHub CLI. The paid common handshake has therefore not been run here, and no registry entry is promoted. All 21 cells remain closed and the Stage-II natural trajectory count remains 0.
