import unittest

from arena.process_reality_dynamics_v0_4 import (
    build_process_reality_measurement,
    canonical_event_signature,
    compare_process_reality,
)


class ProcessRealityDynamicsV04Test(unittest.TestCase):
    def _event(self, eid, idx, turn, actor, boundary, action, target, *, source_index=None):
        diff = {'behavior_phase': 'REALIZATION'}
        if source_index is not None:
            diff['source_event_index'] = source_index
            diff['action_key'] = target.split(':', 1)[1] if target.startswith('shared_state:') else None
        return {
            'behavior_event_id': eid,
            'trajectory_id': 'run-A',
            'event_index': idx,
            'turn': turn,
            'boundary_id': boundary,
            'behavior_phase': 'REALIZATION',
            'actor': actor,
            'action_type': action,
            'target_ref': target,
            'realization_status': 'REALIZED',
            'source_refs': [f'arena_event:{source_index}'] if source_index is not None else [],
            'structured_diff': diff,
        }

    def test_three_layer_measurement_from_selected_root(self):
        root = self._event('root', 10, 8, 'inventory', 'SHARED_STATE', 'write', 'shared_state:k', source_index=32)
        d1 = self._event('d1', 11, 9, 'ops_lead', 'AGENT_TURN', 'execute', 'turn:9')
        d2 = self._event('d2', 12, 10, 'ads', 'SHARED_STATE', 'write', 'shared_state:x', source_index=40)
        d3 = self._event('d3', 13, 10, 'finance', 'AGENT_TURN', 'execute', 'turn:10')
        d4 = self._event('d4', 14, 11, 'ops_lead', 'FINAL_REOPEN', 'revise', 'run-A:FINAL:001')
        relations = [
            {'source_behavior_event_id': 'root', 'target_behavior_event_id': 'd1', 'relation_type': 'STATE_MUTATION_TO_AGENT_TURN_VISIBILITY'},
            {'source_behavior_event_id': 'd1', 'target_behavior_event_id': 'd2', 'relation_type': 'AGENT_TURN_TO_ACTION_PROPOSAL'},
            {'source_behavior_event_id': 'd1', 'target_behavior_event_id': 'd3', 'relation_type': 'AGENT_TURN_TO_ACTION_PROPOSAL'},
            {'source_behavior_event_id': 'd2', 'target_behavior_event_id': 'd4', 'relation_type': 'FINAL_STATE_VERSION_TO_REVISION'},
            {'source_behavior_event_id': 'd3', 'target_behavior_event_id': 'd4', 'relation_type': 'MESSAGE_READ_TO_AGENT_TURN'},
        ]
        dynamics = {'jump_candidates': [
            {
                'candidate_id': 'root-jump', 'behavior_event_id': 'root', 'event_index': 10, 'turn': 8,
                'actor': 'inventory', 'boundary_id': 'SHARED_STATE', 'candidate_types': ['HIGH_CERTAINTY_STATE_WRITE'],
            },
            {
                'candidate_id': 'desc-jump', 'behavior_event_id': 'd2', 'event_index': 12, 'turn': 10,
                'actor': 'ads', 'boundary_id': 'SHARED_STATE', 'candidate_types': ['HIGH_CERTAINTY_STATE_WRITE'],
            },
        ]}
        trace = {
            'run_id': 'run-A', 'run_status': 'RUN_COMPLETE', 'observation_censored': False,
            'runtime_transform_records': [{
                'experiment_origin': True, 'actor': 'ads', 'turn': 10,
            }],
            'final_state': {},
        }
        m = build_process_reality_measurement(
            trace=trace,
            adapter_result={'behavior_events': [root, d1, d2, d3, d4]},
            dynamics_view=dynamics,
            lineage_view={'lineage_relations': relations},
            target_source_event_index=32,
            target_state_key='k',
            target_candidate_id='selected-J0',
            branch_start_turn=8,
        )
        self.assertEqual('ROOT_RESOLVED', m['mechanism_measurement_status'])
        self.assertEqual(1, m['r2_jump_recurrence']['descendant_rejump_count'])
        first = m['r2_jump_recurrence']['first_descendant_rejump']
        self.assertEqual(2, first['event_distance'])
        self.assertEqual(2, first['turn_distance'])
        self.assertEqual(2, first['lineage_depth'])
        self.assertTrue(first['direct_experiment_exposure'])
        self.assertTrue(first['candidate_family_continuity'])
        inertia = m['r3_inherited_inertia']
        self.assertEqual(1, inertia['branch_merge_metrics']['branch_node_count'])
        self.assertEqual(1, inertia['branch_merge_metrics']['merge_node_count'])
        self.assertEqual(1, inertia['role_reentry']['role_reentry_count'])
        paths = m['root_descendant_topology']['observed_path_families']
        self.assertEqual(2, paths['observed_path_family_count'])
        self.assertFalse(paths['path_family_overflow'])
        all_text = '\n'.join(paths['observed_path_family_signatures'])
        self.assertNotIn('run-A', all_text)
        self.assertNotIn('turn:9', all_text)

    def test_pair_comparison_reports_reconvergence_survival_and_path_families(self):
        control = {
            'trajectory_id': 'A',
            'root_descendant_topology': {
                'canonical_edge_multiset': {'e1': 2, 'e2': 1},
                'canonical_ordered_event_signatures': ['x', 'a', 'm', 'z'],
                'observed_path_families': {'observed_path_family_signatures': ['p1', 'p2']},
            },
            'full_post_context_topology': {'canonical_edge_multiset': {'n': 1}},
            'r2_jump_recurrence': {
                'descendant_rejump_count': 1,
                'first_rejump_event_distance': 4,
                'first_rejump_turn_distance': 2,
                'first_descendant_rejump': {'candidate_id': 'c1'},
            },
            'r3_inherited_inertia': {
                'continuation_root_reach_depth': 3,
                'continuation_root_reachable_event_count': 6,
                'affected_agent_ids': ['ads', 'ops'],
                'root_descendant_cross_actor_relation_count': 3,
                'branch_merge_metrics': {'branch_node_count': 1, 'merge_node_count': 1},
                'role_reentry': {'role_reentry_count': 1},
            },
        }
        intervention = {
            'trajectory_id': 'B',
            'root_descendant_topology': {
                'canonical_edge_multiset': {'e1': 1, 'e3': 1},
                'canonical_ordered_event_signatures': ['x', 'b', 'm', 'q'],
                'observed_path_families': {'observed_path_family_signatures': ['p1', 'p3']},
            },
            'full_post_context_topology': {'canonical_edge_multiset': {'n': 1}},
            'r2_jump_recurrence': {
                'descendant_rejump_count': 2,
                'first_rejump_event_distance': 3,
                'first_rejump_turn_distance': 1,
                'first_descendant_rejump': {'candidate_id': 'i1'},
            },
            'r3_inherited_inertia': {
                'continuation_root_reach_depth': 4,
                'continuation_root_reachable_event_count': 7,
                'affected_agent_ids': ['finance', 'ops'],
                'root_descendant_cross_actor_relation_count': 4,
                'branch_merge_metrics': {'branch_node_count': 2, 'merge_node_count': 0},
                'role_reentry': {'role_reentry_count': 2},
            },
        }
        row = compare_process_reality(control, intervention, comparison_id='pair')
        layer2 = row['layer2_inherited_inertia']
        self.assertEqual(1, layer2['shared_path_prefix_event_count'])
        self.assertEqual('m', layer2['first_signature_reconvergence']['canonical_event_signature'])
        self.assertAlmostEqual(1 / 3, layer2['control_descendant_edge_survival_in_intervention'])
        layer3 = row['layer3_path_topology']
        self.assertEqual(['p1'], layer3['shared_path_families'])
        self.assertEqual(['p2'], layer3['control_only_path_families'])
        self.assertEqual(['p3'], layer3['intervention_only_path_families'])
        self.assertEqual(['ops'], layer2['shared_affected_agents'])
        self.assertFalse(row['terminal_outcome_comparison_is_primary'])

    def test_canonical_signature_preserves_structure_not_instance_identity(self):
        left = self._event('a', 1, 4, 'ops', 'FINAL_REOPEN', 'finalize', 'run-A:FINAL:1')
        right = self._event('b', 91, 44, 'ops', 'FINAL_REOPEN', 'finalize', 'run-B:FINAL:999')
        right['trajectory_id'] = 'run-B'
        self.assertEqual(canonical_event_signature(left), canonical_event_signature(right))


if __name__ == '__main__':
    unittest.main()
