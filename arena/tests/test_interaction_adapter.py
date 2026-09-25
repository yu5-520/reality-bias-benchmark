import copy
import json
import unittest
from pathlib import Path

from arena.core import stable_hash
from arena.engine import run_arena_once
from arena.interaction_adapter import InteractionAdapter, project_legacy_trace, validate_interactions
from arena.interaction_conformance import conformance
from arena.providers import ScriptedProvider

ROOT = Path(__file__).resolve().parents[2]


class InteractionAdapterTests(unittest.TestCase):
    def test_native_common_pool_projection_preserves_trace_and_distinguishes_exposure(self):
        domain = json.loads((ROOT / "arena/domains/ecommerce.json").read_text())
        config = json.loads((ROOT / "arena/config/arena_v0.2.json").read_text())
        scripted = [
            {"actions": [
                {"type": "write_state", "key": "new_evidence", "value": "unconfirmed", "status": "provisional", "basis": "input"},
                {"type": "invoke_agent", "agent_id": "inventory", "request": "check"},
            ]},
            {"actions": [{"type": "message", "to": "ops_lead", "content": "checked"}]},
            {"actions": [{"type": "finalize", "answer": "first"}]},
            {"actions": [{"type": "finalize", "answer": "second"}]},
        ]
        trace = run_arena_once(domain, config, ScriptedProvider(scripted), "offline-interaction")
        original_hash = stable_hash(trace)
        events = project_legacy_trace(trace)
        self.assertEqual(stable_hash(trace), original_hash)
        self.assertEqual(validate_interactions(events)["status"], "PASS")
        schema = json.loads((ROOT / "schemas/interaction_event_v1.schema.json").read_text())
        self.assertEqual(set(events[0]), set(schema["required"]))
        self.assertTrue(any(e["surface"] == "delegate" for e in events))
        self.assertTrue(any(e["surface"] == "receive_message" and e["parent_event_ids"] for e in events))
        self.assertTrue(any(e["surface"] == "shared_state" and e["observation"] == "INPUT_EXPOSED"
                            and e["carrier_ref"] == "state:new_evidence" and e["parent_event_ids"] for e in events))
        self.assertFalse(any(e["observation"] == "EXECUTED" for e in events))
        self.assertEqual(conformance(events, expected_architecture="shared_common_pool",
                         raw_lookup=lambda ref: bool(ref))["status"], "PASS")
        broken = copy.deepcopy(trace)
        broken["message_ledger"] = []
        with self.assertRaisesRegex(ValueError, "missing_native_send_or_ledger_for_input"):
            project_legacy_trace(broken)

    def test_external_boundaries_are_observation_only_and_require_provenance(self):
        adapter = InteractionAdapter(run_id="offline", architecture_id="a2a_remote_boundary", adapter_version="transport-v1")
        task = adapter.remote_task(actor="manager", recipient="remote", native_ref="remote-request-1",
            raw_ref="raw:request:1", carrier_ref="remote:task:1", observation="DELIVERED", payload={"task": "x"})
        result = adapter.artifact_return(actor="remote", recipient="manager", native_ref="remote-reply-1",
            raw_ref="raw:reply:1", carrier_ref="remote:artifact:1", observation="RECORDED",
            payload={"result": "unverified"}, parent_event_ids=[task["event_id"]])
        self.assertEqual(validate_interactions(adapter.events)["status"], "PASS")
        self.assertEqual(result["parent_event_ids"], [task["event_id"]])
        self.assertFalse(result["source_refs"])  # Unknown provenance is not invented.
        self.assertEqual(conformance(adapter.events, expected_architecture="a2a_remote_boundary",
                         raw_lookup=lambda ref: True, require_boundary=True)["status"], "PASS")
        with self.assertRaises(ValueError):
            adapter.resource_read(actor="worker", native_ref="r", raw_ref="", carrier_ref="r",
                                  observation="INPUT_EXPOSED")
        with self.assertRaises(ValueError):
            adapter.memory_retrieve(actor="worker", native_ref="r", raw_ref="raw:r", carrier_ref="r",
                                    observation="INPUT_EXPOSED", parent_event_ids=["unseen"])

    def test_contract_fails_on_missing_parent_tampering_and_missing_raw(self):
        adapter = InteractionAdapter(run_id="offline", architecture_id="direct_peer_messaging", adapter_version="peer-v1")
        sent = adapter.send_message(actor="a", recipient="b", native_ref="sent:1", raw_ref="raw:sent:1",
            carrier_ref="message:1", observation="DELIVERED", payload="x")
        adapter.receive_message(actor="b", native_ref="inbox:1", raw_ref="raw:inbox:1",
            carrier_ref="message:1", observation="INPUT_EXPOSED", parent_event_ids=[sent["event_id"]])
        self.assertEqual(validate_interactions(adapter.events)["status"], "PASS")
        self.assertEqual(conformance(adapter.events, expected_architecture="direct_peer_messaging",
                         raw_lookup=lambda ref: ref != "raw:inbox:1")["status"], "FAIL")
        corrupted = copy.deepcopy(adapter.events)
        corrupted[1]["carrier_ref"] = "message:other"
        self.assertEqual(validate_interactions(corrupted)["status"], "FAIL")
        checked = conformance(adapter.events, expected_architecture="direct_peer_messaging",
                              raw_lookup=lambda ref: True, required_carrier_route=True)
        self.assertEqual(checked["status"], "PASS")
        self.assertEqual(checked["gates"]["lineage_reconstructability"], "PASS")
        self.assertEqual(checked["gates"]["authority_transition_auditability"], "NOT_ASSESSED")
        self.assertEqual(conformance(adapter.events, expected_architecture="direct_peer_messaging",
                         raw_lookup=lambda ref: True, require_boundary=True)["status"], "PASS")
        pool = adapter.shared_state(actor="b", native_ref="native:pool", raw_ref="raw:pool",
            carrier_ref="state:x", observation="INPUT_EXPOSED", payload="x")
        self.assertTrue(pool["event_id"])
        result = conformance(adapter.events, expected_architecture="direct_peer_messaging",
                             raw_lookup=lambda ref: True, require_boundary=True)
        self.assertIn("adapter_contract:peer_exposed_common_pool", result["failures"])

    def test_registered_structures_and_compatibility_surface(self):
        plan = json.loads((ROOT / "configs/architecture_conditioned_v1.json").read_text())
        self.assertEqual(len(plan["core_architectures"]), 5)
        self.assertEqual(len(plan["extensions_excluded_from_core"]), 2)
        self.assertFalse(plan["formal"]["paid_subject_execution_authorized"])
        self.assertFalse(plan["foundation"]["discovery_inventory_value_is_trajectory_count"])
        self.assertEqual(plan["formal"]["total_trajectory_range"], [90, 150])


if __name__ == "__main__":
    unittest.main()
