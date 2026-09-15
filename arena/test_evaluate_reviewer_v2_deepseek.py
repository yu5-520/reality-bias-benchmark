import json
import tempfile
import unittest
from pathlib import Path

from . import evaluate_reviewer_v2_deepseek as e


class ReviewerV2DeepSeekAdapterTests(unittest.TestCase):
    def test_cost_uses_cache_breakdown(self):
        cfg = {'pricing_snapshot_usd_per_million_tokens': {'peak': {'input_cache_hit': 1, 'input_cache_miss': 2, 'output': 3}}}
        usage = {'prompt_tokens': 15, 'prompt_cache_hit_tokens': 10, 'prompt_cache_miss_tokens': 5, 'completion_tokens': 2}
        self.assertAlmostEqual(e.cost_usd(usage, cfg, 'peak'), (10 + 10 + 6) / 1_000_000)

    def test_cost_falls_back_to_cache_miss(self):
        cfg = {'pricing_snapshot_usd_per_million_tokens': {'peak': {'input_cache_hit': 1, 'input_cache_miss': 2, 'output': 3}}}
        usage = {'prompt_tokens': 10, 'completion_tokens': 2}
        self.assertAlmostEqual(e.cost_usd(usage, cfg, 'peak'), (20 + 6) / 1_000_000)

    def test_target_refs(self):
        self.assertEqual(e.target_ref('R2', {'target_candidate': {'event_ref': 'r:EVENT:0001'}}), 'r:EVENT:0001')
        self.assertEqual(e.target_ref('R4', {'run_id': 'r', 'structural_window': {'structural_round_id': 'round-1'}}), 'round-1')

    def test_r2_record_preserves_uncertainty_and_launch_hash(self):
        packet = {'evidence_batch_hash': 'b', 'packet_id': 'p', 'packet_hash': 'h', 'target_candidate': {'event_ref': 'r:EVENT:0001', 'effect_scope': 'REALIZED_STRUCTURAL_EFFECT'}}
        final = {
            'epistemic_transition': 'UNCERTAIN', 'goal_relation': 'ORIGINAL_GOAL',
            'goal_focus_transition': 'NO_MATERIAL_SHIFT', 'local_retrospective_outcome': 'NOT_REWORK',
            'authorization_judgment': 'UNCERTAIN', 'rationale': 'insufficient evidence',
            'confidence': 0.4, 'uncertainties': ['source unresolved'], 'evidence_refs': [],
        }
        row = e.make_record('R2', packet, final, 'rid', 'mh', 'ph', {'model': 'm', 'id': 'resp'}, {}, 1, [], None, 'AUTH-REF', 'launch-hash')
        self.assertEqual(row['epistemic_transition'], 'UNCERTAIN')
        self.assertEqual(row['authorization_judgment'], 'UNCERTAIN')
        self.assertFalse(row['context_expansion_used'])
        self.assertEqual(row['authorization_ref'], 'AUTH-REF')
        self.assertEqual(row['launch_record_hash'], 'launch-hash')

    def test_launch_record_rejects_not_authorized(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            packets = td / 'p.jsonl'
            packets.write_text(json.dumps({'packet_id': 'p'}) + '\n', encoding='utf-8')
            cfg = td / 'cfg.json'; cfg.write_text('{}', encoding='utf-8')
            prompt = td / 'prompt.md'; prompt.write_text('x', encoding='utf-8')
            record = {
                'status': 'NOT_AUTHORIZED',
                'execute_real_api': False,
                'authorization_ref': None,
                'scientific_role': 'REANNOTATION_CALIBRATION_UNDER_REVISED_SEMANTIC_CONTRACT',
                'packet_files': {'R2': {'sha256': e.sha256_file(packets), 'unit_count': 1}},
                'model_config_sha256': e.sha256_file(cfg),
                'prompt_hashes': {'R2': e.sha256_file(prompt)},
                'runtime_policy': {
                    'malformed_output_retries_max': 2,
                    'context_expansion_max_per_packet': 1,
                    'semantic_uncertainty_retry': False,
                    'subject_rerun_on_reviewer_failure': False,
                    'max_workers': 1,
                },
                'spend_policy': {
                    'launch_max_spend_usd': 0.5,
                    'repository_level_absolute_ceiling_usd': 2.0,
                    'price_mode_for_ceiling': 'peak',
                },
                'accepted_returned_model_values': ['deepseek-flash'],
            }
            with self.assertRaises(ValueError):
                e.validate_launch_record(record, 'R2', packets, cfg, prompt, 'AUTH', 0.5, 2, 'peak')

    def test_launch_record_accepts_exact_binding(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            packets = td / 'p.jsonl'
            packets.write_text(json.dumps({'packet_id': 'p'}) + '\n', encoding='utf-8')
            cfg = td / 'cfg.json'; cfg.write_text('{}', encoding='utf-8')
            prompt = td / 'prompt.md'; prompt.write_text('x', encoding='utf-8')
            record = {
                'status': 'AUTHORIZED',
                'execute_real_api': True,
                'authorization_ref': 'AUTH',
                'scientific_role': 'REANNOTATION_CALIBRATION_UNDER_REVISED_SEMANTIC_CONTRACT',
                'packet_files': {'R2': {'sha256': e.sha256_file(packets), 'unit_count': 1}},
                'model_config_sha256': e.sha256_file(cfg),
                'prompt_hashes': {'R2': e.sha256_file(prompt)},
                'runtime_policy': {
                    'malformed_output_retries_max': 2,
                    'context_expansion_max_per_packet': 1,
                    'semantic_uncertainty_retry': False,
                    'subject_rerun_on_reviewer_failure': False,
                    'max_workers': 1,
                },
                'spend_policy': {
                    'launch_max_spend_usd': 0.5,
                    'repository_level_absolute_ceiling_usd': 2.0,
                    'price_mode_for_ceiling': 'peak',
                },
                'accepted_returned_model_values': ['deepseek-flash'],
            }
            binding = e.validate_launch_record(record, 'R2', packets, cfg, prompt, 'AUTH', 0.5, 2, 'peak')
            self.assertEqual(binding['accepted_returned_model_values'], ['deepseek-flash'])
            self.assertTrue(binding['launch_record_hash'])


if __name__ == '__main__':
    unittest.main()
