import unittest

from arena.orchestration_compare import proposal_summary, verify_comparison_record
from arena.orchestration_preflight import build_offline_preflight


class OrchestrationComparisonTest(unittest.TestCase):
    def test_offline_preflight_separates_proposal_from_realization(self):
        free_trace, structured_trace, comparison = build_offline_preflight()
        self.assertTrue(verify_comparison_record(comparison))
        self.assertEqual('RUN_COMPLETE', free_trace['run_status'])
        self.assertEqual('RUN_COMPLETE', structured_trace['run_status'])
        self.assertTrue(comparison['same_task_hash'])
        self.assertTrue(comparison['same_agent_registry_hash'])
        self.assertEqual(
            'ENGINEERING_ONLY_NOT_SCIENTIFIC_EVIDENCE',
            comparison['scientific_status'],
        )

        free = proposal_summary(free_trace)
        structured = proposal_summary(structured_trace)
        self.assertGreaterEqual(free['proposal_invoke_count'], 1)
        self.assertGreaterEqual(free['realized_invoke_count'], 1)
        self.assertGreaterEqual(structured['proposal_invoke_count'], 1)
        self.assertGreaterEqual(structured['policy_blocked_invoke_count'], 1)
        self.assertEqual(0, structured['realized_invoke_count'])

    def test_structured_trace_preserves_original_blocked_proposal(self):
        _, structured_trace, _ = build_offline_preflight()
        controls = [
            (call.get('provider_response') or {}).get('structured_routing')
            for call in structured_trace['model_calls']
        ]
        controls = [x for x in controls if isinstance(x, dict)]
        self.assertTrue(controls)
        blocked = [row for control in controls for row in control.get('blocked_actions') or []]
        self.assertTrue(any(row.get('action', {}).get('type') == 'invoke_agent' for row in blocked))
        self.assertTrue(any(
            action.get('type') == 'invoke_agent'
            for control in controls
            for action in (control.get('original_subject_envelope') or {}).get('actions') or []
        ))
        self.assertFalse(any(
            event.get('action_type') == 'invoke_agent' and event.get('realized_in_baseline')
            for event in structured_trace['events']
        ))


if __name__ == '__main__':
    unittest.main()
