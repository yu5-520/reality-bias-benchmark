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
