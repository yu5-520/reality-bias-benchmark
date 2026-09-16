import unittest

from arena.process_reality_dynamics_v0_2 import resolve_source_jump_root, build_process_reality_measurement


class ProcessRealityDynamicsV02Test(unittest.TestCase):
    def _adapter(self):
        return {
            'behavior_events': [
                {
                    'behavior_event_id': 't:derived:77',
                    'event_index': 77,
                    'turn': 8,
                    'actor': 'inventory',
                    'boundary_id': 'SHARED_STATE',
                    'action_type': 'write',
                    'target_ref': 'shared_state:inventory_stockout_assessment_v1',
                    'realization_status': 'REALIZED',
                    'source_refs': ['arena_event:32'],
                    'structured_diff': {'source_event_index': 32},
                    'behavior_phase': 'REALIZATION',
                },
                {
                    'behavior_event_id': 't:derived:78',
                    'event_index': 78,
                    'turn': 9,
                    'actor': 'ops_lead',
                    'boundary_id': 'AGENT_TURN',
                    'action_type': 'other',
                    'target_ref': 'turn:9',
                    'realization_status': 'REALIZED',
                    'source_refs': [],
                    'structured_diff': {},
                },
                {
                    'behavior_event_id': 't:derived:79',
                    'event_index': 79,
                    'turn': 10,
                    'actor': 'ops_lead',
                    'boundary_id': 'SHARED_STATE',
                    'action_type': 'write',
                    'target_ref': 'shared_state:next',
                    'realization_status': 'REALIZED',
                    'source_refs': ['arena_event:40'],
                    'structured_diff': {'source_event_index': 40},
                },
            ]
        }

    def test_resolves_source_event_not_derived_event_index(self):
        resolved = resolve_source_jump_root(
            adapter_result=self._adapter(),
            target_source_event_index=32,
            target_state_key='inventory_stockout_assessment_v1',
        )
        self.assertEqual('RESOLVED_EXACT_SOURCE_EVENT', resolved['status'])
        self.assertEqual('t:derived:77', resolved['behavior_event']['behavior_event_id'])
        self.assertNotEqual(32, resolved['behavior_event']['event_index'])

    def test_unresolved_root_does_not_impute_zero(self):
        measurement = build_process_reality_measurement(
            trace={'run_id': 't', 'run_status': 'RUN_COMPLETE', 'runtime_transform_records': [], 'final_state': {}},
            adapter_result=self._adapter(),
            dynamics_view={'jump_candidates': []},
            lineage_view={'lineage_relations': []},
            target_source_event_index=999,
            target_state_key='missing',
            target_candidate_id='candidate:x',
            branch_start_turn=8,
        )
        self.assertEqual('ROOT_UNRESOLVED_NO_ZERO_IMPUTATION', measurement['mechanism_measurement_status'])
        self.assertIsNone(measurement['r2_jump_recurrence']['descendant_rejump_count'])
        self.assertIsNone(measurement['r3_inherited_inertia']['root_reachable_event_count'])
        self.assertIsNone(measurement['r3_inherited_inertia']['affected_agent_count'])

    def test_resolved_root_traces_lineage(self):
        adapter = self._adapter()
        measurement = build_process_reality_measurement(
            trace={'run_id': 't', 'run_status': 'RUN_COMPLETE', 'runtime_transform_records': [], 'final_state': {}},
            adapter_result=adapter,
            dynamics_view={'jump_candidates': [
                {'candidate_id': 'J1', 'behavior_event_id': 't:derived:79', 'turn': 10}
            ]},
            lineage_view={'lineage_relations': [
                {'source_behavior_event_id': 't:derived:77', 'target_behavior_event_id': 't:derived:78', 'relation_type': 'STATE_VISIBLE'},
                {'source_behavior_event_id': 't:derived:78', 'target_behavior_event_id': 't:derived:79', 'relation_type': 'TURN_TO_ACTION'},
            ]},
            target_source_event_index=32,
            target_state_key='inventory_stockout_assessment_v1',
            target_candidate_id='candidate:J0',
            branch_start_turn=8,
        )
        self.assertEqual('ROOT_RESOLVED', measurement['mechanism_measurement_status'])
        self.assertEqual(2, measurement['r3_inherited_inertia']['root_reachable_event_count'])
        self.assertEqual(2, measurement['r3_inherited_inertia']['root_reach_depth'])
        self.assertEqual(1, measurement['r2_jump_recurrence']['descendant_rejump_count'])


if __name__ == '__main__':
    unittest.main()
