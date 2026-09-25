# Stage-II v7.21: prospective Action Contract v2 for T2/T3

Date: 2026-09-26. Status: **T1 NATURAL ROW 7/7 FROZEN UNDER HISTORICAL CONTRACT v1; C1+C2 FROZEN 2/4; T2/T3 PROSPECTIVELY GATED BY ACTION CONTRACT v2**.

C1 and C2 closed the experiment-owned action-envelope ambiguity without changing any framework implementation. C1 made the already-existing type-tagged serialization visible and moved X4 from 0/32 parser-accepted turns to 19/32. C2 additionally made the already-existing `max_actions=5` parser limit visible and reached 32/32 parser-accepted turns. No further parser-tuning contrast is justified.

This checkpoint therefore freezes a prospective model-visible contract boundary instead of rerunning T1.

## Contract map

- **T1 → `v1_t1_historical`**. The prompt remains byte-for-byte unaugmented by the new contract helper. All seven T1 first attempts remain immutable and are interpreted under the historical contract that actually produced them.
- **T2/T3 → `v2_t2_t3_prospective`** for the experiment-defined JSON-action surfaces used by X2–X7. The parser and action semantics are unchanged; only its pre-existing requirements are stated explicitly to the subject:
  - top-level `actions` list;
  - each action object contains `type`;
  - `type` equals one `available_actions` key;
  - action arguments sit beside `type`;
  - at most five actions per turn.
- **X1 AutoGen is excluded** from this helper because it keeps its native AutoGen tool interface. This is intentionally not a universal X adapter.

The machine-readable boundary is `stage2/native_v7/action_contract_registry.json`. The helper `action_contract.py` only augments model-visible prompt text/payload according to the frozen task map. It does not route calls, translate framework messages, change parser code, add tools, alter role scheduling or mutate observations.

The native integrations remain heterogeneous: X2 MetaGPT retains MetaGPT Environment/Message scheduling, X3 retains official A2A role services, and X4–X7 continue using only their registered capability boundaries on the frozen software-engineering host. The monitor remains external.

## Evidence accounting

This creates a deliberate version boundary across task families. T1 terminal/task outcomes must not be pooled as though they were collected under v2. T1 remains useful as the natural discovery/calibration row and as evidence for the C1/C2 local diagnosis. T2/T3 are the prospective rows after the execution contract was made internally coherent.

No natural trajectory is created by this checkpoint. Contrast accounting remains **2/4**. The next admissible scientific action is the one-shot **T2 row (X1–X7)** under the frozen task-specific contract map; after those seven attempts are preserved, perform read-only cross-cell audit before opening T3.
