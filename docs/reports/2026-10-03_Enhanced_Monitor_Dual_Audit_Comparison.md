# Enhanced monitor comparison against the two frozen semantic audits

This report records the local analysis performed on 2 October 2026 and packaged on 3 October. It uses existing frozen trajectories, enhanced P2 v2 replay and original semantic audits. No subject was rerun, provider called, or repair executed. This is a post-hoc descriptive comparison, not a preregistered generalization test.

## A complete monitoring design

The design joins two stages: during execution, preserve observations and flag available structural signals; after termination, freeze the evidence and reconstruct the observed route, checking state changes and process accounts against the completed trajectory. Retrospective evidence cannot establish an earlier warning. The current enhancement comparison evaluates the second stage; historical online results retain their own evidence and timing limits.

Objects are graph-construction and inspection material. Several candidates can belong to one route, and one node can connect several candidates. Repair is intended to use the complete available observation map to choose justified changes, not to issue one repair per candidate. Completeness of an observation map is relative to captured evidence; it does not establish a complete causal or semantic graph. Graph reachability does not grant write authority. The local repair package remains a historical comparison and an extension experiment, rather than the unit defining the monitoring architecture.

## Frozen references and baseline recovery

Layer B is the DeepSeek monitor-blind partial-evidence audit: 84 trajectories, 244 records, 97 positive structures across 59 trajectories (14 SUPPORTED and 83 SUPPORTED_CANDIDATE). Layer C is the GPT-5.6 Sol full-context audit: 80 eligible trajectories, 40 positive events across 25 trajectories. The models and evidence conditions both differ; cross-audit differences cannot be attributed to evidence depth alone.

Original packet builders from commit 8d87da2 reconstruct the historical evidence numbering. All 84 B and 80 C packet hashes agree with the original audits. B reference data are pinned to commit 445e50d1c269b74405beb4c10980fc3b4be70f87 and their SHA256. Current chronology-corrected builders must not be substituted for these historical builders.

The original B matching algorithm reproduces all 97 positive classifications and selected warning identities: 16 specific matches, 29 family-compatible partial localizations, 45 misses and 7 unmatched unobservable references. Warning states reproduce 36 supported, 18 rejected and 901 unsupported unique hashes. C's 40 historical event classifications reproduce individually: 22 specific matches, 10 evidence-level localizations and 8 misses. This does not reconstruct or validate all historical C warning classifications or lead-time estimates.

## Common retrospective matching

Both monitors are compared within the same trajectory against the same audit text and cited evidence. The primary conservative check removes only the object-type prefix and requires the entire remaining identifier, at least four characters, with path-aware token boundaries. It does not reduce paths to filenames or stems. A core association finds the identifier in the audit mechanism or referenced semantic-node state; an evidence-only association finds it in cited evidence preview/path. Both count as object localization, not confirmed source/consumer identity, semantic adoption, permission violation, or detector accuracy.

The primary comparison has no invented mapping from new candidate reasons to old structure families and makes no cross-clock ordering inference. The separately retained legacy lexical analysis uses the old filename/stem substring rule; its larger counts must not be substituted for the conservative counts. In B, an apparent legacy-only lost match comes from the generic stem `legacy` in `file:checkout_app/legacy.py` (G3-X2-T3-REF-01); this is not evidence of a lost semantic route.

| Reference population | Old object localization | Enhanced object localization | Gained | Lost |
| --- | ---: | ---: | ---: | ---: |
| B positive/candidate structures | 31/97 (32.0%) | 48/97 (49.5%) | 17 | 0 |
| B SUPPORTED only | 7/14 (50.0%) | 10/14 (71.4%) | 3 | 0 |
| C original positive/candidate events | 29/40 (72.5%) | 37/40 (92.5%) | 8 | 0 |
| C chronology-reviewed positives | 27/33 (81.8%) | 32/33 (97.0%) | 5 | 0 |

The original B broad result (45/97) uses family and temporal conditions, including family-only partial matches. It is not the same metric as 31/97 above. The old C lexical result is 32/40 and the enhanced lexical result 40/40, but full-identifier matching gives the more conservative 29/40 and 37/40 reported here.

Seven original C positives were downgraded by the existing chronology review. For the eight reviewed events that remain positive, `corrected_comparison.json` uses the corrected rationale and corrected cited packet evidence, with packet hashes verified. The other 25 positives retain their untargeted original audit. This is a targeted-review update, not a new full independent audit. The label-only overlay in `comparison_summary.json` is kept separately: its total coverage agrees, but its core/evidence tier counts differ. Use `corrected_comparison.json` for the updated interpretation (old 12 core + 15 evidence-only; enhanced 17 core + 15 evidence-only).

## System-specific application value

| System | B old → enhanced | C original old → enhanced |
| --- | --- | --- |
| AutoGen | 15/15 → 15/15 | 15/15 → 15/15 |
| MetaGPT | 2/13 → 2/13 | 3/3 → 3/3 |
| A2A | 0/18 → 16/18 | 0/8 → 8/8 |
| MCP | 6/20 → 6/20 | 3/3 → 3/3 |
| RAG | 3/11 → 3/11 | 5/5 → 5/5 |
| MemoryBank | 4/14 → 5/14 | 3/4 → 3/4 |
| LongLLMLingua | 1/6 → 1/6 | 0/2 → 0/2 |

The concentrated A2A gain is a concrete application result, not a requirement that all seven systems improve equally. The old A2A monitor emitted zero candidates in this population; the enhancement emits 66 objects. After chronology review, five retained A2A positives change from 0/5 to 5/5 localization. This supports suitability for the tested A2A implementation and its evidence surfaces, not an intrinsic advantage for every A2A deployment.

Examples: G3-X3-T2 identifies run.py and checkout_app/checkout.py for retained R/P events; G5-X3-T2 identifies launcher/service/test objects for retained R/P events. G2-X6-T3-REF-01 gains an exact memory-record identifier association. Unchanged counts in other systems do not measure whether graph provenance or route usability improved; those are different endpoints.

## Node associations, provenance and repair units

The original C positives reference 71 distinct semantic nodes. Full-identifier associations cover 39/71 old and 49/71 enhanced. All referenced nodes have an object association in 14/40 old and 24/40 enhanced events. These are lexical evidence associations, not independently adjudicated node detection, verified edges, complete causal paths, or demonstrated route repair.

Exact archive-member/line and checksum binding is recorded separately. Enhanced candidates share a cited member/record with 14/97 B and 36/40 C positive references. Four B and three C associations go beyond literal object-name matching. Some are whole snapshot-member associations, so they are not promoted to specific semantic-node matches. Corrected C event G3-X7-T2:CPR01 remains unmatched by the conservative object rule despite broader snapshot provenance.

Across the same 84 trajectories, object candidates increase from 996 to 1,501 (+50.7%). The old 955 figure is a different denominator: globally unique warning hashes. Neither candidate count nor unlinked candidate count is a measured human workload, false-positive rate, defect count, or number of repairs. Shared objects can appear in positive and negative audit events. For example, G2-X4-T2 has 11 old and 16 enhanced candidates while role expansion remains insufficient to establish P.

Future route-repair evaluation should measure supported node/edge coverage, graph discontinuities, successful source-to-consequence tracing, justified repair scope, preservation of healthy paths, and post-repair continuation/regeneration. No new route-repair efficacy is claimed in this data release.

## Data and reproduction

Results: `stage2/replication_v2/enhanced_monitor_dual_audit_comparison_v1/`.
The seal binds code, frozen dependencies, reference corpus, result files, the joined input hash and all 84 replay graph hashes. Detailed records retain event IDs, matching objects and evidence refs. Sources and the historical packet builders are included under `scripts/stage2_monitor_audit_comparison/sources/`.

Materialize the G2A–G5A frozen source checkouts using the existing pinned source configuration, and reproduce the P2 v2 replay following `docs/protocols/StageII_P2_Replay_Correction_v2.md`. Then run:

```bash
python scripts/run_stage2_monitor_dual_audit_comparison.py \
  --source-root /path/to/chronology_sources \
  --replay-root /path/to/enhanced_monitor_p2_v2 \
  --work-dir /tmp/monitor-dual-audit-reproduction
```

The work directory must be empty. An optional `--reuse-inputs /path/to/joined_inputs.json` avoids rebuilding historical packets only when its exact sealed SHA256 matches. Every result is compared with the frozen JSON, both historical audit comparisons are checked, and a validation receipt is emitted. No original experiment, semantic model review, or repair is rerun.
