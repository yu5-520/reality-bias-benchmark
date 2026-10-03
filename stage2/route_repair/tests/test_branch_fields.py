import copy
import io
import json
import tarfile
import tempfile
import unittest
from pathlib import Path

from stage2.r7_checkpoint_v1.common import digest
from stage2.monitor_enhancement.evidence_graph import EvidenceGraph
from stage2.monitor_enhancement.snapshot_append import AppendOnlyEvidenceGraph
from stage2.route_repair.route_context import CompleteRouteContext
from stage2.route_repair.branch_fields import (
    BranchConstraintError, NativeFieldBranchExecutor, build_branch_policy,
    compile_branch_plan, seal, transform,
)


class FieldBranchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.files = {"source.json": '{"status":"fact","other":17}\n',
                      "plan.json": '{"gate":"required","other":"keep"}\n', "untouched.py": "x=1\n"}
        graph = EvidenceGraph()
        for n, path in enumerate(self.files):
            graph.add_observation({"schema": "RB-STAGE2-ENHANCED-OBSERVATION-v1",
                "observation_id": "obs:"+str(n), "event_ref": "old:"+str(n),
                "evidence_ref": "raw:"+str(n), "object_refs": ["file:"+path], "native_sequence": n})
        self.graph = graph.snapshot()
        raw = {"checkpoint_ledger.json": json.dumps({"checkpoints": [{"boundary":"TERMINAL", "checkpoint_hash":"cp", "event_ref":"end", "model_decision_sequence":3}]}).encode(),
               "checkpoints/cp/manifest.json": json.dumps({"checkpoint_hash":"cp","event_ref":"end", "application_file_hashes": {p:digest(t.encode()) for p,t in self.files.items()}}).encode()}
        raw.update({"checkpoints/cp/application/"+p:t.encode() for p,t in self.files.items()})
        self.archive = self.root / "archive.tar.gz"
        with tarfile.open(self.archive,"w:gz") as tf:
            for name,data in raw.items():
                info=tarfile.TarInfo(name);info.size=len(data);tf.addfile(info,io.BytesIO(data))
        case={"full_id":"fixture", "graph_hash":self.graph["graph_hash"], "archive_sha256":digest(self.archive.read_bytes()), "terminal_checkpoint_hash":"cp"}
        self.ctx=CompleteRouteContext(self.graph,self.archive,case)
        self.policy=build_branch_policy(self.ctx, original_task={"user_request":"broad original task"},
            branch_id="fixture-branch", semantic_id="fixture-only-not-natural-finding",
            route_refs=["file:source.json","file:plan.json"], grants=[
                {"target_ref":"file:source.json","kind":"JSON_LEAF_REPLACE","pointer":"/status"},
                {"target_ref":"file:plan.json","kind":"JSON_LEAF_REPLACE","pointer":"/gate"}],
            evidence=[self.ctx.locator("checkpoints/cp/application/source.json")])
        self.actions=[{"action_id":"a1","target_ref":"file:source.json","kind":"JSON_LEAF_REPLACE","pointer":"/status", "before_value_hash":digest("fact"),"value":"unconfirmed","reason":"offline fixture source operation","depends_on":[]},
                      {"action_id":"a2","target_ref":"file:plan.json","kind":"JSON_LEAF_REPLACE","pointer":"/gate", "before_value_hash":digest("required"),"value":"pending","reason":"offline fixture ordered operation","depends_on":["a1"]}]

    def tearDown(self):
        self.ctx.close();self.temp.cleanup()

    def plan(self, actions=None):
        return compile_branch_plan(self.ctx,self.policy,actions or self.actions,preserve_refs=["file:untouched.py"])

    def executor(self, plan=None):
        return NativeFieldBranchExecutor(self.ctx,plan or self.plan(),self.root/"branch",trusted_policy=self.policy)

    def test_two_native_actions_preserve_other_fields_and_complete_history(self):
        executor=self.executor();result=executor.execute()
        self.assertEqual(result["status"],"PASS_OFFLINE_NATIVE_EXECUTION")
        self.assertEqual(result["applied_action_ids"],["a1","a2"])
        self.assertEqual(json.loads((executor.root/"source.json").read_text()),{"status":"unconfirmed","other":17})
        self.assertEqual(json.loads((executor.root/"plan.json").read_text()),{"gate":"pending","other":"keep"})
        self.assertTrue(result["unrelated_application_preserved"])
        self.assertTrue(result["historical_archive_preserved"])
        after=json.loads((executor.out/"full_graph_after.json").read_text())
        self.assertTrue({n["ref"] for n in self.graph["nodes"]} <= {n["ref"] for n in after["nodes"]})
        self.assertEqual(result["semantic_repair_effect"],"NOT_EVALUATED")
        self.assertEqual(result["live_provider_calls"],0)

    def test_outside_field_rejected_before_branch_creation(self):
        actions=copy.deepcopy(self.actions);actions[0]["pointer"]="/other"
        with self.assertRaisesRegex(BranchConstraintError,"FIELD_OUTSIDE_BRANCH"):self.plan(actions)
        self.assertFalse((self.root/"branch").exists())

    def test_whole_object_write_is_rejected(self):
        actions=copy.deepcopy(self.actions);actions[0]["kind"]="REPLACE_FILE"
        with self.assertRaisesRegex(BranchConstraintError,"ACTION_KIND_DRIFT"):self.plan(actions)

    def test_field_type_and_container_changes_rejected(self):
        for value in [False,{},[]]:
            actions=copy.deepcopy(self.actions);actions[0]["value"]=value
            with self.assertRaises(BranchConstraintError):self.plan(actions)

    def test_agent_cannot_reseal_wider_policy(self):
        plan=self.plan();plan["policy"]["original_task"]={"user_request":"different"}
        plan["policy"]=seal({k:v for k,v in plan["policy"].items() if k!="policy_hash"},"policy_hash")
        plan=seal({k:v for k,v in plan.items() if k!="plan_hash"},"plan_hash")
        with self.assertRaisesRegex(BranchConstraintError,"TRUSTED_POLICY_MISMATCH"):self.executor(plan)

    def test_cyclic_or_forward_dependency_rejected(self):
        actions=copy.deepcopy(self.actions);actions[0]["depends_on"]=["a2"]
        with self.assertRaisesRegex(BranchConstraintError,"DEPENDENCY"):self.plan(actions)

    def test_stale_branch_blocks_before_any_write(self):
        executor=self.executor();(executor.root/"source.json").write_text("{}")
        result=executor.execute()
        self.assertEqual(result["native_write_attempts"],0)
        self.assertEqual(result["status"],"BLOCKED_WITH_PARTIAL_EVIDENCE")

    def test_midplan_preserve_drift_stops_and_retains_first_action(self):
        executor=self.executor()
        def inject(action,root):
            if action["action_id"]=="a2":(root/"untouched.py").write_text("changed\n")
        result=executor.execute(before_action=inject)
        self.assertEqual(result["applied_action_ids"],["a1"])
        self.assertFalse(result["unrelated_application_preserved"])
        self.assertEqual(json.loads((executor.root/"plan.json").read_text())["gate"],"required")
        self.assertTrue((executor.out/"native_action_receipts.json").exists())
        self.assertEqual(result["status"],"BLOCKED_WITH_PARTIAL_EVIDENCE")

    def test_ambiguous_duplicate_json_is_rejected(self):
        with self.assertRaisesRegex(BranchConstraintError,"AMBIGUOUS_JSON_KEY"):
            transform('{"a":1,"a":2}',{"kind":"JSON_LEAF_REPLACE","pointer":"/a","before_value_hash":digest(2),"value":3},{"kind":"JSON_LEAF_REPLACE","pointer":"/a"})

    def test_exact_text_span_preserves_unicode_prefix_suffix(self):
        text="前缀 old 后缀";start=text.index("old");end=start+3
        grant={"kind":"TEXT_SPAN_REPLACE","start":start,"end":end,"span_hash":digest(b"old")}
        action={"kind":"TEXT_SPAN_REPLACE","start":start,"end":end,"before_value_hash":digest(b"old"),"value":"new"}
        output,_=transform(text,action,grant)
        self.assertEqual(output,"前缀 new 后缀")
        action["end"]+=1
        with self.assertRaisesRegex(BranchConstraintError,"SPAN_OUTSIDE_BRANCH"):transform(text,action,grant)

    def test_live_mode_is_blocked(self):
        with self.assertRaisesRegex(BranchConstraintError,"LIVE_BRANCH_REPAIR_NOT_READY"):
            build_branch_policy(self.ctx,original_task="task",branch_id="b",route_refs=[],grants=[],evidence=[],semantic_id="s",mode="LIVE")

    def test_unknown_relation_cannot_authorize_a_write(self):
        with self.assertRaisesRegex(BranchConstraintError,"UNVERIFIED_MUTATION"):
            compile_branch_plan(self.ctx,self.policy,self.actions,verify_refs=["file:source.json"])

    def test_source_witness_hash_drift_is_rejected(self):
        with self.assertRaisesRegex(BranchConstraintError,"SOURCE_WITNESS_DRIFT"):
            build_branch_policy(self.ctx,original_task="task",branch_id="b",semantic_id="s",
                route_refs=["file:source.json"],grants=self.policy["field_grants"][:1],
                evidence=[{"member":"checkpoints/cp/application/source.json","member_sha256":"bad"}])

    def test_repeated_execution_is_rejected(self):
        executor=self.executor();executor.execute()
        with self.assertRaisesRegex(BranchConstraintError,"ALREADY_EXECUTED"):executor.execute()

    def test_unknown_or_private_native_state_has_no_fallback(self):
        with self.assertRaisesRegex(BranchConstraintError,"UNSUPPORTED_NATIVE_SURFACE"):
            build_branch_policy(self.ctx,original_task="task",branch_id="b",semantic_id="s",
                route_refs=["file:source.json"],grants=[{"target_ref":"state:private-memory","kind":"JSON_LEAF_REPLACE","pointer":"/status"}],
                evidence=[self.ctx.locator("checkpoints/cp/application/source.json")])

    def test_plan_action_id_cannot_escape_receipt_directory(self):
        actions=copy.deepcopy(self.actions);actions[0]["action_id"]="../escape"
        with self.assertRaisesRegex(BranchConstraintError,"NONEXACT_ACTION_ID"):self.plan(actions)

    def test_two_fields_in_one_object_require_order_and_preserve_other_object(self):
        grants=[{"target_ref":"file:source.json","kind":"JSON_LEAF_REPLACE","pointer":"/status"},
                {"target_ref":"file:source.json","kind":"JSON_LEAF_REPLACE","pointer":"/other"}]
        policy=build_branch_policy(self.ctx,original_task="original task",branch_id="two-fields",semantic_id="fixture",
            route_refs=["file:source.json"],grants=grants,evidence=[self.ctx.locator("checkpoints/cp/application/source.json")])
        actions=[copy.deepcopy(self.actions[0]),{"action_id":"a2","target_ref":"file:source.json","kind":"JSON_LEAF_REPLACE",
            "pointer":"/other","before_value_hash":digest(17),"value":18,"reason":"second field fixture","depends_on":["a1"]}]
        plan=compile_branch_plan(self.ctx,policy,actions)
        result=NativeFieldBranchExecutor(self.ctx,plan,self.root/"branch",trusted_policy=policy).execute()
        self.assertEqual(result["applied_action_ids"],["a1","a2"])
        self.assertTrue(result["unrelated_application_preserved"])
        self.assertEqual(json.loads((self.root/"branch/application/source.json").read_text()),{"status":"unconfirmed","other":18})
        actions[1]["depends_on"]=[]
        with self.assertRaisesRegex(BranchConstraintError,"SAME_OBJECT_ORDER_REQUIRED"):compile_branch_plan(self.ctx,policy,actions)

    def test_native_wrong_output_is_retained_and_stops_next_action(self):
        executor=self.executor();native_write=executor.checkout.write_file
        def faulty(path,content):return native_write(path,content+" ")
        executor.checkout.write_file=faulty
        result=executor.execute()
        self.assertEqual(result["native_write_attempts"],1)
        self.assertEqual(result["applied_action_ids"],[])
        self.assertIn("POSTCONDITION",result["error"]["message"])
        receipts=json.loads((executor.out/"native_action_receipts.json").read_text())
        self.assertNotEqual(receipts[0]["after_hash"],receipts[0]["expected_output_hash"])

    def test_preserve_ref_cannot_be_a_write_ref(self):
        with self.assertRaisesRegex(BranchConstraintError,"PRESERVE_WRITE_CONFLICT"):
            compile_branch_plan(self.ctx,self.policy,self.actions,preserve_refs=["file:source.json"])


class SnapshotAppendTests(unittest.TestCase):
    def test_roundtrip_and_snapshot_corruption(self):
        graph=EvidenceGraph();snapshot=graph.snapshot()
        self.assertEqual(AppendOnlyEvidenceGraph.from_snapshot(snapshot).snapshot(),snapshot)
        snapshot["laws"]["temporal_proximity_is_not_dependency"]=False
        with self.assertRaises(ValueError):AppendOnlyEvidenceGraph.from_snapshot(snapshot)


if __name__ == "__main__":
    unittest.main()
