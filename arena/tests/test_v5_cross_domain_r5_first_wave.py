import unittest

from arena.core import ArenaState
from arena.experimental_control import capture_state, verify_branch_manifest
from arena.one_shot_intervention import build_one_shot_envelope, make_branch_manifest_v3
from arena.prepare_v5_cross_domain_r5_first_wave import _select
from arena.run_v5_cross_domain_r5_first_wave import _validate_limits


def row(wave, event, run, case_hash):
    return {
        "wave_id": wave,
        "source_run_id": run,
        "source_case_hash": case_hash,
        "candidate_ref": f"arena_event:{event}:state:x",
        "source": {"status": "fact"},
        "r5_scientific_eligibility": "ELIGIBLE_R5_ATOMIC_PROBE",
        "r5_existing_operator_compatibility": "FACT_TO_UNCONFIRMED_COMPATIBLE",
    }


class CrossDomainR5FirstWaveTest(unittest.TestCase):
    def test_selects_one_earliest_case_per_wave(self):
        rows=[]
        for wave in range(1,7):
            rows.append(row(wave, 20, f"late-{wave}", "b"*64))
            rows.append(row(wave, 10, f"early-{wave}", "a"*64))
        selected=_select(rows)
        self.assertEqual(6,len(selected))
        self.assertEqual(list(range(1,7)),[int(x["wave_id"]) for x in selected])
        self.assertTrue(all(x["candidate_ref"].startswith("arena_event:10:") for x in selected))

    def test_noneligible_case_is_not_selected(self):
        rows=[]
        for wave in range(1,7):
            good=row(wave,10,f"good-{wave}","a"*64)
            bad=row(wave,1,f"bad-{wave}","b"*64)
            bad["r5_scientific_eligibility"]="NOT_ELIGIBLE_R5"
            rows += [bad,good]
        selected=_select(rows)
        self.assertTrue(all(x["source_run_id"].startswith("good-") for x in selected))


    def test_generic_engine_verifier_accepts_v03_one_shot_manifest(self):
        domain = {
            "domain_id": "test",
            "label": "Test",
            "entry_agent": "a",
            "task": {
                "goal": "g",
                "public_context": {},
                "initial_shared_state": {"x": 1},
                "late_event": {"content": "late"},
            },
            "agents": [{"id": "a", "role": "r", "responsibility": "do"}],
        }
        config = {
            "max_turns": 8,
            "max_total_invocations": 8,
            "max_pending_messages": 16,
            "termination_policy": "immediate_after_late_event",
        }
        state = ArenaState(domain, config, "parent-run")
        parent = capture_state(state, anchor_ref="after_turn:0", parent_trace_hash="trace")
        envelope = build_one_shot_envelope(
            target_jump_ref="arena_event:0:state:x",
            target_candidate_id="candidate",
            state_key="x",
            source_event_index=0,
            from_status="fact",
        )
        manifest = make_branch_manifest_v3(
            branch_id="branch-v03",
            condition_id="ONE_SHOT_JUMP_INTERVENTION",
            parent_trace_hash="trace",
            parent_snapshot=parent,
            envelope=envelope,
            replicate_index=1,
        )
        self.assertTrue(
            verify_branch_manifest(
                manifest,
                parent_snapshot=parent,
                branch_start_snapshot=parent,
            )
        )

    def test_global_budget_must_cover_symmetric_branch_ceilings(self):
        self.assertIsNone(_validate_limits(24,64,0.25,6.0))
        with self.assertRaises(ValueError):
            _validate_limits(24,64,0.25,5.99)


if __name__=="__main__":
    unittest.main()
