# R7 execution fixtures

This directory contains the fail-closed configuration contracts for the first formal R7 Structural Inertia Control / Localized Recovery design.

## Three conditions

- `C1_ONE_SHOT` — one experiment-origin prompt-visible exposure followed by free continuation.
- `C2_PERSISTENT_FIELD` — the same semantic correction re-exposed on each eligible downstream turn inside the fixed horizon.
- `C3_ALR` — rollback to the exact pre-J0 checkpoint, re-execution of the natural authority-ancestor turn, and one localized authority-status transform only if the target commit naturally reappears.

The common comparison object is the same frozen natural J0 and post-J0 reference parent. C3 necessarily starts from the exact pre-J0 recovery checkpoint because reopening the transition that created J0 is the recovery mechanism; this must not be misreported as all three arms literally starting from the same runtime snapshot.

## Files

- `r7_three_arm_fixture.example.json` — exact frozen source/J0/checkpoint/horizon and arm semantics. Current protocol: `RB-R7-STRUCTURAL-INERTIA-CONTROL-v1.2`.
- `r7_formal_subject_gate_v0.1.json` — formal paid-run gate defaults and integrity requirements. This file is a gate contract only and has `authorization_status: NOT_AUTHORIZED`.

## Integrity rules

Before a formal provider call, the runtime must verify:

- exact frozen source artifact digests;
- exact common post-J0 reference parent and pre-J0 C3 checkpoint;
- same task, agent registry, model/provider binding, semantic correction and post-Jump horizon;
- provider hidden-state replay is not claimed;
- C3 non-reproduction is preserved rather than retried away;
- raw evidence is frozen and uploaded before structural derivation;
- semantic CPR review remains deferred;
- no automatic paid evaluator is in the subject chain.

Engineering smoke evidence and real-model subject evidence are different evidence roles and cannot be interchanged.

The formal subject workflow remains dormant unless a manual dispatch supplies the exact external authorization phrase required by the guarded runner. Merely merging these fixtures does not authorize paid calls.
