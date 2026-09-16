# v4 First Offline Phase — Artifact Checklist

Date: 2026-09-16

Implemented in the current v4 offline layer:

- R Plan v4.0;
- Theory Contract v0.4;
- System Behavior Measurement Plan v4;
- experimental-variable registry v0.1;
- measurement-boundary registry v0.1;
- behavior-event schema v0.1;
- system-trajectory measurement schema v4;
- registry schemas;
- behavior-first normalization/validation module;
- deterministic system-behavior preflight;
- `R2-ARENA-TRACE-v0.3` → `RB-BEHAVIOR-EVENT-v0.1` source adapter;
- proposal / realization / read / node-execution phase separation;
- deterministic Arena trace-adapter preflight;
- adapter unit tests and CI validation;
- R5/R6 protocol v0.4;
- real-run freeze template v0.2;
- README alignment;
- migration/open-item/scope notes.

Still open before any new v4 real evidence:

- formal Jump detector freeze;
- formal operational/penetration-boundary freeze;
- registry/hash binding into new real-run manifests;
- branch-continuation-aware v4 slicing;
- exact v4 subject-evidence binding to adapter/measurement/registry hashes.

The adapter deliberately leaves Jump status as `NOT_RUN_DETECTOR_NOT_FROZEN`; successful behavior normalization is not treated as Reality Bias evidence.

No paid model call was made by this update.