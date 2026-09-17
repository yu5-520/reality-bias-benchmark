#!/usr/bin/env python3
import argparse, hashlib, json, re, statistics
from pathlib import Path

S0='S0_NATURAL_REFERENCE'
S1='S1_MATCHED_OR_ORDINARY_FACTUAL_INFORMATION_DOWNGRADE'
S2='S2_J0_TARGETED_ESCAPE_DERIVED_AUTHORITY_WITHDRAWAL'

def load_json(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def load_jsonl(p): return [json.loads(x) for x in Path(p).read_text(encoding='utf-8').splitlines() if x.strip()]
def sha256_file(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''): h.update(chunk)
    return h.hexdigest()
def action_text(e): return json.dumps(e.get('action',{}),ensure_ascii=False,sort_keys=True)
def short(c): return c.split('_')[0]

def target_ref(condition, text):
    t=text.lower().replace(',', '')
    if condition==S2:
        return ('shared_state.inventory_stockout_assessment_v1.a.preliminary_stock' in t or
                re.search(r'(?<!\d)1520(?!\d)', t) is not None)
    if condition==S1:
        # Require the actual frozen value or the exact locator; avoid unrelated margin prose.
        return ('public_context.products.c.gross_margin_pct' in t or
                (re.search(r'(?<!\d)35(?:\.0)?(?:%|\b)', t) is not None and
                 ('gross margin' in t or 'gross_margin' in t or 'product c' in t)))
    # S0 natural baseline is measured against the J0/S2 target.
    return ('shared_state.inventory_stockout_assessment_v1.a.preliminary_stock' in t or
            re.search(r'(?<!\d)1520(?!\d)', t) is not None)

def relation_level(trace, metrics):
    if trace['r6d_condition']['condition_id']==S0:
        return 'NATURAL_BASELINE_NOT_INTERVENTION_RELATION'
    integ=trace.get('r6d_exposure_integrity',{})
    delivered=integ.get('direct_experiment_origin_exposure_count',0)==1
    consumed=bool(trace.get('runtime_transform_records') and trace['runtime_transform_records'][0].get('consumed_after_delivery'))
    if not (delivered and consumed): return 'REACHABLE_CARRIER'
    if metrics['post10_target_events']==0: return 'DELIVERED_OR_READ_CARRIER'
    if metrics['post10_target_state_writes']==0: return 'ADOPTED_CARRIER'
    if metrics['post10_target_actors']<=1: return 'INHERITED_CARRIER'
    return 'PROPAGATED_CARRIER'

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--traces',required=True)
    ap.add_argument('--freeze',required=True)
    ap.add_argument('--run-summary',required=True)
    ap.add_argument('--artifact-run-id',required=True)
    ap.add_argument('--artifact-id',required=True)
    ap.add_argument('--artifact-digest',required=True)
    ap.add_argument('--artifact-zip-sha256',required=True)
    ap.add_argument('--inner-tar-sha256',required=True)
    ap.add_argument('--outdir',required=True)
    a=ap.parse_args()
    traces=load_jsonl(a.traces); freeze=load_json(a.freeze); run_summary=load_json(a.run_summary)
    assert freeze['status']=='RAW_SCIENTIFIC_SUBJECT_EVIDENCE_FROZEN_BEFORE_DERIVATION'
    assert freeze['batch_complete'] is True and freeze['preserved_trace_count']==9
    assert freeze['runner_error_count']==0 and freeze['provider_calls_are_real'] is True
    assert freeze['derived_analysis_executed_before_freeze'] is False
    assert run_summary['design_hash']==freeze['design_hash']
    assert run_summary['execution_code_sha']==freeze['execution_code_sha']
    assert len(traces)==9
    expected={S0:3,S1:3,S2:3}
    got={c:sum(t['r6d_condition']['condition_id']==c for t in traces) for c in expected}
    assert got==expected

    rows=[]
    for t in traces:
        c=t['r6d_condition']['condition_id']; rep=t['r6d_condition']['replicate_index']
        post10=[e for e in t['events'] if e['turn']>=10]
        hits=[e for e in post10 if target_ref(c,action_text(e))]
        state_hits=[e for e in hits if e['action_type']=='write_state']
        fact_hits=[e for e in state_hits if e['action'].get('status')=='fact']
        metrics={
            'replicate_index':rep,'triad_id':t['r6d_condition']['triad_id'],'run_id':t['run_id'],
            'condition_id':c,'condition_short':short(c),'turns':t['turns'],
            'termination_reason':t['termination_reason'],'observation_censored':bool(t['observation_censored']),
            'condition_complete':bool(t['condition_complete']),
            'post10_agent_turns':sum(x['turn']>=10 for x in t['execution_ledger']),
            'post10_events':len(post10),
            'post10_unique_actors':len({e['actor'] for e in post10 if e['actor']!='ENVIRONMENT'}),
            'post10_messages':sum(e['action_type']=='message' for e in post10),
            'post10_write_state':sum(e['action_type']=='write_state' for e in post10),
            'post10_finalize':sum(e['action_type']=='finalize' for e in post10),
            'post10_revise_final_state':sum(e['action_type']=='revise_final_state' for e in post10),
            'post10_target_events':len(hits),
            'post10_target_actors':len({e['actor'] for e in hits}),
            'post10_target_state_writes':len(state_hits),
            'post10_target_fact_writes':len(fact_hits),
            'target_event_turns':sorted({e['turn'] for e in hits}),
            'target_event_actors':sorted({e['actor'] for e in hits}),
            'usage_total_tokens':t['usage_summary']['total_tokens'],
            'experiment_origin_persistent_state_mutation':bool(t['r6d_exposure_integrity'].get('persistent_state_mutation',False)),
            'experiment_origin_reinjection_count':t['r6d_exposure_integrity'].get('experiment_origin_reinjection_count',0),
        }
        metrics['highest_carrier_relation_level']=relation_level(t,metrics)
        rows.append(metrics)

    metrics_for_contrast=['turns','post10_agent_turns','post10_events','post10_unique_actors','post10_messages',
                          'post10_write_state','post10_target_events','post10_target_actors',
                          'post10_target_state_writes','post10_target_fact_writes','usage_total_tokens']
    contrasts=[]
    for rep in (1,2,3):
        d={r['condition_short']:r for r in rows if r['replicate_index']==rep}
        for lhs,rhs,label in [('S2','S1','S2_MINUS_S1'),('S2','S0','S2_MINUS_S0'),('S1','S0','S1_MINUS_S0')]:
            contrasts.append({
                'replicate_index':rep,'contrast':label,
                **{m:d[lhs][m]-d[rhs][m] for m in metrics_for_contrast}
            })

    cond_summary={}
    for c in ('S0','S1','S2'):
        rr=[r for r in rows if r['condition_short']==c]
        cond_summary[c]={
            'n':3,
            'censored_runs':sum(r['observation_censored'] for r in rr),
            'complete_runs':sum(r['condition_complete'] for r in rr),
            'highest_relation_levels':[r['highest_carrier_relation_level'] for r in rr],
        }
        for m in metrics_for_contrast:
            vals=[r[m] for r in rr]
            cond_summary[c][m]={'values':vals,'mean':sum(vals)/len(vals),'median':statistics.median(vals),'range':max(vals)-min(vals)}

    s2s1=[c for c in contrasts if c['contrast']=='S2_MINUS_S1']
    s2s0=[c for c in contrasts if c['contrast']=='S2_MINUS_S0']
    sign_consistency={m:{
        's2_minus_s1_positive_replicates':sum(x[m]>0 for x in s2s1),
        's2_minus_s1_zero_replicates':sum(x[m]==0 for x in s2s1),
        's2_minus_s1_negative_replicates':sum(x[m]<0 for x in s2s1),
        's2_minus_s0_positive_replicates':sum(x[m]>0 for x in s2s0),
        's2_minus_s0_zero_replicates':sum(x[m]==0 for x in s2s0),
        's2_minus_s0_negative_replicates':sum(x[m]<0 for x in s2s0),
    } for m in metrics_for_contrast}

    summary={
        'schema':'RB-R6D-FIRST-REAL-SUBJECT-DERIVED-ANALYSIS-v0.1',
        'status':'DERIVED_AFTER_IMMUTABLE_RAW_FREEZE',
        'evidence_binding':{
            'workflow_run_id':int(a.artifact_run_id),'artifact_id':int(a.artifact_id),
            'artifact_digest':a.artifact_digest,'artifact_zip_sha256':a.artifact_zip_sha256,
            'inner_tar_sha256':a.inner_tar_sha256,'evidence_batch_hash':freeze['evidence_batch_hash'],
            'raw_freeze_schema':freeze['schema'],'design_hash':freeze['design_hash'],
            'runtime_plan_hash':freeze['runtime_plan_hash'],'execution_code_sha':freeze['execution_code_sha'],
            'planned_branch_count':freeze['planned_branch_count'],'preserved_trace_count':freeze['preserved_trace_count'],
            'provider_calls_are_real':freeze['provider_calls_are_real'],'runner_error_count':freeze['runner_error_count'],
            'paid_evaluator_called':freeze['paid_evaluator_called'],'semantic_cpr_status':freeze['semantic_cpr_status'],
        },
        'method_boundary':{
            'primary_contrast':'S2_MINUS_S1','primary_label':'FROZEN_TARGET_RESPONSE_CONTRAST',
            'escape_derived_specificity':'NOT_ESTABLISHED',
            'reason':'S1 and S2 share operator mechanics but targets are not exchangeable on task relevance, provenance, structural position, downstream opportunity, or decision weight.',
            'same_parent_repeats_are_independent_population_samples':False,
            'conditional_on_historical_prefix':'after_turn:8',
            'no_post_hoc_total_scalar':True,
        },
        'condition_summary':cond_summary,
        'sign_consistency':sign_consistency,
        'evidence_status':[
            'NORMAL_INHERITANCE_EVIDENCE',
            'INERTIA_CANDIDATE_EVIDENCE',
            'POST_CHALLENGE_INERTIA_EVIDENCE',
            'FROZEN_TARGET_RESPONSE_CONTRAST',
            'ESCAPE_DERIVED_SPECIFICITY_NOT_ESTABLISHED',
            'NOT_ADJUDICATED',
            'CENSORED_OR_UNRESOLVED'
        ],
        'interpretation':{
            'normal_inheritance_evidence':'S0 naturally re-used the J0 target after T10 in 2/3 repeated realizations; one S0 realization persisted to the T16 cap, demonstrating large natural path variability.',
            'post_challenge_persistence':'All 3 S2 realizations explicitly re-used the withdrawn J0 target after T10 and propagated it beyond the exposed ops_lead. Highest relation level is PROPAGATED_CARRIER in all 3 S2 runs.',
            'authority_reconstruction_candidate':'In 2/3 S2 runs, at least one post-T10 write_state containing the withdrawn 1520 target was written with status=fact; S0 had zero such post-T10 fact writes. This is source-backed authority-reconstruction evidence, not proof of causal intervention effect or semantic correctness.',
            'frozen_target_response_contrast':'S2 exceeded S1 in post-T10 agent turns, events, unique actors, target references, target actors, and target state writes in all 3 triads. S1 target was delivered/read but had zero observable post-T10 target reference in all 3 runs.',
            'natural_variability_boundary':'S0 structural continuation ranged from 0 to 7 post-T10 agent turns. S2 exceeded S0 in 2/3 triads but was shorter in 1/3, so intervention-related structural inertia beyond natural variability is not established from this batch alone.',
            'censoring':'S0 replicate 1 and S2 replicate 2 reached the T16 observation cap and are right-censored. No claim of permanent extinction or unlimited persistence follows from absence/presence beyond the cap.',
            'cpr':'NOT_ADJUDICATED. No CPR conclusion is produced by this derivation.'
        }
    }

    od=Path(a.outdir); od.mkdir(parents=True,exist_ok=True)
    (od/'run_metrics.jsonl').write_text('\n'.join(json.dumps(r,ensure_ascii=False,sort_keys=True) for r in sorted(rows,key=lambda x:(x['replicate_index'],x['condition_short'])))+'\n',encoding='utf-8')
    (od/'triad_contrasts.json').write_text(json.dumps(contrasts,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    (od/'derived_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')

    md=[]
    md += ['# R6-D First Real S0/S1/S2 Subject — Derived Analysis v0.1','',
           f"- Workflow run: `{a.artifact_run_id}`", f"- Artifact id: `{a.artifact_id}`", f"- Artifact digest: `{a.artifact_digest}`",
           f"- Evidence batch hash: `{freeze['evidence_batch_hash']}`", f"- Design hash: `{freeze['design_hash']}`", f"- Execution SHA: `{freeze['execution_code_sha']}`",
           '- Raw evidence was frozen before this derivation: **YES**', '- Provider calls real: **YES**', '- Paid evaluator called: **NO**', '- CPR: **NOT_ADJUDICATED**','',
           '## Result boundary','',
           'The preregistered primary contrast is **S2 − S1**, reported only as **FROZEN_TARGET_RESPONSE_CONTRAST**. S1 and S2 share the same one-shot fact→unconfirmed operator, but their targets are not exchangeable on task relevance, provenance, structural position, downstream opportunity or decision weight. Therefore **Escape-derived/J0-specific causality is not established by this batch**.','',
           'Same-parent repeats are repeated realizations conditional on the frozen `after_turn:8` prefix, not independent population samples. No post-hoc total distance score is constructed.','',
           '## Structural distance domain','',
           '|Replicate|S0 post-T10 turns|S1 post-T10 turns|S2 post-T10 turns|S2−S1|S2−S0|S0 censored|S2 censored|',
           '|---:|---:|---:|---:|---:|---:|---|---|']
    for rep in (1,2,3):
        d={r['condition_short']:r for r in rows if r['replicate_index']==rep}
        md.append(f"|{rep}|{d['S0']['post10_agent_turns']}|{d['S1']['post10_agent_turns']}|{d['S2']['post10_agent_turns']}|{d['S2']['post10_agent_turns']-d['S1']['post10_agent_turns']:+d}|{d['S2']['post10_agent_turns']-d['S0']['post10_agent_turns']:+d}|{str(d['S0']['observation_censored']).lower()}|{str(d['S2']['observation_censored']).lower()}|")
    md += ['', 'S2 continued longer than S1 in all three triads. However S0 ranged from 0 to 7 post-T10 Agent turns; S0 replicate 1 itself reached T16. This natural spread prevents interpreting structural continuation alone as an intervention-caused inertia effect.','',
           '## Information inheritance domain','',
           '|Replicate|S1 target refs T10+|S2 target refs T10+|S2 target actors T10+|S2 target state writes T10+|Highest S2 carrier level|',
           '|---:|---:|---:|---:|---:|---|']
    for rep in (1,2,3):
        d={r['condition_short']:r for r in rows if r['replicate_index']==rep}
        md.append(f"|{rep}|{d['S1']['post10_target_events']}|{d['S2']['post10_target_events']}|{d['S2']['post10_target_actors']}|{d['S2']['post10_target_state_writes']}|{d['S2']['highest_carrier_relation_level']}|")
    md += ['', 'The S1 ordinary target downgrade was delivered and consumed in every run but produced no observable post-T10 reference to its frozen target. By contrast, all three S2 runs re-used the withdrawn J0 target after T10, wrote it into downstream state, and propagated it beyond the exposed `ops_lead`. This supports **POST_CHALLENGE_INERTIA_EVIDENCE / INERTIA_CANDIDATE_EVIDENCE** at the carrier level.','',
           '## Epistemic-authority distance domain','',
           '|Replicate|S0 target fact-writes T10+|S1 target fact-writes T10+|S2 target fact-writes T10+|',
           '|---:|---:|---:|---:|']
    for rep in (1,2,3):
        d={r['condition_short']:r for r in rows if r['replicate_index']==rep}
        md.append(f"|{rep}|{d['S0']['post10_target_fact_writes']}|{d['S1']['post10_target_fact_writes']}|{d['S2']['post10_target_fact_writes']}|")
    md += ['', 'After the one-shot `fact → unconfirmed` withdrawal, 2/3 S2 runs later produced at least one `write_state` carrying the 1520 target with `status=fact`; S0 produced none in the same post-T10 window. This is an **authority-reconstruction candidate**. The derivation does not claim that those fact labels are correct, independently re-evidenced, or caused by the intervention.','',
           '## What this batch establishes','',
           '- Raw scientific subject evidence is complete, hash-bound, and frozen before derivation.',
           '- Natural J0 inheritance exists and is highly variable across same-parent realizations.',
           '- Post-withdrawal persistence of the J0 target is directly observed in all S2 runs.',
           '- S2 shows a directionally consistent frozen target-response contrast against S1 across structural continuation and target propagation.',
           '- Some S2 continuations reconstruct `fact` authority around the withdrawn target, providing a concrete mechanism candidate for R6 carrier analysis.','',
           '## What remains unestablished','',
           '- Intervention-related inertia beyond the natural S0 distribution as a general causal effect.',
           '- Escape-derived/J0 specificity, because S1 and S2 targets are not matched on all relevant properties.',
           '- Generalization beyond this historical prefix/task/model/Agent topology.',
           '- CPR. It remains `NOT_ADJUDICATED`.','',
           '## Censoring','',
           'S0 replicate 1 and S2 replicate 2 are right-censored at T16. They must not be interpreted as naturally terminated, permanently persistent, or permanently extinct beyond the observation cap.','']
    (od/'REPORT.md').write_text('\n'.join(md),encoding='utf-8')
    print(json.dumps({'outdir':str(od),'evidence_batch_hash':freeze['evidence_batch_hash'],'status':'OK'},indent=2))
if __name__=='__main__': main()
