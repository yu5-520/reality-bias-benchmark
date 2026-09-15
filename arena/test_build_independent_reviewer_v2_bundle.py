import json
import tempfile
import unittest
from pathlib import Path

from . import build_independent_reviewer_v2_bundle as b


class IndependentV2BundleTests(unittest.TestCase):
    def test_leakage_scanner_rejects_prior_result_cue(self):
        with self.assertRaises(ValueError):
            b.scan_text('x', 'This text contains CN-R-042 and must not enter the reviewer workspace.')

    def test_leakage_scanner_allows_neutral_semantic_prompt(self):
        b.scan_text('x', 'Judge whether an unsupported epistemic promotion occurred. Return UNCERTAIN if evidence is insufficient.')

    def test_validate_packet_rejects_adjudicated_boundary(self):
        original = b.EXPECTED['R2']
        row = {
            'packet_id': 'p',
            'review_layer': 'R2',
            'packet_version': original['packet_version'],
            'prior_reviewer_outputs_included': False,
            'expected_mechanism_mapping_included': False,
            'boundary_fields': {'epistemic_transition': 'UNSUPPORTED_PROMOTION'},
            'context_expansion': {'max_attempts': 1, 'allowed_refs': []},
        }
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'p.jsonl'
            p.write_text(json.dumps(row) + '\n', encoding='utf-8')
            old_sha, old_count = original['packet_sha256'], original['packet_count']
            try:
                original['packet_sha256'] = b.sha256_file(p)
                original['packet_count'] = 1
                with self.assertRaises(ValueError):
                    b.validate_packets('R2', p)
            finally:
                original['packet_sha256'] = old_sha
                original['packet_count'] = old_count

    def test_forbidden_cues_do_not_include_generic_agent_reviewer_word(self):
        self.assertNotIn('reviewer', [x.lower() for x in b.FORBIDDEN_CUES])


if __name__ == '__main__':
    unittest.main()
