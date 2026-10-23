"""Independent high-precision arithmetic/KKT check; no root model imports/reruns."""
from decimal import Decimal, localcontext
from pathlib import Path
import hashlib
import json

OUT = Path('log/20261023/action_rule_search/constructive')
SOURCE = Path('log/20261023/action_rule_search/API_FALSIFIER.json')
saved = json.loads(SOURCE.read_text(encoding='utf-8'))
comparisons=[]
max_error=Decimal(0)

def check(label, reference, value):
    global max_error
    error=abs(Decimal(str(value))-reference)
    assert error < Decimal('1e-12'), (label, str(error))
    max_error=max(max_error,error)
    comparisons.append({'label':label,'decimal_reference':str(reference),'saved':value,'absolute_error':str(error)})

with localcontext() as ctx:
    ctx.prec=60
    D=Decimal
    errors=[]
    for item in saved['n_cases']+[saved['unit_converted_n100']]:
        converted='n' not in item
        n=D(100 if converted else item['n'])
        scale=D(10 if converted else 1)
        p=scale
        r=scale/D(2)
        variance=scale*scale
        tau=variance/n
        bound=(2*variance*D(20).ln()/n).sqrt()
        # Complete square: A*(delta-center)^2 + constant.
        A=p*p+tau
        center=p*r/A
        endpoints=[-bound,bound]
        candidates=endpoints+([center] if -bound<=center<=bound else [])
        optimum=min(candidates,key=lambda z:A*(z-center)**2)
        objective=(r-p*optimum)**2+tau*optimum**2
        derivative=2*A*(optimum-center)
        if optimum==bound:
            assert derivative<=0
        elif optimum==-bound:
            assert derivative>=0
        else:
            assert abs(derivative)<D('1e-50')
        prefix='converted' if converted else f'n{int(n)}'
        for key,reference in [('tau',tau),('bound',bound),('unbounded_ridge',center),('delta',optimum),('prediction',p*optimum),('bounded_ridge_objective',objective)]:
            check(prefix+'.'+key,reference,item[key])
        if converted:
            check(prefix+'.prediction_in_original_units',optimum,item['prediction_in_original_units'])
            converted_delta=optimum
        else:
            squared_error=(D('.5')-optimum)**2
            check(prefix+'.api_squared_error',squared_error,item['api_squared_error'])
            check(prefix+'.unbounded_ridge_squared_error',(D('.5')-center)**2,item['unbounded_ridge_squared_error'])
            errors.append(squared_error)
            if n==100: first_delta=optimum
    check('dimensionless_coefficient_change',abs(converted_delta-first_delta),saved['dimensionless_coefficient_change'])
    assert errors[0]<errors[1]<errors[2]

result={'status':'PASS_INDEPENDENT_DECIMAL_KKT','source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'arithmetic_checks':len(comparisons),'max_saved_difference':str(max_error),'checks':comparisons,'scope':'reconstructs saved deterministic cases with 60-digit Decimal and completed-square KKT; no root code import, predictive fit or biological values','root_supplied_test_directions':True}
(OUT/'RESULT_ARITHMETIC.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='checks'},indent=2))
