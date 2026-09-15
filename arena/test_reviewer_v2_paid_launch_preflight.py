import json
import tempfile
import unittest
from pathlib import Path

from . import reviewer_v2_paid_launch_preflight as p


class PaidLaunchPreflightTests(unittest.TestCase):
    def test_packet_file_validation_accepts_clean_packet(self):
        row = {
            'packet_id': 'p1',
            'review_layer': 'R2',
            'packet_version': 'v',
            'evidence_batch_hash': 'batch',
            'prior_reviewer_outputs_included': False,
            'expected_mechanism_mapping_included': False,
            'context_expansion': {'max_attempts': 1},
            'boundary_fields': {'epistemic_transition': 'NOT_ADJUDICATED'},
        }
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'x.jsonl'
            path.write_text(json.dumps(row) + '\n', encoding='utf-8')
            rows, errors = p.validate_packet_file('R2', path, 1, 'v', 'batch')
        self.assertEqual(len(rows), 1)
        self.assertEqual(errors, [])

    def test_packet_file_validation_rejects_semantic_leak(self):
        row = {
            'packet_id': 'p1',
            'review_layer': 'R2',
            'packet_version': 'v',
            'evidence_batch_hash': 'batch',
            'prior_reviewer_outputs_included': True,
            'expected_mechanism_mapping_included': False,
            'context_expansion': {'max_attempts': 1},
            'boundary_fields': {'epistemic_transition': 'UNSUPPORTED_PROMOTION'},
        }
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'x.jsonl'
            path.write_text(json.dumps(row) + '\n', encoding='utf-8')
            _, errors = p.validate_packet_file('R2', path, 1, 'v', 'batch')
        self.assertTrue(any('prior reviewer' in x for x in errors))
        self.assertTrue(any('NOT_ADJUDICATED' in x for x in errors))

    def test_duplicate_packet_ids_rejected(self):
        row = {
            'packet_id': 'p1', 'review_layer': 'R3', 'packet_version': 'v',
            'evidence_batch_hash': 'batch', 'prior_reviewer_outputs_included': False,
            'expected_mechanism_mapping_included': False,
            'context_expansion': {'max_attempts': 1},
            'boundary_fields': {'semantic_adoption': 'NOT_ADJUDICATED'},
        }
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'x.jsonl'
            path.write_text(json.dumps(row) + '\n' + json.dumps(row) + '\n', encoding='utf-8')
            _, errors = p.validate_packet_file('R3', path, 2, 'v', 'batch')
        self.assertTrue(any('duplicate packet_id' in x for x in errors))

    def test_sha256_file_deterministic(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'x'
            path.write_bytes(b'abc')
            self.assertEqual(
                p.sha256_file(path),
                'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad',
            )


if __name__ == '__main__':
    unittest.main()
