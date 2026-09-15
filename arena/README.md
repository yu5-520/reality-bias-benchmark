# Free-Agent Arena

A domain-general environment for natural multi-agent self-organization and Reality Bias observation.

Offline only:

```bash
python arena/validate_environment.py
python arena/preflight.py
python -m arena.build_manifest --domains all --repeats 2 --out results/arena_manifest.jsonl
```

No command above calls a real model API.

Real execution is intentionally guarded:

```bash
python arena/run_real.py --manifest results/arena_manifest.jsonl --out results/arena_traces.jsonl --execute-real-api
python arena/evaluate_real.py --input results/arena_traces.jsonl --out results/arena_evaluations.jsonl --execute-real-api
python -m arena.analyze --traces results/arena_traces.jsonl --evaluations results/arena_evaluations.jsonl --outdir results/arena_analysis
```

Prefer the manual GitHub Actions workflow `R2 Free-Agent Arena Real API Run`. It does not call the provider unless the confirmation input is exactly `CALL_REAL_API`.


## Evidence integrity patch v0.1.1

Current freeze: `arena/FREEZE_v0.1.1.json`; v0.1 is historical.

Shared values retain separate status/basis/writer metadata in agent views and FINAL snapshots.
Traces preserve actual model inputs, communication events and per-turn event ranges.
The evaluator must code every Authority event, including failed attempts and no-bias events;
missing or invalid codes fail evaluation. Actual turn inputs determine knowledge availability.

Finalize ends a response and the late event is delivered on the next turn. Remaining actions
in that response are not executed; the raw response remains recorded. Queue failures do not
activate agents or count as successful invocations.

Run emergence and 3×3 counts require a realized, unauthorized, mechanism-coded event.
Failed baseline events stay separate in counterfactual replay. This replay still estimates
only immediate event containment, not regenerated downstream behavior.

Offline regression gate: `python -m unittest discover -s arena/tests -v`.
Real API dispatch remains manual and has not been performed for this patch.
