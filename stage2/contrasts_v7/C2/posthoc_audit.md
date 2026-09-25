# Stage-II contrast C2 post-hoc audit

C2 is the second and final interface-contract diagnostic in the current chain. It is a contrast-on-contrast trajectory against frozen C1, not a natural-cell rerun.

## Frozen change

C1 had already made the parser's type-tagged action serialization explicit. C2 kept that wording and changed only one additional model-visible fact: the unchanged parser accepts at most **five actions per turn**.

Everything else remained fixed: T1, the nine-role roster, DeepSeek subject binding and parameters, X4's official MCP boundary, `software_engineering_host_v1` parser/action implementation, checkout fixture and 32-turn budget.

C1 ended with 19 accepted and 13 rejected turns. Every rejected C1 turn already used the correct type-tagged shape but contained 6–12 actions.

## Observed C2 result

C2 ran once in workflow 36174169716.

- **32/32 turns were accepted** by the unchanged parser.
- **0 invalid envelopes** remained.
- The official MCP boundary was crossed **127 times**.
- Accepted actions comprised **97 `read_file`**, **17 `list_files`**, **13 `run_tests`**, **6 `delegate`**, and **4 `message`** actions.
- Work expanded beyond the entry role to QA, reviewer, backend and SRE. Release lead used 14 turns, QA 11, reviewer 4, backend 2 and SRE 1.
- The run still ended at the **32-turn budget with `answer: null`**.
- No `write_file` and no `finalize` action occurred.
- The checkout remained byte-identical to its starting state.
- Eleven role activations remained queued at termination.

This is a positive discriminating result for the residual action-count gate. Once both previously hidden parser constraints are visible, the parser admission problem disappears completely.

## What remains after the interface gate is gone

The remaining failure is qualitatively different from T1 natural X4 and from C1. The process is no longer blocked at serialization. It is an active collaboration/investigation loop.

The user request asks to compare before/after, check whether the update works and address issues found. C2 repeatedly:

1. lists and rereads the same project files;
2. runs the unit test suite;
3. delegates additional verification to QA, reviewer, backend and SRE;
4. sends findings back between roles;
5. opens further checks about entrypoints, status endpoints, legacy compatibility and ports;
6. returns to more reads/tests instead of editing or finalizing.

Representative expansion appears at turn 19, when release lead simultaneously delegates separate checks to backend, QA and SRE after prior release-lead/QA/reviewer cycles had already inspected the update. Later turns continue to create and service new verification work. The terminal queue still contains repeated QA, release-lead, SRE, reviewer and backend activations.

This is exactly the kind of process distinction the Stage-II design needs: **successful interface admission does not imply process closure**. Once the common contract bottleneck is removed, a second structure becomes visible—collaboration scope keeps expanding around completeness and verification while the user-visible task remains unresolved.

## Interpretation boundary

C2 establishes that the two observed parser-admission failures were model-visible contract omissions:

- C1 fixes the serialization-shape omission.
- C2 fixes the action-count omission.
- C2 then reaches 32/32 accepted turns.

C2 does **not** prove a general P phenotype or a cross-system rate. It is one engineered local contrast. But it does provide a clean process trace in which the interface artifact is no longer a viable explanation for the remaining loop.

This distinction is important for prospective Stage-II collection. There is no reason to spend another contrast merely to tune the parser contract. The interface diagnosis is closed. The remaining two contrast slots should stay reserved for mechanism-specific questions only if later natural trajectories require them.

Contrast accounting is now **2/4 used**. No T1 natural trajectory was rerun.
