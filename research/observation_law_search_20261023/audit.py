"""Verify saved arithmetic and seals without rerunning experiments."""
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/observation_law_search'


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            result.update(chunk)
    return result.hexdigest()


def main():
    checks = []
    def check_seal(relative):
        payload = json.loads((ROOT / relative).read_text(encoding='utf-8'))
        entries = payload.get('files', payload.get('sha256', {}))
        if not entries and all(isinstance(v, str) and len(v) == 64 for v in payload.values()):
            entries = payload
        if isinstance(entries, list):
            entries = {row['path']: row['sha256'] for row in entries}
        for name, expected in entries.items():
            assert digest(ROOT / name) == expected, (relative, name)
        checks.append({'seal': relative, 'entries_verified': len(entries)})

    check_seal('log/20261023/mixed_feedback_estimator/VERIFICATION.json')
    check_seal('log/20261023/observation_law_search/ROOT_FREEZE.json')
    for role in ['biology', 'constructive', 'frontier']:
        # First and result seals have differing schemas; both maps and lists are supported.
        for path in sorted((OUT / role).glob('*.json')):
            payload = json.loads(path.read_text(encoding='utf-8'))
            if 'seal' in path.name.lower():
                if ('files' in payload or isinstance(payload.get('sha256'), dict) or
                    all(isinstance(v, str) and len(v) == 64 for v in payload.values())):
                    check_seal(path.relative_to(ROOT).as_posix())
                if 'cross_sha256' in payload:
                    cross_name = 'RESULT_CROSS.md' if path.name.startswith('RESULT_') else 'CROSS.md'
                    assert digest(path.parent / cross_name) == payload['cross_sha256']
                    checks.append({'cross_seal': path.relative_to(ROOT).as_posix(),
                                   'cross_digest_verified': True})
    capture = json.loads((OUT / 'biology/WITNESS.json').read_text(encoding='utf-8'))
    for world, actions in capture['worlds_survival_capture'].items():
        for action, (survival, inclusion) in actions.items():
            assert Fraction(survival)*Fraction(inclusion) == Fraction(1, 10)
    assert capture['best_tumor_killing_intervention'] == {'A': 'V', 'B': 'U'}

    saved = json.loads((OUT / 'SNAPSHOT_WITNESS.json').read_text(encoding='utf-8'))
    assert saved['status'] == 'PASS_SYNTHETIC_ONLY'
    for row in saved['time_dependent']:
        expected = math.expm1(-row['diffusivity'])/row['diffusivity']
        assert abs(expected-row['analytic_shift']) < 1e-12
        assert abs(expected-row['numerical_shift']) < 1e-8
        assert row['max_pde_residual'] < 1e-12
    for row in saved['autonomous']:
        k, omega = .25, row['omega']
        denominator = k*k+omega*omega
        cosine_integral = (k+math.exp(-k)*(-k*math.cos(omega)+omega*math.sin(omega)))/denominator
        sine_integral = (omega+math.exp(-k)*(-k*math.sin(omega)-omega*math.cos(omega)))/denominator
        covariance = .4+.6*math.exp(-.5)
        means = {'A': [-cosine_integral, -sine_integral], 'B': [sine_integral, -cosine_integral]}
        harms = {}
        for name, expected_mean in means.items():
            action = row['actions'][name]
            for index, expected in enumerate(expected_mean):
                assert abs(expected-action['analytic_mean_T'][index]) < 1e-12
                assert abs(expected-action['numeric_mean_T'][index]) < 1e-8
            harms[name] = math.exp(.1)*.5*math.erfc(-expected_mean[0]/math.sqrt(2*covariance))
            assert abs(harms[name]-action['absolute_tail_harm']) < 1e-12
        assert min(harms, key=harms.get) == row['preferred_action']
        assert row['max_pde_residual'] < 1e-12
    result = {'status': 'PASS_LOCAL', 'utc': datetime.now(timezone.utc).isoformat(),
              'checks': checks, 'arithmetic': 'capture thinning, two temporal shifts, four force responses/tails',
              'experiment_reruns': 0, 'biological_values_read': 0,
              'limitation': 'Local continuity/arithmetic, not historical global provenance repair or biological replication.'}
    (OUT / 'AUDIT.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
