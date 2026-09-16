import unittest

from arena.run_branch_one_shot_real import (
    AUTH_PHRASE,
    validate_symmetric_limits,
    verify_trace_exposure_invariants,
)


class ProspectiveOneShotForwardGuardTest(unittest.TestCase):
    def test_phase_specific_authorization_phrase(self):
        self.assertEqual('CALL_REAL_R5MID_PROSPECTIVE_ONESHOT_API', AUTH_PHRASE)
        self.assertNotEqual('CALL_REAL_R2R6_PROSPECTIVE_NATURAL_API', AUTH_PHRASE)
        self.assertNotEqual('CALL_REAL_R5MID_ONESHOT_BRANCH_API', AUTH_PHRASE)

    def test_symmetric_budget_envelope_must_fit_global_ceiling(self):
        self.assertTrue(validate_symmetric_limits(
            row_count=4,
            per_branch_max_calls=64,
            per_branch_spending_ceiling=0.25,
            global_spending_ceiling=1.0,
        ))
        with self.assertRaises(ValueError):
            validate_symmetric_limits(
                row_count=4,
                per_branch_max_calls=64,
                per_branch_spending_ceiling=0.25,
                global_spending_ceiling=0.5,
            )

    def test_exposure_integrity_is_zero_control_one_intervention(self):
        parent = {'turns': 8, 'queue': ['ops_lead']}
        envelope = {'envelope_hash': 'E', 'state_key': 'k'}
        control = {'condition_id': 'CONTROL_CONTINUATION'}
        intervention = {'condition_id': 'ONE_SHOT_JUMP_INTERVENTION'}
        self.assertEqual(0, verify_trace_exposure_invariants(
            trace={'runtime_transform_records': []}, row=control, envelope=envelope, parent_snapshot=parent
        )['direct_experiment_origin_exposure_count'])
        record = {
            'experiment_origin': True,
            'envelope_hash': 'E',
            'state_key': 'k',
            'persistent_state_mutation': False,
            'consumed_after_delivery': True,
            'turn': 9,
            'actor': 'ops_lead',
            'delivery_hash': 'D',
        }
        result = verify_trace_exposure_invariants(
            trace={'runtime_transform_records': [record]}, row=intervention, envelope=envelope, parent_snapshot=parent
        )
        self.assertEqual(1, result['direct_experiment_origin_exposure_count'])
        with self.assertRaises(ValueError):
            verify_trace_exposure_invariants(
                trace={'runtime_transform_records': [record, record]}, row=intervention, envelope=envelope, parent_snapshot=parent
            )


if __name__ == '__main__':
    unittest.main()
