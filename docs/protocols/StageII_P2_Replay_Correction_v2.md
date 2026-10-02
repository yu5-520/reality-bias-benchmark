# P2 native evidence replay correction

The P2 v1 graph-promotion decision and its old/new localization comparison are withdrawn. Its legacy adapter expects a different archive layout: the G2–G5 native streams and checkpoint states were not ingested correctly. Audit-selected chronology records cannot substitute for a complete independently built observation graph. The original v1 results and closure are preserved as historical records, not as current acceptance evidence.

The active entrypoint is `scripts/run_stage2_p2_evidence_graph_replay_v2.py`. The old entrypoint fails closed. This correction changes derived analysis only: it never re-executes a subject, calls a provider, changes framework protocols or applies a repair.

## Evidence and interpretation

| Surface | Native evidence | Ordering and limits |
| --- | --- | --- |
| AutoGen / MetaGPT | Observer index plus hash-bound raw payload | Producer capture sequence; post-round history/memory copies are observations, not necessarily distinct messages |
| A2A | Request/response bytes plus per-role metadata | Per-role capture sequence; not a global decision clock or proof of execution start order |
| MCP | Client/server JSON-RPC streams | Invocation clock and within-capture line; a write request is not a confirmed write |
| RAG / MemoryBank / LongLLMLingua | Frozen observer payloads and declared carriers | Capture sequence; retrieval or textual exposure is not semantic adoption |
| Checkpoints | Ledger-bound file manifests, file bytes, declared carriers, host inbox copies | Model-decision ledger where available; explicit native boundary otherwise; snapshots are not added to native reuse counts |

Every observation preserves its archive SHA256, member SHA256, JSON pointer/line, occurrence locator when applicable, local sequence, clock, version and exact field value hash together. File mentions additionally retain character spans. Event identity includes the occurrence; identical content does not collapse repeated captures.

Edges establish recorded observation or a queryable reverse index. Exposure-based reuse hypotheses remain UNKNOWN. Paths do not grant write authority. The six complete route maps are retrospective observation maps, not prospective repair packages. The adapter does not decode every framework-native internal state or model reasoning process.

Two evidence boundaries are retained: G5-X4-T1 has no MCP calls but a complete invalid-action history; G5-X3-T1 has a receipt-bound failed attempt, only its available native evidence and start checkpoint, and no fabricated terminal or old candidate artifact. Other unexplained missing streams fail closed.

## Evaluation

New graphs and structural inspection candidates are fixed before loading any semantic review. The 65 targeted corrected reviews are evaluated separately by status. Only exact relative file paths in the corrected rationale enter the file-mention proxy. Generic words, legacy counter-explanations and uncorrected historical positive denominators are excluded. A missing file mention is not a detector miss. Node-level detection accuracy requires separately defined node-level reference labels.

This analysis establishes evidence ingestion and traceability, not detector superiority, live latency, automatic CPR judgement, or complete-route repair efficacy. Candidate counts are inspection workload units, not defect counts. Existing primary monitor and local repair experiments retain their original scope.

## Reproduce

Materialize the four public source commits identified in `configs/stage2_g{2..5}_ab_paired_semantic_audit_v1.json`, then run:

```bash
python -m unittest discover -s stage2/monitor_enhancement/tests -v
python -m unittest discover -s stage2/route_repair/tests -v
python scripts/run_stage2_p2_evidence_graph_replay_v2.py --out /tmp/p2-native-replay
python scripts/validate_stage2_p2_replay_v2.py --root /tmp/p2-native-replay --receipt /tmp/p2-validation.json
python scripts/inspect_stage2_evidence_graph.py --graphs /tmp/p2-native-replay/graphs --cell G2-X4-T2 --object file:web/app.js --archive stage2/replication_v2/G2/natural_A/X4-T2/first_attempt.tar.gz
```

The replay requires a fresh output directory. Source bindings are pinned by SHA256; each run records exact implementation hashes. Source code, compact result indexes and validation receipts can be reviewed in Git. Complete generated graphs are reproducible from those pinned inputs and are also retained as workflow artifacts (90-day retention; artifacts are not permanent archival storage). No workflow writes results to main.

## Recovery provenance

The prior unpublished local correction was removed during workspace maintenance. This implementation was reconstructed from the recorded correction requirements against public base commit `237cfa2516c57f8be3a78365e0089e8967e79830`. Prior local commit identities and validation receipts are not reused. This recovery run creates its own implementation binding, results and validation receipt.
