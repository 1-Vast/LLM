"""Independent primal/dual one-anchor audit on exact designed measures."""
from datetime import datetime, timezone
from fractions import Fraction as Q
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/operator_renewal/root'
LOG = OUT.parent / 'functional'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def law(first, second, upper=False):
    if upper:
        x = (first - second) / (1 - first)
        mass = (1 - first) / (1 - x)
        return [(x, mass), (Q(1), 1 - mass)]
    x = second / first
    mass = first / x
    return [(Q(0), 1 - mass), (x, mass)]


def m(distribution, order):
    return sum(p * x**order for x, p in distribution)


def interval(firsts, ratios):
    return (max(a*a/r for a, r in zip(firsts, ratios)),
            min(a/r for a, r in zip(firsts, ratios)))


def main():
    files = [OUT / 'FUNCTIONAL_AUDIT_PROTOCOL.md', LOG / 'INDEPENDENT_ORIGINAL.md',
             LOG / 'INDEPENDENT_SEAL.json', LOG / 'synthetic_result.json', Path(__file__)]
    with (OUT / 'FUNCTIONAL_AUDIT_FREEZE.json').open('x', encoding='utf-8') as handle:
        json.dump({'utc': datetime.now(timezone.utc).isoformat(),
            'before_independent_calculation': True,
            'files': [{'path': p.relative_to(ROOT).as_posix(), 'sha256': sha(p)} for p in files]}, handle, indent=2)
    firsts = [Q(1, 2), Q(3, 5), Q(99, 100)]
    seconds = [Q(3, 8), Q(9, 25), Q(9801, 10000)]
    c1, c2 = sum(firsts)/3, sum(seconds)/3
    r1, r2 = [a/c1 for a in firsts], [s/c2 for s in seconds]
    checks = []

    def check(name, condition):
        checks.append({'name': name, 'passed': bool(condition)})
        assert condition, name

    def validate(distribution, a, s, label):
        check(label, sum(p for _, p in distribution) == 1
              and all(0 <= x <= 1 and 0 <= p <= 1 for x, p in distribution)
              and m(distribution, 1) == a and m(distribution, 2) == s)

    low, high = interval(firsts, r2)
    check('joint_pool_normalizations', sum(r1)/3 == sum(r2)/3 == 1)
    check('gauge_interval', (low, high) == (Q(5717, 10000), Q(5717, 9900)))
    measures = [law(a, r*high, upper=(index == 1))
                for index, (a, r) in enumerate(zip(firsts, r2))]
    for index, (distribution, a, r) in enumerate(zip(measures, firsts, r2)):
        validate(distribution, a, r*high, 'attaining_joint_law_' + str(index))
    check('same_pool_anchor_and_second_panel', sum(m(mu, 1) for mu in measures)/3 == c1
          and sum(m(mu, 2) for mu in measures)/3 == high)
    # Polynomial lower dual: x^4 >= 3b^2*x^2 - 2b^3*x.
    # Polynomial upper dual: x^4 <= q2*x^2 + q1*x + q0.
    b = r2[0]*high/firsts[0]
    a = (firsts[1] - r2[1]*high)/(1-firsts[1])
    q2, q1, q0 = 1+2*a+3*a*a, -2*a*(1+a)**2, a*a*(1+2*a)
    slope = 3*b*b*r2[0] - q2*r2[1]
    intercept = -2*b**3*firsts[0] - q1*firsts[1] - q0
    check('dual_slope_negative', slope < 0)
    gap = m(measures[0], 4) - m(measures[1], 4)
    check('joint_primal_attains_global_affine_dual', gap == slope*high + intercept and gap > 0)
    conservative = Q(27, 128) - Q(753, 5324)
    check('shared_gauge_tightening_is_strict', gap > conservative)
    # The symbolic nonnegative factorizations are the continuous-domain proof;
    # grid checks below only verify exact coefficient evaluation independently.
    for x in [Q(i, 11) for i in range(12)] + [a, b]:
        check('dual_identity_at_' + str(x),
              x**4-(3*b*b*x*x-2*b**3*x) == x*(x-b)**2*(x+2*b)
              and q2*x*x+q1*x+q0-x**4 == (1-x)*(x-a)**2*(x+1+2*a))
    stresses = []
    for scale in (Q(1), Q(3, 4), Q(1, 2)):
        trial_c1 = c1*scale
        means = [r*trial_c1 for r in r1]
        lo, hi = interval(means, r2)
        witnesses = []
        for step in range(21):
            gauge = lo + (hi-lo)*Q(step, 20)
            joint = [law(first, r*gauge, upper=(index == 1))
                     for index, (first, r) in enumerate(zip(means, r2))]
            for index, (mu, first, r) in enumerate(zip(joint, means, r2)):
                validate(mu, first, r*gauge, f'stress_{scale}_{step}_{index}')
            diff = m(joint[0], 4)-m(joint[1], 4)
            if diff < 0 and not witnesses:
                witnesses.append({'c2': str(gauge), 'A4_minus_B4': str(diff),
                    'laws': [[{'z': str(x), 'mass': str(p)} for x, p in mu] for mu in joint]})
        stresses.append({'anchor_scale': str(scale), 'c1': str(trial_c1),
                         'c2_interval': [str(lo), str(hi)], 'reverse_rank_witnesses': witnesses})
    check('true_anchor_no_reversal', not stresses[0]['reverse_rank_witnesses'])
    check('half_anchor_has_explicit_reversal', bool(stresses[2]['reverse_rank_witnesses']))
    result = {'kind': 'exact synthetic continuous-moment primal/dual audit',
        'all_passed': True, 'checks': checks,
        'sharp_shared_gauge_pair_gap': str(gap), 'conservative_original_gap': str(conservative),
        'dual_slope': str(slope), 'stresses': stresses,
        'scope': 'One fixture global continuous-moment optimum; no generic complexity or biological calibration claim',
        'new_biological_scalar_reads': 0, 'fits': 0, 'code_sha256': sha(Path(__file__)),
        'freeze_sha256': sha(OUT / 'FUNCTIONAL_AUDIT_FREEZE.json')}
    with (OUT / 'FUNCTIONAL_AUDIT_RESULT.json').open('x', encoding='utf-8') as handle:
        json.dump(result, handle, indent=2)
    print(json.dumps({k: v for k, v in result.items() if k != 'checks'}))


if __name__ == '__main__':
    main()
