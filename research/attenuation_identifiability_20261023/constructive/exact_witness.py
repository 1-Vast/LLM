import json
import math
from fractions import Fraction as F
from pathlib import Path

# Exact pre-log ratios and normalized-coordinate contrasts, without data fitting.
x=a=b=F(1)
ratio=(1+x+a+b)*(1+x)/((1+x+a)*(1+x+b))
assert ratio==F(8,9) and ratio<1
raw=[(F(1),F(1)),(F(2),F(1)),(F(2),F(1)),(F(3),F(1))]
assert all(raw[3][i]-raw[1][i]-raw[2][i]+raw[0][i]==0 for i in range(2))
fractions=[u/(u+v) for u,v in raw]
mixed_cp=fractions[3]-fractions[1]-fractions[2]+fractions[0]
assert mixed_cp==F(-1,12)
# Jensen-only witness: all population means=1; double is a balanced 0/2 mixture.
j_double=math.log(2)-math.log(3)/2
mixed_log=math.log(3)/2-math.log(2)
assert abs(mixed_log+j_double)<1e-15 and j_double>0
# Persistent group-specific control bias across distinct technical strata.
c=F(2,5);single_a=single_b=double=F(1);control=F(1)+c
g=-(single_a-control+single_b-control)
r=double-single_a-single_b+control
assert g==2*c and r==c and r/g==F(1,2)
out={'status':'PASS','log_curvature':{'absolute_additive_ratio':str(ratio),'log_mixed':math.log(float(ratio))},
     'composition':{'absolute_pairs':[[str(t) for t in row] for row in raw],'normalized_mixed_fraction':str(mixed_cp),'CP10K_mixed':str(10000*mixed_cp)},
     'heterogeneity':{'equal_absolute_means':1,'double_distribution':[0,2],'mixed_log':mixed_log,'mixed_J':j_double},
     'systematic_control':{'c':str(c),'g':str(g),'r':str(r),'beta':str(r/g),'assumption':'persistent same systematic control bias across different gems, not same random error'},
     'scope':'Analytic identifiability counterexamples, no biological observations or fits'}
p=Path('D:/MAESTRO/log/20261023/attenuation_identifiability/constructive');p.mkdir(parents=True,exist_ok=True)
(p/'EXACT_WITNESS.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out,indent=2))
