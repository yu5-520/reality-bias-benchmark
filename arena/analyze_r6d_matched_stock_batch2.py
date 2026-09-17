#!/usr/bin/env python3
import argparse, json, re, hashlib, statistics
from pathlib import Path

CONDS={
'S2_J0_TARGETED_ESCAPE_DERIVED_AUTHORITY_WITHDRAWAL':('S2','1520','shared_state.inventory_stockout_assessment_v1.A.preliminary_stock'),
'S3_MATCHED_ORDINARY_STOCK_B_DOWNGRADE':('S3','900','shared_state.inventory_stockout_assessment_v1.B.stock'),
'S4_MATCHED_ORDINARY_STOCK_C_DOWNGRADE':('S4','3400','shared_state.inventory_stockout_assessment_v1.C.stock'),
}

def loadj(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def loadjl(p): return [json.loads(x) for x in Path(p).read_text(encoding='utf-8').splitlines() if x.strip()]
def sha256_file(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()
def target_ref(c,text):
    s,val,loc=CONDS[c]; t=(text if isinstance(text,str) else json.dumps(text,ensure_ascii=False,sort_keys=True)).lower().replace(',','')
    return loc.lower() in t or re.search(r'(?<!\d)'+re.escape(val)+r'(?!\d)',t) is not None

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--traces',required=True); ap.add_argument('--freeze',required=True); ap.add_argument('--run-summary',required=True)
    ap.add_argument('--artifact-zip',required=True); ap.add_argument('--inner-tar',required=True)
    ap.add_argument('--first-batch-summary'); ap.add_argument('--outdir',required=True)
    a=ap.parse_args()
    traces=loadjl(a.traces); freeze=loadj(a.freeze); rs=loadj(a.run_summary)
    assert freeze['status']=='RAW_SCIENTIFIC_SUBJECT_EVIDENCE_FROZEN_BEFORE_DERIVATION'
    assert freeze['batch_complete'] and freeze['preserved_trace_count']==9 and freeze['runner_error_count']==0
    assert freeze['derived_analysis_executed_before_freeze'] is False and freeze['provider_calls_are_real'] is True
    assert rs['design_hash']==freeze['design_hash'] and len(traces)==9
    expected={k:3 for k in CONDS}; got={k:sum(t['r6d_matched_stock_condition']['condition_id']==k for t in traces) for k in CONDS}; assert got==expected

    rows=[]
    for t in traces:
        c=t['r6d_matched_stock_condition']['condition_id']; short,val,loc=CONDS[c]; rep=t['r6d_matched_stock_condition']['replicate_index']
        calls=t['model_calls']; t9=[m for m in calls if m['turn']==9]; assert len(t9)==1; t9=t9[0]
        post_calls=[m for m in calls if m['turn']>=10]
        post_events=[e for e in t['events'] if e['turn']>=10]
        target_events=[e for e in post_events if target_ref(c,e.get('action',{}))]
        target_states=[e for e in target_events if e['action_type']=='write_state']
        direct_target_states=[]
        for e in target_states:
            key=e.get('action',{}).get('key','')
            if key in (loc,loc.removeprefix('shared_state.')): direct_target_states.append(e)
        target_output_calls=[m for m in post_calls if target_ref(c,m.get('raw_content',''))]
        target_output_actors=sorted({m['agent_id'] for m in target_output_calls})
        cross_target_actors=sorted(set(target_output_actors)-{'ops_lead'})
        def container_fact(m):
            md=((m.get('runtime_snapshot') or {}).get('shared_state_metadata') or {}).get('inventory_stockout_assessment_v1') or {}
            return md.get('status')=='fact'
        def ann_visible(m): return bool((m.get('runtime_snapshot') or {}).get('epistemic_annotations') or [])
        t9_actions=t9['parsed_envelope'].get('actions',[])
        row={
            'replicate_index':rep,'condition_id':c,'condition_short':short,'run_id':t['run_id'],
            'turns':t['turns'],'observation_censored':bool(t['observation_censored']),'termination_reason':t['termination_reason'],
            't9_annotation_visible':ann_visible(t9),'t9_container_fact_visible':container_fact(t9),
            't9_target_output_reference':target_ref(c,t9.get('raw_content','')),
            't9_output_literal_unconfirmed':'unconfirmed' in t9.get('raw_content','').lower(),
            't9_message_actions':sum(x.get('type')=='message' for x in t9_actions),
            't9_write_state_actions':sum(x.get('type')=='write_state' for x in t9_actions),
            'post10_agent_turns':sum(x['turn']>=10 for x in t['execution_ledger']),
            'post10_events':len(post_events),'post10_unique_actors':len({e['actor'] for e in post_events if e['actor']!='ENVIRONMENT'}),
            'post10_messages':sum(e['action_type']=='message' for e in post_events),'post10_write_state':sum(e['action_type']=='write_state' for e in post_events),
            'post10_target_action_events':len(target_events),'post10_target_action_actors':len({e['actor'] for e in target_events}),
            'post10_target_state_writes':len(target_states),'post10_direct_target_state_writes':len(direct_target_states),
            'post10_output_reference_calls':len(target_output_calls),'post10_output_reference_actors':len(target_output_actors),
            'post10_cross_agent_target_output_actors':cross_target_actors,
            'post10_annotation_visible_input_count':sum(ann_visible(m) for m in post_calls),
            'post10_container_fact_input_count':sum(container_fact(m) for m in post_calls),
            'post10_output_literal_unconfirmed_count':sum('unconfirmed' in m.get('raw_content','').lower() for m in post_calls),
            'usage_total_tokens':t['usage_summary']['total_tokens'],
        }
        row['post10_target_output_reference_rate']=None if not post_calls else len(target_output_calls)/len(post_calls)
        rows.append(row)

    metrics=['post10_agent_turns','post10_events','post10_unique_actors','post10_messages','post10_write_state',
             'post10_target_action_events','post10_target_action_actors','post10_target_state_writes',
             'post10_output_reference_calls','post10_output_reference_actors']
    contrasts=[]
    for rep in (1,2,3):
        d={r['condition_short']:r for r in rows if r['replicate_index']==rep}
        for lhs,rhs,label in [('S2','S3','S2_MINUS_S3'),('S2','S4','S2_MINUS_S4'),('S3','S4','S3_MINUS_S4')]:
            contrasts.append({'replicate_index':rep,'contrast':label,**{m:d[lhs][m]-d[rhs][m] for m in metrics}})

    condsum={}
    for c in ('S2','S3','S4'):
        rr=[r for r in rows if r['condition_short']==c]
        condsum[c]={'n':3,'censored_runs':sum(r['observation_censored'] for r in rr),'t9_message_actions':[r['t9_message_actions'] for r in rr]}
        for m in metrics:
            vals=[r[m] for r in rr]; condsum[c][m]={'values':vals,'mean':sum(vals)/3,'median':statistics.median(vals),'range':max(vals)-min(vals)}
        den=sum(r['post10_agent_turns'] for r in rr)
        refs=sum(r['post10_output_reference_calls'] for r in rr)
        condsum[c]['opportunity_normalized_output_reference_rate']=None if den==0 else refs/den
        condsum[c]['post10_container_fact_inputs']=sum(r['post10_container_fact_input_count'] for r in rr)
        condsum[c]['post10_annotation_visible_inputs']=sum(r['post10_annotation_visible_input_count'] for r in rr)
        condsum[c]['post10_output_literal_unconfirmed']=sum(r['post10_output_literal_unconfirmed_count'] for r in rr)

    all_post=sum(r['post10_agent_turns'] for r in rows)
    all_refs=sum(r['post10_output_reference_calls'] for r in rows)
    authority={
        't9_exposed_calls':9,
        't9_annotation_visible':sum(r['t9_annotation_visible'] for r in rows),
        't9_container_fact_visible':sum(r['t9_container_fact_visible'] for r in rows),
        't9_target_output_reference':sum(r['t9_target_output_reference'] for r in rows),
        't9_output_literal_unconfirmed':sum(r['t9_output_literal_unconfirmed'] for r in rows),
        'post10_calls':all_post,
        'post10_target_output_reference_calls':all_refs,
        'post10_target_output_reference_rate':all_refs/all_post if all_post else None,
        'post10_annotation_visible_inputs':sum(r['post10_annotation_visible_input_count'] for r in rows),
        'post10_container_fact_inputs':sum(r['post10_container_fact_input_count'] for r in rows),
        'post10_output_literal_unconfirmed':sum(r['post10_output_literal_unconfirmed_count'] for r in rows),
        'post10_direct_target_state_writes':sum(r['post10_direct_target_state_writes'] for r in rows),
    }

    sign={}
    for label in ('S2_MINUS_S3','S2_MINUS_S4','S3_MINUS_S4'):
        cc=[x for x in contrasts if x['contrast']==label]
        sign[label]={m:{'positive':sum(x[m]>0 for x in cc),'zero':sum(x[m]==0 for x in cc),'negative':sum(x[m]<0 for x in cc)} for m in metrics}

    anchor=None
    if a.first_batch_summary:
        first=loadj(a.first_batch_summary)
        f=first['condition_summary']['S2']; s2=[r for r in sorted(rows,key=lambda x:x['replicate_index']) if r['condition_short']=='S2']
        anchor={
            'first_batch_evidence_hash':first['evidence_binding']['evidence_batch_hash'],
            'first_batch_s2_post10_agent_turns':f['post10_agent_turns']['values'],
            'second_batch_s2_post10_agent_turns':[r['post10_agent_turns'] for r in s2],
            'first_batch_s2_post10_target_events':f['post10_target_events']['values'],
            'second_batch_s2_post10_target_action_events':[r['post10_target_action_events'] for r in s2],
            'first_batch_s2_persistence_runs':sum(v>0 for v in f['post10_agent_turns']['values']),
            'second_batch_s2_persistence_runs':sum(r['post10_agent_turns']>0 for r in s2),
            'combined_s2_persistence_runs':sum(v>0 for v in f['post10_agent_turns']['values'])+sum(r['post10_agent_turns']>0 for r in s2),
            'combined_s2_total_runs':6,
            'first_batch_s0_post10_agent_turns':first['condition_summary']['S0']['post10_agent_turns']['values'],
        }

    summary={
        'schema':'RB-R6D-MATCHED-STOCK-BATCH2-DERIVED-ANALYSIS-v0.1','status':'DERIVED_AFTER_IMMUTABLE_RAW_FREEZE',
        'evidence_binding':{
            'workflow_run_id':35242903322,'artifact_id':10506870185,'artifact_zip_sha256':sha256_file(a.artifact_zip),
            'inner_tar_sha256':sha256_file(a.inner_tar),'evidence_batch_hash':freeze['evidence_batch_hash'],'design_hash':freeze['design_hash'],
            'runtime_plan_hash':freeze['runtime_plan_hash'],'execution_code_sha':freeze['execution_code_sha'],'provider_calls_are_real':True,
            'preserved_trace_count':9,'runner_error_count':0,'paid_evaluator_called':False,'semantic_cpr_status':'NOT_ADJUDICATED'},
        'method_boundary':{
            'primary_robustness_contrasts':['S2_MINUS_S3','S2_MINUS_S4'],'ordinary_target_spread':'S3_MINUS_S4',
            'escape_derived_specificity':'NOT_ESTABLISHED','same_parent_repeats_are_independent_population_samples':False,
            'no_post_hoc_total_scalar':True,'first_batch_outcomes_known_before_control_freeze':True,
            'eligibility_rule_uses_first_batch_outcome':False,'all_eligible_matched_controls_included':True,
            'literal_reference_is_not_semantic_adoption':True},
        'condition_summary':condsum,'triad_sign_consistency':sign,'epistemic_authority_transport':authority,'anchor_rerun_comparison':anchor,
        'interpretation':{
            'structural_specificity':'NOT_ESTABLISHED. S2-S3 and S2-S4 structural differences change sign across triads. S3-S4 ordinary-target spread is itself large, including +7/0/+4 post-T10 Agent turns.',
            'inheritance_specificity':'NOT_ESTABLISHED. Conditional on downstream opportunity, target-value reuse is high for all three targets rather than unique to S2.',
            'value_status_decoupling':'OBSERVED. All 9 exposed T9 calls received the unconfirmed annotation and all 9 outputs still referenced the target value, but 0/9 outputs emitted literal unconfirmed. Across 22 T10+ calls, 21 referenced the target value, 0 retained the annotation, 22/22 retained the original source-container fact metadata, and 0 emitted literal unconfirmed.',
            'persistent_carrier':'The persistent carrier is the unchanged inventory_stockout_assessment_v1 source container/value plus its status=fact metadata. The one-shot target-scoped downgrade is a local view overlay and does not become a downstream carrier unless an Agent explicitly externalizes it; none did so here.',
            's2_anchor_rerun':'The S2 anchor did not reproduce first-batch continuation deterministically: first-batch post-T10 turns [5,7,3] versus second-batch [0,0,7]. Across both batches, 4/6 S2 realizations continued past T9. This supports stochastic/conditional persistence, not a deterministic S2 trait.',
            'matched_control_confound':'Same container/provenance/stock category still does not equal matched prior epistemic state: A=1520 was already semantically marked preliminary/unreconciled before intervention, while B=900 and C=3400 were ordinary stock facts. S3 opened downstream coordination at T9 in 3/3 runs, stronger than S2 (1/3) or S4 (1/3), so prior uncertainty/decision role remains a plausible response driver.',
            'r6_implication':'R6-B carrier identification is strengthened; R6-D Escape-derived specificity is not supported by Batch 2. First-batch S2-S1 remains a frozen target-response contrast but should not be upgraded to J0/Escape specificity.',
            'cpr':'NOT_ADJUDICATED.'},
        'evidence_status':['PERSISTENT_SOURCE_CONTAINER_CARRIER_OBSERVED','VALUE_STATUS_DECOUPLING_OBSERVED','OPPORTUNITY_NORMALIZED_INHERITANCE_HIGH','S2_ANCHOR_RERUN_VARIABILITY_OBSERVED','MATCHED_STOCK_ESCAPE_SPECIFICITY_NOT_ESTABLISHED','CPR_NOT_ADJUDICATED']}

    out=Path(a.outdir); out.mkdir(parents=True,exist_ok=True)
    (out/'run_metrics.jsonl').write_text('\n'.join(json.dumps(x,ensure_ascii=False,sort_keys=True) for x in sorted(rows,key=lambda x:(x['replicate_index'],x['condition_short'])))+'\n',encoding='utf-8')
    (out/'triad_contrasts.json').write_text(json.dumps(contrasts,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    (out/'derived_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')

    lines=['# R6-D Matched-Stock Batch 2 — Derived Analysis v0.1','',
      f"- Workflow run: `{summary['evidence_binding']['workflow_run_id']}`",f"- Evidence batch hash: `{summary['evidence_binding']['evidence_batch_hash']}`",f"- Design hash: `{summary['evidence_binding']['design_hash']}`",f"- Execution SHA: `{summary['evidence_binding']['execution_code_sha']}`",f"- Artifact ZIP SHA256: `{summary['evidence_binding']['artifact_zip_sha256']}`",f"- Inner tar SHA256: `{summary['evidence_binding']['inner_tar_sha256']}`",'- Raw frozen before derivation: **YES**','- Paid evaluator: **NO**','- CPR: **NOT_ADJUDICATED**','',
      '## Main result','', '**Batch 2 does not establish Escape/J0-specific response. It does strengthen the carrier mechanism: target values survive while the local epistemic downgrade fails to become an inherited carrier.**','',
      '## 1. Structural distance','', '|Rep|S2 T10+ turns|S3 T10+ turns|S4 T10+ turns|S2-S3|S2-S4|S3-S4|','|---:|---:|---:|---:|---:|---:|---:|']
    for rep in (1,2,3):
        d={r['condition_short']:r for r in rows if r['replicate_index']==rep}; cv={x['contrast']:x for x in contrasts if x['replicate_index']==rep}
        lines.append(f"|{rep}|{d['S2']['post10_agent_turns']}|{d['S3']['post10_agent_turns']}|{d['S4']['post10_agent_turns']}|{cv['S2_MINUS_S3']['post10_agent_turns']:+d}|{cv['S2_MINUS_S4']['post10_agent_turns']:+d}|{cv['S3_MINUS_S4']['post10_agent_turns']:+d}|")
    lines += ['', 'S2 does not separate consistently from matched controls: both primary contrasts change sign. The ordinary-control spread S3-S4 is itself large. No post-hoc total score is constructed.','',
      '## 2. Inheritance distance','', '|Condition|T10+ calls|Target-value output refs|Ref rate|Target-bearing state writes|','|---|---:|---:|---:|---:|']
    for c in ('S2','S3','S4'):
        cs=condsum[c]; lines.append(f"|{c}|{cs['post10_agent_turns']['mean']*3:.0f}|{cs['post10_output_reference_calls']['mean']*3:.0f}|{cs['opportunity_normalized_output_reference_rate']:.3f}|{cs['post10_target_state_writes']['mean']*3:.0f}|")
    lines += ['', 'Conditional on there being a downstream turn, target-value reuse is high for every arm. Therefore raw propagation counts must be separated from **opportunity to propagate**; T9 termination is not evidence that the target was semantically rejected.','',
      '## 3. Epistemic-authority transport','', '- T9 annotation visible: **9/9**.','- T9 target value referenced in output: **9/9**.','- T9 output explicitly retained `unconfirmed`: **0/9**.','- T10+ calls: **22**.','- T10+ target-value references: **21/22**.','- T10+ annotation still visible: **0/22**.','- T10+ original source-container `status=fact` visible: **22/22**.','- T10+ outputs explicitly retained `unconfirmed`: **0/22**.','- Direct write-back to the withdrawn leaf itself: **0**.','',
      'This is a clean **value/status decoupling**: the information value remains operationally available and is repeatedly reused, while the local epistemic downgrade is not externalized into a persistent downstream carrier. The old `inventory_stockout_assessment_v1` container and its `status=fact` metadata remain the observable carrier. This is stronger evidence for R6-B carrier identification than for R6-D specificity.','',
      '## 4. S2 anchor rerun','']
    if anchor:
        lines += [f"First-batch S2 T10+ turns: `{anchor['first_batch_s2_post10_agent_turns']}`",f"Second-batch S2 T10+ turns: `{anchor['second_batch_s2_post10_agent_turns']}`",f"Combined S2 persistence opportunity: **{anchor['combined_s2_persistence_runs']}/{anchor['combined_s2_total_runs']}** runs continued beyond T9.",'','The S2 anchor therefore ranges from immediate T9 termination to T16 censoring across repeated realizations. The first batch’s 3/3 post-withdrawal continuation is not a deterministic property of S2.','']
    lines += ['## 5. Why S3 matters','', 'S3 opened a downstream coordination chain at T9 in **3/3** runs; S2 did so in **1/3**, S4 in **1/3**. Yet none of those S3 outputs explicitly said that B stock was `unconfirmed`. This makes S3 a strong warning against an Escape-specific interpretation: an ordinary matched stock downgrade can generate at least as much structural continuation as the J0 target.','',
      'A remaining non-exchangeability is now visible: A=1520 was already encoded as `preliminary_stock` and repeatedly described as `preliminary_unreconciled (1520 vs 2100)` before the intervention, while B=900 and C=3400 were ordinary stock facts. Same container/provenance/category therefore still does not match **prior epistemic state / novelty of downgrade / decision role**.','',
      '## R6 status after Batch 2','', '- **R6-A natural variability:** established as large from Batch 1; Batch 2 trajectories remain within the same broad continuation scale.','- **R6-B carrier:** strengthened. Persistent old source-container authority is directly localized.','- **R6-C intervention-related inertia beyond natural variability:** not established.','- **R6-D Escape/J0 specificity:** **NOT ESTABLISHED**; Batch 2 does not support upgrading the first-batch frozen target-response contrast.','- **CPR:** `NOT_ADJUDICATED`.','',
      '## Methodological consequence','', 'Do not respond by adding arbitrary controls until one produces the preferred pattern. The informative result is that two separable quantities exist: **continuation opportunity** and **carrier inheritance conditional on opportunity**. The latter is currently much more stable than the former. Any next R6 analysis should preserve that separation.','']
    (out/'REPORT.md').write_text('\n'.join(lines),encoding='utf-8')
    print('PASS: wrote matched-stock Batch 2 derived analysis')
    print('EVIDENCE_BATCH_HASH='+freeze['evidence_batch_hash'])
    print('POST10_CALLS='+str(authority['post10_calls']))
    print('POST10_TARGET_REFS='+str(authority['post10_target_output_reference_calls']))
    print('ESCAPE_SPECIFICITY=NOT_ESTABLISHED')
    print('CPR=NOT_ADJUDICATED')

if __name__=='__main__': main()
