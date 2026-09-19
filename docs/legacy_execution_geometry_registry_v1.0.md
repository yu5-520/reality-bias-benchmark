# Legacy Execution Geometry Registry v1.0

Date: 2026-09-19

Historical execution code is retained for evidence reproducibility but is not the forward canonical experiment geometry.

| Historical interface | Historical geometry | Forward role |
| --- | --- | --- |
| `prepare_v5_cross_domain_r5_first_wave.py` / runner | 2 replicate pairs × control/intervention | LEGACY + supplementary local sensitivity |
| `prepare_v5_cross_domain_r5_second_wave.py` / runner | 2 replicate pairs × control/intervention | LEGACY + supplementary local sensitivity |
| `prepare_r7_three_arm_plan.py` / runner | C1/C2/C3 × replicate(s) | LEGACY historical compatibility |
| `r7-three-arm-subject-real.yml` | three-arm execution | LEGACY historical compatibility |
| `r7-c3-chat-authorization-bridge.yml` | C3-only repeated historical operator test | supplementary engineering robustness |

Forward canonical interfaces:

- `arena/prepare_v5_cross_domain_r5_canonical.py`
- `arena/run_v5_cross_domain_r5_canonical.py`
- `arena/freeze_v5_cross_domain_r5_canonical.py`
- `arena/prepare_r7_dual_intervention_plan.py`
- `arena/run_r7_dual_intervention_real.py`
- `arena/freeze_r7_dual_intervention_evidence.py`

Historical files must not be deleted because their frozen artifacts remain evidence-bound.
