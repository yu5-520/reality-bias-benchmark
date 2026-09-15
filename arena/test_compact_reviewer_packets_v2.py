import unittest

from . import compact_reviewer_packets_v2 as c


def event(idx, actor, action_type, authority, action):
    return {
        'event_index': idx,
        'turn': idx + 1,
        'actor': actor,
        'action_type': action_type,
        'authority_class': authority,
        'realized_in_baseline': True,
        'action': action,
    }


def call(actor, turn, start, end, state, summary, actions):
    payload = {
        'goal': 'optimize the original task',
        'public_context': {'market': 'demo'},
        'your_private_context': {'role_note': actor},
        'shared_state': state,
        'shared_state_metadata': {
            k: {'status': 'provisional', 'writer': 'a', 'event_index': 0, 'basis': 'forecast'}
            for k in state
        },
        'final_state': None,
        'inbox': [],
        'active_agents': [actor],
        'available_specialists': [{'id': actor, 'role': 'specialist'}],
        'remaining_turn_budget': 10,
        'protocol_note': 'keep uncertainty explicit',
    }
    return {
        'agent_id': actor,
        'turn': turn,
        'event_index_start': start,
        'event_index_end': end,
        'messages': [{'role': 'user', 'content': __import__('json').dumps(payload)}],
        'decision_summary': summary,
        'parsed_envelope': {'decision_summary': summary, 'actions': actions},
        'raw_content': 'SHOULD_NOT_BE_COPIED_TO_COMPACT_PACKET',
    }


def fixture_trace():
    return {
        'run_id': 'run',
        'events': [
            event(0, 'a', 'write_state', 'I', {'type': 'write_state', 'key': 'forecast', 'value': 12, 'status': 'provisional'}),
            event(1, 'b', 'write_state', 'I', {'type': 'write_state', 'key': 'plan', 'value': 'hold'}),
        ],
        'model_calls': [
            call('a', 1, 0, 1, {'forecast': 12, 'other': 'large-context-value'}, 'forecast 12 is provisional', [{'type': 'write_state', 'key': 'forecast', 'value': 12, 'status': 'provisional'}]),
            call('b', 2, 1, 2, {'forecast': 12, 'other': 'large-context-value'}, 'use forecast conditionally', [{'type': 'write_state', 'key': 'plan', 'value': 'hold'}]),
        ],
    }


def candidate():
    return {
        'measurement_version': 'R234-MEASUREMENT-V2-v0.1',
        'r2_index_version': 'R234-R2-STRUCTURAL-CANDIDATE-INDEX-v0.1',
        'evidence_batch_hash': 'b',
        'run_id': 'run',
        'event_ref': 'run:EVENT:0000',
        'event_index': 0,
        'turn': 1,
        'actor': 'a',
        'action_type': 'write_state',
        'authority_class': 'I',
        'realized_in_baseline': True,
        'effect_scope': 'REALIZED_STRUCTURAL_EFFECT',
        'candidate_types': ['STATE_WRITE_CANDIDATE'],
        'structural_facts': {'state_key': 'forecast', 'same_key_prior_event_ref': None},
        'semantic_review': {'C': 'NOT_ADJUDICATED', 'P': 'NOT_ADJUDICATED', 'R': 'NOT_ADJUDICATED', 'authorization': 'NOT_ADJUDICATED', 'semantic_adoption': 'NOT_ADJUDICATED', 'decision_effective': 'NOT_ADJUDICATED'},
        'candidate_id': 'cand0',
    }


class CompactPacketsTests(unittest.TestCase):
    def test_r2_keeps_natural_language_but_not_raw_content(self):
        row = c.build_r2_packets(fixture_trace(), [candidate()], 'goal', 'b')[0]
        self.assertEqual(row['target_call']['output']['decision_summary'], 'forecast 12 is provisional')
        self.assertNotIn('raw_content', row['target_call'])
        self.assertEqual(row['boundary_fields']['epistemic_transition'], c.NOT_ADJUDICATED)
        self.assertFalse(row['prior_reviewer_outputs_included'])
        self.assertEqual(row['context_expansion']['max_attempts'], 1)

    def test_compact_state_preserves_keys_hash_and_selected_value(self):
        row = c.build_r2_packets(fixture_trace(), [candidate()], 'goal', 'b')[0]
        block = row['target_call']['visible_input']['shared_state']
        self.assertEqual(block['selected_values'], {'forecast': 12})
        self.assertEqual(block['keys'], ['forecast', 'other'])
        self.assertTrue(block['full_state_hash'])
        self.assertIn('forecast', block['metadata_index'])
        self.assertIn('other', block['metadata_index'])

    def test_r3_contains_downstream_natural_language_without_prior_verdict(self):
        window = {
            'source_candidate_id': 'cand0',
            'window_id': 'win3',
            'incoming_structural_relations': [],
            'outgoing_structural_relations': [],
            'same_key_history_refs': [],
            'downstream_output_event_refs': ['run:EVENT:0001'],
        }
        row = c.build_r3_packets(fixture_trace(), [candidate()], [window], 'goal', 'b')[0]
        self.assertEqual(row['downstream_calls'][0]['output']['decision_summary'], 'use forecast conditionally')
        self.assertEqual(row['boundary_fields']['semantic_adoption'], c.NOT_ADJUDICATED)
        self.assertFalse(row['expected_mechanism_mapping_included'])

    def test_r4_remains_neutral(self):
        window = {
            'window_id': 'win4',
            'round_index': 1,
            'evidence_refs': ['run:EVENT:0000', 'run:EVENT:0001'],
            'interval': {'event_index_start': 0, 'event_index_end': 1},
            'semantic_outcome': {'black_hole': 'NOT_ADJUDICATED'},
        }
        row = c.build_r4_packets(fixture_trace(), [candidate()], [window], 'goal', 'b')[0]
        self.assertEqual(len(row['interval_calls']), 2)
        self.assertEqual(row['boundary_fields']['black_hole'], c.NOT_ADJUDICATED)
        self.assertFalse(row['prior_reviewer_outputs_included'])

    def test_packet_hash_is_deterministic(self):
        a = c.build_r2_packets(fixture_trace(), [candidate()], 'goal', 'b')[0]
        b = c.build_r2_packets(fixture_trace(), [candidate()], 'goal', 'b')[0]
        self.assertEqual(a['packet_hash'], b['packet_hash'])


if __name__ == '__main__':
    unittest.main()
