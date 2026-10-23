"""Independent Decimal arithmetic audit of saved root scalar results; no rerun."""
from decimal import Decimal as D, getcontext
import hashlib,json
from pathlib import Path
getcontext().prec=60
root=Path('.')
out=Path('log/20261023/action_rule_search')
freeze=json.loads((out/'API_FREEZE.json').read_text(encoding='utf-8'))
for p,h in freeze['files'].items():
    assert hashlib.sha256((root/p).read_bytes()).hexdigest()==h
result=json.loads((out/'API_FALSIFIER.json').read_text(encoding='utf-8'))
errors=[]
for row in result['n_cases']:
    n=D(row['n']); radius=(D(2)*D(20).ln()/n).sqrt()
    ridge=D('.5')/(1+1/n)
    estimate=min(radius,ridge)
    for key,value in [('bound',radius),('unbounded_ridge',ridge),('delta',estimate),('api_squared_error',(D('.5')-estimate)**2)]:
        error=abs(D(str(row[key]))-value)
        assert error<D('1e-15')
        errors.append(float(error))
converted=result['unit_converted_n100']
bound=(D(2)*100*D(20).ln()/100).sqrt()
ridge=D(50)/101
assert ridge<bound
assert abs(D(str(converted['delta']))-ridge)<D('1e-15')
report=dict(status='PASS_SAVED_ARITHMETIC_AND_FREEZE',scope='Decimal reconstruction, not root model rerun or biological validation',root_frozen_files=len(freeze['files']),max_absolute_error=max(errors),saved_values_checked=len(errors)+1)
(out/'frontier'/'ROOT_API_AUDIT.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
