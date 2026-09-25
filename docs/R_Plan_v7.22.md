# Stage-II v7.22: Action Contract v2 subject revalidation promoted

Date: 2026-09-26. Status: **T1 NATURAL ROW 7/7 FROZEN UNDER v1; C1+C2 FROZEN 2/4; ACTION CONTRACT v2 SUBJECT_READY FOR X1–X7; T2 UNOPENED; T3 CLOSED**.

Action Contract v2 changed the execution snapshot covered by the original common provider receipt, so collection was intentionally returned to `NATIVE_RUNNER_VERIFIED_SUBJECT_PENDING` rather than weakening provenance checks. The original readiness receipt remains preserved as immutable T1/v1 history in `stage2/native_v7/readiness/receipt_v1.json`.

A new one-call, non-scientific provider handshake was then executed on the exact v2 snapshot at commit `129b35500613c9db70818ee947a4b45ba6fd0b05` in workflow run `36176860170`. The handshake:

- made exactly one provider call;
- executed no T1–T3 task and reserved no natural cell;
- preserved the natural evidence count at 7 before and after the call;
- reported no remaining X6/X7 asset blockers;
- made X1–X7 eligible for reviewed promotion;
- bound the current subject/model configuration and exact v2 execution-file hashes.

The exact receipt is committed as `stage2/native_v7/readiness/receipt_v2.json`, SHA-256 `7c771677352a715d9085266b9d2b38a4453f523491128931e9e39c476b45e42d`. The registry now points to that receipt and promotes all seven X conditions to `SUBJECT_READY`. The historical v1 receipt and per-probe historical readiness evidence remain separately retained.

This promotion changes only readiness metadata, the committed receipt and the derived matrix. It does not alter Action Contract v2 execution files, any X framework implementation, task/role/model inputs, X6/X7 real study assets, observers, T1 raw evidence or C1/C2 contrast evidence.

Natural collection remains **7/21**. Contrast accounting remains **2/4**. The next scientific action is exactly one T2 natural attempt for each X1–X7 under the frozen task-specific contract map. T3 stays closed until all seven T2 attempts are preserved and the T2 row receives a read-only cross-cell semantic/process audit.
