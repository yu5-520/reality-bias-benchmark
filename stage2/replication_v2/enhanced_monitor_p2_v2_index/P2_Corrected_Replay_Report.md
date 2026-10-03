# Corrected native evidence replay

84 frozen trajectories; 19,473 native capture records; 439,621 field-bound observations. All observation locators and value hashes resolved against their source archives.

The v1 replay used an incompatible legacy archive adapter. Its graph promotion and old/new localization comparison are withdrawn; frozen historical files remain unchanged.

Capture records, field observations, snapshot states and inspection candidates are different units. Repeated captures (including post-round memory copies) do not establish new messages, semantic adoption or causal dependency.

Each clock is local to its producer. The six complete maps are retrospective observation maps with no write authorization. Native-state decoding is limited to declared carriers and host inbox snapshots; it is not a complete model-internal trace.

The 65 targeted corrected reviews are evaluated separately by status using exact file mentions in corrected rationales only. This proxy is neither event localization nor recall. No detector superiority, live performance or route-repair benefit is established.

```json
{
  "schema": "RB-STAGE2-P2-CORRECTED-REPLAY-v2",
  "trajectories": 84,
  "totals": {
    "native_records": 19473,
    "observer_records": 9742,
    "ledger_bound_checkpoints": 3551,
    "checkpoint_file_changes": 122,
    "checkpoints": 3552,
    "last_observed_file_count": 1024,
    "terminal_checkpoint_present": 80,
    "observations": 439621,
    "resolved_observations": 439621,
    "nodes": 40798,
    "edges": 647367,
    "candidates": 1501,
    "old_candidate_records": 996,
    "wire_records": 9731,
    "native_ref_ordered_checkpoints": 1,
    "failed_attempt_without_terminal_record": 1,
    "explicit_zero_native_call_history": 1
  },
  "old_unique_candidate_hashes": 955,
  "reference_records": 65,
  "reference_strata": {
    "NOT_ESTABLISHED": {
      "records": 45,
      "graph_exact_file_mention": 3,
      "old_exact_file_mention": 3,
      "new_exact_file_mention": 2
    },
    "NEGATIVE_BOUNDARY": {
      "records": 12,
      "graph_exact_file_mention": 9,
      "old_exact_file_mention": 8,
      "new_exact_file_mention": 9
    },
    "SUPPORTED_CANDIDATE": {
      "records": 2,
      "graph_exact_file_mention": 0,
      "old_exact_file_mention": 0,
      "new_exact_file_mention": 0
    },
    "SUPPORTED": {
      "records": 6,
      "graph_exact_file_mention": 1,
      "old_exact_file_mention": 1,
      "new_exact_file_mention": 1
    }
  },
  "execution": {
    "natural_reruns": 0,
    "provider_calls": 0,
    "evaluator_calls": 0,
    "repair_calls": 0
  },
  "claims": {
    "detector_superiority_established": false,
    "live_monitoring_tested": false,
    "authority_transitions_automatically_identified": false,
    "route_repair_efficacy_tested": false
  }
}
```
