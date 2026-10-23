"""Exact checks of proposal formulas; no biological or learned model inputs."""
from fractions import Fraction as F
from pathlib import Path
import json
root=Path('D:/MAESTRO/log/20261022/contrast_mechanism_scout')
records=[]
for scale in [F(1),F(1,10**12)]:
    raw=[scale,2*scale,3*scale]
    norm=[v/sum(raw) for v in raw]
    assert sum(norm)==1
    records.append(dict(raw_total=str(sum(raw)),normalized_total=str(sum(norm)),weights=list(map(str,norm))))
assert records[0]['weights']==records[1]['weights']
# Negative coefficients do not imply a unique negative-direction update.
g=[F(1),F(2),F(3)]
signed=[F(-1,10),F(6,10),F(5,10)]
convex=[F(0),F(4,10),F(6,10)]
assert sum(signed)==sum(convex)==1
assert sum(x*y for x,y in zip(g,signed))==sum(x*y for x,y in zip(g,convex))==F(13,5)
out=dict(scope='EXACT_ALGEBRA_ONLY',support_gate_examples=records,
         negative_coefficient_equivalent_convex_update='13/5',checks_passed=5,
         limitations='Does not deny signed updates outside a convex hull for other independent directions. No biological information or performance follows.')
(root/'ALGEBRA_RESULT.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out,indent=2))
