import unittest

from . import reviewer_packets_v2 as r


class ReviewerPacketsV2Tests(unittest.TestCase):
    def test_black_hole_is_review_candidate_not_semantic_truth(self):
        rows = [
            {'run_id': 'x', 'round_index': 1, 'interval': {'model_call_count': 2, 'realized_event_count': 4, 'unique_actors': ['a'], 'unique_state_keys': ['x'], 'invocation_count': 0, 'revision_count': 0, 'usage': {'total_tokens': 100}}},
            {'run_id': 'x', 'round_index': 2, 'interval': {'model_call_count': 2, 'realized_event_count': 4, 'unique_actors': ['a'], 'unique_state_keys': ['x'], 'invocation_count': 0, 'revision_count': 0, 'usage': {'total_tokens': 150}}},
        ]
        out = r.add_black_hole_review_candidates(rows)
        self.assertEqual(out[0]['structural_review_candidates'], [])
        self.assertIn('BLACK_HOLE_REVIEW_CANDIDATE', out[1]['structural_review_candidates'])
        self.assertTrue(out[1]['black_hole_review_trigger']['semantic_progress_required'])
        self.assertNotIn('black_hole', out[1])

    def test_r3_packet_materializes_natural_language_without_semantic_label(self):
        trace = {
            'run_id': 'x',
            'events': [
                {'event_index': 0, 'turn': 1, 'actor': 'a', 'action_type': 'write_state', 'authority_class': 'I', 'realized_in_baseline': True, 'action': {'type': 'write_state', 'key': 'stock', 'value': 12, 'status': 'provisional'}},
                {'event_index': 1, 'turn': 2, 'actor': 'b', 'action_type': 'write_state', 'authority_class': 'I', 'realized_in_baseline': True, 'action': {'type': 'write_state', 'key': 'plan', 'value': 'hold'}},
            ],
            'model_calls': [
                {'agent_id': 'a', 'turn': 1, 'event_index_start': 0, 'event_index_end': 1, 'messages': [{'role': 'user', 'content': '{"goal":"g","shared_state":{}}'}], 'decision_summary': 'stock may be 12', 'raw_content': '{"decision_summary":"stock may be 12"}'},
                {'agent_id': 'b', 'turn': 2, 'event_index_start': 1, 'event_index_end': 2, 'messages': [{'role': 'user', 'content': '{"goal":"g","shared_state":{"stock":12}}'}], 'decision_summary': 'I use stock 12 conditionally', 'raw_content': '{"decision_summary":"I use stock 12 conditionally"}'},
            ],
        }
        candidate = {'candidate_id': 'c0', 'event_ref': 'x:EVENT:0000', 'event_index': 0, 'candidate_types': ['STATE_WRITE_CANDIDATE'], 'effect_scope': 'REALIZED_STRUCTURAL_EFFECT', 'structural_facts': {}}
        window = {'source_candidate_id': 'c0', 'window_id': 'w0', 'incoming_structural_relations': [], 'outgoing_structural_relations': [], 'same_key_history_refs': [], 'downstream_output_event_refs': ['x:EVENT:0001']}
        packet = r.build_r3_packets(trace, [candidate], [window], task_goal='g', batch_hash='h')[0]
        self.assertEqual(packet['target_call']['decision_summary'], 'stock may be 12')
        self.assertEqual(packet['downstream_call_context'][0]['call']['decision_summary'], 'I use stock 12 conditionally')
        self.assertEqual(packet['boundary_fields']['semantic_adoption'], r.NOT_ADJUDICATED)
        self.assertFalse(packet['prior_reviewer_outputs_included'])

    def test_r4_packet_requires_semantic_outcome(self):
        trace = {
            'run_id': 'x',
            'events': [{'event_index': 0, 'turn': 1, 'actor': 'a', 'action_type': 'write_state', 'authority_class': 'I', 'realized_in_baseline': True, 'action': {'key': 'x', 'value': 1}}],
            'model_calls': [{'agent_id': 'a', 'turn': 1, 'event_index_start': 0, 'event_index_end': 1, 'messages': [], 'decision_summary': 'd', 'raw_content': '{}'}],
        }
        candidate = {'candidate_id': 'c0', 'event_ref': 'x:EVENT:0000', 'event_index': 0, 'actor': 'a', 'action_type': 'write_state', 'authority_class': 'I', 'candidate_types': ['STATE_WRITE_CANDIDATE'], 'effect_scope': 'REALIZED_STRUCTURAL_EFFECT'}
        window = {'run_id': 'x', 'round_index': 1, 'window_id': 'w', 'structural_round_id': 's', 'anchor_event_ref': 'x:EVENT:0000', 'closing_event_ref': 'x:EVENT:0000', 'evidence_refs': ['x:EVENT:0000'], 'interval': {'event_index_start': 0, 'event_index_end': 0, 'candidate_ids': ['c0'], 'model_call_count': 1, 'realized_event_count': 1, 'unique_actors': ['a'], 'unique_state_keys': ['x'], 'invocation_count': 0, 'revision_count': 0, 'usage': {'total_tokens': 5}}, 'structural_review_candidates': [], 'resource_vector': {}}
        packet = r.build_r4_packets(trace, [candidate], [window], task_goal='g', batch_hash='h')[0]
        self.assertEqual(packet['boundary_fields']['laundering'], r.NOT_ADJUDICATED)
        self.assertEqual(packet['boundary_fields']['black_hole'], r.NOT_ADJUDICATED)
        self.assertEqual(packet['interval_agent_calls'][0]['decision_summary'], 'd')


if __name__ == '__main__':
    unittest.main()
