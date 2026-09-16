<!-- Repo-native report source. Publication layout is defined by RB-PROCESS-REALITY-REPORT-STANDARD-v1.0. -->

**Reporting standard:** `RB-PROCESS-REALITY-REPORT-STANDARD-v1.0`  
**Evidence status:** frozen; reporting projection only  

**REALITY BIAS | PROCESS REALITY**

One-shot intervention process evidence report

Group B | Bounded local perturbation followed by natural continuation | v3

| **Condition**                 | ONE_SHOT_JUMP_INTERVENTION                                                                                      |
|-------------------------------|-----------------------------------------------------------------------------------------------------------------|
| **Frozen runs**               | B1 and B2                                                                                                       |
| **Representative trajectory** | B1: structurally richest valid intervention run                                                                 |
| **Single change**             | inventory_stockout_assessment_v1 status: fact -> unconfirmed                                                   |
| **Delivery**                  | first post-Jump Operations Lead turn; consumed after one exposure; no reinjection; no persistent state mutation |

Group B is designed to isolate one bounded change in the agent-visible runtime view and then return control to the natural multi-agent process. The report therefore separates the intervention marker from all subsequent agent actions: only the blue star is experimental; every downstream message, state write, Jump and finalization is observed from the run.

## Notation and visual grammar

| **Code / mark**   | **Meaning**                                         | **Visual role**          |
|-------------------|-----------------------------------------------------|--------------------------|
| T#                | executed agent turn                                 | time order               |
| E#                | source event in frozen event ledger                 | evidence lookup          |
| M#                | recorded agent message                              | information handoff      |
| J#                | structural Jump derived under v0.4                  | structural transition    |
| O / A / I / F     | Operations Lead / Advertising / Inventory / Finance | agent identity           |
| solid arrow       | observed message handoff                            | information causality    |
| thick dashed line | descendant Jump lineage                             | structural inheritance   |
| blue star         | one-shot intervention exposure                      | experimental change only |

# Intervention contract

| **Field**                          | **Frozen value**                 |
|------------------------------------|----------------------------------|
| Target source event                | E32 / J0                         |
| State key                          | inventory_stockout_assessment_v1 |
| Prompt-visible change              | fact -> unconfirmed             |
| Delivery turn / actor              | T9 / O                           |
| Delivery policy                    | FIRST_POST_JUMP_AGENT_TURN       |
| Consumed after delivery            | true                             |
| Persistent state mutation          | false                            |
| Experiment-origin reinjection      | 0                                |
| Direct experiment-origin exposures | 1 per B run                      |

# Representative intervention trajectory: B1

> **Figure display:** publication figure is embedded in the finalized DOCX export; the caption and all referenced evidence remain versioned below.

Figure 1 | Full B1 execution chronology. The blue band marks the single experimental exposure between J0 at T8 and the resumed Operations Lead turn at T9. The run contains no later experiment-origin reinjection.

> **Figure display:** publication figure is embedded in the finalized DOCX export; the caption and all referenced evidence remain versioned below.

Figure 2 | B1 temporal causal path after J0. M20 is the recorded Inventory-to-Operations Lead handoff. The one-shot change is visible once before T9. Three descendant Jumps (J1-J3) then arise within T9 before finalization.

## B1 reference dictionary

| **Ref** | **Time** | **Actor / route** | **Jump** | **Frozen meaning**                         |
|---------|----------|-------------------|----------|--------------------------------------------|
| E32     | T8       | I                 | J0       | inventory_stockout_assessment_v1 -> fact  |
| E34     | T8       | I                 | -        | finalized                                  |
| E35     | T9       | O                 | J1       | promo_inventory_plan_v1 -> recommendation |
| E36     | T9       | O                 | J2       | final_operating_plan_v1 -> recommendation |
| E37     | T9       | O                 | J3       | final state revised                        |
| E38     | T9       | O                 | -        | finalized                                  |
| M20     | T8->T9  | I->O             | -        | observed agent message                     |

## B1 causal reading

| **Stage**                      | **Observed sequence**              | **Structural reading**                                                   |
|--------------------------------|------------------------------------|--------------------------------------------------------------------------|
| Root                           | T8 I: E32/J0 -> M20               | same natural root and same recorded handoff as matched control           |
| Perturbation                   | one-shot at first post-Jump O turn | only prompt-visible status changes; persistent state remains unchanged   |
| Immediate descendant structure | T9 O: E35/J1, E36/J2, E37/J3       | the resumed turn produces three registered descendant structural changes |
| Termination                    | E38 finalization                   | the realized path remains local to O rather than recruiting new agents   |

# Intervention replicate B2

B2 is also fully frozen and measured. Its post-root continuation is more compact than B1 and is therefore displayed as a short causal path plus the same reference dictionary.

> **Figure display:** publication figure is embedded in the finalized DOCX export; the caption and all referenced evidence remain versioned below.

Figure 3 | B2 temporal causal path after J0. The one-shot exposure is followed by a single descendant Jump at T9 and finalization.

| **Ref** | **Time** | **Actor / route** | **Jump** | **Frozen meaning**                         |
|---------|----------|-------------------|----------|--------------------------------------------|
| E32     | T8       | I                 | J0       | inventory_stockout_assessment_v1 -> fact  |
| E34     | T8       | I                 | -        | finalized                                  |
| E35     | T9       | O                 | J1       | final_operating_plan_v1 -> recommendation |
| E36     | T9       | O                 | -        | finalized                                  |
| M20     | T8->T9  | I->O             | -        | observed agent message                     |

# Within-intervention structural variability

| **Run** | **re-Jumps** | **Reachable** | **Depth** | **Path families** | **Branch** | **Merge** | **Re-entry** | **Cross-agent** | **Affected sequence** |
|---------|--------------|---------------|-----------|-------------------|------------|-----------|--------------|-----------------|-----------------------|
| B1      | 3            | 9             | 3         | 4                 | 1          | 1         | 0            | 1               | O                     |
| B2      | 1            | 5             | 3         | 2                 | 1          | 0         | 0            | 1               | O                     |

The intervention condition also shows conditional variability: B1 expands locally within the resumed Operations Lead turn, while B2 remains compact. The experiment therefore does not imply a fixed direction of path size; the paired report tests whether a bounded change is associated with reorganization of realized process structure.

# Evidence provenance and traceability

The report is a display layer over evidence that was recorded and frozen before report generation. A trajectory can be shown compactly without being absent from the evidence set. All runs below have preserved raw traces and v0.4 measurements.

| **Label** | **Frozen run ID**                                                               | **Condition**              | **Status**   | **Events** | **Messages** | **Measurement hash** |
|-----------|---------------------------------------------------------------------------------|----------------------------|--------------|------------|--------------|----------------------|
| B1        | prospective-ecommerce-natural-0001:oneshot-pair:0001:one_shot_jump_intervention | ONE_SHOT_JUMP_INTERVENTION | RUN_COMPLETE | 39         | 20           | ff647ff4a4138f4a...  |
| B2        | prospective-ecommerce-natural-0001:oneshot-pair:0002:one_shot_jump_intervention | ONE_SHOT_JUMP_INTERVENTION | RUN_COMPLETE | 37         | 20           | e58bcb3743c1ed75...  |

| **Provenance field**                  | **Frozen value**                                                 |
|---------------------------------------|------------------------------------------------------------------|
| Evidence batch hash                   | 244d10dfd7655eef7ac99db4731e85daab62fe9a2546b89e7d27720fbb8c20f7 |
| Raw traces SHA256                     | 102089199c7e1292e80444e339b84b00d2124e298f9ab849844dda0116473ef7 |
| Plan hash                             | a24c98901422bbccfc9a040a6bc14575b1c710edd518c0d9c2facf7a57926351 |
| Parent state hash                     | aca000a63106a393efe35dad4e0051e09f0e0cf0d6ced09640f6f9fd2eb2a47c |
| Execution code SHA                    | 8a33444741c9f9e016ffbd72aa5955a6da81187d                         |
| Measurement schema                    | RB-PROCESS-REALITY-MECHANISM-MEASUREMENT-v0.4                    |
| Raw evidence frozen before derivation | true                                                             |
| Semantic CPR status                   | NOT_ADJUDICATED                                                  |

> Interpretive boundary: structural Jump, branch, merge, re-entry, reach and path-family measurements are structural observations. Semantic CPR, generalized causal effects and cross-model generality are not adjudicated by this frozen batch.
