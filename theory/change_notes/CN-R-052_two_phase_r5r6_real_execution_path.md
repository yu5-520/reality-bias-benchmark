# CN-R-052 — Two-Phase Guarded R5/R6 Real Execution Path

Date: 2026-09-16  
Status: PREPARED / ZERO PROVIDER CALLS

## 1. Change

R5/R6 real-model execution is now split into two paid phases with an offline evidence-selection boundary between them.

This is a methodological constraint, not just an implementation detail.

### Phase A

`baseline subject run → before/after-turn state snapshots → structural candidate index → structural-only replayable anchor selection`

### Offline boundary

`freeze baseline evidence → preserve no-anchor/failed/censored outcomes → freeze parent snapshot and intervention plan before branch outcomes`

### Phase B

`same frozen parent → control/intervention branch continuations → Measurement v3 → recovery/semantic review later`

Phase-A authorization does not authorize Phase B.

## 2. Why the split is required

A confirmatory R5 branch anchor must be selected before branch outcomes exist.

Running baseline discovery and intervention branches inside one unconstrained paid loop would make it easier to:

- select anchors after seeing favorable branch behavior;
- regenerate baseline trajectories that fail to produce a convenient candidate;
- blur source evidence, selection evidence and intervention evidence;
- accidentally treat one spending authorization as permission for later experimental phases.

The two-phase path makes those boundaries explicit.

## 3. Structural anchor rule

Implemented:

- `arena/config/r5r6_anchor_rule_v0.1.json`
- `arena/anchor_selection.py`
- `arena/tests/test_anchor_selection.py`

The current candidate rule selects the lowest-event-index replayable `HIGH_CERTAINTY_STATE_WRITE_CANDIDATE` under a structural-only rule.

The selector requires an `after_turn:<candidate turn>` state snapshot and can preserve `NO_ELIGIBLE_STRUCTURAL_ANCHOR` without rerunning the subject.

Selection does not establish semantic C, Jump truth, unauthorized promotion, Authority Penetration or causal importance.

## 4. Phase-A manifest and runner

Implemented:

- `arena/build_branch_baseline_manifest.py`
- `arena/run_branch_baseline_real.py`
- `arena/tests/test_branch_baseline_manifest.py`
- `arena/tests/test_r5r6_real_guard.py`
- `.github/workflows/r5r6-baseline-snapshot-real.yml`
- `docs/R5_R6_real_run_freeze_template_v0.1.md`

The runner freezes before/after-turn snapshots, trace/journal evidence, selection packages and usage/budget records.

Standard evidence-batch compatibility is preserved by writing journals beside `traces.jsonl` under the expected `.journals` path.

## 5. Phase-A paid guard

Exact authorization phrase:

`CALL_REAL_R5R6_BASELINE_API`

In addition, real execution requires:

- named provider matching model config;
- explicit model-config binding;
- explicit positive spending ceiling;
- matching currency;
- explicit positive subject-call cap;
- exact prepared manifest/hash bindings;
- `--execute-real-api`.

Workflow defaults are `PREPARE_ONLY`, provider `UNRESOLVED`, spending ceiling `0`, and call cap `0`.

Generic “执行/继续” repository instructions do not satisfy the paid-run gate.

## 6. Non-regeneration rule

Phase A preserves objective outcomes including:

- `ANCHOR_SELECTED`;
- `NO_ELIGIBLE_STRUCTURAL_ANCHOR`;
- `SKIPPED_NONCOMPLETE_BASELINE`;
- provider failure;
- budget censoring/stop.

A baseline is not automatically regenerated merely because it does not yield a branchable candidate.

## 7. Current boundary

Only the Phase-A infrastructure is prepared.

No real provider call has been dispatched by this update.

Phase-B branch continuation still requires future evidence-dependent manifest preparation and a separate explicit spending authorization after baseline evidence is frozen.
