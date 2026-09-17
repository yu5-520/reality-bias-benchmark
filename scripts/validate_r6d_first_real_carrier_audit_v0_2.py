#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'results'/'reports'/'2026-09-17'/'R6D_First_Real_Carrier_Mechanism_Audit_v0_2.md'
MAN=ROOT/'manifests'/'r6d_first_real_carrier_audit_2026-09-17_v0_2.json'
SCRIPT=ROOT/'arena'/'analyze_r6d_carrier_audit_v0_2.py'
def req(c,m):
    if not c: raise SystemExit('FAIL: '+m)
def main():
    m=json.loads(MAN.read_text()); r=REPORT.read_text(); s=SCRIPT.read_text()
    req(m['schema']=='RB-R6D-FIRST-REAL-CARRIER-MECHANISM-AUDIT-BINDING-v0.2','schema mismatch')
    req(m['scientific_subject']['design_hash']=='d8783a9c3e0a264c3119ee72e63db9b61d51f0d633ff6dde66068751c31701de','design hash drift')
    req(m['scientific_subject']['evidence_batch_hash']=='0d4dd464d10bfc9a5b4307856e2c070bfaa521951e00cd0f147eeb80063e4beb','evidence batch drift')
    req(m['scientific_subject']['artifact_digest']=='sha256:da14f406fdc574178901a6e5129b6257496cbfb584b852da812923573f0cd927','artifact digest drift')
    f=m['mechanism_findings']
    req(f['s2_t9_exact_withdrawal_annotation_delivered_and_read_runs']==3,'S2 T9 delivery count mismatch')
    req(f['s2_t9_target_value_used_in_output_runs']==3,'S2 T9 target-use count mismatch')
    req(f['s2_t9_literal_unconfirmed_reexpressed_in_output_runs']==0,'unexpected literal unconfirmed output')
    req(f['s2_post_t9_observed_calls']==15 and f['s2_post_t9_target_visible_input_calls']==15,'S2 post-T9 target visibility mismatch')
    req(f['s2_post_t9_withdrawal_annotation_visible_input_calls']==0,'one-shot annotation leaked downstream')
    req(f['s2_post_t9_j0_container_fact_metadata_visible_calls']==15,'container fact carrier count mismatch')
    req(f['s2_post_t9_target_value_used_in_output_calls']==15,'S2 target output count mismatch')
    req(f['s1_t9_target_used_in_output_runs']==0 and f['s1_post_t9_target_output_calls']==0,'S1 target-use boundary mismatch')
    req(f['s0_t9_j0_target_used_in_output_runs']==3 and f['s0_post_t9_target_value_used_in_output_calls']==9,'S0 natural baseline mismatch')
    req(m['interpretation']['withdrawal_status_propagation']=='NOT_OBSERVED_DOWNSTREAM','withdrawal propagation overclaim')
    req(m['interpretation']['proposition_level_authority_reconstruction']=='NOT_ESTABLISHED','proposition-level authority overclaim')
    req(m['interpretation']['intervention_related_inertia_beyond_natural_variability']=='NOT_ESTABLISHED','causal overclaim')
    req(m['interpretation']['escape_derived_specificity']=='NOT_ESTABLISHED','specificity overclaim')
    req(m['interpretation']['cpr']=='NOT_ADJUDICATED','CPR overclaim')
    req(m['forward_correction']['does_not_rewrite_historical_v0_1_files'] is True,'append-only correction boundary missing')
    for p in ['does **not** show the one-shot `unconfirmed` status being propagated downstream','container-level fact reassertion candidate','container authority and nested-proposition authority cannot be treated as equivalent','ESCAPE_DERIVED_SPECIFICITY_NOT_ESTABLISHED']:
        req(p in r,'report missing boundary: '+p)
    for p in ['S0_NATURAL_REFERENCE','S1_MATCHED_OR_ORDINARY_FACTUAL_INFORMATION_DOWNGRADE','S2_J0_TARGETED_ESCAPE_DERIVED_AUTHORITY_WITHDRAWAL','target_container_fact_reassertion_events','unrelated_fact_container_carrying_target_events']:
        req(p in s,'derivation script missing required audit field: '+p)
    req(m['authorization_boundary']=={'cpr_semantic_adjudication_authorized':False,'new_provider_call_authorized':False,'paid_evaluator_authorized':False,'r7_recovery_subject_authorized':False},'authorization boundary drift')
    print('PASS: R6-D first real carrier mechanism audit v0.2 static binding is synchronized and interpretation-bounded')
if __name__=='__main__': main()
