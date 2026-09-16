import unittest

from arena.system_behavior import (
    BOUNDARY_REGISTRY_SCHEMA,
    SystemBehaviorValidationError,
    RegistryBundle,
    build_system_trajectory_measurement,
    make_behavior_event,
    validate_behavior_event,
    validate_registry_crossrefs,
)


class SystemBehaviorTests(unittest.TestCase):
    def test_repo_registries_cross_validate(self):
        bundle = RegistryBundle.load()
        self.assertEqual(bundle.boundaries["schema"], BOUNDARY_REGISTRY_SCHEMA)
        variable_ids = {row["variable_id"] for row in bundle.variables["variables"]}
        boundary_ids = {row["boundary_id"] for row in bundle.boundaries["boundaries"]}
        self.assertIn("EPISTEMIC_STATUS_DOWNGRADE", variable_ids)
        self.assertIn("ORCHESTRATION_STRUCTURE", variable_ids)
        self.assertIn("SHARED_STATE", boundary_ids)
        self.assertIn("RECOVERY_CHECKPOINT", boundary_ids)

    def test_behavior_event_is_structural_and_semantic_blind(self):
        bundle = RegistryBundle.load()
        event = make_behavior_event(
            behavior_event_id="bev-1",
            trajectory_id="traj-1",
            event_index=3,
            turn=2,
            boundary_id="SHARED_STATE",
            actor="inventory",
            action_type="write",
            realization_status="REALIZED",
            state_before_hash="before",
            state_after_hash="after",
            target_ref="shared:key",
            source_refs=["msg-1"],
            parent_event_refs=["bev-0"],
        )
        validate_behavior_event(event, boundary_registry=bundle.boundaries)
        self.assertEqual(event["semantic_status"], "NOT_ADJUDICATED")
        self.assertNotEqual(event["state_before_hash"], event["state_after_hash"])
        self.assertTrue(event["behavior_event_hash"])

    def test_unknown_boundary_fails_closed(self):
        bundle = RegistryBundle.load()
        event = make_behavior_event(
            behavior_event_id="bev-2",
            trajectory_id="traj-1",
            event_index=4,
            turn=2,
            boundary_id="SHARED_STATE",
            actor="inventory",
            action_type="write",
            realization_status="REALIZED",
            state_before_hash="before",
            state_after_hash="after",
        )
        event["boundary_id"] = "UNKNOWN_BOUNDARY"
        with self.assertRaises(SystemBehaviorValidationError):
            validate_behavior_event(event, boundary_registry=bundle.boundaries)

    def test_system_measurement_holds_r2_r3_r4_together(self):
        event = make_behavior_event(
            behavior_event_id="bev-3",
            trajectory_id="traj-2",
            event_index=1,
            turn=1,
            boundary_id="INVOCATION",
            actor="ops_lead",
            action_type="invoke",
            realization_status="PROPOSAL",
            state_before_hash="s0",
            state_after_hash="s0",
        )
        measurement = build_system_trajectory_measurement(
            measurement_id="m-1",
            trajectory_id="traj-2",
            source_trace_hash="tracehash",
            source_version="fixture-v1",
            termination_status="RUN_COMPLETE",
            behavior_events=[event],
            jump_candidate_refs=["jump-1"],
            first_jump_candidate_ref="jump-1",
            first_jump_turn=1,
            descendant_event_count=2,
            affected_agent_count=1,
            operational_boundary_crossing_count=0,
            retrospective_window_refs=["rw-1"],
            experimental_variables=[
                {
                    "variable_id": "ORCHESTRATION_STRUCTURE",
                    "stage": "STRUCTURE",
                    "registry_version": "0.1",
                    "condition": "EMERGENT_FREE_ROUTING",
                    "intervention_hash": None,
                }
            ],
        )
        self.assertEqual(measurement["r2"]["jump_candidate_count"], 1)
        self.assertEqual(measurement["r3"]["descendant_event_count"], 2)
        self.assertEqual(measurement["r4"]["retrospective_window_count"], 1)
        self.assertEqual(measurement["semantic_status"], "NOT_ADJUDICATED")
        self.assertTrue(measurement["measurement_hash"])

    def test_crossref_validation_rejects_unknown_boundary(self):
        bundle = RegistryBundle.load()
        bad_variables = dict(bundle.variables)
        bad_variables["variables"] = [dict(row) for row in bundle.variables["variables"]]
        bad_variables["variables"][0] = dict(bad_variables["variables"][0])
        bad_variables["variables"][0]["target_boundary_family"] = ["DOES_NOT_EXIST"]
        with self.assertRaises(SystemBehaviorValidationError):
            validate_registry_crossrefs(bad_variables, bundle.boundaries)


if __name__ == "__main__":
    unittest.main()
