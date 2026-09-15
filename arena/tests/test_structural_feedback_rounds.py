import unittest

from arena.structural_feedback import derive_structural_feedback_rounds


def settled(idx, turn, actor, version, action_type='finalize'):
    return {
        'event_index': idx,
        'turn': turn,
        'actor': actor,
        'action_type': action_type,
        'realized_in_baseline': True,
        'final_state_after': {'status': 'FINAL', 'version': version},
        'action': {'type': action_type},
    }


def contribution(idx, turn, actor, action_type='message', message_id=None):
    action = {'type': action_type}
    if message_id:
        action['message_id'] = message_id
    return {
        'event_index': idx,
        'turn': turn,
        'actor': actor,
        'action_type': action_type,
        'realized_in_baseline': True,
        'action': action,
        'final_state_after': None,
    }


def call(turn, actor, final_state, start, end, input_messages=None, input_invocations=None, state_origins=None):
    metadata = {}
    for i, event_index in enumerate(state_origins or []):
        metadata[f'k{i}'] = {'event_index': event_index}
    return {
        'turn': turn,
        'agent_id': actor,
        'status': 'completed',
        'runtime_snapshot': {
            'final_state': final_state,
            'shared_state_metadata': metadata,
        },
        'input_message_ids': list(input_messages or []),
        'input_invocation_ids': list(input_invocations or []),
        'event_index_start': start,
        'event_index_end': end,
    }


class StructuralFeedbackRoundTests(unittest.TestCase):
    def test_two_non_overlapping_return_rounds(self):
        v1 = {'status': 'FINAL', 'version': 1}
        v2 = {'status': 'FINAL', 'version': 2}
        v3 = {'status': 'FINAL', 'version': 3}
        trace = {
            'run_id': 'two-rounds',
            'observation_censored': False,
            'events': [
                {**settled(0, 1, 'lead', 1), 'final_state_after': v1},
                contribution(1, 2, 'inventory', 'message', 'M1'),
                {**settled(2, 3, 'lead', 2), 'final_state_after': v2},
                contribution(3, 4, 'ads', 'write_state'),
                {**settled(4, 5, 'lead', 3, 'revise_final_state'), 'final_state_after': v3},
            ],
            'model_calls': [
                call(1, 'lead', None, 0, 1),
                call(2, 'inventory', v1, 1, 2),
                call(3, 'lead', v1, 2, 3, input_messages=['M1']),
                call(4, 'ads', v2, 3, 4),
                call(5, 'lead', v2, 4, 5, state_origins=[3]),
            ],
        }
        result = derive_structural_feedback_rounds(trace)
        self.assertEqual(result['counter_status'], 'RECORDED')
        self.assertEqual(result['version'], 'R4-STRUCTURAL-FEEDBACK-ROUND-v0.2')
        self.assertTrue(result['semantic_blind'])
        self.assertEqual(result['round_count'], 2)
        self.assertEqual(result['rounds'][0]['exposure_actor'], 'inventory')
        self.assertEqual(result['rounds'][0]['return_actor'], 'lead')
        self.assertIn('message_read', result['rounds'][0]['return_evidence_modes'])
        self.assertEqual(result['rounds'][0]['closing_event_ref'], 'two-rounds:EVENT:0002')
        self.assertEqual(result['rounds'][1]['exposure_actor'], 'ads')
        self.assertIn('state_version_visible', result['rounds'][1]['return_evidence_modes'])
        self.assertEqual(result['rounds'][1]['closing_event_ref'], 'two-rounds:EVENT:0004')
        self.assertEqual(result['rounds'][0]['bias_labels'], 'NOT_ADJUDICATED')

    def test_propagation_without_return_is_not_feedback_round(self):
        v1 = {'status': 'FINAL', 'version': 1}
        v2 = {'status': 'FINAL', 'version': 2}
        trace = {
            'run_id': 'one-way',
            'events': [
                {**settled(0, 1, 'lead', 1), 'final_state_after': v1},
                {**settled(1, 2, 'inventory', 2), 'final_state_after': v2},
            ],
            'model_calls': [
                call(1, 'lead', None, 0, 1),
                call(2, 'inventory', v1, 1, 2),
            ],
        }
        result = derive_structural_feedback_rounds(trace)
        self.assertEqual(result['round_count'], 0)
        self.assertIsNotNone(result['open_tail'])
        self.assertFalse(result['open_tail']['return_to_anchor_observed'])

    def test_same_actor_reprocessing_does_not_create_round(self):
        v1 = {'status': 'FINAL', 'version': 1}
        v2 = {'status': 'FINAL', 'version': 2}
        trace = {
            'run_id': 'same-actor',
            'events': [
                {**settled(0, 1, 'lead', 1), 'final_state_after': v1},
                contribution(1, 2, 'lead', 'write_state'),
                {**settled(2, 2, 'lead', 2), 'final_state_after': v2},
            ],
            'model_calls': [
                call(1, 'lead', None, 0, 1),
                call(2, 'lead', v1, 1, 3, state_origins=[1]),
            ],
        }
        result = derive_structural_feedback_rounds(trace)
        self.assertEqual(result['round_count'], 0)

    def test_missing_runtime_snapshot_is_not_reconstructed(self):
        trace = {
            'run_id': 'legacy',
            'events': [settled(0, 1, 'lead', 1)],
            'model_calls': [{'turn': 1, 'agent_id': 'lead', 'status': 'completed'}],
        }
        result = derive_structural_feedback_rounds(trace)
        self.assertEqual(result['counter_status'], 'NOT_RECORDED_IN_SOURCE_VERSION')
        self.assertIsNone(result['round_count'])

    def test_censored_open_tail_stays_open(self):
        v1 = {'status': 'FINAL', 'version': 1}
        trace = {
            'run_id': 'censored-tail',
            'observation_censored': True,
            'events': [
                {**settled(0, 1, 'lead', 1), 'final_state_after': v1},
                contribution(1, 2, 'inventory', 'message', 'M1'),
            ],
            'model_calls': [
                call(1, 'lead', None, 0, 1),
                call(2, 'inventory', v1, 1, 2),
            ],
        }
        result = derive_structural_feedback_rounds(trace)
        self.assertEqual(result['round_count'], 0)
        self.assertIsNotNone(result['open_tail'])
        self.assertEqual(result['open_tail']['status'], 'OPEN_AT_OBSERVATION_BOUNDARY')
        self.assertFalse(result['open_tail']['return_to_anchor_observed'])


if __name__ == '__main__':
    unittest.main()
