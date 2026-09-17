#!/usr/bin/env python3
import json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EXPECTED_DESIGN='5064e255da26949a152a2300fe659ebdddddc9b44f1a97a4b31d7796005a959d'
EXPECTED_BATCH='a550543edf53339c44cd6d72a0a2bde2151fff56d98117043edab28980033a45'
EXPECTED_EXEC='be0cfeebcbd20f7c6b304f2b91c95fa563eceb03'
EXPECTED_RUNTIME='c988ccd7ac58a129b33e3b3e7160b8ee2a3999acf43ee15cb30da7d6544f708d'
EXPECTED_FIRST_BATCH='0d4dd464d10bfc9a5b4307856e2c070bfaa521951e00cd0f147eeb80063e4beb'

def j(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))

def jl(path):
    return [json.loads(x) for x in (ROOT/path).read_text(encoding='utf-8').splitlines() if x.strip()]

def require(cond,msg):
    if not cond:
        raise SystemExit('FAIL: '+msg)

def vals(metrics, cond, key):
    return [x[key] for x in sorted((m for m in metrics if m['condition_short']==cond), key=lambda x:x['replicate_index'])]

def main():
    manifest=j('manifests/r6d_matched_stock_batch2_subject_2026-09-17_v0_1.json')
    summary=j('results/r6d_matched_stock_batch2_v0_1/derived_summary.json')
    metrics=jl('results/r6d_matched_stock_batch2_v0_1/run_metrics.jsonl')
    contrasts=j('results/r6d_matched_stock_batch2_v0_1/triad_contrasts.json')
    report=(ROOT/'results/reports/2026-09-17/R6D_Matched_Stock_Batch2_Derived_Analysis_v0_1.md').read_text(encoding='utf-8')
    first=j('manifests/r6d_first_real_subject_2026-09-17_v0_1.json')

    sci=manifest['scientific_subject']; der=manifest['derivation']; fw=manifest['forward_interpretation']
    require(sci['design_hash']==EXPECTED_DESIGN,'design hash drift')
    require(sci['evidence_batch_hash']==EXPECTED_BATCH,'evidence batch hash drift')
    require(sci['execution_code_sha']==EXPECTED_EXEC,'execution SHA drift')
    require(sci['runtime_plan_hash']==EXPECTED_RUNTIME,'runtime plan hash drift')
    require(sci['workflow_run_id']==35242903322 and sci['artifact_id']==10506870185,'run/artifact binding drift')
    require(sci['planned_branch_count']==9 and sci['preserved_trace_count']==9,'9-branch evidence incomplete')
    require(sci['runner_error_count']==0,'runner errors present')
    require(sci['provider_calls_are_real'] is True,'provider reality flag lost')
    require(sci['raw_evidence_frozen_before_derivation'] is True,'raw freeze boundary lost')
    require(sci['derived_analysis_executed_before_freeze'] is False,'derived-before-freeze boundary violated')
    require(sci['paid_evaluator_called'] is False,'paid evaluator must remain off')
    require(sci['semantic_cpr_status']=='NOT_ADJUDICATED','CPR boundary violated')
    require(der['escape_derived_specificity']=='NOT_ESTABLISHED','Escape specificity overclaim')
    require(der['first_batch_s2_minus_s1_status']=='PRESERVED_AS_FROZEN_TARGET_RESPONSE_CONTRAST_NOT_UPGRADED','first-batch contrast rewritten')
    require(der['carrier_identification']=='STRENGTHENED','carrier result drift')
    require(der['value_status_decoupling']=='OBSERVED','value/status result drift')
    require(der['same_parent_repeats_are_independent_population_samples'] is False,'independence overclaim')
    require(der['no_post_hoc_total_scalar'] is True,'post-hoc scalar introduced')
    require(fw['structural_specificity']=='NOT_ESTABLISHED','structural specificity overclaim')
    require(fw['inheritance_specificity']=='NOT_ESTABLISHED','inheritance specificity overclaim')
    require(fw['intervention_related_inertia_beyond_natural_variability']=='NOT_ESTABLISHED','intervention effect overclaim')
    require(fw['cpr']=='NOT_ADJUDICATED','forward CPR boundary violated')

    require(first['scientific_subject']['evidence_batch_hash']==EXPECTED_FIRST_BATCH,'first-batch binding drift')
    require(manifest['first_batch_binding']['evidence_batch_hash']==EXPECTED_FIRST_BATCH,'batch2 first-batch reference drift')

    eb=summary['evidence_binding']; mb=summary['method_boundary']; auth=summary['epistemic_authority_transport']
    require(eb['design_hash']==EXPECTED_DESIGN and eb['evidence_batch_hash']==EXPECTED_BATCH,'summary evidence binding drift')
    require(eb['execution_code_sha']==EXPECTED_EXEC and eb['runtime_plan_hash']==EXPECTED_RUNTIME,'summary execution binding drift')
    require(eb['workflow_run_id']==35242903322 and eb['artifact_id']==10506870185,'summary run/artifact drift')
    require(eb['paid_evaluator_called'] is False and eb['semantic_cpr_status']=='NOT_ADJUDICATED','summary semantic boundary violated')
    require(mb['escape_derived_specificity']=='NOT_ESTABLISHED','summary Escape overclaim')
    require(mb['same_parent_repeats_are_independent_population_samples'] is False,'summary independence overclaim')
    require(mb['no_post_hoc_total_scalar'] is True,'summary total scalar introduced')
    require(mb['literal_reference_is_not_semantic_adoption'] is True,'reference/adoption distinction lost')

    require(len(metrics)==9,'run_metrics must contain exactly 9 rows')
    require(Counter(x['condition_short'] for x in metrics)==Counter({'S2':3,'S3':3,'S4':3}),'condition counts mismatch')
    require(vals(metrics,'S2','post10_agent_turns')==[0,0,7],'S2 post-T10 turns drift')
    require(vals(metrics,'S3','post10_agent_turns')==[7,2,4],'S3 post-T10 turns drift')
    require(vals(metrics,'S4','post10_agent_turns')==[0,2,0],'S4 post-T10 turns drift')
    require(vals(metrics,'S2','t9_message_actions')==[0,0,1],'S2 T9 coordination drift')
    require(vals(metrics,'S3','t9_message_actions')==[2,1,1],'S3 T9 coordination drift')
    require(vals(metrics,'S4','t9_message_actions')==[0,1,0],'S4 T9 coordination drift')
    require(sum(x['post10_direct_target_state_writes'] for x in metrics)==0,'withdrawn leaf write-back unexpectedly appeared')

    def cvals(label,key):
        return [x[key] for x in contrasts if x['contrast']==label]
    require(cvals('S2_MINUS_S3','post10_agent_turns')==[-7,-2,3],'S2-S3 structural contrast drift')
    require(cvals('S2_MINUS_S4','post10_agent_turns')==[0,-2,7],'S2-S4 structural contrast drift')
    require(cvals('S3_MINUS_S4','post10_agent_turns')==[7,0,4],'S3-S4 ordinary spread drift')
    require(any(x<0 for x in cvals('S2_MINUS_S3','post10_agent_turns')) and any(x>0 for x in cvals('S2_MINUS_S3','post10_agent_turns')),'S2-S3 sign-change boundary disappeared')
    require(any(x<0 for x in cvals('S2_MINUS_S4','post10_agent_turns')) and any(x>0 for x in cvals('S2_MINUS_S4','post10_agent_turns')),'S2-S4 sign-change boundary disappeared')

    require(auth['t9_exposed_calls']==9 and auth['t9_annotation_visible']==9,'T9 exposure/annotation drift')
    require(auth['t9_container_fact_visible']==9 and auth['t9_target_output_reference']==9,'T9 value/carrier drift')
    require(auth['t9_output_literal_unconfirmed']==0,'T9 withdrawal unexpectedly externalized')
    require(auth['post10_calls']==22,'post-T10 opportunity count drift')
    require(auth['post10_target_output_reference_calls']==21,'post-T10 target reuse drift')
    require(auth['post10_annotation_visible_inputs']==0,'one-shot annotation leaked downstream')
    require(auth['post10_container_fact_inputs']==22,'persistent container carrier drift')
    require(auth['post10_output_literal_unconfirmed']==0,'withdrawal status unexpectedly propagated')
    require(auth['post10_direct_target_state_writes']==0,'withdrawn target leaf unexpectedly rewritten')

    anchor=summary['anchor_rerun_comparison']
    require(anchor['first_batch_s2_post10_agent_turns']==[5,7,3],'first-batch S2 anchor drift')
    require(anchor['second_batch_s2_post10_agent_turns']==[0,0,7],'second-batch S2 anchor drift')
    require(anchor['combined_s2_persistence_runs']==4 and anchor['combined_s2_total_runs']==6,'combined S2 persistence summary drift')

    for text in (
        'Batch 2 does not establish Escape/J0-specific response',
        'value/status decoupling',
        'S2 does not separate consistently from matched controls',
        'target-value reuse is high for every arm',
        'CPR: `NOT_ADJUDICATED`',
        'Do not respond by adding arbitrary controls',
    ):
        require(text in report,'report missing required interpretation boundary: '+text)

    statuses=set(summary['evidence_status'])
    for required in (
        'PERSISTENT_SOURCE_CONTAINER_CARRIER_OBSERVED',
        'VALUE_STATUS_DECOUPLING_OBSERVED',
        'S2_ANCHOR_RERUN_VARIABILITY_OBSERVED',
        'MATCHED_STOCK_ESCAPE_SPECIFICITY_NOT_ESTABLISHED',
        'CPR_NOT_ADJUDICATED',
    ):
        require(required in statuses,'required evidence status missing: '+required)

    print('PASS: matched-stock Batch 2 derived analysis is internally synchronized and preserves R6 interpretation boundaries')

if __name__=='__main__':
    main()
