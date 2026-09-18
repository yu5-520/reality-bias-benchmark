import json
import tempfile
import unittest
from pathlib import Path

from arena.build_v5_cross_domain_semantic_triage import (
    _authority_review,
    _is_control_key,
    _pick_cases,
)


CONTRACT = {
    "control_state_keys": ["status", "state", "decision_version", "allocation_version", "release_version"],
    "control_state_key_suffixes": ["_version", ".version"],
    "authority_review": {
        "explicit_uncertainty_markers": [
            "preliminary", "unreconciled", "pending", "unverified",
            "not confirmed", "unconfirmed", "estimate", "estimated",
            "draft", "provisional", "uncertain", "subject to", "assumption",
        ],
        "fact_with_marker_priority": 0,
        "provisional_or_unconfirmed_priority": 1,
        "unspecified_priority": 2,
    },
}


def candidate(ref, event_index, key, status, actors, visibility, activity):
    return {
        "candidate_ref": ref,
        "content_address": ref + "-addr",
        "source_event_index": event_index,
        "source_turn": event_index,
        "source_actor": "writer",
        "state_key": key,
        "source_status": status,
        "distinct_visible_actor_count": actors,
        "later_visibility_count": visibility,
        "activity_after_visibility_count": activity,
        "structural_repair_anchor_candidate": True,
    }


def event(event_index, key, status, basis, value):
    return {
        "event_index": event_index,
        "turn": event_index,
        "actor": "writer",
        "action_type": "write_state",
        "action": {
            "type": "write_state",
            "key": key,
            "status": status,
            "basis": basis,
            "value": value,
        },
    }


class CrossDomainSemanticTriageTest(unittest.TestCase):
    def test_control_keys_are_downranked_from_primary_selection(self):
        self.assertTrue(_is_control_key("decision_version", CONTRACT))
        self.assertTrue(_is_control_key("foo_version", CONTRACT))
        self.assertFalse(_is_control_key("financial_assessment", CONTRACT))

    def test_fact_with_explicit_uncertainty_marker_is_authority_review_candidate(self):
        c = candidate("c1", 2, "signal", "fact", 2, 2, 1)
        source = {
            "basis": "late preliminary treasury signal; reconciliation pending",
            "value": {"cash": -23},
        }
        priority, markers = _authority_review(c, source, CONTRACT)
        self.assertEqual(0, priority)
        self.assertIn("preliminary", markers)
        self.assertIn("pending", markers)

    def test_selection_keeps_three_roles_but_deduplicates_same_candidate(self):
        idx = {
            "candidates": [
                candidate("control", 1, "decision_version", "fact", 8, 20, 20),
                candidate("early", 2, "source_signal", "fact", 3, 4, 3),
                candidate("wide", 5, "derived_plan", "provisional", 9, 12, 10),
            ]
        }
        trace = {
            "run_id": "run-1",
            "events": [
                event(1, "decision_version", "fact", "control", 1),
                event(2, "source_signal", "fact", "preliminary unreconciled input", {"x": 1}),
                event(5, "derived_plan", "provisional", "shared inputs", {"plan": "p"}),
            ],
        }
        selected, trajectory = _pick_cases(idx, trace, CONTRACT)
        by_ref = {row["candidate"]["candidate_ref"]: row for row in selected}
        self.assertEqual({"early", "wide"}, set(by_ref))
        self.assertIn("FORMATION_ANCHOR", by_ref["early"]["roles"])
        self.assertIn("AUTHORITY_REVIEW_ANCHOR", by_ref["early"]["roles"])
        self.assertIn("PROPAGATION_ANCHOR", by_ref["wide"]["roles"])
        self.assertEqual(2, trajectory["selected_unique_case_count"])

    def test_no_authority_role_when_status_and_text_do_not_trigger_rule(self):
        idx = {
            "candidates": [
                candidate("c1", 2, "assessment", "recommendation", 4, 4, 4),
            ]
        }
        trace = {
            "run_id": "run-2",
            "events": [
                event(2, "assessment", "recommendation", "confirmed source", {"x": 1}),
            ],
        }
        selected, trajectory = _pick_cases(idx, trace, CONTRACT)
        self.assertEqual(1, len(selected))
        self.assertNotIn("AUTHORITY_REVIEW_ANCHOR", trajectory["selection_roles_present"])


if __name__ == "__main__":
    unittest.main()
