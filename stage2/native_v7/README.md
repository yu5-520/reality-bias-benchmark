# Stage-II v7: native execution / external observation

This directory is the active forward Stage-II architecture. All seven X conditions have verified native entrypoints; X1–X5 now cite the frozen common subject receipt, while X6/X7 remain asset-pending. Natural collection remains 0/21.

The v6.x scaffold proved that the seven targets could be pinned and recorded, but it normalized heterogeneous systems through a shared `CodingArena`/transport/context contract. v7 removes that assumption: X1/X2 use their native multi-agent runtimes, X3 uses native A2A communication, and X4–X7 attach only at their native capability boundaries to the frozen de-instrumented software-engineering host.

`registry.json` is a registry, not an adapter interface. `collect.py` refuses cells whose X remains `NATIVE_RUNNER_VERIFIED_SUBJECT_PENDING`.

The monitor is external. `observer.py` preserves already-produced bytes/events, while framework-specific observers add native evidence beneath the observer root. Common semantic/structural indexing happens after the run. No observer may rewrite framework messages or control scheduling.

## Subject-readiness boundary

`subject_readiness.py` implements the next fail-closed gate. It may perform **one** manually authorized, non-scientific provider handshake for the common frozen DeepSeek subject binding. It never executes T1–T3, reserves a cell, calls a paid evaluator, or edits `registry.json`.

A successful handshake creates a receipt only. A later reviewed commit must cite that receipt before any X can be changed to `SUBJECT_READY`. X6 additionally requires a frozen real study embedding manifest; X7 requires a frozen real LongLLMLingua study checkpoint manifest. The synthetic engineering assets used by their smokes can never satisfy those gates.

`docs/R_Plan_v7.10.md` specifies the promotion evidence: the committed receipt and execution snapshot are verified before an individual X opens. X6/X7 additionally compare their actual local checkpoint files with the committed study manifest **before** cell reservation. A pending X does not hold the other X cells closed.

Run the offline architecture checks with:

```bash
python -m stage2.native_v7.freeze
python -m unittest discover -s stage2/native_v7/tests -v
```

Stage-II natural trajectory count remains **0 / 21**; consult `docs/R_Plan_v7.11.md` for receipt provenance and per-X readiness.
