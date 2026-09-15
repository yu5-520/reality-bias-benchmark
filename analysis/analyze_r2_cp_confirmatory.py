#!/usr/bin/env python3
import argparse,csv,json,math
from collections import defaultdict
from pathlib import Path

CONDITIONS=['baseline','prompt_only','structured_io','i_only','v_only','t_only','full']
MATCH={'C':'i_only','P':'v_only'}


def mean(xs):return sum(xs)/len(xs) if xs else float('nan')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--input',required=True);ap.add_argument('--outdir',required=True);a=ap.parse_args()
    rows=[json.loads(x) for x in Path(a.input).read_text(encoding='utf-8').splitlines() if x.strip()]
    od=Path(a.outdir);od.mkdir(parents=True,exist_ok=True)
    groups=defaultdict(list); items=defaultdict(list)
    for r in rows:
        groups[(r['bias'],r['condition'])].append(r)
        items[(r['bias'],r['item_id'],r['trigger_strength'],r['condition'])].append(r)

    def summ(vals):
        n=len(vals);events=sum(v['score']['primary_event_present'] for v in vals)
        return {
          'n':n,
          'generation_rate':mean([v['score']['bias_generation'] for v in vals]),
          'primary_event_rate':mean([v['score']['primary_event_present'] for v in vals]),
          'realization_rate':mean([v['score']['bias_realization'] for v in vals]),
          'task_success_rate':mean([v['score']['task_success'] for v in vals]),
          'refusal_rate':mean([v['score']['model_refusal'] for v in vals]),
          'authority_match_rate':sum(v['primary_authority_matches_hypothesis'] for v in vals)/max(1,events),
        }

    dim=[]
    for b in ('C','P'):
        for c in CONDITIONS:dim.append({'bias':b,'condition':c,**summ(groups[(b,c)])})
    with (od/'dimension_level.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=dim[0].keys());w.writeheader();w.writerows(dim)

    itemrows=[]
    for (b,i,s,c),vals in sorted(items.items()):itemrows.append({'bias':b,'item_id':i,'trigger_strength':s,'condition':c,**summ(vals)})
    with (od/'item_level.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=itemrows[0].keys());w.writeheader();w.writerows(itemrows)

    rates={(x['bias'],x['condition']):x['realization_rate'] for x in dim}
    effects=[]
    for b in ('C','P'):
        gate=MATCH[b]; other='P' if b=='C' else 'C'
        pe=rates[(b,'baseline')]-rates[(b,gate)]
        off=rates[(other,'baseline')]-rates[(other,gate)]
        ratio=math.inf if abs(off)<1e-12 and pe>0 else (pe/off if abs(off)>=1e-12 else 0.0)
        effects.append({'bias':b,'matching_gate':gate,'baseline_realization':rates[(b,'baseline')],'matching_gate_realization':rates[(b,gate)],'primary_effect':pe,'off_target_effect':off,'primary_effect_ratio':ratio})
    with (od/'primary_effects.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=effects[0].keys());w.writeheader();w.writerows(effects)

    unique={r['shared_trace_id'] for r in rows}
    md=['# R2 Partial Confirmatory Mapping — Frozen C/P Families','',
        f'- Condition cells: {len(rows)}',f'- Unique API traces: {len(unique)}','',
        '|Bias|Condition|n|Generation|Primary event|Realization|Task success|Refusal|Authority match|',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for x in dim:
        md.append(f"|{x['bias']}|{x['condition']}|{x['n']}|{x['generation_rate']:.3f}|{x['primary_event_rate']:.3f}|{x['realization_rate']:.3f}|{x['task_success_rate']:.3f}|{x['refusal_rate']:.3f}|{x['authority_match_rate']:.3f}|")
    md += ['','## Matching-gate effects','', '|Bias|Gate|Baseline BRR|Gate BRR|Primary effect|Off-target effect|Ratio|','|---|---|---:|---:|---:|---:|---:|']
    for e in effects:
        ratio='inf' if math.isinf(e['primary_effect_ratio']) else f"{e['primary_effect_ratio']:.3f}"
        md.append(f"|{e['bias']}|{e['matching_gate']}|{e['baseline_realization']:.3f}|{e['matching_gate_realization']:.3f}|{e['primary_effect']:.3f}|{e['off_target_effect']:.3f}|{ratio}|")
    md += ['','This is a partial confirmatory test for the already calibrated C/I and P/V families. It cannot by itself produce an overall R2 PASS because the R dimension is under stateful micro-workflow investigation.']
    (od/'SUMMARY.md').write_text('\n'.join(md),encoding='utf-8');print('\n'.join(md))

if __name__=='__main__':main()
