from fractions import Fraction as F
from pathlib import Path
import json

checks=[]
def check(name, condition):
    assert condition, name
    checks.append(name)

def loss(c,r):
    return c*c+(1-r*c)**2

c=F(1,2)
check('stationarity',4*c-2==0)
check('correct_state_cost',loss(F(0),F(1))==1)
check('invented_state_cost',loss(c,F(1))==F(1,2))
check('objective_prefers_invented_difference',loss(c,F(1))<loss(F(0),F(1)))
check('invented_nonlinear_function',c*c==F(1,4))
family=[]
for n in [1,2,10,100]:
    x,r=F(1,n),F(n)
    check('inverse_exact_'+str(n),1-r*x==0)
    check('factual_error_'+str(n),loss(x,r)==F(1,n*n))
    family.append(dict(c=str(x),r=str(r),inverse_error='0',factual_error=str(x*x)))
out=dict(scope='exact synthetic example, not biology or novelty',checks=checks,fixed_inverse_optimum=str(c),fixed_inverse_loss=str(loss(c,F(1))),invented_squared_function=str(c*c),family=family)
Path('log/20261023/action_rule_search/frontier/FALSIFIER.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out,indent=2))
