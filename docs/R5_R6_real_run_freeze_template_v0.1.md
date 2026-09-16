# R5 / R6 Real-Model Run Freeze Template v0.1

Date: 2026-09-16  
Status: TEMPLATE / NOT AUTHORIZED / NOT A FORMAL SUBJECT FREEZE

This template separates R5/R6 real-model work into two paid phases with an offline selection boundary between them.

No provider call is authorized by this document.

## 1. Phase architecture

### Phase A — Baseline Snapshot Collection

Purpose:

- run the normal Free-Agent subject condition;
- freeze deterministic Arena snapshots before/after each completed turn;
- derive structural candidates under the frozen measurement contract;
- select a replayable branch anchor using a frozen structural-only rule;
- perform **no branch continuation** and **no paid semantic evaluation**.

Current implementation candidates:

- `arena/build_branch_baseline_manifest.py`
- `arena/run_branch_baseline_real.py`
- `arena/config/r5r6_anchor_rule_v0.1.json`
- `.github/workflows/r5r6-baseline-snapshot-real.yml`

### Offline Boundary — Anchor Freeze

After Phase A evidence is frozen:

- preserve every baseline, including runs with no eligible anchor;
- never rerun a baseline merely to manufacture an eligible anchor;
- freeze the selected candidate, parent snapshot/hash, branch-start policy and intervention spec before branch outcomes exist;
- semantic Reviewer labels do not select the confirmatory anchor.

### Phase B — Branch Continuation

Purpose:

- start control/intervention branches from the same frozen parent identity;
- apply exactly the preregistered intervention to the intervention branch;
- run repeated continuations under separately authorized provider calls;
- freeze Measurement-v3 branch records and structural comparisons;
- defer semantic C/P/R/penetration/recovery adjudication.

**Phase B is not yet authorized by a Phase-A authorization record.** It requires a separate run-freeze and separate spending authorization.

## 2. Current structural anchor rule candidate

Repository candidate:

`arena/config/r5r6_anchor_rule_v0.1.json`

Current rule selects the lowest-event-index replayable:

`HIGH_CERTAINTY_STATE_WRITE_CANDIDATE`

with:

- `action_type = write_state`;
- realized event required;
- `after_turn:<candidate turn>` snapshot required;
- non-terminal snapshot required;
- semantic Reviewer labels forbidden during selection;
- branch outcomes unavailable during selection.

This is only a structural candidate rule. Selection does not establish semantic C, unauthorized epistemic promotion, Jump truth, Authority Penetration or causal importance.

## 3. Phase-A unresolved fields — MUST freeze before provider calls

- `provider`: **UNRESOLVED**
- `model/config`: **UNRESOLVED**
- `baseline run count`: **UNRESOLVED**
- `maximum subject-call budget`: **UNRESOLVED**
- `explicit spending ceiling`: **UNRESOLVED**
- `currency`: **UNRESOLVED**
- `run-start commit SHA`: **UNRESOLVED**
- `final baseline manifest hash`: **UNRESOLVED**
- `final anchor-rule hash`: bind exact repository file at run start

The workflow defaults deliberately keep provider unresolved, spending ceiling `0`, call cap `0`, and confirmation `PREPARE_ONLY`.

## 4. Phase-A paid authorization gate

Real baseline calls require all of the following:

- exact provider ID matching the chosen model config;
- exact subject model config path/version/hash;
- positive baseline run count;
- explicit positive subject-call cap;
- explicit positive spending ceiling;
- currency matching the model pricing snapshot;
- exact authorization phrase:

`CALL_REAL_R5R6_BASELINE_API`

- explicit execution of the guarded baseline job.

Generic instructions such as “执行”, “继续”, repository-update approval, or a previous R7 authorization do not satisfy this gate.

## 5. Phase-A evidence package

Each attempted baseline preserves, where available:

- manifest row and bindings;
- full subject trace;
- append-only journal;
- before/after-turn state snapshots;
- state hashes;
- usage and cost-guard records;
- run status / failure / censoring;
- deterministic structural candidate index;
- anchor-selection package or explicit no-anchor status;
- standard evidence batch outputs;
- authorization record.

No baseline is silently regenerated because it lacks an eligible anchor.

## 6. Anchor-selection outcomes

Allowed objective outcomes include:

- `ANCHOR_SELECTED`
- `NO_ELIGIBLE_STRUCTURAL_ANCHOR`
- `SKIPPED_NONCOMPLETE_BASELINE`

All are preserved.

A no-anchor result is not an experiment failure and must not trigger replacement sampling unless a later protocol explicitly preregisters a new independent collection phase.

## 7. Phase-B fields — intentionally unresolved until baseline evidence exists

- selected parent trace/evidence hash;
- selected parent state hash;
- selected candidate ID/event ref;
- intervention field/key and exact state transition;
- control/intervention replicate count;
- Jump-positive detector/version;
- primary branch metrics;
- provider/model binding;
- subject-call cap;
- spending ceiling/currency;
- exact Phase-B authorization phrase;
- final branch manifest hashes.

These fields must not be guessed before Phase-A evidence is frozen.

## 8. Measurement boundary

Current deterministic branch implementation uses:

`RB-TRAJECTORY-MEASUREMENT-v3.0.1`

and keeps semantic fields as `NOT_ADJUDICATED`.

A structural branch difference is not automatically:

- C/P/R;
- Authority Penetration;
- recovery success;
- a general causal effect.

Those claims require the separately frozen semantic/causal criteria.

## 9. Failure and censoring

- provider/transport failure is preserved;
- budget stop is preserved;
- incomplete/censored baseline is preserved;
- failed baseline is not automatically rerun;
- missing snapshot/state cannot be reconstructed as if recorded;
- branch continuation is never launched from an invalid or fabricated parent snapshot.

## 10. Current execution boundary

Offline preparation and validation may proceed without API calls.

Phase A paid collection requires explicit authorization as defined above.

Phase B branch continuation remains separately unauthorized even if Phase A is later approved and completed.
