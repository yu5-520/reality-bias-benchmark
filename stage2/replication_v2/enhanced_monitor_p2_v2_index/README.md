# Validated P2 replay index

This directory is a compact, permanent index of the validated recovery replay. It is not the complete replay output directory. `manifest.json` binds all full-output files, including 84 graph archives, six complete observation maps and candidate records; those large derived files are reproducible and are retained in the linked workflow artifact.

- Source implementation: commit `de511e398fb86e96c65164e88c1af8878a6792ca`. Exact file hashes in `run_binding.json` are authoritative. The local source-base commit records provenance, not a claim that an unmodified checkout produced the output.
- Workflow: https://github.com/yu5-520/reality-bias-benchmark/actions/runs/36974367401
- Complete graphs/maps: artifact `p2-native-evidence-de511e398fb86e96c65164e88c1af8878a6792ca` after successful completion; retention 90 days. This workflow independently reconstructs from the public pinned source archives. Its run-binding provenance will differ from the local recovery binding.
- Rebuild using `scripts/run_stage2_p2_evidence_graph_replay_v2.py` and validate the full output using `scripts/validate_stage2_p2_replay_v2.py`. Do not pass this compact index to the full-output validator.
- Local validation: `validation.json`; exact source-field bindings were checked during graph construction. The worked field query verifies all 285 observations against the raw archive again; `field_inspection_example.json` retains representative locators.

The recovery run supersedes prior unpublished local numbers. It contains 19,473 native capture records, 3,552 checkpoints, 439,621 bound observations, 40,798 nodes and 647,367 edges. The 1,501 candidates are inspection candidates, not diagnosed defects. No natural run or paid model call was made.
