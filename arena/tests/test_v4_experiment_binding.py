import copy
import json
import tempfile
import unittest
from pathlib import Path

from arena.anchor_selection import select_anchor
from arena.branch_plan import build_branch_plan
from arena.engine import run_arena_once
from arena.io_utils import load_json, sha256_file, write_jsonl
from arena.providers import ScriptedProvider
from arena.v4_experiment_binding import (
    BINDING_SCHEMA,
    build_v4_research_binding,
    load_and_verify_v4_binding,
    prepare_v4_binding,
    verify_v4_research_binding,
)


ROOT = Path(__file__).resolve().parents[2]


class V4ExperimentBindingTests(unittest.TestCase):
    def setUp(self):
        self.domain_path = ROOT / "arena/domains/ecommerce.json"
        self.arena_path = ROOT / "arena/config/arena_v0.3.json"
        self.model_path = ROOT / "arena/config/model_deepseek_v0.2.json"
        self.rule_path = ROOT / "arena/config/r5r6_anchor_rule_v0.2.json"
        self.domain = load_json(self.domain_path)
        self.config = load_json(self.arena_path)
        self.rule = load_json(self.rule_path)

    def _bundle(self):
        anchors = []
        trace = run_arena_once(
            self.domain,
            self.config,
            ScriptedProvider([
                {
                    "decision_summary": "ask inventory",
                    "actions": [
                        {
                            "type": "invoke_agent",
                            "agent_id": "inventory",
                            "request": "Check stock.",
                        }
                    ],
                },
                {
                    "decision_summary": "write branchable candidate",
                    "actions": [
                        {
                            "type": "write_state",
                            "key": "inventory_view",
                            "value": "Stockout certain",
                            "status": "fact",
                            "basis": "binding fixture",
                        },
                        {
                            "type": "message",
                            "to": "ops_lead",
                            "content": "Continue planning from this state.",
                        },
                    ],
                },
                {
                    "decision_summary": "finish",
                    "actions": [{"type": "finalize", "answer": "Plan."}],
                },
                {
                    "decision_summary": "finish late",
                    "actions": [{"type": "finalize", "answer": "Plan late."}],
                },
            ]),
            "v4-binding-fixture",
            logical_seed=1,
            state_snapshot_callback=anchors.append,
        )
        trace.update({
            "provider": "deepseek",
            "domain_hash": sha256_file(self.domain_path),
            "arena_config_path": "arena/config/arena_v0.3.json",
            "arena_config_version": self.config["version"],
            "arena_config_hash": sha256_file(self.arena_path),
            "model_config_path": "arena/config/model_deepseek_v0.2.json",
            "model_config_version": load_json(self.model_path).get("config_version"),
            "model_config_hash": sha256_file(self.model_path),
            "anchor_rule_path": "arena/config/r5r6_anchor_rule_v0.2.json",
            "anchor_rule_hash": sha256_file(self.rule_path),
            "code_commit_sha": "BASELINE_BINDING_TEST_SHA",
        })
        selection = select_anchor(
            trace,
            anchors,
            self.rule,
            evidence_hash="binding-fixture-evidence",
            selection_id="BINDING-FIXTURE-SEL",
        )
        self.assertEqual("ANCHOR_SELECTED", selection["selection_status"])
        return build_branch_plan(
            selection,
            trace,
            replicates=2,
            branch_code_sha="V4_BINDING_TEST_SHA",
        )

    def _write_plan_dir(self, path: Path, bundle):
        path.mkdir(parents=True, exist_ok=False)
        (path / "branch_plan.json").write_text(
            json.dumps(bundle["plan"], ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (path / "parent_snapshot.json").write_text(
            json.dumps(bundle["parent_snapshot"], ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (path / "intervention_start_snapshot.json").write_text(
            json.dumps(bundle["intervention_start_snapshot"], ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        write_jsonl(path / "branch_execution_manifest.jsonl", bundle["branch_rows"])
        write_jsonl(path / "branch_manifests.jsonl", bundle["branch_manifests"])

    def test_binding_freezes_plan_variable_and_all_v4_interfaces(self):
        bundle = self._bundle()
        binding = build_v4_research_binding(
            bundle,
            code_sha="V4_BINDING_TEST_SHA",
            branch_plan_file_sha256="a" * 64,
        )
        self.assertEqual(BINDING_SCHEMA, binding["schema"])
        self.assertEqual("EPISTEMIC_STATUS_DOWNGRADE", binding["experimental_variable_id"])
        self.assertEqual("MID", binding["experimental_variable_stage"])
        required_interfaces = {
            "source_lineage_rules",
            "measurement_contract",
            "branch_start_state_anchor_schema",
            "branch_trajectory_comparison_schema",
            "v4_review_contract",
            "v4_review_packet_policy",
            "v4_bounded_review_packet_schema",
            "v4_semantic_authority_review_schema",
            "v4_review_packet_generator",
            "v4_branch_anchor_review_packet_generator",
            "first_paper_analysis_contract",
            "first_paper_analysis_contract_schema",
            "first_paper_structural_analysis_schema",
            "first_paper_semantic_analysis_schema",
        }
        self.assertTrue(required_interfaces.issubset(binding["interface_bindings"]))
        self.assertTrue(binding["first_paper_analysis_contract_hash"])
        self.assertFalse(binding["paid_api_authorized"])
        self.assertEqual("NOT_ADJUDICATED", binding["semantic_status"])
        self.assertTrue(
            verify_v4_research_binding(
                binding,
                bundle,
                code_sha="V4_BINDING_TEST_SHA",
                branch_plan_file_sha256="a" * 64,
            )
        )

    def test_binding_rejects_interface_or_code_drift(self):
        bundle = self._bundle()
        binding = build_v4_research_binding(
            bundle,
            code_sha="V4_BINDING_TEST_SHA",
            branch_plan_file_sha256="b" * 64,
        )
        tampered = copy.deepcopy(binding)
        tampered["interface_bindings"]["v4_review_contract"]["sha256"] = "0" * 64
        tampered["binding_hash"] = stable = __import__("arena.core", fromlist=["stable_hash"]).stable_hash(
            {k: v for k, v in tampered.items() if k != "binding_hash"}
        )
        self.assertTrue(stable)
        with self.assertRaises(ValueError):
            verify_v4_research_binding(
                tampered,
                bundle,
                code_sha="V4_BINDING_TEST_SHA",
                branch_plan_file_sha256="b" * 64,
            )
        with self.assertRaises(ValueError):
            verify_v4_research_binding(
                binding,
                bundle,
                code_sha="DIFFERENT_CODE_SHA",
                branch_plan_file_sha256="b" * 64,
            )

    def test_prepared_binding_is_required_and_reloads_exactly(self):
        bundle = self._bundle()
        with tempfile.TemporaryDirectory() as tmp:
            plan_dir = Path(tmp) / "plan"
            self._write_plan_dir(plan_dir, bundle)
            with self.assertRaises(ValueError):
                load_and_verify_v4_binding(
                    plan_dir,
                    bundle,
                    code_sha="V4_BINDING_TEST_SHA",
                )
            binding = prepare_v4_binding(
                plan_dir=plan_dir,
                code_sha="V4_BINDING_TEST_SHA",
            )
            loaded = load_and_verify_v4_binding(
                plan_dir,
                bundle,
                code_sha="V4_BINDING_TEST_SHA",
            )
            self.assertEqual(binding["binding_hash"], loaded["binding_hash"])
            self.assertEqual(
                binding["branch_plan_file_sha256"],
                sha256_file(plan_dir / "branch_plan.json"),
            )

    def test_binding_cannot_replace_paid_authorization(self):
        bundle = self._bundle()
        binding = build_v4_research_binding(
            bundle,
            code_sha="V4_BINDING_TEST_SHA",
            branch_plan_file_sha256="c" * 64,
        )
        self.assertEqual("NOT_AUTHORIZED", binding["authorization_status"])
        self.assertFalse(binding["paid_api_authorized"])
        self.assertFalse(binding["automatic_paid_evaluator"])


if __name__ == "__main__":
    unittest.main()
