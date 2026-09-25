# Stage-II v7: native execution / external observation

This directory is the active forward Stage-II architecture. All seven X conditions retain verified native entrypoints and are `SUBJECT_READY` under the Action Contract v2 common readiness receipt. The original common subject receipt is preserved separately as historical T1/v1 provenance. X6/X7 retain their committed real pretrained study manifests and successful real-load verification. T1 natural attempts for X1–X7 remain archived under `stage2/natural_v7/`; the T1 first-attempt row is closed at 7/7.

The v6.x scaffold proved that the seven targets could be pinned and recorded, but it normalized heterogeneous systems through a shared `CodingArena`/transport/context contract. v7 removes that assumption: X1/X2 use their native multi-agent runtimes, X3 uses native A2A communication, and X4–X7 attach only at their native capability boundaries to the frozen de-instrumented software-engineering host.

`registry.json` is a registry, not an adapter interface. `collect.py` refuses cells whose X remains `NATIVE_RUNNER_VERIFIED_SUBJECT_PENDING`.

The monitor is external. `observer.py` preserves already-produced bytes/events, while framework-specific observers add native evidence beneath the observer root. Common semantic/structural indexing happens after the run. No observer may rewrite framework messages or control scheduling.

## Subject-readiness boundary

`subject_readiness.py` implements the next fail-closed gate. It may perform **one** manually authorized, non-scientific provider handshake for the common frozen DeepSeek subject binding. It never executes T1–T3, reserves a cell, calls a paid evaluator, or edits `registry.json`.

A successful handshake creates a receipt only. A reviewed registry commit must cite that receipt before any X can be changed to `SUBJECT_READY`. X6 additionally requires its frozen real study embedding manifest and X7 its frozen real LongLLMLingua checkpoint manifest; those requirements are now satisfied by the committed manifests under `stage2/native_v7/study/`. Synthetic smoke assets remain ineligible.

`docs/R_Plan_v7.14.md` records the completed X6/X7 promotion. During natural execution, X6/X7 still compare the actual local checkpoint files with the committed study manifest **before** cell reservation; promotion does not waive that fail-closed check.

Run the offline architecture checks with:

```bash
python -m stage2.native_v7.freeze
python -m unittest discover -s stage2/native_v7/tests -v
```

The frozen architecture matrix retains `subject_trajectory_count: 0` as the prerecording baseline. Its readiness state now reopens all seven X conditions under the reviewed v2 receipt. The current raw collection count is **7 / 21**. T1 first attempts are frozen for X1–X7; X2–X7 ended without terminal answers, while X1 has a terminal answer. The seven-cell post-hoc audit is now frozen in `stage2/natural_v7/T1_posthoc_audit.{json,md}`. C1 and C2 are recorded and audited under `stage2/contrasts_v7/`. C1 crosses the serialization gate; C2 makes the existing `max_actions=5` limit visible and reaches 32/32 parser-accepted turns. Contrast accounting is 2/4. Prospective Action Contract v2 is frozen for T2/T3 (`docs/R_Plan_v7.21.md`), while T1 remains historical v1 and immutable. The v2 common provider readiness receipt and reviewed promotion are complete (`docs/R_Plan_v7.22.md`). T2 is the next unopened natural row; T3 stays closed until T2 is preserved and audited.

R_Plan_v7.24 freezes the complete one-shot T2 row. Natural collection is now 14 / 21 (T1 7/7 + T2 7/7). X4-T2 and X6-T2 are preserved runner failures and must not be rerun. T2 read-only audit is next; T3 remains closed.

The T2 seven-cell read-only audit is frozen in `stage2/natural_v7/T2_posthoc_audit.{json,md}` and summarized by `docs/R_Plan_v7.25.md`. The Action Contract v2 gate is considered crossed; T3 is the next admissible one-shot row. Natural collection remains 14/21 and contrast accounting remains 2/4.

T3 is predeclared as the terminal one-shot natural row by `docs/R_Plan_v7.26.md`, using `stage2-v7-t3-natural-row.yml` behind its exact issue bridge. No contrast is spent before this row; after it is frozen, the full 21-cell read-only audit is required before choosing either remaining contrast.

R_Plan_v7.27 freezes the terminal one-shot T3 row. Natural collection is now complete at 21 / 21 (T1 7/7 + T2 7/7 + T3 7/7). No natural cell may be rerun. T3 read-only audit and the full cross-task/cross-layer audit are next; contrast accounting remains 2/4.
