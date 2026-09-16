import unittest

from arena.process_reality_dynamics_v0_3 import (
    build_process_reality_measurement,
    canonical_event_signature,
    compare_process_reality,
)


class ProcessRealityDynamicsV03Test(unittest.TestCase):
    def test_canonical_signature_removes_run_and_ephemeral_ids(self):
        a = {
            'actor': 'ops_lead', 'boundary_id': 'FINAL_REOPEN', 'action_type': 'finalize',
            'target_ref': 'run-A:FINAL:001', 'realization_status': 'REALIZED',
            'structured_diff': {'behavior_phase': 'REALIZATION'},
            'turn': 9, 'node_id': 'turn:9', 'behavior_event_id': 'run-A:event:99'
        }
        b = {
            'actor': 'ops_lead', 'boundary_id': 'FINAL_REOPEN', 'action_type': 'finalize',
            'target_ref': 'run-B:FINAL:777', 'realization_status': 'REALIZED',
            'structured_diff': {'behavior_phase': 'REALIZATION'},
            'turn': 31, 'node_id': 'turn:31', 'behavior_event_id': 'run-B:event:2'
        }
        self.assertEqual(canonical_event_signature(a), canonical_event_signature(b))
        self.assertNotIn('run-A', canonical_event_signature(a))
        self.assertNotIn('turn:9', canonical_event_signature(a))

        msg_a = {
            'actor': 'strategy', 'boundary_id': 'MESSAGE_HANDOFF', 'action_type': 'message',
            'target_ref': 'message:abc', 'realization_status': 'REALIZED',
            'structured_diff': {'behavior_phase': 'REALIZATION', 'action_to': 'ads'}
        }
        msg_b = {
            'actor': 'strategy', 'boundary_id': 'MESSAGE_HANDOFF', 'action_type': 'message',
            'target_ref': 'message:xyz', 'realization_status': 'REALIZED',
            'structured_diff': {'behavior_phase': 'REALIZATION', 'action_to': 'ads'}
        }
        self.assertEqual(canonical_event_signature(msg_a), canonical_event_signature(msg_b))

    def test_inertia_scope_excludes_unrelated_post_branch_activity(self):
        root = {
            'behavior_event_id': 'run:root', 'trajectory_id': 'run', 'event_index': 10, 'turn': 8,
            'boundary_id': 'SHARED_STATE', 'actor': 'inventory', 'action_type': 'write',
            'target_ref': 'shared_state:k', 'realization_status': 'REALIZED',
            'source_refs': ['arena_event:32'],
            'structured_diff': {'behavior_phase': 'REALIZATION', 'source_event_index': 32, 'action_key': 'k'},
        }
        d1 = {
            'behavior_event_id': 'run:d1', 'trajectory_id': 'run', 'event_index': 11, 'turn': 9,
            'boundary_id': 'AGENT_TURN', 'actor': 'inventory', 'action_type': 'execute',
            'target_ref': 'turn:9', 'realization_status': 'REALIZED',
            'structured_diff': {'behavior_phase': 'AGENT_TURN'},
        }
        d2 = {
            'behavior_event_id': 'run:d2', 'trajectory_id': 'run', 'event_index': 12, 'turn': 10,
            'boundary_id': 'SHARED_STATE', 'actor': 'ads', 'action_type': 'write',
            'target_ref': 'shared_state:x', 'realization_status': 'REALIZED',
            'structured_diff': {'behavior_phase': 'REALIZATION', 'source_event_index': 40, 'action_key': 'x'},
        }
        u1 = {
            'behavior_event_id': 'run:u1', 'trajectory_id': 'run', 'event_index': 13, 'turn': 9,
            'boundary_id': 'AGENT_TURN', 'actor': 'finance', 'action_type': 'execute',
            'target_ref': 'turn:9', 'realization_status': 'REALIZED',
            'structured_diff': {'behavior_phase': 'AGENT_TURN'},
        }
        u2 = {
            'behavior_event_id': 'run:u2', 'trajectory_id': 'run', 'event_index': 14, 'turn': 10,
            'boundary_id': 'AGENT_TURN', 'actor': 'strategy', 'action_type': 'execute',
            'target_ref': 'turn:10', 'realization_status': 'REALIZED',
            'structured_diff': {'behavior_phase': 'AGENT_TURN'},
        }
        relations = [
            {'source_behavior_event_id': 'run:root', 'target_behavior_event_id': 'run:d1', 'relation_type': 'STATE_MUTATION_TO_AGENT_TURN_VISIBILITY'},
            {'source_behavior_event_id': 'run:d1', 'target_behavior_event_id': 'run:d2', 'relation_type': 'AGENT_TURN_TO_ACTION_PROPOSAL'},
            {'source_behavior_event_id': 'run:u1', 'target_behavior_event_id': 'run:u2', 'relation_type': 'MESSAGE_READ_TO_AGENT_TURN'},
        ]
        measurement = build_process_reality_measurement(
            trace={'run_id': 'run', 'run_status': 'RUN_COMPLETE', 'runtime_transform_records': [], 'final_state': {}},
            adapter_result={'behavior_events': [root, d1, d2, u1, u2]},
            dynamics_view={'jump_candidates': [
                {'behavior_event_id': 'run:d2', 'turn': 10, 'candidate_id': 'desc'},
                {'behavior_event_id': 'run:u2', 'turn': 10, 'candidate_id': 'independent'},
            ]},
            lineage_view={'lineage_relations': relations},
            target_source_event_index=32,
            target_state_key='k',
            target_candidate_id='J0',
            branch_start_turn=8,
        )
        self.assertEqual(1, measurement['r2_jump_recurrence']['descendant_rejump_count'])
        self.assertEqual(1, measurement['r2_jump_recurrence']['independent_new_jump_count'])
        self.assertEqual(2, measurement['r3_inherited_inertia']['continuation_root_reachable_event_count'])
        self.assertEqual(1, measurement['r3_inherited_inertia']['root_descendant_cross_actor_relation_count'])
        self.assertEqual(2, measurement['full_post_context_topology']['cross_actor_relation_count'])
        root_edges = measurement['root_descendant_topology']['canonical_edge_multiset']
        self.assertEqual(2, sum(root_edges.values()))
        self.assertTrue(all('finance' not in edge and 'strategy' not in edge for edge in root_edges))

    def test_pair_comparison_uses_root_topology_as_primary_structure(self):
        control = {
            'trajectory_id': 'A',
            'root_descendant_topology': {
                'canonical_edge_multiset': {'edge-a': 2, 'edge-b': 1},
                'canonical_ordered_event_signatures': ['x', 'y'],
            },
            'full_post_context_topology': {'canonical_edge_multiset': {'noise': 4}},
            'r2_jump_recurrence': {'descendant_rejump_count': 1},
            'r3_inherited_inertia': {
                'continuation_root_reach_depth': 3, 'continuation_root_reachable_event_count': 5,
                'affected_agent_count': 2, 'root_descendant_cross_actor_relation_count': 2,
            },
        }
        intervention = {
            'trajectory_id': 'B',
            'root_descendant_topology': {
                'canonical_edge_multiset': {'edge-a': 1, 'edge-c': 1},
                'canonical_ordered_event_signatures': ['x', 'q'],
            },
            'full_post_context_topology': {'canonical_edge_multiset': {'noise': 4}},
            'r2_jump_recurrence': {'descendant_rejump_count': 2},
            'r3_inherited_inertia': {
                'continuation_root_reach_depth': 4, 'continuation_root_reachable_event_count': 6,
                'affected_agent_count': 3, 'root_descendant_cross_actor_relation_count': 3,
            },
        }
        row = compare_process_reality(control, intervention, comparison_id='PAIR')
        self.assertEqual(1, row['root_descendant_topology']['shared_path_prefix_event_count'])
        self.assertEqual(['edge-b'], row['root_descendant_topology']['control_only_edge_signatures'])
        self.assertEqual(['edge-c'], row['root_descendant_topology']['intervention_only_edge_signatures'])
        self.assertEqual(1.0, row['full_post_context_topology']['edge_set_jaccard'])
        self.assertFalse(row['terminal_outcome_comparison_is_primary'])


if __name__ == '__main__':
    unittest.main()
