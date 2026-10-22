"""Exact constructive rewrites and invariant counterexamples, not fitted biology."""
from fractions import Fraction as F
import hashlib,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'log/20261022/caf_mechanics_qualification'

def main():
    r0,r1,ymax,g,q,u=F(1,10),F(2,5),F(2),F(3,4),F(1,5),F(3,10)
    a=r1*ymax*g;identities=[]
    for r in [F(0),F(1,4),F(1,2),F(3,4),F(1)]:
        y=ymax*r*g;original=(r0+r1*y)*(1-r)-q*u*r
        riccati=r0+(a-r0-q*u)*r-a*r*r
        identities.append(dict(R=str(r),original=str(original),riccati=str(riccati),equal=original==riccati))
    recovered=1-.8*math.exp(-10)
    gain_forcing=F(2)*max(F(1,2)/F(1)-1,F(0))
    over=F(1,10)+F(2)*(F(1)-F(1,10))
    negative=F(1)+F(1,5)*(F(1)-F(1))-F(2)*F(1)
    grid=[]
    for k in [F(0),F(1,2),F(1)]:
        for loss in [F(0),F(1,2),F(1)]:
            for r in [F(0),F(1,4),F(1,2),F(3,4),F(1)]:
                nxt=r+k*(1-r)-loss*r
                grid.append(dict(k=str(k),loss=str(loss),R=str(r),next=str(nxt),bounded=0<=nxt<=1))
    checks=dict(agfr_exact_riccati_rewrite=all(r['equal'] for r in identities),restored_force_permitted_model_recovers_D=recovered>.9999,low_R_gain_forcing_is_zero=gain_forcing==0,discrete_over_reserve=over>1,discrete_negative_reserve=negative<0,corrected_grid_invariant=all(r['bounded'] for r in grid))
    result=dict(status='PASS' if all(checks.values()) else 'FAIL',checks=checks,agfr_identities=identities,restored_D_at_t10=recovered,low_R_gain_forcing=str(gain_forcing),overshoot=str(over),negative=str(negative),corrected_grid=grid,code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),biological_fits=0,assay_scalar_casts=0)
    with (P/'MECHANISM_AUDIT_RESULT.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
    print(json.dumps(dict(status=result['status'],checks=checks,agfr_equation='0.1+0.44R-0.6R^2',restored_D_at_t10=recovered,overshoot=str(over),negative=str(negative),corrected_grid_cases=len(grid))));assert all(checks.values())

if __name__=='__main__':main()
