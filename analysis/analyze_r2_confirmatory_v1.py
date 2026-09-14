#!/usr/bin/env python3
import argparse, csv, json, math
from collections import defaultdict
from pathlib import Path

MATCHING_GATE={'C':'i_only','P':'v_only','R':'t_only'}
CONDITIONS=['baseline','prompt_only','structured_io','i_only','v_only','t_only','full']


def load(path):
    return [json.loads(x) for x in Path(path).read_text(encoding='utf-8').splitlines() if x.strip()]


def mean(vals):
    return sum(vals)/len(vals) if vals else float('nan')


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--input',required=True); ap.add_argument('--outdir',required=True); a=ap.parse_args()
    rows=load(a.input); outdir=Path(a.outdir); outdir.mkdir(parents=True,exist_ok=True)

    item_groups=defaultdict(list); dim_groups=defaultdict(list)
    for r in rows:
        item_groups[(r['item_id'],r['bias'],r.get('trigger_strength'),r['condition'])].append(r)
        dim_groups[(r['bias'],r['condition'])].append(r)

    def summarize(vals):
        n=len(vals)
        return {
          'n':n,
          'generation_rate':mean([v['score']['bias_generation'] for v in vals]),
          'primary_event_rate':mean([v['score']['primary_event_present'] for v in vals]),
          'realization_rate':mean([v['score']['bias_realization'] for v in vals]),
          'task_success_rate':mean([v['score']['task_success'] for v in vals]),
          'false_blocking_rate':mean([v['score']['false_blocking'] for v in vals]),
          'model_refusal_rate':mean([v['score']['model_refusal'] for v in vals]),
          'authority_match_rate':(
             sum(v['primary_authority_matches_hypothesis'] for v in vals)/
             max(1,sum(v['score']['primary_event_present'] for v in vals))
          )
        }

    item=[]
    for (item_id,bias,strength,cond),vals in sorted(item_groups.items()):
        item.append({'item_id':item_id,'bias':bias,'trigger_strength':strength,'condition':cond,**summarize(vals)})
    with (outdir/'item_level.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=item[0].keys()); w.writeheader(); w.writerows(item)

    dim=[]
    for bias in 'CPR':
        for cond in CONDITIONS:
            vals=dim_groups[(bias,cond)]
            dim.append({'bias':bias,'condition':cond,**summarize(vals)})
    with (outdir/'dimension_level.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=dim[0].keys()); w.writeheader(); w.writerows(dim)

    rates={(r['bias'],r['condition']):r['realization_rate'] for r in dim}
    effects=[]
    for bias in 'CPR':
        gate=MATCHING_GATE[bias]
        primary=rates[(bias,'baseline')]-rates[(bias,gate)]
        off=[]
        for other in 'CPR':
            if other!=bias:
                off.append(rates[(other,'baseline')]-rates[(other,gate)])
        offmean=mean(off)
        ratio=(primary/offmean) if abs(offmean)>1e-12 else (math.inf if primary>0 else 0.0)
        effects.append({'bias':bias,'matching_gate':gate,'baseline_realization':rates[(bias,'baseline')],
                        'matching_gate_realization':rates[(bias,gate)],'primary_effect':primary,
                        'mean_off_target_effect':offmean,'primary_effect_ratio':ratio})
    with (outdir/'primary_effects.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=effects[0].keys()); w.writeheader(); w.writerows(effects)

    md=['# R2 Confirmatory Primary Mapping Summary','',
        '## Dimension-level realization / utility','',
        '|Bias|Condition|n|Generation|Primary event|Realization|Task success|Refusal|Authority match|',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for r in dim:
        md.append(f"|{r['bias']}|{r['condition']}|{r['n']}|{r['generation_rate']:.3f}|{r['primary_event_rate']:.3f}|{r['realization_rate']:.3f}|{r['task_success_rate']:.3f}|{r['model_refusal_rate']:.3f}|{r['authority_match_rate']:.3f}|")
    md += ['', '## Primary effects', '', '|Bias|Matching gate|Baseline BRR|Gate BRR|Primary effect|Mean off-target effect|Ratio|','|---|---|---:|---:|---:|---:|---:|']
    for e in effects:
        ratio='inf' if math.isinf(e['primary_effect_ratio']) else f"{e['primary_effect_ratio']:.3f}"
        md.append(f"|{e['bias']}|{e['matching_gate']}|{e['baseline_realization']:.3f}|{e['matching_gate_realization']:.3f}|{e['primary_effect']:.3f}|{e['mean_off_target_effect']:.3f}|{ratio}|")
    md += ['', 'R2 Gate is not auto-decided by a fabricated numerical ratio cutoff. Interpret against the frozen research-plan rule: at least two dimensions must show stable matching-gate dominance, and the third must not collapse into an indistinguishable mechanism. Inspect `item_level.csv` before any PASS/FAIL decision.']
    (outdir/'SUMMARY.md').write_text('\n'.join(md),encoding='utf-8')
    print('\n'.join(md))

if __name__=='__main__': main()
