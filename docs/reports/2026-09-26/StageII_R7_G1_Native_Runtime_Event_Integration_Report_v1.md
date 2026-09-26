# Stage-II R7 G1 Native Runtime Event Integration Report v1

Date: 2026-09-26  
Status: **NATIVE EVENT → CHECKPOINT → PREFIX MONITOR INTEGRATION PASS / SCIENTIFIC SUBJECT EXECUTION CLOSED**

## 1. Purpose

The prior phases separately proved checkpointing and the prefix-only monitor. This phase tests the actual bridge between native execution and those two systems.

The required property is not merely that each subsystem works alone. A completed native model turn must produce an exact resumable checkpoint, then its already-realized structural action/carrier evidence must enter the prefix monitor without changing the native control flow, checkout effects, or framework/protocol boundary.

## 2. Passive runtime bridge

The prospective provider tap copies the already-returned action envelope and returns the original provider result unchanged.

The bridge does not inject monitor data into prompts. It waits until the native round/turn has completed and a FULL_NATIVE checkpoint has been recorded. Only then does it normalize the completed action copy into structural events and feed the prefix monitor against that checkpoint.

For external information carriers, temporal co-occurrence with an action is deliberately **not** treated as proof of downstream lineage.

## 3. X2 MetaGPT integration

Deterministic native MetaGPT execution and the monitored prospective execution used the same scripted five-decision path.

Result:

- native rounds: **5**;
- content-addressed checkpoints: **7** = task start + five completed rounds + terminal;
- normalized structural events: **6**;
- structural candidates: **1**;
- repair packages: **1**;
- `COMPLETE_FOR_STRUCTURED_REPAIR`: **1**;
- control-flow equivalence: **PASS**;
- checkout equivalence: **PASS**;
- provider/subject calls: **0**.

The repeated `README.md` structural episode first became repair-eligible after model decision 3. Its exact frozen parent was:

`d691d1706181e2f0446c853d1d9c21a0be9bd9d0f03e1c169019114af6957367`.

Natural A then continued to model decision 5 without changing the frozen package or parent.

The resulting prospective run-manifest hash was:

`dd073aaf44d7c6814847fbbbef0e0446f7e9f7e468067d25dfb45e642a23161f`.

## 4. X5 RAG + common host integration

The RAG condition exercises both host actions and an immutable external information carrier.

Result:

- scripted model decisions: **5**;
- checkpoints: **7**;
- normalized structural events: **21**;
- candidates/packages: **4**;
- one repeated application-file package: `COMPLETE_FOR_STRUCTURED_REPAIR`;
- three repeated RAG-hit packages: `LINEAGE_GAP_BLOCKED`;
- control-flow equivalence: **PASS**;
- checkout equivalence: **PASS**;
- provider/subject calls: **0**.

The repair-eligible file package froze after decision 3 at:

`e7ac2c57721af99ef0073cc624e8f644d4cf9f63343a1daabc47511e7e6e0261`.

Natural A again continued to decision 5.

The RAG hits remained observable pressure/support candidates, but because the runtime evidence did not machine-bind them to a legal downstream repair surface, the monitor did **not** infer such a lineage from temporal proximity. All three stayed `LINEAGE_GAP_BLOCKED`.

The prospective run-manifest hash was:

`02ed2c25a187986170265f4d8decb1aa318f7838d2011d85e190704c6c1113fa`.

## 5. Parent-freeze clarification

This phase exposes an important timing distinction.

`checkpoint freshness at package freeze` is not the same question as `is that checkpoint still the current state after natural A later continues?`

For the G1 A/B geometry, the exact repair parent must be valid **when the package freezes**. After that, natural A is supposed to continue and be frozen before B begins. Those later A decisions do not retroactively invalidate the already-content-addressed parent.

The controller therefore now exposes both views:

- `repair_parent_at_freeze()` — historical exact parent bound to the package;
- `repair_parent()` — stricter check for callers asking whether that same parent is still the current runtime state.

In both X2 and X5 preflight, the historical parent remained available after A completed, while the stricter current-state check correctly reported that later model decisions had occurred.

## 6. X1 and X3 remain fail-closed

This integration does not manufacture unsupported mid-run state.

- X1 AutoGen in-flight parent: `CHECKPOINT_BOUNDARY_BLOCKED`;
- X3 nested active A2A call parent: `CHECKPOINT_BOUNDARY_BLOCKED`.

Their already-verified checkpoint infrastructure is retained for legal quiescent boundaries, but G1 does not patch the frameworks or protocols to invent new ones.

## 7. Run-manifest readiness

Each prospective run can now bind:

- frozen scientific inputs;
- checkpoint ledger;
- natural A archive hash;
- prefix-monitor output hash;
- repair-package gate state;
- provider accounting;
- semantic-audit lock state.

The manifest remains `LOCKED_UNTIL_A_AND_B_FROZEN` for semantic audit.

## 8. Handoff

The offline integration stack is now complete enough to define the final G1 scientific execution readiness gate and explicit subject-call ceiling.

No scientific subject call or active repair call is authorized by this report itself.
