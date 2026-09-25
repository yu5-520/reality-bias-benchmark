# Stage-II runtime binding lock — R Plan v6.3

Date: 2026-09-25. Status: **RUNTIME TARGET / SUBJECT PROFILE LOCK; NATIVE SMOKE STILL REQUIRED**.

This prospective clarification advances Day 1 without creating subject evidence. It preserves v6.0-v6.2, the 21-cell geometry, T1-T3 prompts, nine software-engineering roles and all frozen Stage-I evidence.

## Subject profile

Stage II reuses the existing Software Engineering arena subject profile rather than silently changing the model while changing system layer:

- provider: DeepSeek;
- model alias: `deepseek-flash`, expected `DeepSeek-V4.1-Flash`;
- thinking disabled; temperature 0.7; maximum 4096 output tokens per model call;
- maximum 32 turns, 64 model invocations and 128 pending messages per natural trajectory;
- transport timeout 60 s with at most two transport attempts;
- no automatic paid evaluator;
- exactly one natural trajectory per passed X1-X7 × T1-T3 cell.

The machine-readable binding is `stage2/subject.json`.

## Runtime targets

`stage2/runtime_bindings.json` freezes the exact implementation target for every probe. X3 and X4 bind protocol identity separately from their official Python SDK identity. The remaining source commits are inherited from v6.2. X5 remains the in-repository retrieval implementation with its frozen SHA-256.

## Gate semantics

A successful install/import/symbol probe means only **runtime surface ready**. It is not a native evidence smoke and cannot open the 21-cell subject gate.

The next gate still requires, for each probe: actual native capture through the frozen hook; original boundary bytes and native locator; a completed non-study smoke sequence ending in termination; evidence-chain validation; and a runtime manifest binding installed version, implementation identity, hook, subject profile and repository code SHA.

If a probe cannot expose its real boundary, it becomes `ENGINEERING_BLOCKED`; no framework substitution or Common-Pool alias is allowed.

No paid subject call, new R5, R6 intervention or R7 repair is authorized by this file.
