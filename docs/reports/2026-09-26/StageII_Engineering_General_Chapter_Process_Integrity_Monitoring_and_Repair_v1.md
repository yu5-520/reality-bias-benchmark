# Stage-II Engineering General Chapter: Process-Integrity Monitoring, Localization, Repair Boundaries, and Validation v1.0

Date: 2026-09-26  
Status: **FORWARD NORMATIVE ENGINEERING PARENT / PEER TO EXPERIMENTAL GENERAL CHAPTER**  
Role: **ENGINEERING GENERAL CHAPTER FOR STAGE-II MONITORING AND REPAIR**  
Machine-readable registry: `configs/stage2_engineering_general_principles_v1.json`  
Experimental peer chapter: `StageII_Experimental_General_Chapter_Process_Reality_Methodology_and_Principles_v2.md`

## 0. Purpose

This chapter freezes the engineering architecture derived from the process-reality programme.

The engineering objective is not “make every trajectory succeed.”

The objective is:

> **observe native probabilistic execution without taking control of it; localize process-integrity risks through source-bound evidence; intervene only where a legal native-preserving repair surface exists; verify both the repair boundary and the downstream process after intervention.**

The engineering stack is:

`native execution`
-> `external passive monitor`
-> `structural warning`
-> `semantic/lineage localization`
-> `checkpoint/resumability adjudication`
-> `repair eligibility gate`
-> `immutable structured repair package`
-> `one-shot local repair`
-> `repair executor exit`
-> `continued watch-only monitoring`
-> `post-repair process audit`.

This chapter is parallel to the Experimental General Chapter. Experimental rules determine how natural evidence is generated. Engineering rules determine how that evidence can be monitored, localized, and legally repaired.

---

# 1. Engineering framework principles

## ENG-FP-01 — Externality

The monitor/repair architecture is external to the studied system.

It may attach to exposed events, messages, calls, files, host-owned state, protocol traffic, or public/native checkpoint surfaces.

It does not become the normal scheduler, manager, or hidden execution runtime of the subject system.

---

## ENG-FP-02 — Native-preservation priority

Engineering capability is subordinate to native framework/protocol fidelity.

If a desired monitor or repair function requires changing the upstream framework's meaning, protocol semantics, agent communication behavior, or security boundary, that function is inadmissible for this experiment.

---

## ENG-FP-03 — Monitoring before intervention

The system must be observable before it is repairable.

A repair surface is not created merely because an intervention would be scientifically convenient.

---

## ENG-FP-04 — Observability is not intervenability

A system may support:

- complete external monitoring;
- structural warning;
- semantic audit;
- lineage reconstruction;
- terminal analysis;

while still lacking a legal same-parent repair branch.

Therefore:

`observable != resumable != repairable`.

---

## ENG-FP-05 — Localization before repair

No repair may run without a frozen target localization.

The localization must identify the source-bound lineage, relevant carrier/state, target mutation surface, and preserve set.

---

## ENG-FP-06 — Local repair over stochastic rerun

The engineering method prefers localized structural repair from a legal frozen parent over rerunning the whole probabilistic process to obtain a different outcome.

Rerunning is not treated as repair.

---

## ENG-FP-07 — One repair, then exit

The repair executor may apply one pre-frozen repair package.

After application it exits.

It may not remain as a new orchestrator that continuously changes the native system.

---

## ENG-FP-08 — Monitor continues after repair

Monitoring does not stop when the repair is applied.

The monitor remains watch-only through the subsequent trajectory to observe:

- repair effect;
- re-entry;
- regeneration;
- migration;
- new scope expansion;
- process closure;
- terminal outcome.

---

## ENG-FP-09 — Repair is not orchestration

The repair layer must not choose the subject system's subsequent agent order, handoff path, tool sequence, or reasoning route.

The repaired system resumes its native execution.

---

## ENG-FP-10 — Semantic audit remains independent

Post-hoc semantic audit may evaluate whether a warning/localization was meaningful.

It may not feed CPR labels into the natural process or retrospectively rewrite the package that already generated B.

---

# 2. Engineering boundary principles

## ENG-BD-01 — No protocol mutation

The engineering layer may not modify MCP, A2A, or another upstream protocol merely to expose a repair point.

---

## ENG-BD-02 — No framework mutation for experimental convenience

The engineering layer may not patch AutoGen, MetaGPT, or another framework's native scheduling/state semantics merely so that all X conditions support identical repair mechanics.

---

## ENG-BD-03 — No private-state synthesis

Unexposed private runtime state may not be invented, reconstructed, or manually synthesized to create a checkpoint.

---

## ENG-BD-04 — No stochastic-prefix recreation

A repair parent cannot be recreated by calling the model again and hoping to reproduce the same prefix.

The B branch must descend from a legally captured frozen parent.

---

## ENG-BD-05 — Same-parent requirement

A/B process comparison requires a shared frozen parent state sufficient for the relevant continuation.

If the parent is not legally restorable, paired local repair is blocked.

---

## ENG-BD-06 — Native/public state only

Checkpoint state may contain:

- public/native framework state;
- experiment-owned host/service state;
- checkout state;
- model-visible context evidence/hashes;
- remaining budget;
- immutable references/hashes to foreign carriers.

It may not silently copy or mutate foreign private state.

---

## ENG-BD-07 — Preserve-set requirement

Every repair package must declare what must remain unchanged.

The preserve set may include:

- unrelated files;
- unrelated semantic lineages;
- protocol behavior;
- task authorization;
- roles;
- upstream framework state;
- external carrier state;
- security/permission boundaries.

---

## ENG-BD-08 — Explicit mutation surface

The repair package must identify the exact permitted mutation surface.

A vague instruction such as “fix everything related” is not admissible.

---

## ENG-BD-09 — No repair scope growth

The repair executor may not expand from the frozen target into adjacent cleanup, refactoring, optimization, or “while we are here” work.

---

## ENG-BD-10 — Fail closed

If legal parent, mutation surface, preserve set, protocol integrity, or post-repair observability cannot be proven, active repair is refused.

The refusal is recorded as an engineering result.

---

## ENG-BD-11 — X1 AutoGen intervention boundary

X1 remains fully eligible for:

- prospective natural execution;
- external monitoring;
- warning;
- semantic audit;
- legal task-start/terminal native checkpointing.

The current mid-run AutoGen repair parent remains:

`UNPROVEN_FAIL_CLOSED`.

A B branch must not be created by patching AutoGen, synthesizing running-team state, or replaying a stochastic prefix.

---

## ENG-BD-12 — X3 A2A intervention boundary

X3 remains fully eligible for:

- prospective natural execution;
- external A2A wire monitoring;
- warning;
- semantic audit;
- quiescent top-level role-service snapshots.

The nested active call-stack repair parent remains:

`UNPROVEN_FAIL_CLOSED`.

A B branch must not be created by changing A2A protocol semantics, fabricating nested call state, or replaying remote-agent decisions.

---

## ENG-BD-13 — Non-intervention is data

A cell that passes observation but fails repair eligibility is not “missing.”

It contributes evidence about the boundary between observability and intervenability.

---

## ENG-BD-14 — Native security boundaries remain binding

Repair may not bypass an upstream permission, resource, tool, authentication, or protocol boundary that the natural system itself must respect.

---

# 3. Monitoring principles

## ENG-MO-01 — Passive by default

The monitor is read-only during natural A.

It records; it does not steer.

---

## ENG-MO-02 — Full-lifecycle watch

Where exposed surfaces permit, monitoring spans:

- task start;
- each native model decision/action;
- message/protocol calls;
- carrier transformations;
- checkpoint boundaries;
- first repair-eligible point;
- immediately pre-repair;
- immediately post-repair;
- resumed native execution;
- terminal/censored stop.

---

## ENG-MO-03 — Structural warning precedes semantic verdict

Online warnings may be generated from structural evidence such as:

- repeated scope expansion;
- state mismatch;
- repeated review reopening;
- historical residue re-entry;
- repeated carrier transformation;
- recursive memory feedback;
- authority/status mismatch.

A warning is a candidate, not a final CPR judgment.

---

## ENG-MO-04 — Warning is not repair authorization

The presence of a warning does not itself authorize B.

Checkpoint legality, parent freshness, package completeness, and boundary checks must all pass.

---

## ENG-MO-05 — Evidence provenance

Every monitor event should bind, where available:

- system/cell/group;
- sequence;
- native event type;
- actor/role;
- source/carrier;
- content hash;
- checkout/state reference;
- model-decision sequence;
- derived-vs-native marker.

---

## ENG-MO-06 — Native event priority

When a native framework event exists, it is preferred as the primary event source.

Derived monitor events must remain labeled as derived.

---

## ENG-MO-07 — Missing evidence is explicit

The monitor must not fill unobserved semantics.

Missing private state, hidden reasoning, or unavailable protocol detail remains missing.

---

## ENG-MO-08 — Structural and semantic layers remain separable

Online structural detection and post-hoc semantic adjudication may reference the same evidence but remain distinct operations.

This prevents the semantic theory from steering the natural process.

---

## ENG-MO-09 — Coverage accounting

Each report must state which surfaces were observed and which were not.

“Monitored” does not imply identical visibility across all seven X conditions.

---

## ENG-MO-10 — Monitor self-boundary logging

The monitor should record its own attachment points and verify that it did not mutate execution state.

---

# 4. Lineage and localization principles

## ENG-LN-01 — Source-bound localization

A repair candidate must trace back to an identifiable source state, event, artifact, message, carrier, or semantic node.

---

## ENG-LN-02 — Descendant preservation

Lineage must preserve transformed descendants rather than track only exact-string copies.

---

## ENG-LN-03 — Carrier identity

The audit should identify where a semantic state resides:

- message;
- shared state;
- file;
- protocol artifact;
- retrieval hit;
- memory item;
- compressed context;
- plan premise;
- decision gate.

---

## ENG-LN-04 — Consumer identity

The localization records which actor/process read or adopted the carrier when evidence permits.

---

## ENG-LN-05 — Decision linkage

A warning becomes stronger when a recorded downstream decision/action can be linked to the carrier.

Visibility alone is weaker evidence than adoption or decision application.

---

## ENG-LN-06 — Content addressing

Repair targets should be content/hash/lineage-addressed wherever practical, rather than referenced only by natural-language description.

---

## ENG-LN-07 — Full-lineage retrieval

The engineering system should support retrieving the relevant source-to-descendant path for a selected target without requiring the entire experiment to be rerun.

---

# 5. Checkpoint and resumability principles

## ENG-CP-01 — Serialization is not resumability

A state object being serializable does not prove that it can legally resume the same active process.

---

## ENG-CP-02 — Resumability must be demonstrated

A repair parent is admissible only if restore/resume behavior has been preflighted at the relevant boundary.

---

## ENG-CP-03 — Checkpoint classes are explicit

At minimum use explicit classes such as:

- `FULL_NATIVE`;
- `QUIESCENT_NATIVE`;
- `PARTIAL_NATIVE`;
- `HOST_OWNED`;
- `UNPROVEN_FAIL_CLOSED`.

The exact registry may be more detailed, but ambiguous “checkpoint exists” language is prohibited.

---

## ENG-CP-04 — Model-decision freshness

A checkpoint selected as repair parent must not have an uncheckpointed model decision after it.

Otherwise the B branch no longer shares the legally frozen decision prefix.

---

## ENG-CP-05 — Parent freshness is frozen at package time

The relationship between monitor candidate, package, and parent sequence is frozen before B.

A later checkpoint cannot silently replace the original parent because it produces a more favorable branch.

---

## ENG-CP-06 — Foreign carrier immutability

For RAG, MemoryBank, LongLLMLingua, MCP resources, or other foreign carriers, checkpoint/repair must not silently rewrite carrier internals unless the carrier itself is the explicitly authorized repair target and a legal interface exists.

---

## ENG-CP-07 — Checkout identity

Repository state at the repair parent must be content-addressed so A/B descendants can prove their shared parent.

---

## ENG-CP-08 — Remaining-horizon identity

A/B continuations from the same parent use the same remaining execution budget unless a separately frozen contrast explicitly tests horizon.

---

# 6. Repair-eligibility principles

## ENG-EL-01 — Eligibility is evaluated for all 21 natural cells

Every natural G2-G5 cell enters the engineering eligibility assessment after A is frozen.

X1/X3 are not omitted from eligibility accounting.

---

## ENG-EL-02 — Eligibility dimensions

Eligibility requires all of:

1. target candidate exists;
2. sufficient source/lineage localization exists;
3. legal frozen parent exists;
4. parent is resumable at required boundary;
5. allowed mutation surface exists;
6. preserve set is explicit;
7. protocol/framework boundaries remain intact;
8. repair can be applied once and observed afterward.

---

## ENG-EL-03 — No semantic cherry-picking

If multiple eligible packages exist, package selection follows the prospectively frozen structural ordering rule, not post-hoc semantic preference.

---

## ENG-EL-04 — No package means no B

A natural trajectory may be scientifically valuable even if no complete repair package is produced.

Absence of a package is recorded, not “fixed” by inventing a target.

---

## ENG-EL-05 — X1/X3 expected current status

Under the currently frozen native-preservation evidence:

- X1: observation/audit eligible; relevant mid-run B currently blocked;
- X3: observation/audit eligible; relevant nested active B currently blocked.

Future native upstream capabilities may change eligibility, but only prospectively and without modifying historical evidence.

---

# 7. Structured repair-package principles

## ENG-RP-01 — Package immutability

The package used for B is frozen before B begins.

---

## ENG-RP-02 — Earliest eligible package rule

Where multiple complete packages exist, choose the earliest eligible package by the pre-registered sequence/order rule, not the package expected to produce the best effect.

---

## ENG-RP-03 — Explicit target

The package binds target IDs/hashes/lineage references.

---

## ENG-RP-04 — Explicit intended delta

The package states exactly what change is authorized.

---

## ENG-RP-05 — Explicit preserve set

The package states exactly what must remain unchanged.

---

## ENG-RP-06 — Boundary assertions

The package contains explicit protocol/framework/permission/security boundaries that must not be crossed.

---

## ENG-RP-07 — One-shot application

The package may be applied once.

---

## ENG-RP-08 — No adaptive second repair

A poor first repair outcome does not authorize a second automatic package.

---

## ENG-RP-09 — Repair executor exit

After the authorized mutation is complete, the repair executor exits and native execution resumes.

---

## ENG-RP-10 — Package quality is audited separately

Localization/package quality is evaluated independently from terminal task outcome.

A task may succeed despite a poor localization, or fail despite a correctly bounded repair.

---

# 8. Repair-boundary watcher principles

## ENG-RW-01 — Watch the repair itself

The monitor observes not only pre-repair and post-repair states, but also the repair action.

---

## ENG-RW-02 — Mutation-surface check

If repair touches an undeclared target, the watcher records a boundary violation.

---

## ENG-RW-03 — Preserve-set check

The watcher verifies that preserved files/state/protocol surfaces remain unchanged where measurable.

---

## ENG-RW-04 — Protocol-integrity check

The watcher records whether repair altered or bypassed the native protocol/interface.

---

## ENG-RW-05 — Permission/scope check

The watcher detects whether repair expands permissions, files, roles, or resources beyond the package.

---

## ENG-RW-06 — Fail-stop on active violation

Where technically possible without changing the scientific subject semantics, an engineering safety wrapper may prevent execution of an out-of-package repair mutation.

Such prevention is a repair-layer safety action, not a natural-A intervention.

---

# 9. Post-repair validation principles

## ENG-PV-01 — Compare process, not only endpoint

A/B analysis includes process structure, not only whether the user-visible task eventually succeeds.

---

## ENG-PV-02 — CPR dynamics comparison

Post-repair audit asks whether relevant C/P/R structure:

- disappears;
- weakens;
- persists;
- migrates;
- regenerates;
- changes carrier;
- re-enters later.

---

## ENG-PV-03 — Re-entry watch

A repaired source may disappear while a descendant survives elsewhere.

The monitor therefore watches descendant carriers and not only the repaired source field/file.

---

## ENG-PV-04 — Preservation audit

Unrelated structure must be checked for unintended change.

---

## ENG-PV-05 — Repair-generated process expansion

The repair layer itself can create new P-like expansion.

This possibility must be audited rather than assumed absent.

---

## ENG-PV-06 — Terminal outcome is separate

Task success/failure remains one output variable.

It does not summarize localization quality, repair legality, preservation, or process dynamics.

---

## ENG-PV-07 — Multidimensional repair result

At minimum distinguish:

- localization validity;
- parent legality;
- package boundary compliance;
- intended local delta;
- preserve-set integrity;
- downstream process effect;
- CPR migration/re-entry;
- process closure;
- terminal task outcome.

---

# 10. Engineering evidence hierarchy

The forward engineering evidence chain is:

`raw native/host evidence`
-> `monitor evidence`
-> `structural candidate`
-> `lineage localization`
-> `checkpoint ledger`
-> `repair eligibility result`
-> `immutable repair package`
-> `repair-boundary watch`
-> `B continuation evidence`
-> `post-repair semantic/process audit`
-> `engineering claim`.

No later layer may fabricate missing evidence in an earlier layer.

---

# 11. X1/X3 publication-facing interpretation

X1 and X3 are not excluded from the experiment.

Across G2-G5 they remain part of all natural observation groups and may contribute:

- complete native/protocol process evidence;
- external monitoring;
- warnings;
- lineage evidence;
- semantic audit;
- CPR/cross-penetration evidence;
- checkpoint-boundary evidence.

Their current engineering distinction is narrower:

> **the required active mid-process same-parent repair surface is not legally demonstrated under the native-preservation rule.**

Therefore, current non-execution of B for X1/X3 is an intervention-boundary result, not an experimental-population omission.

The engineering chapter forbids solving this by breaking the very framework/protocol fidelity the experiment is designed to preserve.

---

# 12. Relationship to G2-G5

For each future group:

1. run all 21 natural A first attempts;
2. freeze all A evidence;
3. complete 21-cell monitoring/eligibility accounting;
4. X1/X3 remain fully audited even if active B is blocked;
5. repair-capable cells may launch at most one legal B from the frozen parent;
6. repair executor exits;
7. monitor continues;
8. freeze B/post-repair evidence;
9. only then open semantic comparison.

The theoretical maximum repair population is therefore smaller than the natural population by design.

---

# 13. Forward engineering child-report contract

Each future engineering child report includes:

## Relation to Engineering General Chapter

1. adopted engineering principle IDs;
2. observed surfaces and coverage;
3. candidate/localization rule;
4. checkpoint class and parent evidence;
5. eligibility result;
6. repair package ID if any;
7. boundary-watcher result if any;
8. post-repair process evidence if any;
9. preserved unrelated structure;
10. explicit non-claims.

---

# 14. Freeze declaration

This chapter is the forward normative engineering parent for Stage II.

It does not authorize scientific subject/provider calls by itself.

It does not retroactively modify earlier readiness reports.

It supersedes the planning assumption that X1/X3 should be omitted from future natural replication merely because they currently lack a legal paired B.

The forward engineering rule is:

> **observe all seven systems; repair only the legally repairable subset; treat the boundary itself as evidence.**
