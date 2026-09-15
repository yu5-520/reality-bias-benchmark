# Free-Agent Arena

A domain-general environment for natural multi-agent self-organization and Reality Bias observation.

Current Base runtime: **R2-FREE-AGENT-ARENA-v0.3.2** (`arena/config/arena_v0.3.json`).

## Offline validation

```bash
python arena/validate_environment.py
python arena/preflight.py
python -m unittest discover -s arena/tests -v
python -m arena.build_manifest --domains all --repeats 2 --arena-config arena/config/arena_v0.3.json --out results/arena_manifest.jsonl
```

No command above calls a real model API.

Real execution is intentionally guarded:

```bash
python arena/run_real.py --manifest results/arena_manifest.jsonl --out results/arena_traces.jsonl --execute-real-api
```

Subject collection and semantic evaluation are separate operations. A subject run does not automatically call a paid evaluator. Any real provider run requires explicit authorization and a spending ceiling outside this README command list.

## Evidence-first runtime

The Arena records actual model inputs, raw outputs, parsed actions, message lifecycle, invocation execution, runtime snapshots, state history, FINAL/revision state, termination state, remaining work, failures and usage where supported by the source version.

Current v0.3.2 semantics:

- plan FINAL and episode termination are separate;
- the late event is delivered after first FINAL;
- observation continues until quiescence or an explicit budget/safety condition;
- budget censoring is not treated as natural completion;
- semantic review is deferred and append-only;
- historical v0.1/v0.2/v0.3 conditions are not silently pooled.

Offline regression gate:

```bash
python -m unittest discover -s arena/tests -v
```

## Structural measurement boundary

Deterministic code may locate structural candidates such as epistemic-status change, provenance loss, goal/scope change, invocation expansion, reopen/revision, lineage and feedback topology.

It must not silently convert those structures into semantic C/P/R truth.

The forward trajectory model is documented in:

- `../theory/theory_contract_v0.3.md`
- `../docs/trajectory_dynamics_measurement_plan_v3.md`

## Minimal experimental-control layer

The Arena now contains an **intervention-off-by-default** control layer for future R5/R6 work:

```text
Observe → Freeze → Replay deterministic Arena state → Branch → Intervene
```

Files:

- `experimental_control.py`
- `config/experimental_control_v0.1.json`
- `tests/test_experimental_control.py`
- `../docs/experimental_control_layer_v0.1.md`

The layer can:

- capture a content-hashed deterministic Arena state snapshot;
- restore that recorded Arena state;
- bind a branch to parent trace/state hashes and an intervention hash;
- continue `run_arena_once(...)` from an explicit frozen parent state;
- emit optional before/after-turn state anchors through a callback;
- apply narrow deterministic state interventions;
- evaluate an explicit fail-closed minimal commit gate.

These hooks are optional. When omitted, `run_arena_once(...)` keeps the existing Free-Agent baseline behavior.

A restored Arena state does **not** mean provider-internal randomness or hidden model state was replayed. Repeated continuations from one parent are new probabilistic branches and must receive separate evidence identities.

## Branch experiment principle

Preferred R5 form:

```text
same frozen parent state
  ├── original continuation
  └── one preregistered intervention → branch continuation
```

The original trajectory is never overwritten.

Future R7 work may add a small structured/system-owned-routing condition over the same evidence/control substrate. That condition should remain an experimental policy, not a production workflow system.

## Historical notes

- v0.1.x historical method-development samples remain frozen.
- v0.2 introduced evidence-boundary improvements.
- v0.3 separated FINAL from episode termination and added shared R2-R4 structural runtime behavior.
- v0.3.2 hardened strict JSON serialization after v0.3.1 malformed-response failures; it did not rewrite old traces.

[Shared runtime notes](../docs/R234_runtime_v0.3.md) · [CN-R-025](../theory/change_notes/CN-R-025_structural_runtime_v03.md)
