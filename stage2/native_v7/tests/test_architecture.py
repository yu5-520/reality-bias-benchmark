import json
import tempfile
import unittest
from pathlib import Path

from stage2.native_v7.collect import validate_request
from stage2.native_v7.freeze import artifact
from stage2.native_v7.observer import PassiveEventObserver, verify_observer
from stage2.native_v7.policy import load_registry, validate_registry


ROOT = Path(__file__).resolve().parents[3]


class NativeV7Architecture(unittest.TestCase):
    def test_registry_is_heterogeneous_and_external(self):
        registry = load_registry()
        self.assertEqual(registry["schema"], "stage2-native-execution-registry-v2")
        self.assertEqual(set(registry["probes"]), {f"X{i}" for i in range(1, 8)})
        self.assertEqual(
            len({spec["environment_id"] for spec in registry["probes"].values()}), 7
        )
        for spec in registry["probes"].values():
            self.assertEqual(spec["runtime_scope"], "independent")
            self.assertEqual(spec["observer"]["mode"], "external")
            self.assertFalse(spec["observer"]["may_mutate_execution"])
            self.assertTrue(spec["integration_kind"])

    def test_background_host_is_frozen_only_for_capability_layers(self):
        registry = load_registry()
        host = registry["background_substrates"]["software_engineering_host_v1"]
        self.assertEqual(set(host["applies_to"]), {"X4", "X5", "X6", "X7"})
        self.assertEqual(host["status"], "FROZEN_DEINSTRUMENTED_HOST")
        self.assertEqual(
            host["verification"]["state"],
            "NON_STUDY_DEINSTRUMENTED_HOST_EQUIVALENCE_PASS",
        )
        self.assertTrue(host["verification"]["historical_prompt_contains_audit_ids"])
        self.assertFalse(host["verification"]["deinstrumented_prompt_contains_audit_ids"])
        for probe in ("X1", "X2", "X3"):
            self.assertIsNone(registry["probes"][probe]["background_substrate_id"])
        for probe in ("X4", "X5", "X6", "X7"):
            self.assertEqual(
                registry["probes"][probe]["background_substrate_id"],
                "software_engineering_host_v1",
            )

    def test_deinstrumented_host_source_contains_no_monitor_runtime(self):
        raw = (ROOT / "stage2/native_v7/software_host_v1.py").read_text()
        for marker in (
            "NativeCapture",
            "stage2.evidence",
            "PassiveEventObserver",
            "ExternalObserver",
            "event_id",
            "native_locator",
            "hook_id",
        ):
            with self.subTest(marker=marker):
                self.assertNotIn(marker, raw)

    def test_x1_runner_and_subject_receipt_are_verified(self):
        registry = load_registry()
        x1 = registry["probes"]["X1"]
        self.assertEqual(x1["collection_state"], "SUBJECT_READY")
        self.assertEqual(x1["launch"]["state"], "VERIFIED_NATIVE_ENTRYPOINT")
        self.assertTrue(x1["launch"]["argv_template"])
        self.assertEqual(x1["verification"]["state"], "NON_STUDY_NATIVE_SMOKE_PASS")
        self.assertFalse(x1["verification"]["subject_ready"])
        self.assertEqual(validate_request("X1", "T1")[1]["environment_id"], x1["environment_id"])

    def test_x2_runner_and_subject_receipt_are_verified(self):
        registry = load_registry()
        x2 = registry["probes"]["X2"]
        self.assertEqual(x2["collection_state"], "SUBJECT_READY")
        self.assertEqual(x2["launch"]["state"], "VERIFIED_NATIVE_ENTRYPOINT")
        self.assertIsNone(x2["background_substrate_id"])
        self.assertEqual(x2["source_commit"], "11cdf466d042aece04fc6cfd13b28e1a70341b1f")
        self.assertEqual(x2["package_version"], "1.0.0")
        self.assertEqual(x2["verification"]["state"], "NON_STUDY_NATIVE_SMOKE_PASS")
        self.assertEqual(x2["verification"]["turns"], 7)
        self.assertEqual(x2["verification"]["metagpt_rounds"], 7)
        self.assertEqual(x2["verification"]["environment_messages"], 6)
        self.assertFalse(x2["verification"]["subject_ready"])
        self.assertEqual(validate_request("X2", "T1")[1]["environment_id"], x2["environment_id"])

    def test_x3_runner_and_subject_receipt_are_verified(self):
        registry = load_registry()
        x3 = registry["probes"]["X3"]
        self.assertEqual(x3["collection_state"], "SUBJECT_READY")
        self.assertEqual(x3["launch"]["state"], "VERIFIED_NATIVE_ENTRYPOINT")
        self.assertIsNone(x3["background_substrate_id"])
        self.assertEqual(x3["protocol_version"], "1.0.0")
        self.assertEqual(x3["verification"]["state"], "NON_STUDY_NATIVE_SMOKE_PASS")
        self.assertEqual(x3["verification"]["service_count"], 9)
        self.assertEqual(x3["verification"]["a2a_calls"], 3)
        self.assertFalse(x3["verification"]["subject_ready"])
        self.assertEqual(validate_request("X3", "T1")[1]["environment_id"], x3["environment_id"])

    def test_x4_runner_and_subject_receipt_are_verified(self):
        registry = load_registry()
        x4 = registry["probes"]["X4"]
        self.assertEqual(x4["collection_state"], "SUBJECT_READY")
        self.assertEqual(x4["launch"]["state"], "VERIFIED_NATIVE_ENTRYPOINT")
        self.assertEqual(x4["background_substrate_id"], "software_engineering_host_v1")
        self.assertEqual(x4["verification"]["state"], "NON_STUDY_NATIVE_SMOKE_PASS")
        self.assertEqual(x4["verification"]["mcp_calls"], 4)
        self.assertFalse(x4["verification"]["subject_ready"])
        self.assertEqual(validate_request("X4", "T1")[1]["environment_id"], x4["environment_id"])

    def test_x5_runner_and_subject_receipt_are_verified(self):
        registry = load_registry()
        x5 = registry["probes"]["X5"]
        self.assertEqual(x5["collection_state"], "SUBJECT_READY")
        self.assertEqual(x5["launch"]["state"], "VERIFIED_NATIVE_ENTRYPOINT")
        self.assertEqual(x5["background_substrate_id"], "software_engineering_host_v1")
        self.assertEqual(x5["implementation_sha256"], "baf19cd7f7dde0a2f7ebfde254bffac6690e018b88d8d9ea4a811d37a53b12c4")
        self.assertEqual(x5["verification"]["state"], "NON_STUDY_NATIVE_SMOKE_PASS")
        self.assertEqual(x5["verification"]["retrieval_calls"], 1)
        self.assertFalse(x5["verification"]["subject_ready"])
        self.assertEqual(validate_request("X5", "T1")[1]["environment_id"], x5["environment_id"])

    def test_x6_runner_subject_receipt_and_real_study_embedding_are_verified(self):
        registry = load_registry()
        x6 = registry["probes"]["X6"]
        self.assertEqual(x6["collection_state"], "SUBJECT_READY")
        self.assertEqual(x6["launch"]["state"], "VERIFIED_NATIVE_ENTRYPOINT")
        self.assertEqual(x6["background_substrate_id"], "software_engineering_host_v1")
        self.assertEqual(x6["source_commit"], "cf61c4196e4cfdb0f2b7a0316249fa40312dc3a9")
        self.assertEqual(x6["verification"]["state"], "NON_STUDY_NATIVE_SMOKE_PASS")
        self.assertEqual(x6["verification"]["memorybank_writes"], 2)
        self.assertEqual(x6["verification"]["memorybank_retrieval_calls"], 1)
        self.assertEqual(x6["verification"]["reinforced_strength"], 2)
        self.assertTrue(x6["verification"]["subject_ready"])
        self.assertTrue(x6["verification"]["study_embedding_ready"])
        self.assertEqual(x6["study_embedding"]["state"], "FROZEN_MANIFEST_VERIFIED")
        self.assertEqual(
            x6["study_embedding"]["manifest_sha256"],
            "6f7540370b538036406bb621563e0ab98e8745122afe51369ab394c7f6f64f34",
        )
        self.assertEqual(validate_request("X6", "T1")[1]["environment_id"], x6["environment_id"])

    def test_x7_runner_subject_receipt_and_real_study_checkpoint_are_verified(self):
        registry = load_registry()
        x7 = registry["probes"]["X7"]
        self.assertEqual(x7["collection_state"], "SUBJECT_READY")
        self.assertEqual(x7["launch"]["state"], "VERIFIED_NATIVE_ENTRYPOINT")
        self.assertEqual(x7["background_substrate_id"], "software_engineering_host_v1")
        self.assertEqual(x7["source_commit"], "5a4c78ae18ab17a98cf997e8259354e546081d64")
        self.assertEqual(x7["verification"]["state"], "NON_STUDY_NATIVE_SMOKE_PASS")
        self.assertEqual(x7["verification"]["compression_calls"], 1)
        self.assertTrue(x7["verification"]["subject_ready"])
        self.assertTrue(x7["verification"]["study_checkpoint_ready"])
        self.assertEqual(x7["study_checkpoint"]["state"], "FROZEN_MANIFEST_VERIFIED")
        self.assertEqual(
            x7["study_checkpoint"]["manifest_sha256"],
            "bc5cd236ca84a2b213f3a618ef37f7ab10f6716e1b1b134242c2350bd4883e66",
        )
        self.assertEqual(validate_request("X7", "T1")[1]["environment_id"], x7["environment_id"])

    def test_subject_ready_is_per_probe_and_natural_count_remains_zero(self):
        matrix = artifact()
        self.assertEqual(len(matrix["cells"]), 21)
        self.assertEqual({row["subject_trajectory_count"] for row in matrix["cells"]}, {0})
        self.assertEqual(
            {row["probe"] for row in matrix["cells"]},
            {f"X{i}" for i in range(1, 8)},
        )
        self.assertEqual({row["status"] for row in matrix["cells"]}, {"SUBJECT_READY"})
        for probe in ("X6", "X7"):
            with self.subTest(probe=probe):
                self.assertEqual(validate_request(probe, "T1")[1]["collection_state"], "SUBJECT_READY")

    def test_x2_runner_uses_native_metagpt_environment_not_stage2_mailbox(self):
        raw = (ROOT / "stage2/native_v7/x2_metagpt/runner.py").read_text()
        self.assertIn("from metagpt.environment import Environment", raw)
        self.assertIn("class Stage2MetaRole(Role)", raw)
        self.assertIn("env.run(k=1)", raw)
        self.assertIn("env.publish_message(initial)", raw)
        for marker in (
            "stage2.metagpt_transport",
            "from stage2.coding_arena",
            "import stage2.coding_arena",
            "RoleMailboxTransport",
            "SoftwareEngineeringHost",
        ):
            self.assertNotIn(marker, raw)

    def test_x3_runner_uses_native_role_services_not_baseline_mailbox(self):
        runner = (ROOT / "stage2/native_v7/x3_a2a/runner.py").read_text()
        service = (ROOT / "stage2/native_v7/x3_a2a/service.py").read_text()
        proxy = (ROOT / "stage2/native_v7/x3_a2a/proxy.py").read_text()
        self.assertIn("create_client", runner)
        self.assertIn("create_client", service)
        self.assertIn("DefaultRequestHandler", service)
        self.assertIn("create_jsonrpc_routes", service)
        self.assertIn("SendMessageRequest", service)
        self.assertIn("Transparent HTTP-body relay", proxy)
        for marker in (
            "stage2.a2a_transport",
            "from stage2.coding_arena",
            "import stage2.coding_arena",
            "from stage2.transports",
            "import stage2.transports",
        ):
            self.assertNotIn(marker, runner + service)

    def test_x4_runner_uses_frozen_host_and_not_historical_mcp_adapter(self):
        raw = (ROOT / "stage2/native_v7/x4_mcp/runner.py").read_text()
        self.assertIn("SoftwareEngineeringHost", raw)
        self.assertIn("MCPCheckoutProxy", raw)
        for marker in ("stage2.mcp_workspace", "CodingArena", "RoleMailboxTransport"):
            self.assertNotIn(marker, raw)

    def test_x5_runner_attaches_only_at_retrieval_context_boundary(self):
        runner = (ROOT / "stage2/native_v7/x5_rag/runner.py").read_text()
        context = (ROOT / "stage2/native_v7/x5_rag/context.py").read_text()
        self.assertIn("SoftwareEngineeringHost", runner)
        self.assertIn("FrozenRAGContext", runner)
        self.assertIn("stage2.retrieval", context)
        for marker in ("stage2.rag_context", "CodingArena", "RoleMailboxTransport"):
            self.assertNotIn(marker, runner + context)

    def test_x6_runner_attaches_only_at_memory_boundary(self):
        runner = (ROOT / "stage2/native_v7/x6_memorybank/runner.py").read_text()
        context = (ROOT / "stage2/native_v7/x6_memorybank/context.py").read_text()
        self.assertIn("SoftwareEngineeringHost", runner)
        self.assertIn("LocalMemoryRetrieval", context)
        self.assertIn("search_memory", context)
        self.assertIn("init_memory_vector_store", context)
        for marker in ("stage2.memorybank_context", "CodingArena", "RoleMailboxTransport"):
            self.assertNotIn(marker, runner + context)

    def test_x7_runner_attaches_only_at_context_compression_boundary(self):
        runner = (ROOT / "stage2/native_v7/x7_longllmlingua/runner.py").read_text()
        context = (ROOT / "stage2/native_v7/x7_longllmlingua/context.py").read_text()
        self.assertIn("SoftwareEngineeringHost", runner)
        self.assertIn("PromptCompressor", context)
        self.assertIn('rank_method="longllmlingua"', context)
        for marker in ("stage2.longllmlingua_context", "CodingArena", "RoleMailboxTransport"):
            self.assertNotIn(marker, runner + context)

    def test_pending_runner_cannot_smuggle_launch_command(self):
        registry = load_registry()
        registry["probes"]["X2"]["collection_state"] = "PENDING_NATIVE_RUNNER"
        registry["probes"]["X2"]["launch"] = {
            "state": "PENDING_NATIVE_ENTRYPOINT",
            "argv_template": ["python", "anything.py"],
        }
        with self.assertRaisesRegex(ValueError, "pending runner"):
            validate_registry(registry)

    def test_capability_runner_cannot_verify_before_host_freeze(self):
        registry = load_registry()
        registry["background_substrates"]["software_engineering_host_v1"]["status"] = (
            "PENDING_DEINSTRUMENTED_HOST_FREEZE"
        )
        registry["probes"]["X4"]["collection_state"] = "NATIVE_RUNNER_VERIFIED_SUBJECT_PENDING"
        registry["probes"]["X4"]["launch"] = {
            "state": "VERIFIED_NATIVE_ENTRYPOINT",
            "argv_template": ["python", "x4.py"],
        }
        with self.assertRaisesRegex(ValueError, "background host is frozen"):
            validate_registry(registry)

    def test_x1_runner_source_does_not_import_v6_execution_scaffold(self):
        raw = (ROOT / "stage2/native_v7/x1_autogen/runner.py").read_text()
        for marker in ("stage2.coding_arena", "RoleMailboxTransport", "context_adapter"):
            self.assertNotIn(marker, raw)

    def test_passive_event_observer_returns_identical_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            observer = PassiveEventObserver(Path(directory) / "observer", probe="X1")
            raw = b'{"native":"event"}'
            returned = observer.observe(raw, surface="unit-test")
            self.assertIs(returned, raw)
            observer.seal()
            self.assertGreaterEqual(verify_observer(observer.root), 2)


if __name__ == "__main__":
    unittest.main()
