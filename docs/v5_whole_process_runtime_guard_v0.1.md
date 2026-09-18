# Process Reality v5 Whole-Process Runtime Guard v0.1

Date: 2026-09-18  
Status: PREPARED / REAL PROVIDER EXECUTION DISABLED UNTIL EXPLICIT AUTHORIZATION

## 1. Purpose

This runtime guard closes the fresh Whole-Process Batch001 execution path without authorizing it.

Prepared chain:

```text
frozen batch design
  -> immutable manifest
  -> explicit paid authorization gate
  -> natural subject runs
  -> raw evidence freeze
  -> deterministic v5 structural derivation
  -> reusable artifact bundle
```

No semantic evaluator, driver probe, recovery or CPR adjudication is called by this chain.

## 2. Existing Arena engine

The subject runner reuses:

- `arena.engine.run_arena_once`;
- `arena.journal.Journal`;
- `arena.cost_budget.BudgetedProvider`;
- `arena.providers.provider_from_config`.

It does not introduce a second multi-Agent runtime.

## 3. Authorization

Exact phrase:

`CALL_REAL_V5_WHOLE_PROCESS_API`

Execution also requires all of:

- `--execute-real-api`;
- positive per-run call cap;
- positive per-run spending ceiling;
- positive global spending ceiling;
- global ceiling large enough to cover all planned symmetric run ceilings;
- exact manifest/config/code bindings;
- provider credential.

The frozen design file itself remains non-authorizing.

Generic instructions such as `execute`, `continue`, `run the plan`, repository merge or CI success do not satisfy the gate.

## 4. Subject output

The runner preserves:

- authorization record;
- traces;
- journals;
- before/after-turn snapshots;
- error records;
- run summary;
- model/provider/config/hash bindings.

Semantic review is `DEFERRED_APPEND_ONLY`.

## 5. Freeze boundary

Raw evidence is frozen before v5 structural indexing.

The freeze record binds:

- manifest SHA256;
- traces SHA256;
- authorization-record SHA256;
- summary SHA256;
- journal hashes;
- snapshot hashes;
- code/config/theory/measurement/scout/profile hashes.

## 6. Structural derivation

After freeze, deterministic indexing emits one v5 structural index per preserved trace.

The derivation may identify:

- Structural Support candidates;
- Stable Shared Pool candidates;
- Structural Exposure candidates;
- first-candidate distances;
- pool visibility opportunities.

It does not adjudicate direct semantic consumption, CPR or causal driver identity.

## 7. Workflow policy

The real workflow is `workflow_dispatch` only.

All budget inputs default to zero. Therefore even a workflow dispatch with the exact phrase still fails closed unless positive budgets are deliberately supplied.

## 8. Authorization boundary

This document and its repository implementation authorize **zero** provider calls.
