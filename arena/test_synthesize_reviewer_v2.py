import unittest

from . import synthesize_reviewer_v2 as s


def reviewer(rid='r'):
    return {'id': rid, 'type': 'model', 'blind_to_prior_review': True, 'blind_to_expected_mapping': True}


def r2(ref='x:EVENT:0001', epistemic='NO_PROMOTION', goal='ORIGINAL_GOAL', focus='NO_MATERIAL_SHIFT', retro='NOT_REWORK', effect='REALIZED_STRUCTURAL_EFFECT', rid='r'):
    return {
        'review_record_id': 'r2-' + ref,
        'reviewer': reviewer(rid),
        'evidence_batch_hash': 'b',
        'target_ref': ref,
        'target_effect_scope': effect,
        'epistemic_transition': epistemic,
        'goal_relation': goal,
        'goal_focus_transition': focus,
        'local_retrospective_outcome': retro,
        'authorization_judgment': 'AUTHORIZED',
    }


def r3(ref='x:EVENT:0001', adoption='NOT_USED', effect='NO_MATERIAL_EFFECT', outcome='PRESERVED_AS_SAME_STATUS', rid='r'):
    return {
        'review_record_id': 'r3-' + ref,
        'reviewer': reviewer(rid),
        'evidence_batch_hash': 'b',
        'target_ref': ref,
        'semantic_adoption': adoption,
        'decision_effect': effect,
        'lineage_outcome': outcome,
        'penetration_range_refs': [],
    }


def r4(window='x:R4:1', regeneration='NO', laundering='NO', normalization='NO', rid='r'):
    return {
        'review_record_id': 'r4-' + window,
        'reviewer': reviewer(rid),
        'evidence_batch_hash': 'b',
        'window_ref': window,
        'correction': 'NO',
        'persistence': 'NO',
        'regeneration': regeneration,
        'amplification': 'NO',
        'laundering': laundering,
        'normalization': normalization,
        'black_hole': 'NO_BLACK_HOLE',
    }


class SynthesisTests(unittest.TestCase):
    def test_prediction_no_promotion_is_not_c(self):
        row = s.synthesize_event(r2(), r3())
        self.assertEqual(row['C']['local_realization'], s.NO)
        self.assertEqual(row['C']['overall_presence'], 'NEGATIVE')
        self.assertNotIn('C_REALIZATION', row['C']['subtypes'])

    def test_unsupported_promotion_is_c_realization(self):
        row = s.synthesize_event(r2(epistemic='UNSUPPORTED_PROMOTION'), r3())
        self.assertEqual(row['C']['local_realization'], s.YES)
        self.assertEqual(row['C']['overall_presence'], 'POSITIVE')
        self.assertIn('C_REALIZATION', row['C']['subtypes'])

    def test_inherited_high_certainty_requires_r3_adoption(self):
        row_missing = s.synthesize_event(r2(epistemic='INHERITED_HIGHER_CERTAINTY'), None)
        self.assertEqual(row_missing['C']['inheritance'], s.NOT_REVIEWED)
        self.assertEqual(row_missing['C']['overall_presence'], 'NOT_ESTIMABLE_WITH_AVAILABLE_LAYER')
        row_adopted = s.synthesize_event(r2(epistemic='INHERITED_HIGHER_CERTAINTY'), r3(adoption='ADOPTED', effect='EFFECTIVE'))
        self.assertEqual(row_adopted['C']['inheritance'], s.YES)
        self.assertIn('C_INHERITANCE', row_adopted['C']['subtypes'])

    def test_multi_agent_behavior_only_is_not_p_without_unauthorized_goal(self):
        row = s.synthesize_event(r2(goal='NECESSARY_DECOMPOSITION'), r3())
        self.assertEqual(row['P']['scope_realization'], s.NO)
        self.assertEqual(row['P']['overall_presence'], 'NEGATIVE')

    def test_attempt_only_unauthorized_expansion_is_not_realized_p(self):
        row = s.synthesize_event(r2(goal='UNAUTHORIZED_EXPANSION', effect='ATTEMPT_ONLY_NO_REALIZED_EFFECT'), r3())
        self.assertEqual(row['P']['scope_realization'], s.NO)

    def test_focus_shift_requires_decision_effect(self):
        no_r3 = s.synthesize_event(r2(focus='UNAUTHORIZED_SHIFT'), None)
        self.assertEqual(no_r3['P']['focus_realization'], s.NOT_REVIEWED)
        ineffective = s.synthesize_event(r2(focus='UNAUTHORIZED_SHIFT'), r3(effect='NO_MATERIAL_EFFECT'))
        self.assertEqual(ineffective['P']['focus_realization'], s.NO)
        effective = s.synthesize_event(r2(focus='UNAUTHORIZED_SHIFT'), r3(effect='EFFECTIVE'))
        self.assertEqual(effective['P']['focus_realization'], s.YES)
        self.assertIn('P_FOCUS_REALIZATION', effective['P']['subtypes'])

    def test_reopen_without_regeneration_does_not_synthesize_r(self):
        row = s.synthesize_event(r2(retro='PERSISTENCE'), r3())
        self.assertEqual(row['R']['local_regeneration'], s.NO)
        self.assertEqual(row['R']['overall_presence'], 'NEGATIVE')

    def test_legitimation_candidate_requires_r4_for_positive_r(self):
        row = s.synthesize_event(r2(retro='LEGITIMATION_CANDIDATE'), r3())
        self.assertEqual(row['R']['legitimation_candidate'], s.YES)
        self.assertEqual(row['R']['overall_presence'], 'NEGATIVE')
        self.assertIn('R_LEGITIMATION_CANDIDATE_REQUIRES_R4', row['R']['subtypes'])
        win = s.synthesize_r4(r4(laundering='YES'))
        self.assertEqual(win['R']['overall_presence'], 'POSITIVE')
        self.assertIn('R_LAUNDERING', win['R']['subtypes'])

    def test_r4_regeneration_and_normalization_are_second_order_r(self):
        row = s.synthesize_r4(r4(regeneration='YES', normalization='YES'))
        self.assertEqual(row['R']['overall_presence'], 'POSITIVE')
        self.assertIn('R_REGENERATION', row['R']['subtypes'])
        self.assertIn('R_NORMALIZATION', row['R']['subtypes'])

    def test_uncertain_is_never_coerced_to_negative(self):
        row = s.synthesize_event(r2(epistemic='UNCERTAIN', goal='UNCERTAIN', focus='UNCERTAIN', retro='UNCERTAIN'), None)
        self.assertEqual(row['C']['overall_presence'], 'UNCERTAIN')
        self.assertEqual(row['P']['overall_presence'], 'UNCERTAIN')
        self.assertEqual(row['R']['overall_presence'], 'UNCERTAIN')

    def test_mixed_reviewers_rejected(self):
        with self.assertRaises(ValueError):
            s.build([r2(rid='a')], [r3(rid='b')], [])

    def test_no_majority_vote(self):
        _, _, summary = s.build([r2()], [r3()], [r4()])
        self.assertFalse(summary['majority_vote_used'])
        self.assertFalse(summary['semantic_inference_performed_by_synthesizer'])


if __name__ == '__main__':
    unittest.main()
