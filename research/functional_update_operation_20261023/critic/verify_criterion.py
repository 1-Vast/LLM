"""Independent four-world rational reconstruction; never imports root fitter."""
from fractions import Fraction as F
from pathlib import Path
import hashlib
import json

root = Path('D:/MAESTRO')
folder = root / 'log/20261023/functional_update_operation'
freeze = json.loads((folder / 'CRITERION_FREEZE.json').read_text(encoding='utf-8-sig'))
bindings = []
for path, wanted in freeze['files'].items():
    actual = hashlib.sha256((root / path).read_bytes()).hexdigest()
    bindings.append({'path': path, 'expected': wanted, 'actual': actual, 'pass': actual == wanted})
assert all(x['pass'] for x in bindings)
worlds = [(F(r), F(s), F(3, 5)*r*s) for r in (-1, 1) for s in (-1, 1)]
means = {str(r): sum(y for rr, s, y in worlds if rr == r)/2 for r in (F(-1), F(1))}
def risk(predict):
    return sum((predict(r, s)-y)**2 for r, s, y in worlds)/4
calculated = {
    'amplitude': str(F(3, 5)),
    'ordinary_known_sign_mse': str(risk(lambda r, s: F(3, 5)*r*s)),
    'no_update_mse': str(risk(lambda r, s: F(0))),
    'fixed_positive_hidden_sign_mse': str(risk(lambda r, s: F(3, 5)*r)),
    'conditional_hidden_query_mean': {k: str(v) for k, v in means.items()},
    'best_hidden_sign_mse': str(risk(lambda r, s: means[str(r)])),
}
stored = json.loads((folder / 'CRITERION_RESULT.json').read_text())
agreement = {k: stored[k] == value for k, value in calculated.items()}
assert all(agreement.values())
output = {'scope': 'Exact arithmetic and byte hashes only; no biological fit',
          'freeze_bindings': bindings,
          'four_worlds': [{'r': str(r), 'sign': str(s), 'query': str(y)} for r, s, y in worlds],
          'calculated': calculated, 'result_agreement': agreement,
          'root_code_imported_or_run': False,
          'identity': 'Average over hidden sign of (b(r)*r - (3/5)*sign*r)^2 = b(r)^2 + 9/25 for each r.'}
(folder/'critic/CRITERION_INDEPENDENT_CHECK.json').write_text(json.dumps(output, indent=2), encoding='utf-8')
print(json.dumps({'freeze_pass': len(bindings), 'fields_agree': len(agreement), 'calculated': calculated}, indent=2))
