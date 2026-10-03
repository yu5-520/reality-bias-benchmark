# Evidence coverage and old-monitor comparison

## What changed

| Item | Superseded P2 v1 replay | Corrected P2 v2 recovery replay |
| --- | --- | --- |
| Frozen population | G2–G5, 84 trajectories | Same 84 archives; archive SHA256 bindings checked |
| Native ingestion | Legacy layout adapter; each cell emitted the same 13 normalized events | 19,473 native capture records from the seven native surfaces |
| State evolution | Initial fixtures and terminal placeholders did not reconstruct the native checkpoints | 3,552 frozen checkpoints, with 122 observed file-hash changes |
| Field query | Aggregated node arrays did not preserve the joint field/version/time binding | 439,621 observations with archive, member, exact field, local clock, version and value hash kept together |
| Graph | 2,243 nodes / 2,348 edges | 40,798 nodes / 647,367 edges |
| Candidate generation | 62 objects, based on the incomplete replay and audit-selected chronology material | 1,501 structural inspection candidates, fixed before semantic reviews are read |
| Interpretation | Prior graph promotion and localization proxy withdrawn | Evidence coverage and traceability validated; no detector-superiority claim |

These are different recording units, not a multiplier of detection accuracy. Snapshot copies and repeated post-round captures are not new independent messages. Graph edges include direct observation, reverse query indexes and explicitly UNKNOWN reuse hypotheses; they are not all causal edges.

## Frozen old monitor control

The original monitor candidate artifact remains unchanged: 996 records and 955 unique candidate hashes. New candidate counts do not establish higher sensitivity or precision. The 65 chronology-corrected semantic reviews comprise 6 SUPPORTED, 2 SUPPORTED_CANDIDATE, 45 NOT_ESTABLISHED and 12 NEGATIVE_BOUNDARY records. Most corrected rationales do not name exact file paths; therefore an exact-file mention proxy cannot serve as node-level detection truth.

## Concrete field trace

For G2-X4-T2, the object `file:web/app.js` resolves to 285 observations: 94 MCP wire observations and 191 checkpoint-clock observations. Every source locator and field value hash was checked against the frozen archive. The clocks remain separate; this count does not assert 285 writes or semantic adoptions. The representative source locators are retained in `field_inspection_example.json`.

## Implication for the manuscript

The defensible engineering result is a pluggable, cross-system, field-addressable retrospective evidence layer that exposes and locates recorded changes without modifying native protocols. The frozen semantic audits can then explain whether a concrete change altered information authority, task scope or historical-state authority. Live latency, prospective warning quality and complete-route repair outcomes remain separate questions. This correction supplies the observation infrastructure; it does not substitute graph size for a new mechanism or a repair experiment.
