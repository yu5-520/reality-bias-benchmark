# Stage-II v7: native execution / external observation

This directory is the active forward Stage-II architecture.

The v6.x scaffold proved that the seven targets could be pinned, smoke-tested and
recorded, but it also normalized heterogeneous systems through a shared
`CodingArena`/transport/context contract. v7 removes that assumption before any
natural Stage-II trajectory is collected.

`registry.json` is a registry, not an adapter interface. Each X receives an
independent environment and will eventually receive its own verified native
entrypoint. `collect.py` refuses to reserve a natural cell while a probe remains
`PENDING_NATIVE_RUNNER`.

The monitor is external. `observer.py` preserves process-boundary bytes and
framework-specific observers may add native files beneath the observer root.
Common semantic/structural indexing happens after the run. No observer is
allowed to rewrite framework messages or control scheduling.

Run the offline architecture checks with:

```bash
python -m stage2.native_v7.freeze
python -m unittest stage2.native_v7.tests.test_architecture
```

Do not run a natural cell until the selected X has a verified native entrypoint
and observer recorded in `registry.json`.
