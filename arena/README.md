# Free-Agent Arena

A domain-general environment for natural multi-agent self-organization and Reality Bias observation.

Current Base runtime: **R2-FREE-AGENT-ARENA-v0.3.2** (`arena/config/arena_v0.3.json`).

## Offline validation

```bash
python arena/validate_environment.py
python arena/preflight.py
python -m unittest discover -s arena/tests -v
python -m arena.build_manifest --domains all --repeats 2 --arena-config arena/config/arena_v0.3.json --out results/arena_manifest.jsonl
python -m arena.branch_recovery_preflight --outdir results/branch_recovery_preflight
python -m arena.build_branch_baseline_manifest --repeats 2 --model-config arena/config/model_deepseek_v0.2.json --out results/r5r6_baseline_manifest_candidate.jsonl
python -m arena.orchestration_preflight --outdir results/orchestration_preflight
python -m arena.build_orchestration_manifest --repeats 2 --out results/r7_orchestration_manifest_candidate.jsonl
```

No command above calls a real model API.

Subject collection and semantic evaluation are separate operations. A subject run does not automatically call a paid evaluator. Real provider execution is separately guarded and requires an explicit provider/model binding, call/spending limits, and a dedicated authorization phrase.

## Evidence-first runtime

The Arena records actual model inputs, raw outputs, parsed actions, message lifecycle, invocation execution, runtime snapshots, state history, FINAL/revision state, termination state, remaining work, failures and usage where supported by the source version.

Current v0.3.2 semantics:

- plan FINAL and episode termination are separate;
- the late event is delivered after first FINAL;
- observation continues until quiescence or an explicit budget/safety condition;
- budget censoring is not treated as natural completion;
- semantic review is deferred and append-only;
- historical v0.1/v0.2/v0.3 conditions are not silently pooled.

## Structural measurement boundary

Deterministic code may locate structural candidates such as epistemic-status change, provenance loss, goal/scope change, invocation expansion, reopen/revision, lineage and feedback topology.

It must not silently convert those structures into semantic C/P/R truth.

Forward trajectory measurement:

- `../theory/theory_contract_v0.3.md`
- `../docs/trajectory_dynamics_measurement_plan_v3.md`
- `trajectory_measurement_v3.py`

## Minimal experimental-control layer

The Arena contains an **intervention-off-by-default** control layer for R5/R6 work:

```text
Observe → Freeze → Replay deterministic Arena state → Intervene → Branch → Measure
```

Forward files:

- `experimental_control.py`
- `branch_protocol.py`
- `branch_recovery_preflight.py`
- `trajectory_measurement_v3.py`
- `config/experimental_control_v0.1.json`
- `tests/test_experimental_control.py`
- `tests/test_branch_protocol.py`
- `tests/test_branch_recovery_preflight.py`
- `../docs/experimental_control_layer_v0.2.md`
- `../docs/R5_R6_branch_intervention_recovery_protocol_v0.2.md`

Evidence interfaces:

- `../schemas/experimental_branch_manifest_v0.2.schema.json`
- `../schemas/anchor_selection_record_v0.1.schema.json`
- `../schemas/branch_trajectory_measurement_v3.schema.json`
- `../schemas/branch_trajectory_comparison_v3.schema.json`
- `../schemas/recovery_record_v0.1.schema.json`

Historical `experimental_branch_manifest_v0.1.schema.json` and protocol v0.1 remain preserved.

### Parent versus branch-start identity

For an intervention branch:

```text
frozen parent S_t --ΔX--> branch start S'_t --> continuation
```

v0.2 binds both:

- `parent_state_hash`
- `branch_start_state_hash`
- `parent_turn` / `branch_start_turn`
- `parent_event_count` / `branch_start_event_count`

This prevents a changed post-intervention state from being mislabeled as the unchanged parent and allows Measurement v3 to slice continuation-only events deterministically.

A restored Arena state does **not** mean provider-internal randomness or hidden model state was replayed. Repeated continuations from one parent are new probabilistic branches and receive separate evidence identities.

## R5/R6 offline branch preflight

`branch_recovery_preflight.py` runs a zero-provider-call fixture that:

1. builds a baseline trajectory;
2. freezes a structural-only anchor;
3. creates an unchanged control branch;
4. changes one state-status field in the intervention branch;
5. resumes both branches from the same frozen parent identity;
6. verifies the intervention is visible downstream;
7. emits branch Measurement-v3 records and a structural comparison;
8. emits a recovery record while semantic R remains `NOT_ADJUDICATED`.

This is instrumentation validation only and is never counted as scientific subject evidence.

## R5/R6 guarded real baseline phase

Real R5/R6 work is deliberately split into two paid phases. Only **Phase A infrastructure** is currently prepared.

Phase A:

```text
real baseline subject run
  → before/after-turn state snapshots
  → frozen structural candidate index
  → structural-only replayable anchor selection
  → STOP before any branch continuation
```

Files:

- `config/r5r6_anchor_rule_v0.1.json`
- `anchor_selection.py`
- `build_branch_baseline_manifest.py`
- `run_branch_baseline_real.py`
- `tests/test_anchor_selection.py`
- `tests/test_branch_baseline_manifest.py`
- `tests/test_r5r6_real_guard.py`
- `../.github/workflows/r5r6-baseline-snapshot-real.yml`
- `../docs/R5_R6_real_run_freeze_template_v0.1.md`

The frozen structural rule currently targets the first replayable `HIGH_CERTAINTY_STATE_WRITE_CANDIDATE` by event index. That selection is a structural branch candidate only; it does not itself establish C, Jump truth, unauthorized promotion, penetration or causal importance.

Baseline collection preserves `ANCHOR_SELECTED`, `NO_ELIGIBLE_STRUCTURAL_ANCHOR`, and non-complete runs rather than regenerating until a convenient anchor appears.

Real Phase-A execution requires the exact phrase `CALL_REAL_R5R6_BASELINE_API`, a resolved provider/model config, positive call cap, matching currency, and an explicit positive spending ceiling. **Phase-A authorization never authorizes Phase-B branch continuation.**

## Minimal structured / system-owned routing condition

R7 has an offline engineering condition on the same Arena substrate:

- `structured_routing.py`
- `config/structured_ecommerce_v0.1.json`
- `tests/test_structured_routing.py`
- `../docs/R7_orchestration_protocol_v0.1.md`

The v0.1 E-commerce chain is:

```text
ads → inventory → finance → ops_lead
```

The full domain Agent registry remains unchanged, but executable routing is system-owned for this condition. Dynamic `invoke_agent` proposals are preserved inside `provider_response.structured_routing.original_subject_envelope` and blocked from operational realization. This keeps proposal evidence separate from realized graph expansion.

The condition is an experimental policy, not a production workflow system, and it does not establish that structured routing is safer or better than Free Routing.

## R7 offline comparison bundle

`orchestration_preflight.py` executes a zero-provider-call scripted comparison and writes:

- `free_trace.json`
- `structured_trace.json`
- `comparison.json`
- `SUMMARY.txt`

`orchestration_compare.py` normalizes both conditions into one evidence shape containing topology, participation, proposal counts, blocked-action counts and realized-action counts.

The structured fixture deliberately proposes an extra `invoke_agent`; the policy preserves that original proposal while blocking operational realization. Fixture scripts are not identical, so these mechanical deltas are explicitly `ENGINEERING_ONLY_NOT_SCIENTIFIC_EVIDENCE`.

## Paired future R7 manifest and real-run guard

`build_orchestration_manifest.py` prepares exactly two rows per trial:

```text
pair_id
  ├── EMERGENT_FREE_ROUTING
  └── STRUCTURED_SYSTEM_OWNED_ROUTING
```

Within each pair it binds the same task, Agent pool, Arena config, model config and logical-seed identity. Pair execution order is counterbalanced across trials. Prepared rows remain:

`CANDIDATE_UNTIL_EXPLICIT_REAL_RUN_FREEZE_AND_API_AUTHORIZATION`

The future real-run path is guarded by:

- `run_orchestration_real.py`
- `cost_budget.py`
- `../.github/workflows/r7-orchestration-paired-real.yml`
- `../docs/R7_real_run_freeze_template_v0.1.md`

Real execution requires `CALL_REAL_R7_API`, a named provider/model config, positive call cap, matching currency, and an explicit positive spending ceiling. Repository-update instructions do not satisfy that gate.

## Historical notes

- v0.1.x historical method-development samples remain frozen.
- v0.2 introduced evidence-boundary improvements.
- v0.3 separated FINAL from episode termination and added shared R2-R4 structural runtime behavior.
- v0.3.2 hardened strict JSON serialization after v0.3.1 malformed-response failures; it did not rewrite old traces.
- branch-manifest v0.1 remains historical; forward intervention work uses v0.2 parent/start separation.

[Shared runtime notes](../docs/R234_runtime_v0.3.md) · [CN-R-025](../theory/change_notes/CN-R-025_structural_runtime_v03.md)
