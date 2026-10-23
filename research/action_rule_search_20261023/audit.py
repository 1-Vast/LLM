"""Audit saved scalar arithmetic, original seals and predecessor continuity."""
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/action_rule_search'


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1048576), b''):
            value.update(chunk)
    return value.hexdigest()


def entries(payload):
    result = payload.get('files', payload.get('sha256', {}))
    if isinstance(result, list):
        result = {row['path']: row['sha256'] for row in result}
    if isinstance(result, str) and isinstance(payload.get('file'), str):
        return {payload['file']: result}
    if not isinstance(result, dict):
        result = {}
    if not result and all(isinstance(v, str) and len(v) == 64 for v in payload.values()):
        result = payload
    return result


def main():
    verified = []
    seals = [ROOT/'log/20261023/observation_law_search/VERIFICATION.json', OUT/'API_FREEZE.json']
    seals += sorted(path for role in ['biology', 'constructive', 'frontier']
                    for path in (OUT/role).glob('*.json') if 'seal' in path.name.lower())
    for path in seals:
        payload = json.loads(path.read_text(encoding='utf-8'))
        bindings = entries(payload)
        for name, expected in bindings.items():
            bound_path = Path(name)
            if not bound_path.is_absolute():
                bound_path = (path.parent if len(bound_path.parts) == 1 else ROOT)/bound_path
            assert digest(bound_path) == expected, (path, name)
        if bindings:
            verified.append({'seal': path.relative_to(ROOT).as_posix(), 'files': len(bindings)})
    result = json.loads((OUT/'API_FALSIFIER.json').read_text(encoding='utf-8'))
    for row in result['n_cases']:
        n = row['n']
        bound = math.sqrt(2*math.log(20)/n)
        raw = float(Fraction(1, 2)/(1+Fraction(1, n)))
        assert abs(raw-row['unbounded_ridge']) < 1e-12
        assert abs(bound-row['bound']) < 1e-12
        assert abs((.5-min(raw, bound))**2-row['api_squared_error']) < 1e-12
    converted = result['unit_converted_n100']
    assert abs(converted['delta']-result['n_cases'][0]['unbounded_ridge']) < 1e-12
    assert abs(converted['prediction']/10-converted['prediction_in_original_units']) < 1e-12
    assert result['dimensionless_coefficient_change'] > .1
    witness = json.loads((OUT/'frontier/FALSIFIER.json').read_text(encoding='utf-8'))
    assert Fraction(witness['fixed_inverse_optimum']) == Fraction(1, 2)
    assert Fraction(witness['invented_squared_function']) == Fraction(1, 4)
    for row in witness['family']:
        c, inverse = Fraction(row['c']), Fraction(row['r'])
        assert inverse*c == 1
        assert Fraction(row['factual_error']) == c*c
    audit = {'status': 'PASS_LOCAL', 'utc': datetime.now(timezone.utc).isoformat(),
             'seals': verified, 'saved_arithmetic': 'scalar bounds, ridge, units and action-inverse witness',
             'biological_values_read': 0, 'experiment_reruns': 0,
             'scope': 'Local arithmetic/continuity; not global provenance repair or biological confirmation'}
    (OUT/'AUDIT.json').write_text(json.dumps(audit, indent=2), encoding='utf-8')
    print(json.dumps(audit, indent=2))


if __name__ == '__main__':
    main()
