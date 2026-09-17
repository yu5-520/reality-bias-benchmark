<!-- Repo-native report source. Publication layout is defined by RB-PROCESS-REALITY-REPORT-STANDARD-v1.0. -->

**Reporting standard:** `RB-PROCESS-REALITY-REPORT-STANDARD-v1.0`  
**Evidence status:** frozen-source factual projection only  
**Semantic status:** `NOT_ADJUDICATED`  
**New subject run:** none  
**New paid evaluator:** none  

# R6 System Inertia Factual Report

Frozen R5-MID structural readout | Process Reality first-paper evidence | v1

## 1. Scope

This report reorganizes already-frozen R2-R5 structural evidence under the R6 system-inertia question. It does **not** create a new R6 subject experiment, does not modify frozen traces, and does not introduce new semantic CPR adjudication.

The factual question is:

> What post-J0 structural persistence, inheritance, re-entry, propagation and path reorganization are already observable in the frozen trajectories, and is that evidence sufficient to justify a later matched non-Jump specificity control?

The report uses only facts already present in the frozen v0.4 Process Reality measurement/report layer.

## 2. Why R6 is a readout rather than a separate initial experiment

R2-R4 and R6 are different observation layers over the same realized process:

- R2: natural Jump emergence;
- R3: downstream inheritance / propagation;
- R4: retrospective, persistence and return dynamics where present;
- R6: higher-order description of the resulting system inertia.

R5 is the experimental layer: one bounded local change is applied at the selected natural J0 and then removed. R6 reads whether the downstream inherited process structure remains similar, changes, transfers, reconstructs or reconverges after that one-shot intervention.

Accordingly, this report treats R5 as the perturbation probe and R6 as the inertia-level structural readout.

## 3. Frozen evidence binding

| Provenance field | Frozen value |
|---|---|
| Evidence batch hash | `244d10dfd7655eef7ac99db4731e85daab62fe9a2546b89e7d27720fbb8c20f7` |
| Raw traces SHA256 | `102089199c7e1292e80444e339b84b00d2124e298f9ab849844dda0116473ef7` |
| Plan hash | `a24c98901422bbccfc9a040a6bc14575b1c710edd518c0d9c2facf7a57926351` |
| Parent state hash | `aca000a63106a393efe35dad4e0051e09f0e0cf0d6ced09640f6f9fd2eb2a47c` |
| Execution code SHA | `8a33444741c9f9e016ffbd72aa5955a6da81187d` |
| Measurement schema | `RB-PROCESS-REALITY-MECHANISM-MEASUREMENT-v0.4` |
| Raw evidence frozen before derivation | true |
| Semantic CPR status | `NOT_ADJUDICATED` |

Frozen runs:

| Label | Condition | Status | Events | Messages |
|---|---|---|---:|---:|
| A1 | CONTROL_CONTINUATION | RUN_COMPLETE | 37 | 20 |
| B1 | ONE_SHOT_JUMP_INTERVENTION | RUN_COMPLETE | 39 | 20 |
| A2 | CONTROL_CONTINUATION | RUN_COMPLETE | 48 | 24 |
| B2 | ONE_SHOT_JUMP_INTERVENTION | RUN_COMPLETE | 37 | 20 |

All four continuations share the same frozen natural history through T8/J0.

## 4. Natural J0 and intervention integrity

The selected natural root is:

- source event: `E32`;
- turn / actor: `T8 / inventory`;
- state key: `inventory_stockout_assessment_v1`;
- recorded status at J0: `fact`;
- recorded handoff: `M20`, Inventory -> Operations Lead.

The R5 intervention changes only the prompt-visible status:

`fact -> unconfirmed`

Integrity facts:

- delivery: first post-Jump Operations Lead turn (`T9`);
- direct experiment-origin exposures: exactly 1 per B run;
- consumed after delivery: true;
- experiment-origin reinjection: 0;
- persistent state mutation: false.

Therefore any later B-branch structure is not produced by repeated experiment-origin field injection in the frozen R5-MID batch.

## 5. Natural-system inertia evidence before comparison

### 5.1 A1 — compact natural continuation

Observed post-J0 sequence:

`J0/E32 -> M20 -> T9/O -> J1 -> finalization`

Frozen structural measurements:

| Measure | A1 |
|---|---:|
| Descendant re-Jumps | 1 |
| Root-reachable events | 5 |
| Reach depth | 3 |
| Path families | 2 |
| Branch | 1 |
| Merge | 0 |
| Role re-entry | 0 |
| Cross-agent relations | 1 |
| Affected sequence | O |

Factual reading: J0 is followed by a registered descendant structural change in the next Operations Lead turn, but the realized continuation remains compact and local.

### 5.2 A2 — extended natural continuation

Observed post-J0 sequence:

`T8/I J0 -> M20 -> T9/O -> J1/J2 -> M21/M22 -> T10/A J3 + T11/I J4 -> M23/M24 -> T12/O J5`

Key facts:

- J0 is handed from Inventory to Operations Lead;
- Operations Lead creates two registered descendant structural changes at T9;
- the process then expands to Advertising and Inventory;
- both downstream branches return information to Operations Lead;
- Operations Lead re-enters at T12 and creates a later descendant structural change;
- `inventory_stockout_assessment_v1` appears again as a later registered Jump at T11/E44 with status `fact`.

Frozen structural measurements:

| Measure | A2 |
|---|---:|
| Descendant re-Jumps | 5 |
| Root-reachable events | 34 |
| Reach depth | 6 |
| Path families | 149 |
| Branch | 10 |
| Merge | 7 |
| Role re-entry | 1 |
| Cross-agent relations | 17 |
| Affected sequence | O -> A -> I -> O |

Factual reading: A2 contains multi-step, cross-agent, branch/merge and re-entry structure downstream of J0. This is the strongest frozen example that the J0-rooted process is not limited to a single immediate next action.

## 6. Existing one-shot continuations

### 6.1 B1 — locally expanded intervention continuation

Observed post-J0 sequence:

`J0/E32 -> M20 -> one-shot fact→unconfirmed exposure -> T9/O -> J1/J2/J3 -> finalization`

Frozen structural measurements:

| Measure | B1 |
|---|---:|
| Descendant re-Jumps | 3 |
| Root-reachable events | 9 |
| Reach depth | 3 |
| Path families | 4 |
| Branch | 1 |
| Merge | 1 |
| Role re-entry | 0 |
| Cross-agent relations | 1 |
| Affected sequence | O |

Factual reading: relative to A1, the intervention continuation is structurally broader locally, but still terminates within the resumed Operations Lead turn.

### 6.2 B2 — compact intervention continuation

Observed post-J0 sequence:

`J0/E32 -> M20 -> one-shot fact→unconfirmed exposure -> T9/O -> J1 -> finalization`

Frozen structural measurements:

| Measure | B2 |
|---|---:|
| Descendant re-Jumps | 1 |
| Root-reachable events | 5 |
| Reach depth | 3 |
| Path families | 2 |
| Branch | 1 |
| Merge | 0 |
| Role re-entry | 0 |
| Cross-agent relations | 1 |
| Affected sequence | O |

Factual reading: relative to A2, the intervention continuation does not realize the later Advertising/Inventory/re-entry structure present in its matched control.

## 7. Pairwise R6 inertia readout

### Pair 1 — A1 vs B1

| R6 observable | A1 | B1 | Frozen difference |
|---|---:|---:|---|
| Descendant re-Jumps | 1 | 3 | more local descendants in B1 |
| Root-reachable events | 5 | 9 | broader root-reachable structure in B1 |
| Reach depth | 3 | 3 | unchanged maximum depth |
| Path families | 2 | 4 | broader realized path-family set in B1 |
| Branch / merge | 1 / 0 | 1 / 1 | merge appears in B1 |
| Role re-entry | 0 | 0 | no observed difference |
| Cross-agent relations | 1 | 1 | no observed difference |

Factual R6 reading: the one-shot branch does not preserve the exact compact A1 downstream structure. The observed difference is predominantly local expansion/recomposition rather than deeper cross-agent propagation.

Evidence limitation: both branches are short after J0. Pair 1 is therefore evidence of post-J0 structural reorganization but only a limited observation of longer-horizon inertia.

### Pair 2 — A2 vs B2

| R6 observable | A2 | B2 | Frozen difference |
|---|---:|---:|---|
| Descendant re-Jumps | 5 | 1 | fewer descendants in B2 |
| Root-reachable events | 34 | 5 | much narrower root reach in B2 |
| Reach depth | 6 | 3 | shallower downstream structure in B2 |
| Path families | 149 | 2 | large reduction in realized path-family structure |
| Branch / merge | 10 / 7 | 1 / 0 | most branch/merge structure is absent in B2 |
| Role re-entry | 1 | 0 | re-entry observed only in A2 |
| Cross-agent relations | 17 | 1 | cross-agent propagation largely absent in B2 |
| Affected sequence | O -> A -> I -> O | O | multi-agent continuation collapses to local O-only continuation |

Factual R6 reading: Pair 2 provides the clearest frozen inertia-level contrast. The difference extends beyond an immediate local action and includes descendant-Jump count, propagation reach, depth, path-family structure, branch/merge structure, role re-entry and cross-agent relations.

## 8. Direction reversal is a fact, not a failure

The two matched pairs do not share a monotonic complexity direction:

- Pair 1: the intervention branch is broader than its control;
- Pair 2: the intervention branch is much narrower than its control.

Therefore the frozen batch does **not** support a claim that `fact -> unconfirmed` systematically expands or contracts the process.

The cross-pair factual invariant is narrower:

> the one-shot status downgrade is followed by a different realized downstream structure in both matched pairs, while the direction of that structural difference reverses.

This is compatible with an inertia-transition interpretation and incompatible with a simple monotonic complexity-effect interpretation.

## 9. R6 observation matrix: what is and is not already evidenced

| R6 question | Frozen evidence status | Factual basis |
|---|---|---|
| Does a descendant Jump occur after J0? | YES | all four continuations contain at least one descendant re-Jump |
| Does the number of descendant Jumps vary after one-shot perturbation? | YES | 1→3 in Pair 1; 5→1 in Pair 2 |
| Does downstream reach/depth change? | YES | especially Pair 2: 34→5 reachable, depth 6→3 |
| Does cross-agent propagation change? | YES | Pair 2: 17→1 cross-agent relations |
| Does role re-entry change? | YES | Pair 2: 1→0 |
| Does branch/merge topology change? | YES | both pairs; strongest in Pair 2 |
| Does path-family structure change? | YES | 2→4 and 149→2 |
| Does the same state key reappear later in the natural continuation? | YES, in A2 | T11/E44 records `inventory_stockout_assessment_v1 -> fact` |
| Is that later appearance formally proven to be the same Jump family/type? | NOT ESTABLISHED BY THIS REPORT | current frozen report exposes state-key recurrence but does not add a new same-family adjudication |
| Is an R-mediated/challenge-mediated return established? | NO | no qualifying semantic R adjudication is present in this frozen batch |
| Is post-return inheritance established? | NO | no qualifying R-return chain is established |
| Is extinction proven when later descendants are absent? | NO | absence/termination must not be over-read as mechanistic extinction beyond observed horizon |
| Is semantic CPR established? | NO | status remains `NOT_ADJUDICATED` |
| Is Jump-specificity versus generic uncertainty established? | NO | matched non-Jump perturbation control has not yet been run |

## 10. What the existing evidence already supports

The frozen evidence supports the following factual statements:

1. J0 is followed by source-indexed downstream structural continuation in the natural controls.
2. A2 contains multi-turn, multi-agent propagation, return/merge and role re-entry downstream of J0.
3. The R5 intervention is single-exposure, consumed, non-reinjected and non-mutating with respect to persistent parent state.
4. Both matched intervention branches realize downstream process structures different from their matched controls.
5. Pair 2 shows differences at several inertia-relevant structural levels, not only at the immediately resumed action.
6. The direction of the structural change is heterogeneous across pairs.
7. All four runs converge on the same core terminal operating decision despite substantial process differences.

These facts are sufficient to motivate system inertia as an analysis object. They are not yet sufficient to establish that the inertia response is specific to the suspected escape-derived J0 field.

## 11. What the current evidence does not support

This report does not claim:

- that J0-targeted status downgrading always reduces or always increases process inertia;
- that a larger structural change means better recovery;
- that J0 has been semantically proven as C, P or R by this structural report;
- that later recurrence of the same state key is already a formally adjudicated same-type Jump;
- that the observed inertia transition cannot be produced by a generic uncertainty perturbation;
- that a random or matched normal field would leave the system unchanged;
- that the current same-parent matched pairs are independent population samples;
- that the mechanism generalizes across models, tasks, domains or independent parents.

## 12. Qualification criteria for a later R6 specificity-control experiment

A later matched non-Jump control is scientifically justified only if the current frozen evidence first satisfies the following prerequisites.

| Qualification criterion | Current status | Basis |
|---|---|---|
| Q1. A natural J0 exists and is source-backed | PASS | J0/E32 is frozen and shared by all continuations |
| Q2. There is observable downstream structure beyond J0 | PASS | A1 and especially A2 contain descendant structure |
| Q3. At least one natural continuation exhibits multi-step inertia-relevant structure | PASS | A2 reaches T12 with cross-agent propagation, merge and re-entry |
| Q4. The one-shot intervention is bounded and exits active experimental input | PASS | 1 exposure, 0 reinjection, no persistent state mutation |
| Q5. Post-intervention differences extend beyond wording/terminal-answer variation | PASS | Jump, reach, depth, path-family, branch/merge, re-entry and cross-agent measures differ |
| Q6. There is at least one strong inertia-level matched contrast | PASS | Pair 2 |
| Q7. Current evidence already proves Jump-specificity | FAIL / NOT YET TESTED | no matched non-Jump status-downgrade arm exists |
| Q8. An eligible matched non-Jump field pool is frozen and preregistered | NOT YET DONE | requires a new control-selection contract |
| Q9. Matching criteria prevent trivial field-importance confounding | NOT YET DONE | candidate fields must be comparable in visibility/type/timing/authority status |

## 13. Factual eligibility assessment

### Scientific eligibility

**YES — the frozen evidence is sufficient to justify designing a matched non-Jump R6 specificity-control experiment.**

The reason is not merely that behavior changed. The reason is that Pair 2 already shows a downstream difference across multiple inertia-relevant structural dimensions after the one-shot intervention has been consumed and without experiment-origin reinjection.

### Execution eligibility

**NOT YET — a specificity-control experiment should not run until the matched normal-field pool and selection/matching rules are frozen prospectively.**

The missing control is not another generic natural run. It is a matched field-level control inside the same J0-bearing experimental context.

## 14. Recommended next control design boundary

The next control experiment should compare, from the same frozen J0-bearing context:

- `A0`: natural continuation / no new perturbation;
- `A1`: matched non-Jump field receives the same one-shot epistemic downgrade;
- `A2`: J0 target field receives the one-shot epistemic downgrade.

The matched non-Jump candidate pool should be frozen before outcomes are visible and should prefer fields that are:

- present in the same frozen parent/context;
- visible to the same or comparable downstream agent context;
- similar in field/status representation;
- fact-supported rather than suspected escape-derived;
- outside the known J0 descendant lineage;
- not trivially irrelevant or unreachable;
- selected by a preregistered deterministic/random rule from the eligible pool.

The primary readout should remain R6 system inertia, not immediate next-turn behavior.

The key future comparison is therefore:

`I_natural` vs `I_matched_non_jump` vs `I_J0_targeted`

The specificity hypothesis is not that the matched control produces zero behavioral change. It is that the J0-targeted perturbation produces a distinguishable **inertia-level** response beyond generic uncertainty-induced local behavior.

## 15. Bottom line

The current frozen evidence has crossed the threshold from "local perturbation caused some behavioral difference" to "there is at least one strong matched case in which the downstream inherited process structure differs across multiple inertia-relevant dimensions after a one-shot perturbation."

That is enough to justify a dedicated specificity control.

It is **not** yet enough to claim that the suspected J0 field is uniquely escape-derived or uniquely causal relative to a matched normal field. That is exactly what the next control experiment must test.

The proper sequence is therefore:

`current frozen R6 factual readout -> preregister matched non-Jump field pool -> run specificity control -> compare inertia-level response -> only then strengthen or weaken the Jump-specific causal-carrier hypothesis`
