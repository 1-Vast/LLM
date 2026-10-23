from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path

root=Path('D:/MAESTRO');p=root/'log/20261023/functional_mechanism_frontier'
r=json.loads((p/'OPERATION_RESULT.json').read_text(encoding='utf-8'))
f=json.loads((p/'OPERATION_FREEZE.json').read_text(encoding='utf-8'))
hash_checks={path:hashlib.sha256((root/path).read_bytes()).hexdigest()==expected for path,expected in f['files'].items()}
# Independent scalar reconstruction, not import of any root/author implementation.
assert Q(r['fullspan']['remaining_squared_error'])==(Q(0)-Q(1))**2
before=Q(1,10);after=Q(2)*before;competitor=Q(3,20)
assert before<competitor<after
assert [Q(r['drift'][k]) for k in ['before','after','competitor']]==[before,after,competitor]
# Complete the square: (d-1)^2+2d^2=3(d-1/3)^2+2/3.
d=Q(1,3);assert 3*d*d-2*d+1==Q(2,3)
assert Q(r['soft_previous']['unique_minimizer'])==d and Q(r['soft_previous']['hessian'])==6
key=Q(1,20);cov=key**2;cutoff=Q(1,100)
assert cov==Q(r['approximate_null']['covariance'])<cutoff and key==Q(r['approximate_null']['output_drift'])
assert all(hash_checks.values())
out={'status':'PASS','freeze_files':len(hash_checks),'hash_checks':hash_checks,'executed':'Independent Fraction arithmetic and SHA256 only','scope':'No root script import/rerun, SVD, author/model code, biological outcomes or replication'}
(p/'constructive/OPERATION_AUDIT.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out,indent=2))
