<!-- Repo-native report source. Publication layout is defined by RB-PROCESS-REALITY-REPORT-STANDARD-v1.0. -->

**Reporting standard:** `RB-PROCESS-REALITY-REPORT-STANDARD-v1.0`  
**Evidence status:** frozen; reporting projection only  

**REALITY BIAS | PROCESS REALITY**

Control continuation process evidence report

Group A | Natural post-Jump trajectories from the frozen parent | v3

| **Condition**                 | CONTROL_CONTINUATION                                                                         |
|-------------------------------|----------------------------------------------------------------------------------------------|
| **Frozen runs**               | A1 and A2                                                                                    |
| **Representative trajectory** | A2: structurally richest valid control run                                                   |
| **Primary display**           | temporal agent path + message causality + Jump lineage                                       |
| **Evidence policy**           | A1 remains fully indexed and measured; display compression does not reduce evidence coverage |

Group A establishes the natural baseline required by the perturbation experiment. The report therefore prioritizes the order in which agents execute, the messages that carry information forward, the state events that form structural Jumps, and the descendant structure that emerges without an experimental exposure.

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

# Shared task process before J0

All four matched continuations share the same frozen history through T8. The pre-root sequence is shown as an evidence index rather than as a dense interaction network; the causal diagrams begin at J0, where the experimental comparison becomes scientifically relevant.

| **Turn** | **Agent** | **Source events** | **Observed process role**                            |
|----------|-----------|-------------------|------------------------------------------------------|
| T1       | O         | E00-E04           | decompose task; invoke A/I/F; provisional promo plan |
| T2       | O         | E06-E10           | refresh provisional plan; re-invoke I/F/A            |
| T3       | A         | E11-E16           | return advertising assessment; write ads allocation  |
| T4       | I         | E17-E22           | return stockout assessment; write inventory state    |
| T5       | F         | E23-E28           | return finance assessment; revise final state        |
| T6       | O         | E29-E30           | integrate evidence; write final operating plan v1    |
| T7       | A         | E31               | finalize local turn                                  |
| T8       | I         | E32-E34           | write inventory fact J0; send M20 to Operations Lead |

# Representative natural trajectory: A2

> **Figure display:** publication figure is embedded in the finalized DOCX export; the caption and all referenced evidence remain versioned below.

Figure 1 | Full A2 execution chronology. The horizontal spine gives execution order only. T, E and J identifiers resolve directly to the frozen ledgers; long event descriptions are intentionally externalized to the tables.

> **Figure display:** publication figure is embedded in the finalized DOCX export; the caption and all referenced evidence remain versioned below.

Figure 2 | A2 temporal causal path after J0. Solid arrows are recorded agent messages (M#). The upper rail shows descendant Jump inheritance. The key structural feature is not the number of lines but the temporal sequence: J0 at T8 is handed to O at T9, O branches information to A and I, both return evidence, and O re-enters at T12.

## A2 reference dictionary

| **Ref** | **Time**  | **Actor / route** | **Jump** | **Frozen meaning**                                |
|---------|-----------|-------------------|----------|---------------------------------------------------|
| E32     | T8        | I                 | J0       | inventory_stockout_assessment_v1 -> fact         |
| E34     | T8        | I                 | -        | finalized                                         |
| E35     | T9        | O                 | J1       | promo_inventory_plan_v1 -> recommendation        |
| E38     | T9        | O                 | J2       | final state revised                               |
| E39     | T9        | O                 | -        | finalized                                         |
| E41     | T10       | A                 | J3       | ads_allocation_confirmation_v1 -> recommendation |
| E42     | T10       | A                 | -        | finalized                                         |
| E44     | T11       | I                 | J4       | inventory_stockout_assessment_v1 -> fact         |
| E45     | T11       | I                 | -        | finalized                                         |
| E46     | T12       | O                 | J5       | promo_inventory_plan_v1 -> recommendation        |
| E47     | T12       | O                 | -        | finalized                                         |
| M20     | T8->T9   | I->O             | -        | observed agent message                            |
| M21     | T9->T10  | O->A             | -        | observed agent message                            |
| M22     | T9->T11  | O->I             | -        | observed agent message                            |
| M23     | T10->T12 | A->O             | -        | observed agent message                            |
| M24     | T11->T12 | I->O             | -        | observed agent message                            |

## A2 causal reading

| **Stage**               | **Observed sequence**         | **Structural reading**                                           |
|-------------------------|-------------------------------|------------------------------------------------------------------|
| Root                    | T8 I: E32/J0 -> M20 -> T9 O | the selected natural Jump becomes visible to the next agent turn |
| Local recomposition     | T9 O: E35/J1 and E38/J2       | the first descendant structural changes occur one turn after J0  |
| Cross-agent propagation | M21 -> T10 A / M22 -> T11 I | the continuation expands beyond Operations Lead                  |
| Return and merge        | M23 + M24 -> T12 O           | two downstream branches return to the coordinating role          |
| Late descendant         | T12 O: E46/J5                 | the descendant structure persists through role re-entry          |

# Control replicate A1

A1 is a complete frozen run, not missing data. It is displayed compactly because its post-root continuation contains only one descendant re-Jump and no role re-entry.

> **Figure display:** publication figure is embedded in the finalized DOCX export; the caption and all referenced evidence remain versioned below.

Figure 3 | A1 temporal causal path after J0. The same M20 handoff reaches O at T9, followed by one descendant Jump and finalization.

| **Ref** | **Time** | **Actor / route** | **Jump** | **Frozen meaning**                         |
|---------|----------|-------------------|----------|--------------------------------------------|
| E32     | T8       | I                 | J0       | inventory_stockout_assessment_v1 -> fact  |
| E34     | T8       | I                 | -        | finalized                                  |
| E35     | T9       | O                 | J1       | final_operating_plan_v2 -> recommendation |
| E36     | T9       | O                 | -        | finalized                                  |
| M20     | T8->T9  | I->O             | -        | observed agent message                     |

# Within-control structural variability

| **Run** | **re-Jumps** | **Reachable** | **Depth** | **Path families** | **Branch** | **Merge** | **Re-entry** | **Cross-agent** | **Affected sequence** |
|---------|--------------|---------------|-----------|-------------------|------------|-----------|--------------|-----------------|-----------------------|
| A1      | 1            | 5             | 3         | 2                 | 1          | 0         | 0            | 1               | O                     |
| A2      | 5            | 34            | 6         | 149               | 10         | 7         | 1            | 17              | O -> A -> I -> O   |

The natural control condition is not structurally fixed: A1 remains compact whereas A2 expands into cross-agent propagation, branch/merge structure and role re-entry. This conditional variability is part of the process-level baseline and must not be averaged away before the A/B comparison.

# Evidence provenance and traceability

The report is a display layer over evidence that was recorded and frozen before report generation. A trajectory can be shown compactly without being absent from the evidence set. All runs below have preserved raw traces and v0.4 measurements.

| **Label** | **Frozen run ID**                                                         | **Condition**        | **Status**   | **Events** | **Messages** | **Measurement hash** |
|-----------|---------------------------------------------------------------------------|----------------------|--------------|------------|--------------|----------------------|
| A1        | prospective-ecommerce-natural-0001:oneshot-pair:0001:control_continuation | CONTROL_CONTINUATION | RUN_COMPLETE | 37         | 20           | bf3e4b5eddb01dab...  |
| A2        | prospective-ecommerce-natural-0001:oneshot-pair:0002:control_continuation | CONTROL_CONTINUATION | RUN_COMPLETE | 48         | 24           | 40c867d7a1125b17...  |

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
