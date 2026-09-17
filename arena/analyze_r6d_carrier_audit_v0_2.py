#!/usr/bin/env python3
import argparse, json, re
from pathlib import Path

S0='S0_NATURAL_REFERENCE'
S1='S1_MATCHED_OR_ORDINARY_FACTUAL_INFORMATION_DOWNGRADE'
S2='S2_J0_TARGETED_ESCAPE_DERIVED_AUTHORITY_WITHDRAWAL'
J0_KEY='inventory_stockout_assessment_v1'
J0_LOC='shared_state.inventory_stockout_assessment_v1.A.preliminary_stock'
S1_LOC='public_context.products.C.gross_margin_pct'

def load_jsonl(p): return [json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]
def nested(d,*ks):
    for k in ks:
        if not isinstance(d,dict) or k not in d: return None
        d=d[k]
    return d
def payload(mc):
    for m in mc.get('messages',[]):
        if m.get('role')=='user':
            try: return json.loads(m['content'])
            except Exception: return {}
    return {}
def text(obj): return json.dumps(obj,ensure_ascii=False,sort_keys=True).lower()
def has1520(obj): return re.search(r'(?<!\d)1520(?!\d)',text(obj)) is not None
def has35margin(obj):
    s=text(obj)
    return bool(re.search(r'(gross_margin_pct.{0,40}35|35(?:\.0)?%[^\n]{0,60}(margin|product c)|(?:product c|c margin)[^\n]{0,60}35(?:\.0)?%)',s))
def target_visible(p,cid):
    return nested(p,'shared_state',J0_KEY,'A','preliminary_stock')==1520 if cid in (S0,S2) else nested(p,'public_context','products','C','gross_margin_pct')==35
def annotation_visible(p,cid):
    loc=J0_LOC if cid==S2 else S1_LOC if cid==S1 else None
    return bool(loc and any(x.get('target_locator')==loc and x.get('epistemic_status')=='unconfirmed' for x in p.get('epistemic_annotations',[]) if isinstance(x,dict)))
def output_target(events,cid):
    return any(has1520(e.get('action',{})) for e in events) if cid in (S0,S2) else any(has35margin(e.get('action',{})) for e in events)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--traces',required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
    traces=load_jsonl(a.traces); out=[]
    for t in traces:
        cid=t['r6d_condition']['condition_id']; rep=t['r6d_condition']['replicate_index']; ev={e['event_index']:e for e in t['events']}; calls=[]
        for mc in t.get('model_calls',[]):
            turn=ev[mc['event_index_start']]['turn']
            if turn<9: continue
            p=payload(mc); es=[ev[i] for i in range(mc['event_index_start'],mc['event_index_end']+1) if i in ev]
            container_fact=nested(p,'shared_state_metadata',J0_KEY,'status')=='fact'
            target_fact_container=[]; unrelated_fact=[]
            for e in es:
                ac=e.get('action',{})
                if cid not in (S0,S2) or e['action_type']!='write_state' or not has1520(ac): continue
                if ac.get('key')==J0_KEY and ac.get('status')=='fact' and nested(ac,'value','A','preliminary_stock')==1520: target_fact_container.append(e['event_index'])
                elif ac.get('status')=='fact': unrelated_fact.append(e['event_index'])
            calls.append({'turn':turn,'actor':mc['agent_id'],'target_visible':target_visible(p,cid),'annotation_visible':annotation_visible(p,cid),'j0_container_fact':container_fact,'target_output':output_target(es,cid),'literal_unconfirmed_output':any('unconfirmed' in text(e.get('action',{})) for e in es),'target_container_fact_reassertion_events':target_fact_container,'unrelated_fact_container_carrying_target_events':unrelated_fact})
        t9=[x for x in calls if x['turn']==9]; post=[x for x in calls if x['turn']>=10]
        out.append({'replicate_index':rep,'condition_id':cid,'run_id':t['run_id'],'t9_annotation_visible':any(x['annotation_visible'] for x in t9),'t9_target_output_reference':any(x['target_output'] for x in t9),'t9_output_literal_unconfirmed':any(x['literal_unconfirmed_output'] for x in t9),'post_t9_call_count':len(post),'post_t9_target_visible_input_count':sum(x['target_visible'] for x in post),'post_t9_annotation_visible_input_count':sum(x['annotation_visible'] for x in post),'post_t9_j0_container_fact_input_count':sum(x['j0_container_fact'] for x in post),'post_t9_target_output_reference_call_count':sum(x['target_output'] for x in post),'post_t9_output_literal_unconfirmed_call_count':sum(x['literal_unconfirmed_output'] for x in post),'post_t9_cross_agent_target_output_actors':sorted({x['actor'] for x in post if x['actor']!='ops_lead' and x['target_output']}),'target_container_fact_reassertion_events':sorted({i for x in post for i in x['target_container_fact_reassertion_events']}),'unrelated_fact_container_carrying_target_events':sorted({i for x in post for i in x['unrelated_fact_container_carrying_target_events']}),'right_censored':bool(t['observation_censored']),'termination_reason':t['termination_reason']})
    out=sorted(out,key=lambda x:(x['replicate_index'],x['condition_id']))
    Path(a.out).write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'run_count':len(out),'output':a.out},indent=2))
if __name__=='__main__': main()
