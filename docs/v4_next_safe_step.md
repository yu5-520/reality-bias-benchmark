# v4 Next Safe Step

Date: 2026-09-16

The current `R2-ARENA-TRACE-v0.3` source adapter is now implemented and CI-validated.

Before any real provider call, the next engineering boundary is:

```text
BehaviorEvent v0.1
→ frozen structural Jump-candidate detector
→ frozen operational-boundary set
→ branch-continuation-aware v4 slicing
→ exact registry / adapter / measurement hash binding
```

The Jump detector must remain structural and candidate-only. It must not promote state changes, invocations or revisions directly into semantic C/P/R or Authority Penetration.

The operational-boundary set must define what can be mechanically counted before any formal penetration-depth claim is made.

These are offline engineering steps and do not require paid API authorization.