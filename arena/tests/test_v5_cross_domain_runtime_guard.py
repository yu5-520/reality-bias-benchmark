import unittest

from arena.run_v5_cross_domain_real import AUTH_PHRASE, validate_paid_gate


class V5CrossDomainRuntimeGuardTest(unittest.TestCase):
    def test_generic_execute_does_not_authorize(self):
        with self.assertRaises(SystemExit):
            validate_paid_gate(
                execute_real_api=True,
                authorization_phrase="execute",
                per_run_max_calls=32,
                per_run_spending_ceiling=0.1,
                global_spending_ceiling=2.0,
                selected_run_count=20,
            )

    def test_exact_phrase_still_requires_positive_limits(self):
        with self.assertRaises(SystemExit):
            validate_paid_gate(
                execute_real_api=True,
                authorization_phrase=AUTH_PHRASE,
                per_run_max_calls=0,
                per_run_spending_ceiling=0,
                global_spending_ceiling=0,
                selected_run_count=20,
            )

    def test_exact_phrase_requires_global_ceiling_for_whole_wave(self):
        with self.assertRaises(SystemExit):
            validate_paid_gate(
                execute_real_api=True,
                authorization_phrase=AUTH_PHRASE,
                per_run_max_calls=32,
                per_run_spending_ceiling=0.1,
                global_spending_ceiling=1.9,
                selected_run_count=20,
            )

    def test_exact_phrase_and_symmetric_wave_budget_pass(self):
        validate_paid_gate(
            execute_real_api=True,
            authorization_phrase=AUTH_PHRASE,
            per_run_max_calls=32,
            per_run_spending_ceiling=0.1,
            global_spending_ceiling=2.0,
            selected_run_count=20,
        )


if __name__ == "__main__":
    unittest.main()
