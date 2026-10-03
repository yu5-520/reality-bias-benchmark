# Independent post-repair evidence review

The monitoring/repair system now has a separate read-only review interface. It reuses the existing dynamic CPR definitions and complete-lineage requirements without modifying the frozen natural audits or their labels. This new interface admits repair-branch evidence; it is not the historical monitor-blind natural-audit protocol, which excluded post-repair evidence.

Implementation: `stage2/route_repair/independent_review.py`. Requirements: `configs/stage2_independent_repair_review_v1.json`.

## Evidence access and separation

`RepairReviewContext` verifies the before/after graph bindings and recomputes the continuation receipt against exact source captures. The reviewer can query the complete observed-record catalog, any native object/event record, exact old or new sources, and selected source spans. No depth cutoff or selected-route cutoff is applied. Example IDs are deterministic retrieval examples, not chronological or semantic selections.

The public catalog includes the original task, all observation and graph-node identities, native clocks, rule hashes and the required review checks. It excludes the repair proposal, planner meanings, write grants, completion claim, structural candidate labels and prior audit verdicts. Native observations remain admissible evidence. The interface does not supply inferred semantic edges as reference truth.

Quotes must originate from an actual successful read. Host-owned witness IDs bind observation identity, native source locator, text hash and exact character span. The validator rejects invented/unread citations, missing pre-repair or post-exit witnesses, and a path that refers to witnesses outside its assessment.

## Review obligations

Each target requires six separate assessments:

| Check | Required question |
| --- | --- |
| Target transition | Did the disputed semantic/authority transition change in the observed continuation? |
| Old information authority | Does the old C remain active, reinterpreted, reinforced or independently reconstructed? |
| Old task permission | Does the old P continue as a required obligation, change justification or withdraw? |
| Historical re-entry | After R, what happened to those same old C/P, rather than only newly created items? |
| Transformed descendants | Did another carrier/meaning retain the problematic action implication even with different wording/hash? |
| Unrelated semantic progression | Did other semantic routes continue appropriately, beyond unchanged files or host fields? |

Assessment fields separate before/after meaning, authority effects, independent evidence and inherited support. They require a reconstructed source/consumer path, exact witnesses, limitations and not-established relationships. Read or visibility alone cannot support a positive repair assessment. Supported, negated, uncertain and not-applicable assessments remain separate; target resolution cannot be declared not-applicable to obtain overall support.

C/P/R and their coupling are taken directly from `r8_dynamic_semantic_audit_contract_v0.4.json`; semantic visibility and reconstruction rules come from `stage2_r6_grade_semantic_audit_rules_v1.json`. Their content hashes are retained in every catalog and receipt. Source-word continuity is not required. The checker does not decide whether a reviewer has interpreted a quote correctly.

## Reviewer and observation window

A host-retained `IndependentReviewerBinding` supplies reviewer identity, criteria hash and implementation separately from the report. The repair actor cannot bind itself as its own reviewer. This enforces role separation at the interface; a caller-provided Python callable is not an OS sandbox and does not by itself prove cognitive independence or semantic accuracy. A future model adapter must separately configure read-only tools, identity and audit provenance.

No reviewer is invoked without a recorded repair-agent exit and ordered native continuation. A report's closing/censor/failure boundary needs an exact read witness for a native post-exit record. Cross-clock ambiguity remains explicit. Full relevant semantic visibility, natural closure and supported target/other obligations are necessary for `REVIEW_SUPPORTS_REPAIR_WITHIN_OBSERVED_HORIZON`. Partial semantic capture, unresolved relationships, a negative assessment, active censoring or failure cannot support that aggregate outcome. Local positive findings can still be retained in a non-supporting overall review.

Even a complete accepted review remains support from the separately bound reviewer within the observed horizon. The intake validator does not establish semantic truth, universal efficacy, permission to promote a branch, or a fair comparative advantage. Same-parent method/budget/outcome freezing remains a separate prerequisite.

## Current evidence and limitations

The actual G3-X4-T2 engineering branch contains 3,386 observations across 1,237 graph nodes, including the entire 3,343-observation frozen prefix and 43 new branch observations. Six exact read/witness examples verify access to historical and new launcher, frontend and terminal-state sources. No real repair-agent exit or native continuation exists in this branch. The sealed output is therefore `PENDING_NATIVE_CONTINUATION`; no reviewer, model or native action is invoked by preparation.

Dataset: `stage2/replication_v2/independent_repair_review_preparation_v1/`. The catalog is an evidence index, not a claim of complete semantic capture. The twelve interface tests use explicit synthetic traces and scripted reviewer reports. They validate intake behavior, including a supported-report path, but are not independent semantic evaluations of the actual experiment.

This implements evidence access, reviewer binding, report validation and outcome gating. Agent planning, native continuation, an actual independent semantic reviewer adapter and fair comparison are still pending. Live provider entrypoints remain unavailable.
