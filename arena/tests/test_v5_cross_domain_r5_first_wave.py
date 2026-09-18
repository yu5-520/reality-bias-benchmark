import unittest

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

    def test_global_budget_must_cover_symmetric_branch_ceilings(self):
        self.assertIsNone(_validate_limits(24,64,0.25,6.0))
        with self.assertRaises(ValueError):
            _validate_limits(24,64,0.25,5.99)


if __name__=="__main__":
    unittest.main()
