# Process Reality v5 Fresh Whole-Process Run Design v0.1

Date: 2026-09-18  
Status: FROZEN DESIGN CANDIDATE / OFFLINE-READY / REAL PROVIDER NOT AUTHORIZED

## 1. Objective

The first fresh v5 batch should collect reusable full-process evidence rather than reproduce the historical Jump/specificity stack by default.

Primary collection chain:

\`\`\`text
Natural multi-Agent run
  -> freeze raw evidence
  -> integrity validation
  -> v5 structural index
  -> support / pool / exposure candidates
  -> localized semantic audit later
\`\`\`

No driver probe, control-surface intervention, recovery or CPR adjudication is part of the base subject batch.

## 2. Batch geometry

Initial fresh batch:

- domain: ecommerce;
- subject condition: natural / unmanipulated;
- planned repeats: 3;
- Arena runtime: existing R2-FREE-AGENT-ARENA-v0.3.2;
- model binding: existing DeepSeek v0.2 config;
- automatic paid evaluator: false;
- all-event semantic Judge: false;
- outcome-aware rerun: forbidden.

The repeat count is a first reusable process batch, not a population-general sample.

## 3. Why the Arena runtime is retained

The existing runtime already records the evidence needed for v5 structural derivation:

- actual model inputs and outputs;
- per-turn runtime snapshots;
- shared state and shared-state metadata;
- writer and source event index for shared-state entries;
- action events with before/after state;
- message send/read ledger;
- invocation send/read ledger;
- event-index ranges for each model call;
- final/revision state;
- queue/termination state;
- journals, hashes and usage.

The v5 update therefore does **not** alter Agent prompts or require Agents to self-report attention.

## 4. Critical measurement boundary

The runtime can mechanically establish that an addressable shared-state object was **visible** to a downstream Agent.

It cannot mechanically establish that the Agent semantically adopted that object as a premise.

Therefore fresh v5 evidence must separate:

\`POOL_VISIBILITY_OBSERVED\`

from:

\`DIRECT_POOL_CONSUMPTION\`

The latter requires localized semantic audit or stronger source-backed relation evidence.

## 5. Core fresh-run observables

Every run should permit deterministic extraction of:

1. state-materialization events;
2. source event / writer / state-key identity;
3. first later visibility of that state;
4. repeated visibility opportunities;
5. distinct downstream visible actors;
6. structural activity after visibility;
7. first Structural Support candidate;
8. first Stable Shared Pool candidate;
9. first Structural Exposure candidate;
10. source-to-exposure turn/event distance;
11. upstream provenance refs;
12. candidate downstream closure;
13. candidate semantic-audit window.

These are structural candidates, not semantic truth.

## 6. Candidate definitions for Batch001

### Structural Support candidate

A realized shared-state write/revision becomes a support candidate when at least one later model call sees the exact state entry through metadata bound to the originating event index.

### Stable Shared Pool candidate

A support candidate becomes a pool candidate when the exact state entry is visible in at least two later model calls or to at least two distinct downstream actors.

This is a structural addressability/reuse candidate. It does not mean true, confirmed or semantically adopted.

### Structural Exposure candidate

A pool candidate becomes an exposure candidate when repeated/multi-actor visibility co-occurs with later realized process activity inside the observed descendant window.

This rule identifies a cheap scouting anchor only. It does not establish causal dependence.

## 7. First-node readouts

The batch records:

- first_support_candidate_ref;
- first_pool_candidate_ref;
- first_exposure_candidate_ref;
- source_to_support_turn_distance;
- source_to_pool_turn_distance;
- source_to_exposure_turn_distance.

If no candidate is observed, status is \`NOT_OBSERVED_WITHIN_RECORDED_WINDOW\`, not zero mechanism.

## 8. Semantic audit surface

The structural index should emit a bounded candidate window around support/pool/exposure candidates.

Semantic review is deferred until after raw freeze and structural indexing.

Audit expansion is allowed only when a source-backed relation crosses the candidate boundary, and the expansion must be recorded.

## 9. Optional phases are off

Batch001 base collection does not include:

- \`fact -> unconfirmed\`;
- source withdrawal;
- dependency invalidation;
- pool revision;
- control-surface comparison;
- recovery;
- CPR adjudication;
- paid semantic evaluator.

Those can be attached later to the same frozen natural evidence only under separately frozen designs.

## 10. Data reuse

The same frozen runs may later support:

- R2-R4 formation analysis;
- support/pool/exposure localization;
- audit-surface reduction measurement;
- R5 probe planning;
- R6 upstream/downstream trace;
- R7 repair planning;
- R8/R9 append-only semantic review.

## 11. Authorization boundary

Repository preparation, preflight, manifest generation and CI do not authorize paid execution.

Real provider execution requires an exact future authorization record bound to this batch design and the final code/config hashes.
