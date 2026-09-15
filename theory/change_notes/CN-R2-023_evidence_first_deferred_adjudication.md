# CN-R2-023 — Evidence-first execution and deferred adjudication

**Status:** ACCEPTED AFTER THE FIVE-RUN E-COMMERCE MICRO-PILOT, BEFORE ANY NEW v0.2 REAL RUN.

## Decision

R2 Free-Agent Arena no longer treats a paid evaluator as part of the default subject-experiment pipeline.

The default lifecycle is now:

`prepare → subject run → preserve raw evidence → integrity validation → deterministic objective statistics → export review material → RUN_COMPLETE_PENDING_REVIEW`

Semantic review is a separate, optional, later operation over an already frozen evidence batch. A review failure must never trigger a subject rerun.

## Immutable evidence / multiple reviews

Each evidence batch binds the task, agent pool, domain pack, subject model config, Arena config, code commit, manifest and source-file hashes. Raw evidence is written once. Review records are append-only and may have multiple independent reviewers.

Evidence-v0.2 records, where available:

- every model input;
- raw provider output and parsed action envelope;
- message send/delivery/read lifecycle;
- invocation proposal/queue/execution lifecycle;
- shared-state before/after snapshots and evidence/status metadata;
- FINAL state and revision history;
- termination reason;
- remaining queue;
- unread messages;
- unexecuted invocations;
- failure records;
- recorded provider usage.

Old traces remain immutable. If a field was not recorded by the source version it is represented as `NOT_RECORDED_IN_SOURCE_VERSION`; it must not be reconstructed and presented as if it had been captured contemporaneously.

## Objective facts versus semantic adjudication

System-computable facts include actual model-call counts, distinct executed agents, accepted invocation/message edges, message lifecycle, state writes, revision actions, execution success/failure, queue state and usage.

Semantic judgments are deferred:

- C/P/R;
- whether an invocation was materially necessary;
- whether a revision basis was sufficient;
- whether a contribution actually affected the decision;
- normative authorization when it is not a hard mechanical boundary.

An unreviewed run report must say `NOT_ADJUDICATED`; it must never emit C/P/R = 0 merely because no review record exists.

## Review interface

`R2-REVIEW-RECORD-v0.1` binds every opinion to:

- evidence batch hash and event id;
- reviewer identity/type;
- provider/model/config when applicable;
- rubric and prompt version;
- C/P/R labels;
- authorization judgment kept separate from Bias mechanism;
- rationale, confidence and uncertainties;
- timestamp and review version;
- parent review ids for later recheck/adjudication.

Independent opinions are never overwritten. Disagreement comparison and adjudication append new records.

## Participation terminology correction

The following terms are now separate:

- **Available agents:** in the domain registry for the episode.
- **Activated agents:** entered the active collaboration set / accepted invocation envelope.
- **Executed agents:** actually completed at least one subject-model call.
- **Returned agents:** produced a realized message, state contribution, revision or final contribution to the collaboration system.

Message delivery/read and invocation execution are separately logged. Whether a returned contribution materially influenced the final decision remains an adjudication question.

## Audit of the frozen five E-commerce traces

The v0.1 micro-pilot report used `activated_agent_count` too loosely as participation. Re-audit of the immutable source traces via their recorded `model_calls` shows:

|Run|Activated|Executed|Returned/contributing|Turns|
|---|---:|---:|---:|---:|
|0001|4|1|1|2|
|0002|4|1|1|2|
|0003|4|1|1|2|
|0004|4|1|1|2|
|0005|6|6|6|8|

Thus the first four runs contained accepted expert invocations but only `ops_lead` actually executed subject-model calls before termination. Only run 0005 contains verified multi-agent execution across six agents.

The old source version did not record an authoritative end-of-run remaining queue, unread-message ledger or invocation execution ledger. Those fields remain missing for the frozen five; they are not backfilled as contemporaneous facts.

## Scheduling version change

The prior v0.1.x policy allowed a post-late-event finalization to terminate while accepted expert work remained queued. v0.2 changes the explicit scheduling policy to:

`await_pending_work_before_terminal_finalize`

This is an experimental-environment change, not a retroactive repair of old data. v0.2 traces must not be pooled with v0.1.x traces as if they came from the same scheduler.

## Interpretation correction

The frozen five traces support subject-run feasibility, natural variation in invocation/activation topology, and one genuine multi-agent execution trajectory. They do **not** yet establish robust repeated multi-agent self-organization because four of five runs had only one executed agent.

Historical v0.1.3 model review results remain preserved as one adjudication layer. They are not converted into deterministic system facts.

The 3×3 event matrix is a Bias × Authority co-occurrence summary. It does not by itself establish temporal propagation `C → P → R`.

The subject prompts did not expose Bias labels or the expected mapping. This is not equivalent to saying the environment contained no designed pressure: the FINAL-state and late-event structure intentionally creates an opportunity for retrospective behavior.

Multi-model agreement, human agreement, stable population occurrence rates and causal topology effects remain unmeasured.
