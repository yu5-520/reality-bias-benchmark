import unittest
from pathlib import Path

from arena.core import ArenaState
from arena.engine import run_arena_once
from arena.experimental_control import capture_state
from arena.io_utils import load_json
from arena.one_shot_intervention import OneShotRuntimeViewTransform, build_one_shot_envelope
from arena.providers import ScriptedProvider

ROOT = Path(__file__).resolve().parents[2]


class OneShotInterventionTest(unittest.TestCase):
    def setUp(self):
        self.domain = load_json(ROOT / "arena/domains/ecommerce.json")
        self.config = load_json(ROOT / "arena/config/arena_v0.3.json")
        self.state = ArenaState(self.domain, self.config, "one-shot-test")
        self.key = next(iter(self.state.shared_state_metadata))
        self.state.shared_state_metadata[self.key]["status"] = "fact"
        self.state.shared_state_metadata[self.key]["event_index"] = 0
        self.snapshot = capture_state(self.state, anchor_ref="J0", parent_trace_hash="trace:test")
        self.envelope = build_one_shot_envelope(
            target_jump_ref="EVENT:0000",
            target_candidate_id="candidate:J0",
            state_key=self.key,
            source_event_index=0,
            from_status="fact",
        )

    def test_overlay_is_visible_once_and_not_persistent(self):
        transform = OneShotRuntimeViewTransform(self.envelope)
        provider = ScriptedProvider([
            {"decision_summary": "first", "actions": [{"type": "finalize", "answer": "draft"}]},
            {"decision_summary": "second", "actions": [{"type": "finalize", "answer": "final"}]},
        ])
        trace = run_arena_once(
            self.domain,
            self.config,
            provider,
            "one-shot-branch",
            logical_seed=1,
            initial_state_snapshot=self.snapshot,
            runtime_view_transform=transform,
        )
        transform.verify_finished()
        self.assertEqual(1, len(trace["runtime_transform_records"]))
        first = trace["model_calls"][0]["runtime_snapshot"]["shared_state_metadata"][self.key]["status"]
        second = trace["model_calls"][1]["runtime_snapshot"]["shared_state_metadata"][self.key]["status"]
        self.assertEqual("unconfirmed", first)
        self.assertEqual("fact", second)
        self.assertFalse(transform.summary()["persistent_state_mutation"])
        self.assertEqual(0, transform.summary()["experiment_origin_reinjection_count"])


if __name__ == "__main__":
    unittest.main()
