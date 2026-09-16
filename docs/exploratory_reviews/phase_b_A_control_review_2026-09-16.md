# Phase-B Exploratory Review A — Control Continuation

Date: 2026-09-16  
Scope: exploratory pilot review only  
Source run: GitHub Actions `35108633026`  
Condition A: `CONTROL_CONTINUATION`  
Frozen parent: `r5r6-ecommerce-baseline-0002`  
Parent state hash: `9bd705d76b15726b64b941d16604a83933cd1b635bb1af9845e82aa9581a05ce`

## 1. Review status

This report is an exploratory structural review of the Control condition. It is **not** a formal semantic review and is **not** a frozen primary-analysis evidence report.

The original Phase-B run completed subject execution and downstream structural derivation, but its raw evidence artifact was not durably persisted because `actions/upload-artifact` rejected journal filenames containing `:`. Therefore this report uses only run-level facts and hashes that remain independently recorded in the GitHub job log and repository provenance record.

Semantic claims about agent reasoning, C/P/R, Authority Penetration, task quality, causal mechanism or downstream content are intentionally left `NOT_ADJUDICATED`.

## 2. Observed A trajectories

| Pair | Condition | Observed status | Observed turns | Interpretation boundary |
|---|---|---:|---:|---|
| Pair 1 | Control | `RUN_COMPLETE` | 13 | Natural completion observed |
| Pair 2 | Control | `BUDGET_CENSORED` | 32 | Only an observed prefix; natural endpoint unknown |

Observed Control turns: `13` and `32+` where the second value is censored at 32 turns. The arithmetic mean of `22.5` observed turns is **not** a valid estimate of natural episode length because one trajectory is right-censored.

The cumulative engineering spend immediately after the two Control executions was recorded as `0.00475357 USD` after Pair 1 Control and `0.10734904 USD` after the final Pair 2 Control. Because the second value is cumulative across the full four-run sequence, it must not be interpreted as the isolated cost of Pair 2 Control without reconstructing the preceding cumulative increments.

## 3. Structural review

### A1 — Control does not have a stable continuation length in this pilot

The two Control replicates diverged strongly in observed continuation length: one naturally completed at 13 turns, while the other remained active through 32 turns and was censored. This is direct evidence that the frozen parent plus unchanged epistemic status does **not** produce a deterministic continuation length under the current stochastic subject-model setting.

This matters because future A/B interpretation cannot treat one Control trajectory as a fixed baseline. Replicate-level variability is part of the phenomenon being measured, not merely engineering noise to be removed after the fact.

### A2 — The censored Control must remain censored

Pair 2 Control cannot be encoded as a 32-turn natural completion. Its absence of later events means only “not observed beyond the recorded window.” It cannot support claims such as “the Control stopped at 32 turns,” “no later anchor-reachable action occurred,” or “the branch naturally failed to terminate.”

The evidence layer correctly preserved this as `BUDGET_CENSORED` rather than forcing a terminal result.

### A3 — The censoring source is an engineering/observation issue, not a semantic result

The final engineering estimated spend was only `0.10734904 USD`, well below the authorized `2 USD` monetary ceiling. The preserved high-level record does not durably retain enough budget-summary detail to prove which specific guard triggered the censoring. Therefore this report does not infer whether the limiting factor was call count, a runtime guard, or another bounded-resource condition.

That distinction should be made explicit in any later formal report.

## 4. What A currently supports

A supports the following exploratory statements:

1. The unchanged frozen parent can generate materially different continuation lengths across replicates.
2. One Control continuation naturally completed and one was censored, so the Control condition already contains substantial run-to-run variability.
3. A future formal experiment should preserve this variability rather than collapse the Control condition into a single reference trajectory.
4. Censoring must remain first-class in the analysis contract; missing future behavior must not be converted to zero.

## 5. What A does not support

A does **not** currently support:

- a semantic assessment of whether the agents used or ignored `inventory_transfer_feasibility`;
- a claim that Control is more stable, less stable, better, worse, shorter or longer than Intervention;
- a claim about C, P, R, Authority Penetration or Reality Bias;
- a task-success judgment;
- a causal claim;
- a complete estimate of Control episode length.

## 6. Exploratory design implication

The main design signal from A is not “Control is long” or “Control is short.” It is that the same frozen parent can produce a short natural completion and a long censored continuation under repeated execution. That makes within-parent stochastic variability a real component of the experimental object.

For the next formal evidence batch, the current parent-aware paired design remains appropriate, but observation-window and censoring handling should stay explicit. Any future change from natural-until-quiescent observation to a fixed-K observation window would constitute a new experimental version and must not be retroactively applied to this pilot.

## 7. Review conclusion

**Exploratory A assessment:** Control is operationally viable but highly variable in this two-replicate pilot. The strongest finding is the existence of substantial within-condition trajectory variability and one censored run. No semantic or causal conclusion should be drawn from A alone.
