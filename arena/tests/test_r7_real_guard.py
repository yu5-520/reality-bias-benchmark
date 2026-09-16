import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from arena.build_orchestration_manifest import build_rows
from arena.io_utils import load_json
from arena.run_orchestration_real import _authorization_record, _validate_manifest_bindings, ROOT


class R7RealGuardTest(unittest.TestCase):
    def setUp(self):
        self.arena_path = ROOT / 'arena/config/arena_v0.3.json'
        self.policy_path = ROOT / 'arena/config/structured_ecommerce_v0.1.json'
        self.model_path = ROOT / 'arena/config/model_deepseek_v0.2.json'
        self.model = load_json(self.model_path)

    def test_manifest_binds_explicit_provider_and_model(self):
        rows = build_rows(
            repeats=2,
            code_sha='TEST_SHA',
            model_config_path='arena/config/model_deepseek_v0.2.json',
        )
        loaded = _validate_manifest_bindings(
            rows,
            self.arena_path,
            self.policy_path,
            self.model_path,
            'deepseek',
        )
        self.assertEqual(self.model['config_version'], loaded['config_version'])
        self.assertEqual('STRUCTURED_THEN_FREE', rows[2]['pair_order_pattern'])

    def test_provider_mismatch_is_rejected(self):
        rows = build_rows(repeats=1, code_sha='TEST_SHA')
        with self.assertRaises(ValueError):
            _validate_manifest_bindings(
                rows,
                self.arena_path,
                self.policy_path,
                self.model_path,
                'alibaba_cloud_bailian_business_space',
            )

    def test_authorization_record_freezes_money_and_manifest_identity(self):
        rows = build_rows(repeats=1, code_sha='TEST_SHA')
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / 'manifest.jsonl'
            manifest.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows), encoding='utf-8')
            args = SimpleNamespace(
                authorization_phrase='CALL_REAL_R7_API',
                provider='deepseek',
                max_subject_calls=64,
                spending_ceiling=2.5,
                currency='USD',
            )
            record = _authorization_record(
                args,
                rows,
                manifest,
                self.arena_path,
                self.policy_path,
                self.model_path,
                self.model,
            )
            self.assertEqual(2.5, record['spending_ceiling'])
            self.assertEqual('USD', record['currency'])
            self.assertEqual(1, record['pair_count'])
            self.assertEqual(2, record['run_count'])
            self.assertEqual('deepseek', record['provider'])
            self.assertFalse(record['automatic_paid_evaluator'])
            self.assertTrue(record['authorization_hash'])


if __name__ == '__main__':
    unittest.main()
