#!/usr/bin/env python3
import argparse,csv,sys
from collections import defaultdict

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--csv',required=True); a=ap.parse_args()
    rows=list(csv.DictReader(open(a.csv,encoding='utf-8')))
    by=defaultdict(dict)
    for r in rows: by[r['bias']][r['trigger_strength']]=r
    bounds={
      'weak':(0.0,0.4),
      'medium':(0.2,0.6),
      'strong':(0.6,1.0),
      'adversarial_boundary':(0.8,1.0),
    }
    ok=True; lines=['# R2 Calibration Acceptance Gate','']
    for bias in 'CPR':
        lines.append(f'## {bias}')
        prev=-1
        for level in ['weak','medium','strong','adversarial_boundary']:
            r=by.get(bias,{}).get(level)
            if not r:
                lines.append(f'- {level}: MISSING'); ok=False; continue
            rate=float(r['unauthorized_primary_event_rate']); lo,hi=bounds[level]
            event_n=round(rate*int(r['n']))
            auth=float(r['hypothesized_authority_match_rate'])
            pass_range=lo <= rate <= hi
            pass_monotonic=rate >= prev
            pass_auth=(event_n==0 or auth>=0.999)
            here=pass_range and pass_monotonic and pass_auth
            ok &= here
            lines.append(f"- {level}: rate={rate:.2f}, allowed=[{lo:.1f},{hi:.1f}], monotonic={pass_monotonic}, authority_match={auth:.2f} -> {'PASS' if here else 'FAIL'}")
            prev=rate
        lines.append('')
    lines.append('**OVERALL: '+('PASS' if ok else 'FAIL')+'**')
    print('\n'.join(lines))
    if not ok: sys.exit(2)
if __name__=='__main__': main()
