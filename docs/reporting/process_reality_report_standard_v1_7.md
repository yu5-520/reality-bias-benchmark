# Process Reality Report Standard v1.7

Status: **FORWARD ACTIVE / TRAJECTORY-SEMANTIC EVIDENCE PROFILE**  
Date: 2026-09-18  
Predecessor: `RB-PROCESS-REALITY-REPORT-STANDARD-v1.6`  
Default template: `process_reality_experiment_report_template_v3.md`

Historical reports remain immutable.

## 1. Core reporting chain

Forward reports preserve:

`Frozen Evidence -> Structural Reconstruction -> Agent Trajectory -> Relation-Level Semantic Interpretation -> Claim-Boundary Interpretation`

For engineering/control reports, append:

`-> Repair/Control Operation -> Preservation/Re-entry Verification -> Engineering Interpretation`

Structural data establish what happened. Semantic interpretation explains what the realized process means. Neither layer may rewrite the other.

## 2. Primary evidence hierarchy

For multi-Agent process reports, the preferred evidence hierarchy is:

1. exact frozen run identity and source binding;
2. realized Agent path in time order;
3. state/message/invocation objects created along that path;
4. authority/status transitions and downstream use;
5. semantic reading of the path;
6. supporting structural metrics such as reach, depth, branch/merge, re-entry and path families;
7. claim-boundary interpretation.

Aggregate counts are supporting facts. They must not replace the realized process path when the path is available.

## 3. Mandatory structure-path rule

When a report uses a multi-Agent trajectory as evidence, each key trajectory or contrast must expose, where recorded:

- turn/order;
- Agent/role;
- input premise or relevant shared state;
- message/invocation handoff;
- state object or action produced;
- object status/authority;
- later Agent adoption or re-use;
- termination/re-entry/censoring;
- evidence refs/hashes.

The report must then provide a bounded semantic reading of what that path is doing.

Recommended local grammar:

`Structural Path -> Semantic Reading -> Scientific/Engineering Meaning`

## 4. Semantic interpretation as a first-class layer

Semantic interpretation is not a free-form discussion section. It must remain bound to frozen process evidence.

For every major semantic reading, distinguish direct structural fact, semantic relation/inference, alternative compatible interpretation, and claim status.

Preferred relation vocabulary includes `supports`, `constrains`, `depends_on`, `enables`, `conflicts_with`, `reframes`, `drops`, `reconstructs`, `inherits`, `reopens`, `preserves` and `invalidates` when evidence supports those relations.

## 5. Data structure is the factual substrate

State writes, messages, invokes, reads, hashes, lineage edges, status fields, termination reasons and censoring establish the factual base.

Do not infer semantic adoption from literal recurrence, Agent count, path count, reachability or same-key writes alone.

Conversely, semantic interpretation must not omit or contradict recorded structural facts.

## 6. Preserve realized heterogeneity

Do not average away opposite or heterogeneous realized paths before showing them.

If one replicate expands and another contracts, or one repair path reopens multiple Agents while another ends in one turn, report the realized paths first. Summary statistics come after path-level evidence.

Same-parent repeats are repeated realizations, not independent population samples.

## 7. Negative operator evidence is reportable evidence

A failed operator or censored attempt should remain visible when it reveals an engineering or scientific boundary.

Reports should state what the operator expected, what Agents actually did, which semantic object/status/path replaced or blocked the intended operation, and what design change the failure motivated.

Do not hide a failed path merely because a later operator succeeds.

## 8. Process / endpoint separation

`same endpoint != same process`

Terminal correctness, reward, final business decision or task completion remain endpoint variables.

A convergent endpoint may coexist with different Agent paths, different authority carriers and different lineage structures.

## 9. Structural recomputation / semantic novelty separation

`structural recomputation != semantic novelty`

A new event or state write may reaffirm already-compatible meaning rather than create a new semantic decision.

Where repair/control reports reuse compatible state, report which objects were newly emitted structurally, which meanings were genuinely revised, and which meanings were preserved/reaffirmed.

## 10. Inertia and shared-state reporting

Normal shared-state inheritance is not automatically pathological.

Where relevant, distinguish valid shared information inertia, valid decision inertia, valid plan inertia, and problematic authority/semantic-lineage persistence.

A control/recovery report should ask whether problematic lineage can be revised while compatible system memory remains reusable.

## 11. R2-R6 scientific reports

R2-R6 reports may use natural/process trajectories to explain semantic formation, transmission, transformation, support, pool entry, exposure, local response and downstream inertia.

Where a path is central, show the Agent path and the semantic function of each role before aggregate topology.

Historical identifiers remain frozen.

## 12. R7 engineering reports

R7 additionally follows `RB-PROCESS-REALITY-ENGINEERING-REPORT-STANDARD-v1.1`.

R7 reports must preserve Repair Anchor, Semantic Lineage Package/relevant closure, EvidenceSupportedAffectedClosure, RepairClosure, revision identity, selective invalidation/reopen/recompute, preserved compatible structure, residual/re-entry evidence, post-repair watch, engineering cost and the semantic CPR boundary.

The R7 report body must not reduce these operations to protocol names only. It must show the realized Agent trajectories that motivated and validated the operator revisions.

## 13. R8 semantic reports

R8 may adjudicate event-level C/P/R semantics over frozen evidence.

R8 should retain the same path-first evidence discipline: event labels must bind to exact Agent/state/message/lineage evidence and may overlap or transition when supported.

R8 does not mutate R7 or earlier raw evidence.

## 14. Required opening block

Every forward report should state, as applicable: report role, primary question, evidence sets/workflows, interpretation method, main bounded result, claim boundary, reporting-standard version, raw-evidence mutation status, new subject/provider/evaluator calls and CPR status.

## 15. Recommended section order

1. Scope and Evidence Binding
2. Target / Root / Control-Surface Identity
3. Relevant Source / Transformation / Authority / Pool History
4. Experimental / Control Operation
5. **Agent Structural Trajectories and Semantic Interpretation**
6. Supporting Structural / Carrier Measurements
7. Affected / Preserved / Unresolved Partition
8. Selective Recompute / Revision / Recovery Evidence, if applicable
9. Residual / Re-entry / Recurrence Evidence, if applicable
10. Engineering or Scientific Cost, if applicable
11. Process / Terminal Outcome Separation
12. Directly Evidenced
13. Supported Candidates / Open Questions
14. Not Established / Not Adjudicated
15. Interpretation Boundary
16. Evidence Provenance / Freeze Boundary

Specialized standards may retain additional required sections, but the trajectory-semantic layer remains central whenever realized Agent process evidence exists.

## 16. Figures and tables

Prefer time-aligned trajectory figures over all-to-all network diagrams.

A useful figure should expose time/order, Agent role, salient handoffs, state/authority changes, repair/intervention boundary and re-entry/reopen/finalization.

Evidence tables remain mandatory for source binding and exact values. Figures do not replace provenance.

## 17. Claim-status discipline

Use `DIRECTLY_EVIDENCED`, `SUPPORTED` / `OBSERVED`, `SUPPORTED_CANDIDATE`, `UNRESOLVED`, `NOT_ESTABLISHED`, `NOT_OBSERVED`, `CONTRADICTED`, and `NOT_ADJUDICATED`.

Do not promote structural similarity into semantic equivalence, semantic plausibility into causality, or two-run replication into population generality.

## 18. Provenance and freeze boundary

Every report must expose enough provenance to locate the frozen evidence, including as applicable workflow run IDs, artifact IDs/digests, evidence batch hash, raw traces hash, plan/design hash, parent/revision hashes, execution/code SHA, measurement/runtime-plan hashes, evaluator status and CPR status.

Missing events must not be reconstructed as observed events.

## 19. Authorization boundary

A report authorizes no subject run, evaluator call, repair action, semantic adjudication or evidence mutation.

## 20. Forward rule

Unless superseded, all new Process Reality experiment and engineering reports should use `process_reality_experiment_report_template_v3.md` as the default report scaffold.

Historical reports remain bound to the reporting standard named in their own header.
