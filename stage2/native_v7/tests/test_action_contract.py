import json
import unittest
from pathlib import Path

from stage2.native_v7.action_contract import (
    REGISTRY,
    apply_model_visible_action_contract,
    contract_id_for_task,
)
from stage2.native_v7.software_host_v1 import ROLES, SoftwareEngineeringHost


ROOT = Path(__file__).resolve().parents[3]


class Stage2ActionContractVersioning(unittest.TestCase):
    def test_registry_keeps_t1_historical_and_t2_t3_prospective(self):
        self.assertEqual(contract_id_for_task("T1"), "v1_t1_historical")
        self.assertEqual(contract_id_for_task("T2"), "v2_t2_t3_prospective")
        self.assertEqual(contract_id_for_task("T3"), "v2_t2_t3_prospective")
        self.assertEqual(set(REGISTRY["applies_to"]), {"X2", "X3", "X4", "X5", "X6", "X7"})
        self.assertEqual(REGISTRY["excluded_native_interface"], ["X1"])

    def test_t1_prompt_bytes_are_not_augmented_by_contract_helper(self):
        system = "historical-system"
        content = {"available_actions": {"list_files": {}}, "remaining_turns": 32}
        returned_system, returned_content, contract_id = apply_model_visible_action_contract(
            system, content, task_id="T1", max_actions=5
        )
        self.assertEqual(contract_id, "v1_t1_historical")
        self.assertIs(returned_content, content)
        self.assertEqual(returned_system, system)
        self.assertNotIn("action_contract_id", returned_content)
        self.assertNotIn("required_action_envelope", returned_content)
        self.assertNotIn("max_actions_per_turn", returned_content)

    def test_t2_t3_expose_existing_parser_constraints_only(self):
        for task_id in ("T2", "T3"):
            with self.subTest(task_id=task_id):
                system, content, contract_id = apply_model_visible_action_contract(
                    "base",
                    {"available_actions": {"list_files": {}}},
                    task_id=task_id,
                    max_actions=5,
                )
                self.assertEqual(contract_id, "v2_t2_t3_prospective")
                self.assertIn('"actions" list', system)
                self.assertIn("at most 5 action objects", system)
                self.assertEqual(content["max_actions_per_turn"], 5)
                self.assertEqual(content["action_contract_id"], "v2_t2_t3_prospective")
                self.assertIn("required_action_envelope", content)

    def test_contract_rejects_parser_limit_drift(self):
        with self.assertRaisesRegex(ValueError, "max_actions differs"):
            apply_model_visible_action_contract(
                "base", {"available_actions": {}}, task_id="T2", max_actions=6
            )

    def test_capability_host_selects_contract_by_frozen_task(self):
        fixture = ROOT / "stage2/fixtures/project"
        t1 = SoftwareEngineeringHost(task_id="T1", checkout=fixture, provider=object())
        t2 = SoftwareEngineeringHost(task_id="T2", checkout=fixture, provider=object())
        t1_payload = json.loads(t1._prompt(ROLES["entry_agent"], [])[1]["content"])
        t2_payload = json.loads(t2._prompt(ROLES["entry_agent"], [])[1]["content"])
        self.assertNotIn("action_contract_id", t1_payload)
        self.assertEqual(t2_payload["action_contract_id"], "v2_t2_t3_prospective")
        self.assertEqual(t2_payload["max_actions_per_turn"], 5)

    def test_native_x2_x3_use_registry_without_common_runtime_adapter(self):
        x2 = (ROOT / "stage2/native_v7/x2_metagpt/runner.py").read_text()
        x3 = (ROOT / "stage2/native_v7/x3_a2a/service.py").read_text()
        for source in (x2, x3):
            self.assertIn("apply_model_visible_action_contract", source)
            self.assertIn("max_actions=5", source)
        self.assertNotIn("SoftwareEngineeringHost", x2)
        self.assertNotIn("SoftwareEngineeringHost", x3)


if __name__ == "__main__":
    unittest.main()
