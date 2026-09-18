import json
import tempfile
import unittest
from pathlib import Path

from arena.build_v5_cross_domain_localized_semantic_audit import (
    _eligible_by_frozen_rule,
    materialize,
)


class LocalizedSemanticAuditTest(unittest.TestCase):
    def test_rule_requires_authority_fact_and_marker(self):
        base={
            "triage_roles":["AUTHORITY_REVIEW_ANCHOR"],
            "source":{"status":"fact"},
            "authority_review_markers":["provisional"],
        }
        self.assertTrue(_eligible_by_frozen_rule(base))
        self.assertFalse(_eligible_by_frozen_rule({**base,"source":{"status":"provisional"}}))
        self.assertFalse(_eligible_by_frozen_rule({**base,"authority_review_markers":[]}))

    def test_materialize_binds_exact_review_set(self):
        case={
            "case_hash":"a"*64,
            "triage_roles":["AUTHORITY_REVIEW_ANCHOR"],
            "source":{"status":"fact","state_key":"x","basis":"preliminary","value":{"x":1}},
            "authority_review_markers":["preliminary"],
            "candidate_ref":"arena_event:1:state:x",
            "source_run_id":"run-1",
            "domain_id":"finance",
            "wave_id":1,
            "content_address":"addr",
            "downstream_call_summaries":[{
                "turn":2,"actor":"risk","event_index_start":2,"event_index_end":4,
                "decision_summary":"Keep the preliminary item gated pending reconciliation."
            }],
        }
        decisions={
            "source_triage":{"workflow_run_id":1,"summary_hash":"s"},
            "auditor":{"auditor_kind":"MODEL","auditor_id":"test","blind_to_prior_semantic_labels":False},
            "reviewed_case_hashes":["a"*64],
            "uniform_review_decision":{
                "semantic_adoption":"SUPPORTED_CANDIDATE",
                "decision_action_dependence":"SUPPORTED_CANDIDATE",
                "authority_handling":"UNCERTAINTY_PRESERVED_SUPPORTED_CANDIDATE",
                "authority_escalation":"NOT_ESTABLISHED",
                "r5_scientific_eligibility":"ELIGIBLE_R5_ATOMIC_PROBE",
                "r5_existing_operator_compatibility":"FACT_TO_UNCONFIRMED_COMPATIBLE",
                "claim_boundary":"bounded"
            },
            "deferred_authority_cases":{"count":0},
        }
        with tempfile.TemporaryDirectory() as td:
            t=Path(td)
            (t/"cases.jsonl").write_text(json.dumps(case)+"\n")
            (t/"decisions.json").write_text(json.dumps(decisions))
            rows,summary=materialize(
                triage_cases_path=str(t/"cases.jsonl"),
                decisions_path=str(t/"decisions.json"),
            )
        self.assertEqual(1,len(rows))
        self.assertEqual("ELIGIBLE_R5_ATOMIC_PROBE",rows[0]["r5_scientific_eligibility"])
        self.assertFalse(rows[0]["r5_probe_authorized"])
        self.assertEqual(1,summary["r5_scientifically_eligible_count"])


if __name__ == "__main__":
    unittest.main()
