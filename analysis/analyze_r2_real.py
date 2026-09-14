#!/usr/bin/env python3
import argparse, csv, json, math, statistics
from collections import defaultdict
from pathlib import Path

def wilson(k,n,z=1.96):
    if n == 0: return (float('nan'), float('nan'))
    p=k/n; d=1+z*z/n
    c=(p+z*z/(2*n))/d
    h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return max(0,c-h), min(1,c+h)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--input',required=True); ap.add_argument('--outdir',required=True); args=ap.parse_args()
    rows=[json.loads(x) for x in Path(args.input).read_text(encoding='utf-8').splitlines() if x.strip()]
    out=Path(args.outdir); out.mkdir(parents=True,exist_ok=True)

    grouped=defaultdict(list)
    item_grouped=defaultdict(list)
    total_cost_min=total_cost_max=0.0
    for r in rows:
        grouped[(r['bias'],r['condition'])].append(r)
        item_grouped[(r['item_id'],r['condition'])].append(r)
        total_cost_min += r.get('cost_estimate_usd',{}).get('off_peak_usd',0) or 0
        total_cost_max += r.get('cost_estimate_usd',{}).get('peak_usd',0) or 0

    def metrics(rs):
        n=len(rs)
        vals={k:sum(x['score'][k] for x in rs) for k in ['bias_generation','attempted_promotion','bias_realization','task_success','false_blocking','model_refusal']}
        br_lo,br_hi=wilson(vals['bias_realization'],n)
        return {
            'n':n,
            **{k+'_rate':vals[k]/n for k in vals},
            'bias_realization_ci95_low':br_lo,
            'bias_realization_ci95_high':br_hi,
            'mean_evaluator_confidence':statistics.mean(float(x.get('evaluator',{}).get('confidence',0) or 0) for x in rs)
        }

    dim=[]
    for (b,c),rs in sorted(grouped.items()): dim.append({'bias':b,'condition':c,**metrics(rs)})
    item=[]
    for (iid,c),rs in sorted(item_grouped.items()): item.append({'item_id':iid,'bias':rs[0]['bias'],'trigger_strength':rs[0].get('trigger_strength'),'condition':c,**metrics(rs)})

    for name,data in [('dimension_level.csv',dim),('item_level.csv',item)]:
        with (out/name).open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=data[0].keys()); w.writeheader(); w.writerows(data)

    rate={(x['bias'],x['condition']):x['bias_realization_rate'] for x in dim}
    mapping={'C':'i_only','P':'v_only','R':'t_only'}
    lines=['# R2 Wave 1 Summary','',f'Runs analyzed: **{len(rows)}**',f'Estimated API cost range from frozen DeepSeek pricing snapshot: **${total_cost_min:.4f}–${total_cost_max:.4f} USD**','']
    for b,cond in mapping.items():
        base=rate.get((b,'baseline'),float('nan')); match=rate.get((b,cond),float('nan'))
        eff=base-match
        off=[]
        for other in 'CPR':
            if other != b and (other,'baseline') in rate and (other,cond) in rate:
                off.append(rate[(other,'baseline')]-rate[(other,cond)])
        offavg=sum(off)/len(off) if off else float('nan')
        lines.append(f'- **{b}**: baseline BRR={base:.3f}; matching gate BRR={match:.3f}; matching effect={eff:.3f}; mean off-target effect={offavg:.3f}')
    lines += ['', '## Interpretation guardrail', 'This file reports descriptive Wave 1 results only. R2 PASS/FAIL requires inspection of item-level distributions, confidence intervals, evaluator/manual-adjudication agreement, and utility endpoints.']
    (out/'SUMMARY.md').write_text('\n'.join(lines),encoding='utf-8')

if __name__=='__main__': main()
