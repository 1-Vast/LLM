"""Independent exact reconstruction; no root helper or biological data imports."""
from fractions import Fraction as F
import json
from pathlib import Path
out=Path('log/20261023/reusable_error_mechanism/source')
observations={'A':F(3,10),'B':F(-1)}
records=[]
for names in ['AB','BA']:
    threshold=F(0)
    trace=[]
    for name in names:
        old=threshold
        failure=int(observations[name]<0)
        success=int(observations[name]>=old)
        threshold=old+F(3,5)*(failure-success)
        trace.append({'name':name,'y':str(observations[name]),'old':str(old),
                      'failed':failure,'success':success,'new':str(threshold)})
    records.append({'order':names,'trace':trace,'final':str(threshold),
                    'accept_q_two_fifths':F(2,5)>=threshold})
actual={'records':records,'result':'FAIL_LITERAL_BATCH_ORDER_INVARIANCE',
        'biological_fits':0,'scope':'Exact independent supplied-witness audit; no claim about all online adaptation'}
parent=json.loads((out.parent/'MARGIN_CHECK.json').read_text(encoding='utf8'))
assert actual['records']==parent['records'] and actual['result']==parent['result']
(out/'MARGIN_AUDIT.json').write_text(json.dumps(actual,indent=2),encoding='utf8')
print(json.dumps(actual,indent=2))
