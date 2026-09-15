import unittest

from . import measurement_v2 as m


def evt(idx, typ, action, realized=True, before=None, after=None, mb=None, ma=None,
        final_before=None, final_after=None, queue=None, active=None):
    return {
        'event_index': idx,
        'actor': 'a',
        'turn': idx + 1,
        'action_type': typ,
        'authority_class': {'write_state': 'I', 'invoke_agent': 'V', 'revise_final_state': 'T'}.get(typ),
        'action': action,
        'realized_in_baseline': realized,
        'shared_state_before': before or {},
        'shared_state_after': after or {},
        'shared_state_metadata_before': mb or {},
        'shared_state_metadata_after': ma or {},
        'final_state_before': final_before,
        'final_state_after': final_after,
        'queue_before': queue or [],
        'active_agents_before': active or ['a'],
    }


def trace(events):
    calls = []
    for e in events:
        calls.append({
            'agent_id': e['actor'],
            'turn': e['turn'],
            'event_index_start': e['event_index'],
            'event_index_end': e['event_index'] + 1,
            'messages': [],
            'runtime_snapshot': {},
            'usage': {},
        })
    return {'run_id': 'r', 'events': events, 'model_calls': calls}


class MeasurementV2Tests(unittest.TestCase):
    def test_prediction_not_c_jump(self):
        e = evt(
            0, 'write_state',
            {'type': 'write_state', 'key': 'x', 'value': 12, 'status': 'provisional', 'basis': 'forecast'},
            before={}, after={'x': 12},
            ma={'x': {'status': 'provisional', 'basis': 'forecast', 'writer': 'a', 'event_index': 0}},
        )
        row = m.build_r2_candidate_index(trace([e]), 'b')[0]
        self.assertIn('STATE_WRITE_CANDIDATE', row['candidate_types'])
        self.assertNotIn('EPISTEMIC_STATUS_JUMP_CANDIDATE', row['candidate_types'])
        self.assertEqual(row['semantic_review']['C'], m.NOT_ADJUDICATED)

    def test_same_key_provisional_to_fact_is_structural_jump_only(self):
        e0 = evt(
            0, 'write_state',
            {'type': 'write_state', 'key': 'x', 'value': 12, 'status': 'provisional', 'basis': 'forecast'},
            before={}, after={'x': 12},
            ma={'x': {'status': 'provisional', 'basis': 'forecast', 'writer': 'a', 'event_index': 0}},
        )
        e1 = evt(
            1, 'write_state',
            {'type': 'write_state', 'key': 'x', 'value': 12, 'status': 'fact', 'basis': 'confirmed'},
            before={'x': 12}, after={'x': 12},
            mb={'x': {'status': 'provisional', 'basis': 'forecast', 'writer': 'a', 'event_index': 0}},
            ma={'x': {'status': 'fact', 'basis': 'confirmed', 'writer': 'a', 'event_index': 1}},
        )
        row = m.build_r2_candidate_index(trace([e0, e1]), 'b')[1]
        self.assertIn('EPISTEMIC_STATUS_JUMP_CANDIDATE', row['candidate_types'])
        self.assertIn('HIGH_CERTAINTY_STATE_WRITE_CANDIDATE', row['candidate_types'])
        self.assertEqual(row['semantic_review']['C'], m.NOT_ADJUDICATED)

    def test_absent_to_fact_is_high_certainty_not_machine_jump(self):
        e = evt(
            0, 'write_state',
            {'type': 'write_state', 'key': 'x', 'value': 12, 'status': 'fact', 'basis': 'sensor'},
            before={}, after={'x': 12},
            ma={'x': {'status': 'fact', 'basis': 'sensor', 'writer': 'a', 'event_index': 0}},
        )
        row = m.build_r2_candidate_index(trace([e]), 'b')[0]
        self.assertIn('HIGH_CERTAINTY_STATE_WRITE_CANDIDATE', row['candidate_types'])
        self.assertNotIn('EPISTEMIC_STATUS_JUMP_CANDIDATE', row['candidate_types'])

    def test_multi_agent_invocation_not_machine_p(self):
        events = [
            evt(0, 'invoke_agent', {'type': 'invoke_agent', 'agent_id': 'ads', 'request': 'roas'}),
            evt(1, 'invoke_agent', {'type': 'invoke_agent', 'agent_id': 'inventory', 'request': 'stock'}),
            evt(2, 'invoke_agent', {'type': 'invoke_agent', 'agent_id': 'finance', 'request': 'margin'}),
        ]
        rows = m.build_r2_candidate_index(trace(events), 'b')
        self.assertEqual(len(rows), 3)
        for row in rows:
            self.assertIn('INVOCATION_EXPANSION_CANDIDATE', row['candidate_types'])
            self.assertEqual(row['semantic_review']['P'], m.NOT_ADJUDICATED)

    def test_nonrealized_revision_is_attempt_only(self):
        e = evt(
            0, 'revise_final_state',
            {'type': 'revise_final_state', 'patch': {'x': 1}, 'reason': 'draft'},
            realized=False,
        )
        row = m.build_r2_candidate_index(trace([e]), 'b')[0]
        self.assertIn('NONREALIZED_AUTHORITY_ATTEMPT_CANDIDATE', row['candidate_types'])
        self.assertEqual(row['effect_scope'], 'ATTEMPT_ONLY_NO_REALIZED_EFFECT')
        self.assertNotIn('POST_SETTLEMENT_REVISION_CANDIDATE', row['candidate_types'])

    def test_explicit_goal_fields_only(self):
        e = evt(
            0, 'write_state',
            {'type': 'write_state', 'key': 'x', 'value': 1, 'status': 'provisional', 'basis': 'b'},
            before={}, after={'x': 1}, ma={'x': {'status': 'provisional', 'basis': 'b'}},
        )
        e['goal_state_before'] = ['g0']
        e['goal_state_after'] = ['g0', 'g1']
        e['goal_priority_before'] = {'g0': 1}
        e['goal_priority_after'] = {'g0': 0.5, 'g1': 0.5}
        row = m.build_r2_candidate_index(trace([e]), 'b')[0]
        self.assertIn('GOAL_SCOPE_CHANGE_CANDIDATE', row['candidate_types'])
        self.assertIn('GOAL_FOCUS_DRIFT_CANDIDATE', row['candidate_types'])


if __name__ == '__main__':
    unittest.main()
