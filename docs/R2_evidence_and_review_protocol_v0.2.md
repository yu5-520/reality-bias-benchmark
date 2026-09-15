# R2 Evidence & Deferred Review Protocol v0.2

## 1. Default execution lifecycle

A subject experiment ends without a paid semantic evaluator.

`PREPARED → SUBJECT_RUNNING → RUN_COMPLETE_PENDING_REVIEW`

The post-run system steps are deterministic:

1. preserve manifest and raw traces;
2. validate task/agent/model/config/hash bindings;
3. compute objective execution statistics;
4. export event-organized review packets plus an indexed full-evidence store;
5. freeze the evidence-batch hash.

A later review is a separate process:

`PENDING_REVIEW → REVIEWING → REVIEWED`

Review failure does not alter the subject evidence state and never causes a subject rerun.

## 2. Evidence batch contract

The batch metadata binds:

- code commit SHA;
- manifest hash;
- raw trace hash;
- task hash;
- agent-pool hash;
- domain-pack hash;
- Arena config version/hash;
- subject model config version/hash.

The raw trace records model inputs, raw outputs, parsed envelopes, events, state snapshots, message/invocation/execution ledgers, failures, remaining queue and usage when supported by the source trace version.

Legacy data is immutable. Missing instrumentation is explicitly missing, not reconstructed as if it were originally logged.

## 3. Objective statistics

`objective_stats.jsonl` contains only deterministic facts. In particular, it separates:

- available agents;
- activated agents;
- executed agents;
- returned/contributing agents;
- activation topology;
- execution topology;
- messages sent/delivered/read;
- state writes/revisions;
- unread messages;
- unexecuted invocations;
- termination/failure/usage.

Decision impact remains `NOT_ADJUDICATED` unless a review layer supplies an opinion.

## 4. Review packets

`review_packets.jsonl` is organized by Authority-bearing event. Repeated source evidence is referenced through `review_evidence_index.jsonl` rather than duplicated into every packet.

A packet contains structural facts and references but initializes semantic fields to `NOT_ADJUDICATED`.

No subject rerun is required when a rubric, reviewer model, prompt version or adjudication strategy changes.

## 5. Append-only review records

Every independent opinion conforms to `R2-REVIEW-RECORD-v0.1` and binds to the exact evidence-batch hash and event id. Later reviewers may be humans or model agents. Reviewer/model/config/rubric/prompt versions are stored so measurement-method changes remain auditable.

Independent records are not overwritten. A disagreement resolution creates a new `recheck` or `adjudication` record with parent review ids.

## 6. API boundaries

Subject API execution: `.github/workflows/r2-free-agent-arena-real.yml`.

This workflow produces evidence and stops at `PENDING_REVIEW`; it never calls `arena/evaluate_real.py` or any paid semantic evaluator.

Deferred API review: `.github/workflows/r2-arena-review-existing.yml`.

Its default is `PREPARE_ONLY`. Provider calls require explicit `CALL_REVIEW_API` and operate on an existing evidence artifact.

## 7. Versioning / scheduler rule

Arena v0.2 uses `await_pending_work_before_terminal_finalize`. This allows already-accepted expert work to execute before terminal shutdown.

Because v0.1.x used a different terminal scheduling policy, v0.1.x and v0.2 are distinct experimental versions and must not be silently pooled.
