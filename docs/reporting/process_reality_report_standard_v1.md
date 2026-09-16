# Process Reality Report Standard v1.0

Status: **ACTIVE REPORTING STANDARD**  
Language: **English only**  
Primary use: Reality Bias / Process Reality experiment reports  
Reference visual direction: publication-oriented, Nature Machine Intelligence-style scientific figure grammar (not a journal production template)

## 1. Purpose

This standard defines how frozen Process Reality evidence is converted into human-readable scientific reports without replacing, rewriting or reconstructing the source evidence.

The reporting chain is:

`Frozen raw trace -> immutable evidence binding -> frozen structural derivation -> report figure/table`

Reports are evidence projections. They are not substitutes for the frozen trace and must not introduce new experimental events, semantic adjudication or post-hoc synthetic trajectories.

## 2. Core reporting principle

The primary object of reporting is the **process**, not the terminal answer.

Information priority is:

1. temporal agent execution and communication;
2. state transition and structural Jump position;
3. downstream structural lineage and topology;
4. structural measurements;
5. terminal outcome;
6. interpretation boundary.

A report must make it possible to answer: who acted, when, what information was handed off, what state changed, where a Jump occurred, how that Jump propagated, and how the realized path differs from its matched continuation.

## 3. Language and terminology

All report-facing content must be English:

- report title and section headings;
- figure titles and captions;
- diagram labels;
- table headers;
- metric names;
- explanatory prose.

Machine identifiers remain unchanged and appear as provenance fields or compact labels:

- agent IDs such as `ops_lead`, `ads`, `inventory`;
- schema names;
- workflow/run IDs;
- status codes;
- hashes;
- source event IDs.

Do not mix Chinese explanatory text into the publication-facing report.

## 4. Visual grammar

### 4.1 General visual style

Use a publication-oriented scientific layout:

- white background;
- restrained typography;
- Arial/Helvetica-like sans-serif figure text;
- black/dark-grey primary structure;
- at most one restrained accent color for intervention emphasis;
- no dashboard cards, UI chrome, decorative gradients or presentation-style blocks;
- compact lower-case panel labels (`a`, `b`, `c`, ...);
- tables use minimal horizontal rules and no spreadsheet-style full grid unless necessary for trace readability.

The goal is not to imitate a journal page. The goal is to make each figure publication-ready as a scientific display item.

### 4.2 Canonical notation

The main figures use compact evidence notation. Long English descriptions belong in captions and evidence tables.

- `Tn` = executed agent turn;
- `En` = recorded source event;
- `Mn` = recorded message / handoff reference;
- `Jn` = structural Jump or descendant re-Jump;
- `J0` = selected structural root;
- `OS` or a single star marker = one-shot intervention exposure, only when applicable.

A node should contain identifiers, not a sentence. Example:

`T9  O`  
`E38 / J1`

where the evidence table explains the full event meaning.

### 4.3 Edge semantics

The figure must emphasize **line meaning** rather than node prose.

Canonical edge meanings:

- solid directed line: realized temporal / causal handoff;
- dashed directed line: invocation or activation when it must be distinguished from message delivery;
- lineage line: Jump inheritance / descendant relation (`J0 -> J1 -> ...`), visually distinct from ordinary handoff;
- return/re-entry edge: explicit return to a previously active role;
- branch: one upstream state/action producing multiple downstream realized paths;
- merge: multiple downstream paths reconverging into a common realized node;
- state persistence: use a dedicated state lane or compact state marks rather than long cross-figure arcs.

Do **not** draw the complete all-to-all message network in the main figure. Long cross-turn message arcs create visual noise and obscure temporal causality. The full message graph, when needed, belongs in supplementary material or a trace table.

## 5. Time-causal figure rule

The main process figure must be ordered by time.

Preferred layout:

`time -> T1 -> T2 -> T3 -> ...`

with aligned lanes for:

1. agent execution;
2. causally salient message / decision handoff;
3. shared-state evolution;
4. Jump / lineage annotations.

The viewer should be able to read the process from left to right without tracing intersecting spaghetti edges.

When a prior message is reused several turns later, do not draw a long crossing arc by default. Reference the message ID in the later turn (`uses M08`) and resolve its meaning in the evidence table.

## 6. Representative trajectory rule

A report may display one structurally informative trajectory in full when plotting every run would reduce readability.

The selection must be explicit and non-deceptive. Preferred selection rules are:

- structurally richest complete trajectory;
- longest valid root-reachable trajectory;
- predeclared matched pair;
- median-complexity trajectory when representativeness is the goal.

The report must state the rule used.

**Visualization coverage is not evidence coverage.** Runs not expanded as a main figure remain part of the evidence and must appear in a run index and trace/measurement tables.

## 7. Evidence provenance requirements

Every report must include an Evidence Provenance section containing, when available:

- workflow run ID;
- full frozen run ID / pair ID;
- evidence batch hash;
- raw traces SHA256;
- frozen parent-state hash;
- plan hash;
- execution code SHA;
- measurement schema/version;
- measurement hash;
- source event references used in figures;
- report generation date and report-standard version.

Every important figure must be traceable to frozen evidence. A report may introduce compact `E`, `M`, `T` and `J` references, but each must be resolvable in an evidence table or frozen trace.

## 8. Report profiles

### 8.1 Control Process Evidence Report

Purpose: establish how the system naturally proceeds without experimental-origin exposure.

Required sections:

1. Scope and evidence binding
2. Control-condition definition
3. Representative temporal causal trajectory
4. Jump lineage and post-root process spine
5. Agent communication / action ledger
6. State and structural-event ledger
7. Remaining-run evidence index
8. Within-control structural variability
9. Structural measurements
10. Terminal outcome
11. Interpretation boundary
12. Evidence provenance

The control report must make natural process variability visible. Do not collapse repeated controls into a single average trajectory.

### 8.2 One-Shot Intervention Process Evidence Report

Purpose: establish how the same frozen process continues when a bounded one-shot local perturbation is exposed exactly once.

Required sections:

1. Scope and evidence binding
2. Intervention integrity
3. Representative temporal causal trajectory
4. Exact intervention position relative to `J0`
5. Post-intervention process spine
6. Agent communication / action ledger
7. State and structural-event ledger
8. Remaining-run evidence index
9. Structural measurements
10. Terminal outcome
11. Interpretation boundary
12. Evidence provenance

Intervention integrity must explicitly state:

- direct exposure count;
- overlay consumption;
- reinjection count;
- persistent-state mutation status.

### 8.3 Matched A/B Mechanism Validation Report

Purpose: provide the central mechanism evidence connecting local perturbation to downstream process reorganization and to the paper's theoretical propositions.

This is the highest-priority report profile.

Required sections:

1. Scientific question and matched design
2. Experimental integrity
3. Pair 1 time-aligned causal contrast
4. Pair 2 time-aligned causal contrast
5. First divergence analysis
6. Structural Change Filter
7. Cross-pair structural invariants
8. Structural measurement matrix
9. Process-vs-terminal decoupling
10. Theory proposition mapping
11. Claims supported / claims not established
12. Evidence provenance

The A/B report must answer, in order:

- Did the intervention occur exactly where intended?
- What changed first after the intervention?
- Did the change remain local or propagate?
- Which observed differences qualify as structural rather than surface variation?
- Which structural features are shared across pairs despite opposite directional magnitudes?
- Does the evidence support process-topology reorganization?
- Which stronger causal or generalization claims remain unsupported?

## 9. Structural Change Filter

Observed A/B differences must be classified before theoretical interpretation.

Recommended levels:

1. **Surface variation** - wording or formatting differences without process consequence.
2. **Execution variation** - different local action/message realization without structural propagation.
3. **State variation** - a shared-state write or visible state differs.
4. **Local structural change** - agent selection, Jump recurrence, branch/merge or local reach changes.
5. **Propagated structural change** - downstream agent participation, lineage, path family, role re-entry, cross-agent relation or reconvergence structure changes.

Only levels 4-5 should be used as direct evidence for process-topology reorganization.

## 10. Theory mapping rule

The mechanism-validation report must map observations to explicit theoretical propositions rather than ending with an unspecific statement that the theory is "supported".

Each proposition receives one of:

- observed-case support;
- descriptive compatibility;
- not established;
- contradicted by current evidence;
- not adjudicated.

Examples of propositions:

- local structural roots are identifiable in natural runs;
- a bounded local perturbation can propagate beyond the directly altered state;
- downstream process topology can reorganize without a stable monotonic direction;
- similar terminal outcomes can mask materially different process structures;
- a stable directional treatment effect exists;
- a generalized causal law across tasks/models exists.

Do not promote two matched pairs into a generalized causal law.

## 11. Process / terminal separation

Terminal task result is a downstream measurement, not the definition of Process Reality.

Reports should place terminal outcomes after process-topology analysis and explicitly distinguish:

- exact string identity;
- core decision convergence;
- process structural similarity/difference;
- semantic task correctness, when adjudicated separately.

A shared terminal decision must not be used to erase observed process divergence.

## 12. Table rules

Use tables for semantic expansion and complete trace coverage.

Preferred trace table columns:

- Ref
- Turn
- Agent
- Incoming evidence / message refs
- Action
- State write / outgoing evidence
- Structural role

Preferred A/B structural matrix columns:

- Structural feature
- Pair 1 A
- Pair 1 B
- Pair 2 A
- Pair 2 B
- Cross-pair interpretation

Tables must preserve runs that are not expanded in the main figure.

## 13. Caption rules

A figure caption must state:

1. what is shown;
2. what the node/edge symbols mean;
3. which frozen run/pair the figure derives from;
4. whether the figure is a complete trajectory, a root-scoped slice or a representative projection;
5. the interpretation boundary.

Do not describe a reconstructed schematic as an observed trace.

## 14. Non-negotiable integrity rules

A compliant report must not:

- rerun a frozen experimental branch to improve presentation;
- invent missing events;
- silently omit a run from quantitative evidence;
- convert reviewer interpretation into observed system state;
- imply semantic CPR adjudication when status is `NOT_ADJUDICATED`;
- claim monotonic treatment direction when matched pairs reverse direction;
- treat same-parent repeats as independent samples when they are not;
- use terminal output as a substitute for process measurement.

## 15. Versioning

Report artifacts should declare this standard as:

`RB-PROCESS-REALITY-REPORT-STANDARD-v1.0`

Future changes to the scientific meaning of notation, report profiles or evidence requirements require a new standard version. Cosmetic fixes that do not change interpretation may use a patch revision.
