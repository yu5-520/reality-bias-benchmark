import unittest
from arena.r7_lineage_monitoring import build_semantic_lineage_package, build_post_repair_watch_contract, build_full_lineage_observation, evaluate_post_repair_watch

class TestR7LineageMonitoring(unittest.TestCase):
    def test_package_and_watch_do_not_adjudicate_cpr(self):
        packet={"packet_id":"P","repair_anchor_ref":"arena_event:32:state:x","target_semantic_id":"x::v","content_address":"rbca:x","raw_evidence_refs":["raw"],"evidence_supported_affected_closure_refs":["pool:x","desc:x"],"repair_closure_refs":["x:status"]}
        plan={"packet_id":"P","repair_anchor_ref":packet["repair_anchor_ref"],"target_semantic_id":"x::v","target_state_key":"x","authority_from_status":"fact","authority_to_status":"unconfirmed","invalidated_post_anchor_event_refs":["arena_event:33"]}
        app={"repaired_branch_start_event_count":33}
        pkg=build_semantic_lineage_package(packet=packet,runtime_plan=plan)
        watch=build_post_repair_watch_contract(runtime_plan=plan,repair_application=app)
        self.assertEqual("DEFERRED_NOT_ADJUDICATED",pkg["semantic_disposition_status"])
        self.assertEqual("NOT_ADJUDICATED",watch["semantic_cpr_status"])

    def test_full_observation_and_watch_follow_descendants(self):
        trace={"events":[
            {"event_index":32,"action_type":"write_state","action":{"key":"x","status":"fact"},"actor":"a"},
            {"event_index":33,"action_type":"write_state","action":{"key":"y","status":"fact"},"actor":"b","realized_in_baseline":True},
            {"event_index":34,"action_type":"write_state","action":{"key":"x","status":"recommendation"},"actor":"c","realized_in_baseline":True},
        ],"model_calls":[{"turn":9,"agent_id":"b"}],"runtime_transform_records":[]}
        obs=build_full_lineage_observation(trace=trace,arm_id="C3_ALR",anchor_event_index=32,branch_start_event_count=33,target_state_key="x")
        self.assertEqual(["arena_event:33","arena_event:34"],obs["prospective_event_refs"])
        contract={"watch_hash":"W","repair_branch_start_event_count":33,"target_state_key":"x","old_authority_status":"fact"}
        result=evaluate_post_repair_watch(trace=trace,contract=contract)
        self.assertEqual([],result["exact_old_authority_reentry_refs"])
        self.assertEqual(["arena_event:33"],result["closure_expansion_candidate_refs"])

if __name__=="__main__": unittest.main()
