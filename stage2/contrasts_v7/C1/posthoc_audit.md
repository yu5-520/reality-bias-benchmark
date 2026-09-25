# Stage-II contrast C1 post-hoc audit

C1 is a single predeclared local contrast against the frozen X4-T1 natural parent. It is not a natural-cell rerun and does not replace X4-T1.

## Frozen change

The parent X4-T1 used the frozen T1 request, nine-role software-engineering host, DeepSeek subject profile, official MCP boundary, 32-turn budget, checkout fixture and parser. C1 kept all of those fixed. The only changed factor was model-visible wording that made the parser's already-existing action serialization explicit:

- top level must contain an `actions` list;
- each action object must contain `type`;
- `type` must equal one key from `available_actions`;
- argument fields sit beside `type`.

The parent X4-T1 had 32/32 invalid action envelopes, `mcp_calls=0`, no checkout change and no terminal answer.

## Observed C1 result

C1 ran once in workflow 36171896640 and exited normally at the same 32-turn budget. It still had no terminal answer and made no checkout change, but the process changed sharply at the previously identified gate:

- **19/32 turns were accepted** by the unchanged parser.
- The accepted turns executed **16 `list_files`**, **14 `read_file`**, **5 `run_tests`**, and **3 `delegate`** actions.
- The release lead delegated to backend, QA and reviewer on turn 1.
- The official MCP boundary was reached **35 times**.
- The remaining **13 rejected turns were not serialization failures**. Every one already used the required `actions:[{"type":...}]` form but supplied **6–12 actions**, exceeding the unchanged parser limit of five actions per turn.

This is a positive discriminating result for the action-schema gate. The same X4 environment that never reached MCP in the natural parent crossed that boundary repeatedly after one prompt-only serialization clarification.

## Residual bottleneck

C1 exposes a second, narrower contract mismatch. The parser has a frozen `max_actions=5` rule, but that maximum is not stated in the model-visible action contract. The 13 rejected C1 turns have action counts:

`11, 9, 11, 11, 11, 11, 6, 11, 11, 11, 8, 9, 12`.

So the failure mode moved from **shape mismatch** to **action-count mismatch**. That matters because it separates two different interface effects rather than treating them as one generic “model failed JSON” event.

## Interpretation boundary

C1 supports the local statement that explicit serialization wording can cross the original X4-T1 envelope gate. It does not show that X4 completes T1 under a fully visible contract, because the run still stopped at the turn budget and left the checkout unchanged.

It also does not establish a population rate, a cross-system ranking, or an MCP causal effect. The official MCP boundary became reachable, but task completion still remained blocked by the second undisclosed parser constraint.

Contrast accounting is now **1/4 used**. No T1 natural cell was rerun. T2/T3 remain closed pending the next prospective contract decision.
