from fractions import Fraction as F
from pathlib import Path
import json
out=Path('D:/MAESTRO/log/20261022/native_operation/biology')
# Synthetic witness only: no numerical biological files are read.
def survival(e,m,c):return F(1)-e*m*c
base=survival(F(1),F(1),F(1));escape=survival(F(1),F(1),F(0))
u,i,c=F(100),F(80),F(40)
checks={
 'same_MHC_different_contact_has_different_survival':base!=escape,
 'no_effector_erases_contact_difference':survival(F(0),F(1),F(1))==survival(F(0),F(1),F(0)),
 'full_information_direct_interaction_exactly_matches_world':all(survival(F(e),F(m),F(k))==1-F(e*m*k) for e in (0,1) for m in (0,1) for k in (0,1)),
 'common_denominator_contrast_is_algebraically_redundant':(c/u)/(i/u)==c/i,
 'shared_normalizer_does_not_make_new_action':len({(c/u),(i/u),(c/i)})==3 and (c/i)*(i/u)==c/u
}
assert all(checks.values())
result={'kind':'exact synthetic algebra, not biological performance','checks':checks,'all_passed':all(checks.values()),'witness_survival':{'intact_contact':str(base),'lost_contact':str(escape)},'limits':['No claim that real killing is deterministic or binary.','No claim MAGeCK scores or independently normalized published contrasts obey the raw-ratio identity.','No claim of direct-model impossibility with equal full inputs.']}
(out/'algebra_result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
