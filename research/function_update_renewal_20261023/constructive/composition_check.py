"""Finite composition identities, not a biological experiment."""
from pathlib import Path
import json
import numpy as np
rng=np.random.default_rng(1023)
d=5
A,B,DA,DB=[rng.normal(size=(d,d)) for _ in range(4)]
g,s=rng.normal(size=d),rng.normal(size=d)
f=lambda a,b:float(g@a@b@s)
frozen_head_error=abs(f(A,B)-g@(A@B@s))
one_edit_error=abs(f(A+DA,B)-(f(A,B)+g@DA@B@s))
two_exact=f(A+DA,B+DB)
two_linear=f(A,B)+g@DA@B@s+g@A@DB@s
cross=float(g@DA@DB@s)
assert frozen_head_error<1e-12 and one_edit_error<1e-12
assert abs((two_exact-two_linear)-cross)<1e-12 and abs(cross)>.01
result={'scope':'SYNTHETIC_FINITE_ALGEBRA_ONLY','frozen_head_global_identity_error':frozen_head_error,'single_operator_global_identity_error':one_edit_error,'two_operator_actual_minus_first_order':two_exact-two_linear,'exact_second_order_term':cross,'warning':'No global fixed-feature linear equivalence follows for simultaneous multi-operator updates; this does not establish unique expressivity versus direct nonlinear prediction or biological validity.','biological_reads':0,'fits':0}
Path('log/20261023/function_update_renewal/constructive/COMPOSITION_CHECK.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps(result,indent=2))
