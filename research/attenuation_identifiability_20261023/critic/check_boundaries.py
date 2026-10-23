"""Analytic counterexamples only; no source arrays opened."""
import json
import math
from fractions import Fraction as F
from pathlib import Path

# Same means across all conditions. Only double heterogeneity differs.
m=1.
homogeneous_log=math.log(2)
double_log=math.log(3)/2
j_double=math.log1p(m)-double_log
mixed=double_log-homogeneous_log
assert abs(mixed+j_double)<1e-15
assert j_double>0

# Absolute target expression is additive:100 ->200,200 ->300.
# Constant100 background plus compositional closure makes CP effects nonadditive.
raw=[F(100),F(200),F(200),F(300)]
cp=[F(10000)*v/(v+100) for v in raw]
cp_mixed=cp[3]-cp[1]-cp[2]+cp[0]
assert raw[3]-raw[1]-raw[2]+raw[0]==0
assert cp_mixed==F(-2500,3)
out={'same_mean_biological_heterogeneity_example':{
         'm_all_groups':1,'double_cells':[0,2],'other_group_cells':[1,1],
         'mixed_log_mean':mixed,'J_double':j_double,
         'interpretation':'A pure Jensen contribution can reflect actual cell heterogeneity, not technical noise.'},
     'absolute_additive_closure_example':{
         'absolute_targets':[str(x) for x in raw],'background':'100',
         'CP_values':[str(x) for x in cp],'CP_mixed':str(cp_mixed),
         'J_all_conditions':'0',
         'interpretation':'Zero Jensen difference does not make CP/log nonadditivity an absolute biological interaction.'},
     'counterfactual_domain':{
         'nonnegative_not_sufficient':'Each coordinate1..103 equal100 passes nonnegative but totals10300>10000, impossible for a CP10K subset.',
         'negative_case':'m0=4, ma=mb=1 gives CPadd=-2; retain and flag, do not clip or select favorable pairs.'},
     'scope':'Analytic boundaries, not estimates of source attenuation causes.'}
root=Path(__file__).resolve().parents[3]
(root/'log/20261023/attenuation_identifiability/critic/BOUNDARIES.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out))
