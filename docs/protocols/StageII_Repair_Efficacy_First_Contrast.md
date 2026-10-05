# Stage II first repair-efficacy contrast

Status: **FROZEN BEFORE THE SINGLE ENHANCED-B EXECUTION**.

This protocol overrides engineering-completeness sequencing for the paper experiment. The enhanced monitor has already been evaluated; the present scientific question is whether the enhanced repair method changes downstream process behavior more effectively than the historical local/package method.

## 1. One same-parent comparison

The first case is `G3-X4-T2` at native sequence 4, parent checkpoint
`98a72990529ea23b994511beb7bdf19ac5f3aa29c5e06a748711c3362455a2f3`.
The original task, subject configuration, native ceiling 64 and remaining horizon 60 are fixed.

Arm A is not rerun. It is the canonical frozen local repair from workflow `36309205795`,
package `g1pkg:0f95ddfd0d1341eb815d5a83`. That intervention reopened the local file-list
process state and the sealed paired audit classified the downstream result as `REGENERATION`:
the repaired suffix expanded to the turn budget and changed `app.js`,
`checkout_app/api.py` and `index.html`.

Arm B is the only new branch. It uses the already implemented sequence-4
`PrefixMCPContext`, complete prefix evidence graph and source-bound native MCP route repair.
The plan is frozen from prefix-only source inspection before this execution. It changes the
conditional alternate launcher default in `run.py` from legacy-on to current-off while
preserving explicit compatibility mode and the documented direct route. Historical actual
use of the alternate launcher remains unknown and is retained as uncertainty.

## 2. What is deliberately *not* required

Autonomous diagnosis/planning is not part of this efficacy treatment. The evidence-selection
gate contrast, generic planner reliability, seven-system repair reuse, automatic recovery and
additional field infrastructure do not block this experiment.

This separation is intentional. Otherwise the treatment would combine graph quality, planning
reliability, tool-use compliance and repair method in one comparison. Here the repair plan is
source-bound and frozen, so the new observation concerns the downstream effect of the repair
method itself.

## 3. Execution rule

Only Arm B is executed:

`same parent -> frozen route repair -> repair executor exit -> original subject continuation -> enhanced external monitoring -> independent semantic/authority review`

There is no Natural-A rerun, no Arm-A rerun, no automatic retry and no paid reviewer.
The subject retains the original 64-turn ceiling and all 60 calls remaining at the parent.
The B result is frozen whether it finalizes, reaches the ceiling, fails at a native boundary
or produces an unfavorable trajectory.

The repair executor may perform the already frozen one-file route action and its host-defined
controlled verification. Passing that verification is not efficacy. Efficacy is evaluated only
from the continued process.

## 4. Primary comparison

The independent review compares Arm B with the already sealed Arm A on:

- direct target effect and overall process effect;
- route divergence, collaboration-scope change and temporal reach;
- preservation of unrelated process structure;
- old C/P authority after continuation, historical re-entry and transformed descendants;
- process-account consistency and independent reconstruction.

Endpoint correctness is secondary. A write, test pass, final answer or shorter route cannot
alone establish repair success.

## 5. Paper boundary

This is a single same-parent method contrast chosen because the historical local intervention
already exhibits a strong regeneration outcome. It does not estimate repeat-run probability
or universal repair effectiveness. If the enhanced route repair is cleaner, equivalent, worse
or blocked, that first-attempt outcome is retained. Additional cases are selected only after
this result is interpreted.

Machine-readable contract:
`configs/stage2_repair_efficacy_first_contrast_v1.json`.

Runner:
`scripts/run_stage2_repair_efficacy_first_contrast.py`.
