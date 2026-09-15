import unittest

from . import optimize_reviewer_v2_r3_packets as o


def packet(evidence_type='state_version_visible_in_input'):
    call_ref = 'run:CALL:0002'
    return {
        'packet_version': 'R234-REVIEWER-V2-R3-COMPACT-PACKET-v0.1',
        'review_layer': 'R3',
        'packet_id': 'p',
        'packet_hash': 'old',
        'machine_lineage': {
            'outgoing_structural_relations': [{
                'source_ref': 'run:EVENT:0001',
                'target_ref': call_ref,
                'evidence_type': evidence_type,
            }]
        },
        'downstream_calls': [{
            'call_ref': call_ref,
            'agent_id': 'b',
            'turn': 3,
            'role': {'id': 'b', 'role': 'specialist'},
            'input_message_ids': ['M1'],
            'input_invocation_ids': [],
            'visible_input': {
                'your_private_context': {'long': 'private'},
                'inbox': [{'id': 'M1', 'content': 'message'}],
                'active_agents': ['b'],
                'remaining_turn_budget': 8,
                'shared_state': {
                    'keys': ['forecast', 'other'],
                    'selected_values': {'forecast': 12},
                    'selected_metadata': {'forecast': {'status': 'provisional'}},
                    'full_state_hash': 'statehash',
                },
            },
            'output': {'decision_summary': 'use forecast conditionally', 'actions': [{'type': 'write_state', 'key': 'plan', 'value': 'hold'}]},
            'output_events': [{
                'event_ref': 'run:EVENT:0003',
                'action_type': 'write_state',
                'authority_class': 'I',
                'realized_in_baseline': True,
                'action': {'type': 'write_state', 'key': 'plan', 'value': 'hold'},
            }],
        }],
        'context_expansion': {'max_attempts': 1, 'allowed_refs': [call_ref]},
        'boundary_fields': {'semantic_adoption': 'NOT_ADJUDICATED'},
    }


class OptimizeR3Tests(unittest.TestCase):
    def test_state_read_hashes_inbox_and_preserves_selected_state(self):
        row = o.optimize_packet(packet())
        call = row['downstream_calls'][0]
        self.assertEqual(call['lineage_input']['selected_state_values'], {'forecast': 12})
        self.assertEqual(call['lineage_input']['inbox']['mode'], 'HASH_ONLY_NO_DIRECT_MESSAGE_LINEAGE')
        self.assertNotIn('your_private_context', call['lineage_input'])
        self.assertTrue(call['lineage_input']['private_context_hash'])
        self.assertEqual(row['context_expansion']['max_attempts'], 1)
        self.assertFalse(row['compaction_boundary']['semantic_selection_used'])

    def test_message_read_retains_inbox(self):
        row = o.optimize_packet(packet('message_read_into_input'))
        inbox = row['downstream_calls'][0]['lineage_input']['inbox']
        self.assertEqual(inbox['mode'], 'FULL_FOR_STRUCTURAL_MESSAGE_READ')
        self.assertEqual(inbox['value'][0]['content'], 'message')

    def test_action_payload_not_duplicated_in_output_event_refs(self):
        row = o.optimize_packet(packet())
        call = row['downstream_calls'][0]
        self.assertIn('actions', call['output'])
        self.assertNotIn('action', call['output_event_refs'][0])

    def test_semantic_fields_unchanged(self):
        src = packet()
        row = o.optimize_packet(src)
        self.assertEqual(row['boundary_fields'], src['boundary_fields'])
        self.assertEqual(row['machine_lineage'], src['machine_lineage'])

    def test_deterministic(self):
        self.assertEqual(o.optimize_packet(packet())['packet_hash'], o.optimize_packet(packet())['packet_hash'])


if __name__ == '__main__':
    unittest.main()
