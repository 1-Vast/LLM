"""Independent derivative proof and retained-law check of root's synthetic audit."""
from fractions import Fraction as F
from pathlib import Path
import json

base = Path('D:/MAESTRO/log/20261022/operator_renewal')
root = json.loads((base/'root/FUNCTIONAL_AUDIT_RESULT.json').read_text())
m1 = [F(1,2), F(3,5), F(99,100)]
m2 = [F(3,8), F(9,25), F(9801,10000)]
c1, c2 = sum(m1)/3, sum(m2)/3
r1, r2 = [m/c1 for m in m1], [m/c2 for m in m2]
lo = max(a*a/r for a,r in zip(m1,r2))
hi = min(a/r for a,r in zip(m1,r2))

def lower(a,b):
    return b**3/a**2

def upper(a,b):
    d, t = a-b, 1-a
    return b-d*d/t-d**3/t**2

a, b, ri, rj = m1[0], m1[1], r2[0], r2[1]
d, t = b-rj*hi, 1-b
derivative_high = 3*ri**3*hi**2/a**2-rj*(1+2*d/t+3*d*d/t**2)
# Throughout the valid interval, f''=6 ri^3 c/a^2+2 rj^2/t
# +6 rj^2(b-rj*c)/t^2 >0. Thus f' is increasing and f'(hi)<0
# proves f is decreasing everywhere; its global minimum is at hi.
assert lo>0 and t>0 and b-rj*hi>=0
assert derivative_high<0
gap = lower(a,ri*hi)-upper(b,rj*hi)
assert gap==F(root['sharp_shared_gauge_pair_gap'])==F(10919,143748)
assert gap>F(root['conservative_original_gap'])>0
checks=4
stress_differences=[]
for stress in root['stresses']:
    for witness in stress['reverse_rank_witnesses']:
        gauge=F(witness['c2'])
        values=[]
        for index, law in enumerate(witness['laws']):
            pairs=[(F(atom['z']),F(atom['mass'])) for atom in law]
            assert sum(w for _,w in pairs)==1
            assert all(0<=z<=1 and 0<=w<=1 for z,w in pairs)
            first=sum(w*z for z,w in pairs)
            second=sum(w*z*z for z,w in pairs)
            assert first==r1[index]*F(stress['c1'])
            assert second==r2[index]*gauge
            values.append(sum(w*z**4 for z,w in pairs))
            checks+=4
        diff=values[0]-values[1]
        assert diff==F(witness['A4_minus_B4'])<0
        checks+=1
        stress_differences.append(dict(anchor_scale=stress['anchor_scale'],difference=str(diff)))
result=dict(assertions=checks, sharp_gap=str(gap), derivative_at_upper_endpoint=str(derivative_high),
            independent_proof='strictly increasing derivative negative at upper endpoint; all-point minimum follows',
            stress_differences=stress_differences,
            scope='exact designed fixture; hypothetical anchor shifts, not confidence intervals or biological uncertainty')
target=base/'frontier/ROOT_MOMENT_VERIFICATION.json'
if target.exists():
    raise FileExistsError(target)
target.write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
