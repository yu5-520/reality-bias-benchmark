import unittest

from arena.run_v5_whole_process_real import AUTH_PHRASE, validate_paid_gate


class V5WholeProcessRuntimeGuardTest(unittest.TestCase):
    def test_generic_execute_does_not_authorize(self):
        with self.assertRaises(SystemExit):
            validate_paid_gate(
                execute_real_api=True,
                authorization_phrase="execute",
                per_run_max_calls=32,
                per_run_spending_ceiling=0.1,
                global_spending_ceiling=0.3,
                run_count=3,
            )

    def test_exact_phrase_still_requires_positive_budgets(self):
        with self.assertRaises(SystemExit):
            validate_paid_gate(
                execute_real_api=True,
                authorization_phrase=AUTH_PHRASE,
                per_run_max_calls=0,
                per_run_spending_ceiling=0,
                global_spending_ceiling=0,
                run_count=3,
            )

    def test_exact_phrase_and_positive_limits_pass_gate_function(self):
        validate_paid_gate(
            execute_real_api=True,
            authorization_phrase=AUTH_PHRASE,
            per_run_max_calls=32,
            per_run_spending_ceiling=0.1,
            global_spending_ceiling=0.3,
            run_count=3,
        )


if __name__ == "__main__":
    unittest.main()
