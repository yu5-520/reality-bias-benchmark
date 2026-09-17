#!/usr/bin/env python3
import json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EXPECTED_DESIGN='d8783a9c3e0a264c3119ee72e63db9b61d51f0d633ff6dde66068751c31701de'
EXPECTED_BATCH='0d4dd464d10bfc9a5b4307856e2c070bfaa521951e00cd0f147eeb80063e4beb'
EXPECTED_EXEC='11271a20abe67ad21e0e9f6cdac92d8330930f5a'


def j(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))

def jl(path):
    return [json.loads(x) for x in (ROOT/path).read_text(encoding='utf-8').splitlines() if x.strip()]

def require(cond,msg):
    if not cond: raise SystemExit(f'FAIL: {msg}')


def main():
    manifest=j('manifests/r6d_first_real_subject_2026-09-17_v0_1.json')
    summary=j('results/r6d_first_real_subject_v0_1/derived_summary.json')
    metrics=jl('results/r6d_first_real_subject_v0_1/run_metrics.jsonl')
    contrasts=j('results/r6d_first_real_subject_v0_1/triad_contrasts.json')
    report=(ROOT/'results/reports/2026-09-17/R6D_First_Real_Subject_Derived_Analysis_v0_1.md').read_text(encoding='utf-8')

    sci=manifest['scientific_subject']; method=manifest['derivation']
    require(sci['design_hash']==EXPECTED_DESIGN,'design hash drift')
    require(sci['evidence_batch_hash']==EXPECTED_BATCH,'evidence batch hash drift')
    require(sci['execution_code_sha']==EXPECTED_EXEC,'execution SHA drift')
    require(sci['raw_evidence_frozen_before_derivation'] is True,'raw freeze boundary lost')
    require(sci['provider_calls_are_real'] is True,'provider reality flag lost')
    require(sci['runner_error_count']==0,'runner errors present')
    require(sci['planned_branch_count']==9 and sci['preserved_trace_count']==9,'9-branch evidence incomplete')
    require(sci['paid_evaluator_called'] is False,'paid evaluator must remain off')
    require(sci['semantic_cpr_status']=='NOT_ADJUDICATED','CPR boundary violated')
    require(method['primary_label']=='FROZEN_TARGET_RESPONSE_CONTRAST','specificity label drift')
    require(method['escape_derived_specificity']=='NOT_ESTABLISHED','Escape specificity overclaim')
    require(method['same_parent_repeats_are_independent_population_samples'] is False,'independence overclaim')
    require(method['no_post_hoc_total_scalar'] is True,'post-hoc scalar introduced')

    eb=summary['evidence_binding']; mb=summary['method_boundary']
    require(eb['design_hash']==EXPECTED_DESIGN and eb['evidence_batch_hash']==EXPECTED_BATCH,'summary evidence binding drift')
    require(eb['workflow_run_id']==sci['workflow_run_id'] and eb['artifact_id']==sci['artifact_id'],'artifact/run binding mismatch')
    require(eb['semantic_cpr_status']=='NOT_ADJUDICATED','summary CPR boundary violated')
    require(mb['primary_label']=='FROZEN_TARGET_RESPONSE_CONTRAST','summary label drift')
    require(mb['escape_derived_specificity']=='NOT_ESTABLISHED','summary Escape overclaim')
    require(mb['same_parent_repeats_are_independent_population_samples'] is False,'summary sample-independence overclaim')

    require(len(metrics)==9,'run_metrics must contain exactly 9 rows')
    counts=Counter(x['condition_short'] for x in metrics)
    require(counts==Counter({'S0':3,'S1':3,'S2':3}),f'condition counts mismatch: {counts}')
    require(sum(x['observation_censored'] for x in metrics if x['condition_short']=='S0')==1,'S0 censoring mismatch')
    require(sum(x['observation_censored'] for x in metrics if x['condition_short']=='S2')==1,'S2 censoring mismatch')
    require(all(x['post10_target_events']==0 for x in metrics if x['condition_short']=='S1'),'S1 target-reference snapshot drift')
    require(all(x['highest_carrier_relation_level']=='PROPAGATED_CARRIER' for x in metrics if x['condition_short']=='S2'),'S2 propagated-carrier snapshot drift')
    require(sum(x['post10_target_fact_writes']>0 for x in metrics if x['condition_short']=='S2')==2,'S2 fact-reconstruction count drift')

    primary=[x for x in contrasts if x['contrast']=='S2_MINUS_S1']
    require(len(primary)==3,'must have 3 S2-S1 triad contrasts')
    for key in ('post10_agent_turns','post10_events','post10_unique_actors','post10_target_events','post10_target_actors','post10_target_state_writes'):
        require(all(x[key]>0 for x in primary),f'{key} is not positive in all frozen S2-S1 contrasts')
    natural=[x for x in contrasts if x['contrast']=='S2_MINUS_S0']
    require(any(x['post10_agent_turns']<0 for x in natural) and any(x['post10_agent_turns']>0 for x in natural),'natural variability boundary disappeared')

    for text in (
        'FROZEN_TARGET_RESPONSE_CONTRAST',
        'Escape-derived/J0-specific causality is not established by this batch',
        'Same-parent repeats are repeated realizations',
        'CPR: **NOT_ADJUDICATED**',
        'right-censored at T16',
    ):
        require(text in report,f'report missing required boundary text: {text}')

    require('ESCAPE_DERIVED_SPECIFICITY_NOT_ESTABLISHED' in summary['evidence_status'],'required evidence status missing')
    require('POST_CHALLENGE_INERTIA_EVIDENCE' in summary['evidence_status'],'post-challenge evidence status missing')
    print('PASS: first real R6-D derived analysis is internally synchronized and preserves v1.3 interpretation boundaries')

if __name__=='__main__': main()
