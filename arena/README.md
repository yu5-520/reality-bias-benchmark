# Process Reality v5 Whole-Process forward layer

The current forward subject profile is **Process Reality v5 Whole-Process Batch001**.

Forward v5 preparation files:

- `../docs/v5_fresh_whole_process_design_v0.1.md`
- `../configs/v5_whole_process_ecommerce_batch001_v0.1.json`
- `build_v5_whole_process_manifest.py`
- `v5_whole_process_index.py`
- `v5_whole_process_preflight.py`
- `tests/test_v5_whole_process.py`

The existing Arena engine and Agent prompts are intentionally unchanged. v5 derives Structural Support / Stable Shared Pool / Structural Exposure candidates from the runtime evidence already recorded by the Arena.

Important boundary:

`POOL_VISIBILITY_OBSERVED != DIRECT_POOL_CONSUMPTION`

Shared-state visibility is mechanically observable. Semantic adoption/direct consumption remains deferred append-only audit.

Fresh Batch001 is prepared as three natural ecommerce repeats with no intervention, no recovery, no CPR adjudication and no automatic paid evaluator.

Offline preflight:

```bash
python -m arena.v5_whole_process_preflight --outdir results/v5_whole_process_preflight
```

Real provider execution is not authorized by repository preparation. The future exact authorization phrase is `CALL_REAL_V5_WHOLE_PROCESS_API`.

---

# Free-Agent Arena

A domain-general environment for natural multi-agent self-organization and Reality Bias observation.

Current Base runtime: **R2-FREE-AGENT-ARENA-v0.3.2** (`arena/config/arena_v0.3.json`).

## Offline validation

```bash
python arena/validate_environment.py
python arena/preflight.py
python -m unittest discover -s arena/tests -v
python -m arena.system_behavior_preflight --outdir results/system_behavior_preflight
python -m arena.branch_recovery_preflight --outdir results/branch_recovery_preflight
python -m arena.build_branch_baseline_manifest --repeats 2 --model-config arena/config/model_deepseek_v0.2.json --out results/r5r6_baseline_manifest_candidate.jsonl
python -m arena.orchestration_preflight --outdir results/orchestration_preflight
python -m arena.build_orchestration_manifest --repeats 2 --out results/r7_orchestration_manifest_candidate.jsonl
```

No command above calls a real model API.

Subject collection and semantic evaluation are separate operations. Real provider execution is guarded by provider/model binding, call/spending limits and an exact authorization phrase.

## Evidence-first runtime

The Arena records actual model inputs, raw outputs, parsed actions, message lifecycle, invocation execution, runtime snapshots, state history, FINAL/revision state, termination state, remaining work, failures and usage where supported by the source version.

Current v0.3.2 semantics:

- plan FINAL and episode termination are separate;
- late events remain observable after first FINAL where configured;
- observation continues until quiescence or an explicit budget/safety condition;
- budget censoring is not natural completion;
- semantic review is deferred and append-only;
- historical v0.1/v0.2/v0.3 conditions are not silently pooled.

## Measurement hierarchy v4

Forward measurement now uses:

```text
System Trajectory        = experimental / analysis unit
Node / Boundary          = measurement location
Behavior / Transition    = primary observable
C / P / R                = post-hoc semantic annotation
```

Forward theory/measurement:

- `../docs/R_Plan_v4.0.md`
- `../theory/theory_contract_v0.4.md`
- `../docs/system_behavior_measurement_plan_v4.md`

Historical trajectory layer remains preserved:

- `../theory/theory_contract_v0.3.md`
- `../docs/trajectory_dynamics_measurement_plan_v3.md`
- `trajectory_measurement_v3.py`

Deterministic code may locate behavior/state-transition candidates, but must not silently convert them into semantic C/P/R truth.

## Behavior-first layer

Forward files:

- `system_behavior.py`
- `system_behavior_preflight.py`
- `tests/test_system_behavior.py`
- `../configs/experimental_variable_registry_v0.1.json`
- `../configs/measurement_boundary_registry_v0.1.json`
- `../schemas/behavior_event_v0.1.schema.json`
- `../schemas/system_trajectory_measurement_v4.schema.json`

The default evidence chain is:

```text
Behavior Event
→ State Transition
→ structural candidate / lineage / dynamics
→ small semantic review window
```

not a requirement to reconstruct the model's complete hidden reasoning process.

## R2 / R3 / R4 are simultaneous observation layers

One frozen system trajectory may simultaneously support:

- **R2** — Behavior / Jump emergence;
- **R3** — propagation / penetration / inherited inertia;
- **R4** — retrospective / second-order R dynamics.

They are not mandatory separate subject experiments. Semantic review may occur asynchronously after evidence freeze.

## Minimal experimental-control layer

The Arena contains an intervention-off-by-default control layer:

```text
Observe → Freeze → Replay deterministic Arena state → Branch → Intervene → Measure
```

Forward branch/control files include:

- `experimental_control.py`
- `branch_protocol.py`
- `branch_recovery_preflight.py`
- `branch_plan.py`
- `run_branch_real.py`
- `derive_branch_measurements.py`
- `trajectory_measurement_v3.py`
- `../docs/experimental_control_layer_v0.2.md`
- `../docs/R5_R6_branch_intervention_recovery_protocol_v0.4.md`

Evidence interfaces include:

- `../schemas/experimental_branch_manifest_v0.2.schema.json`
- `../schemas/anchor_selection_record_v0.1.schema.json`
- `../schemas/branch_trajectory_measurement_v3.schema.json`
- `../schemas/branch_trajectory_comparison_v3.schema.json`
- `../schemas/behavior_event_v0.1.schema.json`
- `../schemas/system_trajectory_measurement_v4.schema.json`
- `../schemas/recovery_record_v0.1.schema.json`

Historical branch/protocol versions remain preserved.

### Parent versus branch-start identity

For an intervention branch:

```text
frozen parent S_t --ΔX--> branch start S'_t --> continuation
```

Forward branch manifests preserve both parent and branch-start hashes, turns and event-count boundaries.

A restored Arena state does not mean provider-internal randomness or hidden model state was replayed.

## R5/R6 offline branch preflight

`branch_recovery_preflight.py` remains an engineering-only zero-provider fixture that validates:

- baseline trajectory;
- branchable structural anchor;
- unchanged control branch;
- one-variable intervention branch;
- deterministic continuation slicing;
- structural comparison;
- recovery-record plumbing.

It is not scientific subject evidence.

## R5/R6 guarded real Phase A

Phase A infrastructure is prepared and uses the forward selector:

- `config/r5r6_anchor_rule_v0.2.json`
- `anchor_selection.py`
- `build_branch_baseline_manifest.py`
- `run_branch_baseline_real.py`
- `tests/test_anchor_selection.py`
- `tests/test_branch_baseline_manifest.py`
- `tests/test_r5r6_real_guard.py`
- `../.github/workflows/r5r6-baseline-snapshot-real.yml`
- `../docs/R5_R6_real_run_freeze_template_v0.2.md`

The v0.2 rule targets the first replayable `HIGH_CERTAINTY_STATE_WRITE_CANDIDATE` while requiring the exact post-turn snapshot to be nonterminal **and to contain pending continuation work**.

Therefore:

> **nonterminal snapshot ≠ automatically branchable snapshot**

This selector is structural only. It does not establish C, Jump truth, unauthorized promotion, penetration or causal importance.

Phase-A real execution requires exact phrase:

`CALL_REAL_R5R6_BASELINE_API`

plus resolved provider/model, positive call cap, matching currency and positive spending ceiling.

## R5/R6 guarded real Phase B

Phase B infrastructure is also prepared.

Files:

- `branch_plan.py`
- `run_branch_real.py`
- `derive_branch_measurements.py`
- `tests/test_branch_plan.py`
- `tests/test_r5r6_branch_real_guard.py`
- `tests/test_branch_measurement_derivation.py`
- `../.github/workflows/r5r6-frozen-parent-branch-real.yml`
- `../docs/R5_R6_branch_intervention_recovery_protocol_v0.4.md`

The first implemented MID intervention family changes exactly one field:

```text
shared_state_metadata[selected_key].status
high-certainty → provisional
```

The experiment is now registered as `EPISTEMIC_STATUS_DOWNGRADE` in the v0.1 experimental-variable registry.

Phase-B real execution requires exact phrase:

`CALL_REAL_R5R6_BRANCH_API`

plus the frozen Phase-A source package, exact plan/model/config/code bindings, positive call cap and explicit spending ceiling.

Phase-A authorization never authorizes Phase B.

## Multi-position R5 forward design

R5 now distinguishes:

- `PRE` — formation antecedents before Jump;
- `MID` — realization / containment after or around Jump;
- `POST` — stabilization after propagation/penetration.

The current status-downgrade path is one MID experiment, not the definition of all R5 work.

All future confirmatory manipulations should bind:

- `../configs/experimental_variable_registry_v0.1.json`
- `../configs/measurement_boundary_registry_v0.1.json`

## Anchor classes

Forward conceptual anchor classes are:

- `ANTECEDENT_ANCHOR`;
- `TRANSITION_ANCHOR`;
- `PENETRATION_ANCHOR`;
- `CHALLENGE_RECOVERY_ANCHOR`.

The current `HIGH_CERTAINTY_STATE_WRITE_CANDIDATE` selector is a concrete `TRANSITION_ANCHOR` selector for the first MID experiment.

## R7 system-structure boundary

The existing Free-vs-Structured comparison remains the first system-structure condition.

Files:

- `structured_routing.py`
- `config/structured_ecommerce_v0.1.json`
- `orchestration_compare.py`
- `orchestration_preflight.py`
- `build_orchestration_manifest.py`
- `run_orchestration_real.py`
- `../docs/R7_orchestration_protocol_v0.1.md`
- `../.github/workflows/r7-orchestration-paired-real.yml`

R7 is interpreted as a system-structure / boundary-condition family, not a claim that one architecture is universally better.

Real R7 execution requires exact phrase:

`CALL_REAL_R7_API`

plus the frozen provider/model/cost/code conditions.

## Historical notes

- v0.1.x method-development samples remain frozen;
- v0.2 improved the evidence boundary;
- v0.3 separated FINAL from episode termination;
- v0.3.2 hardened strict JSON serialization;
- branch manifest v0.1 remains historical; forward branch work uses v0.2 parent/start separation;
- R Plan v3.2 / Theory v0.3 / Measurement v3 remain the preceding trajectory-dynamics layer;
- v4 adds the system-behavior hierarchy without rewriting prior evidence.

Repository planning or generic “执行/继续” instructions do not authorize paid provider calls.
