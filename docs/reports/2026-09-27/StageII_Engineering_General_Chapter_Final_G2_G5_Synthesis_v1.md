# Stage-II Engineering General Chapter — Final G2–G5 Process-Integrity Synthesis v1

Date: 2026-09-27  
Status: **FINAL SEALED ENGINEERING SYNTHESIS — G2/G3/G4/G5**

Parent engineering chapter: `docs/reports/2026-09-26/StageII_Engineering_General_Chapter_Process_Integrity_Monitoring_and_Repair_v1.md`

This chapter closes the prospective G2–G5 engineering evidence line. It does not replace the four group-level semantic audits. It integrates them under the frozen engineering rules: same-parent repair, one frozen package, one B first attempt, repair-executor exit, watch-only continuation, and post-hoc process-semantic audit.

## 1. Final population and accounting

Across four independently frozen groups:

| Population item | Count |
| --- | ---: |
| Group-cell structural eligibility rows | **48** |
| Canonical B first attempts | **47** |
| Valid same-parent paired-effect samples | **45** |
| B-execution boundaries | **2** |
| Pre-B source-readiness boundaries | **1** |
| Total explicit boundaries | **3** |
| Natural-A reruns used to manufacture pairs | **0** |
| B reruns used to manufacture preferred outcomes | **0** |

The three boundaries are not pooled with the 45 paired-effect samples.

G2 and G4 each preserve an X5-T2 B-execution boundary where the legal frozen repair surface produced no non-no-op mutation. G5 preserves X4-T2 as a pre-B source-readiness boundary because the canonical Natural-A attempt had no legal seal for same-parent restoration.

G3 additionally contains a disclosed control-plane incident: a later workflow executed six duplicate provider-backed attempts. The canonical evidence remains the original first-attempt run, the duplicate outputs are excluded from scientific evidence, and the incident produced a stricter engineering rule rather than a replacement sample.

## 2. Final paired-effect topology

Among the **45 valid same-parent pairs**:

| Process effect | Count |
| --- | ---: |
| Persistence | **18** |
| Mixed effect | **15** |
| Targeted suppression | **3** |
| Targeted redirection | **4** |
| Regeneration | **5** |

Direct target effects:

| Direct target effect | Count |
| --- | ---: |
| Persisted | **18** |
| Redirected | **19** |
| Reduced | **3** |
| Regenerated | **5** |

Therefore:

- direct target changed: **27/45**;
- clean targeted suppression/redirection: **7/45**;
- unrelated structure preserved: **45/45**.

These values are descriptive counts for the frozen Stage-II sample. They are not population prevalence estimates.

## 3. Main engineering result: locality is not efficacy

The central result across all four groups is the repeated separation between **repair locality** and **downstream process efficacy**.

Every valid B remained inside the frozen repair/preserve boundary at repair-executor exit. Yet the downstream process did not collapse to a single success/failure mode. Persistence, mixed continuation, targeted effects and regeneration all remained observable.

A precise local mutation can therefore be legal and correctly bounded while the subsequent system:

- keeps the old process structure;
- redirects only part of the route;
- reopens a previously closed trajectory;
- shifts collaboration structure;
- remains horizon-censored;
- or cleanly suppresses/redirects the targeted process.

For this reason, a binary repair-success field is insufficient.

## 4. Direct target change is not process closure

The direct target changed in **27/45** valid pairs, but only **7/45** reached clean targeted suppression/redirection.

This difference is structurally important. It shows why the engineering report must separate:

1. whether the authorized target changed;
2. whether unrelated structure was preserved;
3. what route followed after repair;
4. whether collaboration scope changed;
5. whether temporal reach changed;
6. whether the process persisted, mixed, regenerated or closed;
7. terminal task outcome.

The repair executor can do exactly what it was authorized to do without determining the subsequent process trajectory.

## 5. Regeneration is a repeated engineering phenomenon

Regeneration appears in **5/45** valid pairs and is present in every group G2–G5.

The strongest examples include trajectories where Natural-A had already finalized and the one-shot intervention reopened a longer post-repair process.

This matters because it rules out a simple engineering assumption that "successful local repair" monotonically reduces process activity. A repair can be local, preserve unrelated structure, and still create new downstream work.

Therefore the external monitor must remain active **after** repair-executor exit.

## 6. Task-family response topology

### T1 — persistence-dominated

Across **16 valid T1 pairs**:

- persistence: **14**;
- mixed effect: **1**;
- regeneration: **1**.

T1 therefore provides the strongest repeated sample pattern of unresolved/invalid process-state inertia under one-shot local process revision.

### T2 — regeneration, mixed continuation, and boundaries

Across **16 attempted T2 group-cells**:

- valid pairs: **13**;
- explicit boundaries: **3**;
- mixed effect: **8**;
- regeneration: **4**;
- targeted redirection: **1**.

All three final engineering boundaries occur in T2. This family most clearly exposes the distinction between broad task authorization, legal mutation surface, source readiness, and downstream process expansion.

### T3 — heterogeneous historical-path response

Across **16 valid T3 pairs**:

- targeted suppression: **3**;
- targeted redirection: **3**;
- mixed effect: **6**;
- persistence: **4**.

G2–G4 showed the same group-level 1/1/1/1 distribution, but G5 broke that symmetry. The earlier recurrence is therefore retained as a sample pattern rather than promoted to a deterministic task law.

## 7. System-condition descriptive topology

The cross-group sample is not used to rank frameworks.

Descriptively:

- X2 contributes 12 valid pairs: 3 persistence, 4 mixed, 3 targeted suppression, 1 targeted redirection, 1 regeneration.
- X4 contributes 11 valid pairs plus the G5 source-readiness boundary: 4 persistence, 3 mixed, 2 targeted redirection, 2 regeneration.
- X5 contributes 10 valid pairs plus two G2/G4 execution boundaries: 3 persistence, 4 mixed, 1 targeted redirection, 2 regeneration.
- X7 contributes 12 valid pairs: 8 persistence and 4 mixed.

These patterns describe the frozen study sample only. They are not framework scores and do not establish named-framework causal superiority or inferiority.

## 8. Boundary taxonomy is part of the engineering result

The final evidence contains two different boundary classes.

### B-execution no-effect boundary

Observed in G2:X5-T2 and G4:X5-T2.

A first B attempt existed, but the frozen legal mutation surface could not express a non-no-op repair. The first attempt was preserved. No automatic second repair, repair-scope enlargement, or rerun was used.

### Pre-B source-readiness boundary

Observed in G5:X4-T2.

A structural package existed, but the canonical Natural-A attempt lacked the seal required for legal same-parent continuation. No B provider call was made. The system did not fabricate a seal or replay the stochastic prefix.

These are engineering boundary observations, not negative repair-effect samples.

## 9. Control-plane integrity became part of the method

G3 exposed a separate problem in the experiment-control layer: receipt absence could temporarily be mistaken for an unconsumed first-attempt slot after provider execution but before evidence freeze.

Six duplicate provider-backed executions occurred in a later non-canonical run. They were disclosed and excluded.

The forward control rule was then hardened:

> **claim the group first-attempt population atomically before any provider call.**

From G5 onward:

- receipt absence is not authorization;
- the evidence branch must advance through a group-scoped execution claim before provider execution;
- a later workflow that cannot create the claim fails closed before provider calls.

This is itself a process-integrity lesson: the monitor/repair experiment requires integrity controls around the experiment-control plane as well as around the subject system.

## 10. Final engineering architecture

The complete Stage-II repair architecture is now:

`external passive monitor`
→ `source/descendant lineage localization`
→ `legal same-parent checkpoint`
→ `immutable structured repair package`
→ `atomic first-attempt execution claim`
→ `one-shot repair`
→ `repair executor exits`
→ `watch-only native continuation`
→ `independent process-semantic audit`
→ `cross-group synthesis`.

The engineering principles that survive all four groups are:

- do not modify native protocols/frameworks for experimental convenience;
- do not use stochastic rerun as repair;
- do not grow repair scope after an unfavorable first result;
- treat source readiness, repair legality, locality and downstream efficacy as separate gates;
- preserve boundaries and failed first attempts as evidence;
- keep semantic audit independent from online structural monitoring;
- keep terminal outcome separate from process integrity.

## 11. Provider-call accounting boundary

Provider accounting remains explicit rather than normalized away.

- G2: **557 known successful B provider calls**; whole-group accounting is incomplete because the failed X5-T2 boundary receipt does not expose a complete provider-call total.
- G3: **616**, complete for the canonical group.
- G4: **616 known successful B provider calls**; whole-group accounting is incomplete for the same X5-T2 boundary reason.
- G5: **675**, complete for the active 11-cell group.

No single exact G2–G5 total is asserted because G2 and G4 do not have complete provider-call accounting for their failed boundary attempts.

## 12. Claim boundary

This final engineering synthesis supports local mechanism and engineering-architecture claims under the frozen same-parent one-shot design.

It does **not** establish:

- population prevalence;
- repeat-run probability;
- universal repair success;
- framework ranking;
- deterministic task-family laws;
- hidden model reasoning;
- endpoint correctness as the definition of process repair success.

The primary object remains **process reality**: what structure actually continued after a legal local intervention.

## 13. Final closure

The G2–G5 engineering evidence chain is closed.

No additional G2–G5 experimental rerun is required for this engineering synthesis.

The next use of these materials is publication/report integration: connect the final engineering chapter with the Stage-II experimental general chapter, the natural-emergence evidence, monitoring metrics, semantic lineage evidence, and the paper's cross-system process-reality narrative.
