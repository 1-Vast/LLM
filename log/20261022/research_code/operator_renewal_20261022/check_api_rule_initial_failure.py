"""Exact literal retention-rule falsifier; no biology or model fitting."""
from fractions import Fraction as Q
from itertools import product
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/operator_renewal/root'
API = OUT.parent / 'api_constructive'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = OUT / 'API_FALSIFIER_PROTOCOL.md'
    receipt = json.loads((API / 'RECEIPT.json').read_text(encoding='utf-8'))
    assert sha(API / 'RESPONSE.md') == receipt['response_sha256']
    bindings = [{'path': p.relative_to(ROOT).as_posix(), 'sha256': sha(p)} for p in (
        protocol, API / 'PROMPT.md', API / 'RESPONSE.md', API / 'RECEIPT.json', Path(__file__))]
    with (OUT / 'API_FALSIFIER_FREEZE.json').open('x', encoding='utf-8') as handle:
        json.dump({'utc': datetime.now(timezone.utc).isoformat(), 'files': bindings,
                   'before_synthetic_calculation': True}, handle, indent=2)

    rows = [(Q(artifact), Q(delta)) for artifact, delta in product((8, 10), (-1, 1))]
    mean_artifact = sum(a for a, _ in rows) / len(rows)
    mean_delta = sum(f for _, f in rows) / len(rows)
    covariance = sum((a - mean_artifact) * (f - mean_delta) for a, f in rows) / len(rows)
    retained, spent, no_spent = [0, 0, 0], [0, 0, 0], [0, 0, 0]
    trace = []
    for artifact, delta in rows:
        d = (Q(1, 10), Q(1, 5), artifact)
        # For three distinct coordinates, the upper quartile contains the
        # largest only under either usual interpolation or a top-ceil(n/4) rule.
        largest = max(range(3), key=d.__getitem__)
        gate = abs(delta) > 2 * Q(1, 10)
        if gate:
            no_spent[largest] = 1
            if not spent[largest]:
                retained[largest] = 1
                spent[largest] = 1
        trace.append({'artifact': str(artifact), 'delta': str(delta),
                      'gate': gate, 'retained_index': largest if gate else None})
    # For every reachable binary flag/weight combination w==spent and either
    # gate value, the flag changes no retained weight under the literal rule.
    flag_identities = 0
    for state in product((0, 1), repeat=3):
        for selected, gate in product(range(3), (False, True)):
            with_flag, without = list(state), list(state)
            if gate:
                without[selected] = 1
                if not state[selected]:
                    with_flag[selected] = 1
            assert with_flag == without
            flag_identities += 1
    checks = {
        'crossed_table_zero_covariance': covariance == 0,
        'crossed_table_exact_independence': all(rows.count((a, f)) == 1 for a, f in product((Q(8), Q(10)), (Q(-1), Q(1)))),
        'functional_gate_fires_every_time': all(row['gate'] for row in trace),
        'only_composition_artifact_retained': retained == [0, 0, 1],
        'spent_flag_same_weights_on_table': retained == no_spent,
        'all_48_reachable_flag_weight_identities': flag_identities == 48,
        'zero_initial_weights_zero_acquisition_scores': all(sum([0, 0, 0][k] * d for k, d in enumerate((Q(1, 10), Q(1, 5), a))) == 0 for a, _ in rows),
        'inverse_propensity_amplifies_lower_not_higher_survival': 1 / Q(3, 10) > 1 / Q(7, 10),
    }
    assert all(checks.values())
    result = {'kind': 'exact synthetic falsifier, not biological evidence', 'checks': checks,
        'all_passed': True, 'trace': trace, 'retained_weights': retained,
        'artifact_function_covariance': str(covariance), 'flag_identities': flag_identities,
        'decision': 'REJECT_API_COMPOSITION_GUARD_AND_CLAIMED_TOY_RESULT',
        'claim_scope': 'One explicit independent-artifact counterexample; no universal utility comparison or overfit theorem',
        'fits': 0, 'biological_scalar_reads': 0, 'code_sha256': sha(Path(__file__)),
        'freeze_sha256': sha(OUT / 'API_FALSIFIER_FREEZE.json')}
    with (OUT / 'API_FALSIFIER_RESULT.json').open('x', encoding='utf-8') as handle:
        json.dump(result, handle, indent=2)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
