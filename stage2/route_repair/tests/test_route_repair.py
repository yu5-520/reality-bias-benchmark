import unittest

from stage2.monitor_enhancement.evidence_graph import EvidenceGraph
from stage2.monitor_enhancement.observation_adapter import adapt_structural_event
from stage2.monitor_enhancement.route_export import export_route_map
from stage2.route_repair.plan import (
    build_boundary_package,
    build_route_repair_plan,
    validate_agent_route_choice,
)
from stage2.route_repair.runner import RouteRepairSession
from stage2.r7_prospective_v1.repair_boundary_watcher import verify_package_hash


class RouteRepairTest(unittest.TestCase):
    def route(self):
        graph = EvidenceGraph()
        event = {
            "sequence": 1,
            "event_ref": "cell:struct:1",
            "actor": "coder",
            "kind": "ACTION_WRITE_FILE",
            "object_refs": ["file:a.py", "file:b.py", "file:c.py"],
            "written_refs": ["file:b.py"],
            "downstream_legal_refs": [],
            "preserve_refs": ["file:c.py"],
        }
        graph.add_observation(
            adapt_structural_event(
                event, trajectory_id="cell", evidence_ref="raw:1"
            )
        )
        graph.add_edge({
            "source_ref": "file:a.py",
            "destination_ref": "file:b.py",
            "relation_type": "PROPAGATED_TO_DESCENDANT",
            "status": "SUPPORTED",
            "basis": "SEMANTIC_REVIEW",
            "evidence_refs": ["audit:1"],
        })
        return export_route_map(
            graph.snapshot(),
            ["file:a.py"],
            authorized_write_refs=["file:b.py"],
            preserve_refs=["file:c.py"],
        )

    def plan(self):
        return build_route_repair_plan(
            self.route(),
            diagnosed_refs=["file:a.py", "file:b.py"],
            task_authorized_write_refs=["file:b.py"],
            checkpoint_manifest={
                "checkpoint_id": "cp:1",
                "checkpoint_hash": "hash:1",
                "event_ref": "cell:struct:1",
                "restore_capability": "FULL_NATIVE",
            },
        )

    def test_repairable_route_is_diagnosis_intersect_authority(self):
        plan = self.plan()
        self.assertEqual(plan["repairable_refs"], ["file:b.py"])
        self.assertEqual(plan["pending_verification_refs"], ["file:a.py"])
        self.assertEqual(plan["repair_gate_status"], "COMPLETE_FOR_ROUTE_REPAIR")
        package = build_boundary_package(plan)
        self.assertTrue(verify_package_hash(package))

    def test_agent_cannot_modify_visible_but_unauthorized_node(self):
        plan = self.plan()
        with self.assertRaisesRegex(ValueError, "outside repairable route"):
            validate_agent_route_choice({
                "modify_refs": ["file:a.py"],
                "preserve_refs": plan["preserve_refs"],
                "verify_refs": [],
            }, plan)

    def test_session_uses_native_executor_then_exits(self):
        plan = self.plan()
        preserve = {"file:c.py": "frozen-c"}

        def executor(request):
            self.assertEqual(request["target_ref"], "file:b.py")
            return {
                "native_interface": "workspace.write_file",
                "mutation_class": "APPLICATION_WRITE",
                "before_hash": "before",
                "after_hash": "after",
            }

        session = RouteRepairSession(
            plan=plan,
            preserve_hashes=preserve,
            native_executor=executor,
            preserve_hash_provider=lambda: preserve,
        )
        result = session.execute({
            "modify_refs": ["file:b.py"],
            "preserve_refs": plan["preserve_refs"],
            "verify_refs": ["file:a.py"],
            "reason_by_ref": {"file:b.py": "repair descendant"},
        })
        self.assertTrue(result["repair_executor_exited"])
        self.assertEqual(len(result["native_action_receipts"]), 1)

    def test_candidate_only_path_requires_verification_before_write(self):
        graph = EvidenceGraph()
        event = {
            "sequence": 1,
            "event_ref": "candidate:struct:1",
            "actor": "coder",
            "kind": "ACTION_READ_FILE",
            "object_refs": ["file:a.py"],
            "written_refs": [],
            "downstream_legal_refs": [],
            "preserve_refs": [],
        }
        graph.add_observation(
            adapt_structural_event(
                event, trajectory_id="candidate", evidence_ref="raw:candidate"
            )
        )
        graph.add_edge({
            "source_ref": "file:a.py",
            "destination_ref": "file:b.py",
            "relation_type": "PROPAGATED_TO_DESCENDANT",
            "status": "CANDIDATE",
            "basis": "SEMANTIC_CANDIDATE",
            "evidence_refs": ["candidate:edge"],
        })
        route = export_route_map(
            graph.snapshot(),
            ["file:a.py"],
            authorized_write_refs=["file:b.py"],
        )
        plan = build_route_repair_plan(
            route,
            diagnosed_refs=["file:b.py"],
            task_authorized_write_refs=["file:b.py"],
            checkpoint_manifest={
                "checkpoint_id": "cp:candidate",
                "checkpoint_hash": "hash:candidate",
                "event_ref": "candidate:struct:1",
                "restore_capability": "FULL_NATIVE",
            },
        )
        self.assertEqual(plan["repairable_refs"], [])
        self.assertEqual(plan["pending_verification_refs"], ["file:b.py"])
        self.assertEqual(plan["repair_gate_status"], "NO_AUTHORIZED_REPAIR_ROUTE")

    def test_no_repair_never_invokes_native_executor(self):
        def forbidden_executor(request):
            self.fail("no-action decision invoked executor")
        session = RouteRepairSession(plan=self.plan(), preserve_hashes={"file:c.py":"same"},
            native_executor=forbidden_executor, preserve_hash_provider=lambda:{"file:c.py":"same"})
        result=session.execute({"decision":"NO_REPAIR_NEEDED","reason":"Inspected route is healthy",
            "modify_refs":[],"preserve_refs":["file:c.py"],"verify_refs":["file:a.py"],"reason_by_ref":{}})
        self.assertEqual(result["native_action_receipts"],[])
        self.assertTrue(result["repair_executor_exited"])


if __name__ == "__main__":
    unittest.main()
