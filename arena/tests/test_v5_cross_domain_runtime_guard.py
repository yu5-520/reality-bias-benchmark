import unittest

from arena.run_v5_cross_domain_real import AUTH_PHRASE, validate_paid_gate


class V5CrossDomainRuntimeGuardTest(unittest.TestCase):
    def test_generic_execute_does_not_authorize(self):
        with self.assertRaises(SystemExit):
            validate_paid_gate(
                execute_real_api=True,
                authorization_phrase="execute",
                authorization_event_id="AUTH",
                per_run_max_calls=32,
                per_run_spending_ceiling=0.1,
                wave_spending_ceiling=1.5,
                first_round_spending_ceiling=9.0,
                selected_run_count=15,
                wave_count=6,
            )

    def test_exact_phrase_requires_shared_authorization_event(self):
        with self.assertRaises(SystemExit):
            validate_paid_gate(
                execute_real_api=True,
                authorization_phrase=AUTH_PHRASE,
                authorization_event_id="",
                per_run_max_calls=32,
                per_run_spending_ceiling=0.1,
                wave_spending_ceiling=1.5,
                first_round_spending_ceiling=9.0,
                selected_run_count=15,
                wave_count=6,
            )

    def test_exact_phrase_still_requires_positive_limits(self):
        with self.assertRaises(SystemExit):
            validate_paid_gate(
                execute_real_api=True,
                authorization_phrase=AUTH_PHRASE,
                authorization_event_id="AUTH",
                per_run_max_calls=0,
                per_run_spending_ceiling=0,
                wave_spending_ceiling=0,
                first_round_spending_ceiling=0,
                selected_run_count=15,
                wave_count=6,
            )

    def test_wave_ceiling_must_cover_15_symmetric_runs(self):
        with self.assertRaises(SystemExit):
            validate_paid_gate(
                execute_real_api=True,
                authorization_phrase=AUTH_PHRASE,
                authorization_event_id="AUTH",
                per_run_max_calls=32,
                per_run_spending_ceiling=0.1,
                wave_spending_ceiling=1.49,
                first_round_spending_ceiling=9.0,
                selected_run_count=15,
                wave_count=6,
            )

    def test_first_round_ceiling_must_cover_six_wave_ceilings(self):
        with self.assertRaises(SystemExit):
            validate_paid_gate(
                execute_real_api=True,
                authorization_phrase=AUTH_PHRASE,
                authorization_event_id="AUTH",
                per_run_max_calls=32,
                per_run_spending_ceiling=0.1,
                wave_spending_ceiling=1.5,
                first_round_spending_ceiling=8.99,
                selected_run_count=15,
                wave_count=6,
            )

    def test_exact_phrase_and_full_six_wave_budget_pass(self):
        validate_paid_gate(
            execute_real_api=True,
            authorization_phrase=AUTH_PHRASE,
            authorization_event_id="AUTH",
            per_run_max_calls=32,
            per_run_spending_ceiling=0.1,
            wave_spending_ceiling=1.5,
            first_round_spending_ceiling=9.0,
            selected_run_count=15,
            wave_count=6,
        )


if __name__ == "__main__":
    unittest.main()
