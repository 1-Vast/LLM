"""Exact synthetic partial-trace improver credit and its ordinary counterpart."""
from fractions import Fraction as F
from pathlib import Path
import hashlib
import json
import platform
import sys


OUT = Path('log/20261022/operator_renewal/recursive')


def events():
    for theta in (0, 1):
        for z in (-1, 1):
            for w, prob in ((-1, F(1, 40)), (0, F(19, 20)), (1, F(1, 40))):
                mass = F(1, 4) * prob * (1 + (2 * theta - 1) * (F(z, 5) + F(w, 10)))
                yield {'theta': theta, 'z': z, 'w': w, 'mass': mass,
                       'reward': 1 + F(w, 2), 'score': F(4 * theta - 2)}


def moment(rows):
    mean = sum(p * x for p, x in rows)
    return {'mean': mean, 'variance': sum(p * (x - mean) ** 2 for p, x in rows)}


def conditional_score(rows, key, value):
    selected = [r for r in rows if key(r) == value]
    return sum(r['mass'] * r['score'] for r in selected) / sum(r['mass'] for r in selected)


def two_level(base, exact, probability, audit):
    # Conventional randomized multilevel/control-variate operation.
    return base + (exact - base) * F(audit) / probability


def main():
    rows = list(events())
    assert sum(r['mass'] for r in rows) == 1
    assert all(r['mass'] > 0 for r in rows)
    samples = {k: [] for k in ('genotype_es', 'full_paes', 'partial_trace', 'uniform_audit', 'adaptive_audit')}
    posterior_checks = 0
    conventional_checks = 0
    for r in rows:
        full_score = conditional_score(rows, lambda t: (t['z'], t['w']), (r['z'], r['w']))
        cheap_score = conditional_score(rows, lambda t: t['z'], r['z'])
        assert full_score == F(2 * r['z'], 5) + F(r['w'], 5)
        assert cheap_score == F(2 * r['z'], 5)
        posterior_checks += 2
        full, cheap = r['reward'] * full_score, r['reward'] * cheap_score
        samples['genotype_es'].append((r['mass'], r['reward'] * r['score']))
        samples['full_paes'].append((r['mass'], full))
        samples['partial_trace'].append((r['mass'], cheap))
        for name, a in (('uniform_audit', F(1, 10)),
                        ('adaptive_audit', F(1, 2) if r['reward'] != 1 else F(1, 100))):
            for audit, pa in ((0, 1 - a), (1, a)):
                # Independently written candidate formula; equality must hold per realization.
                candidate = cheap if not audit else (a * cheap + full - cheap) / a
                assert candidate == two_level(cheap, full, a, audit)
                conventional_checks += 1
                samples[name].append((r['mass'] * pa, candidate))
        r.update(full_score=full_score, cheap_score=cheap_score)
    summary = {k: moment(v) for k, v in samples.items()}
    # Direct derivative of E[R] with respect to Bernoulli probability p.
    reward_by_theta = [sum(2 * r['mass'] * r['reward'] for r in rows if r['theta'] == theta)
                       for theta in (0, 1)]
    derivative = reward_by_theta[1] - reward_by_theta[0]
    assert derivative == F(1, 200)
    assert summary['partial_trace']['mean'] == 0
    for name in ('genotype_es', 'full_paes', 'uniform_audit', 'adaptive_audit'):
        assert summary[name]['mean'] == derivative
    assert summary['full_paes']['variance'] < summary['genotype_es']['variance']
    assert summary['full_paes']['variance'] < summary['adaptive_audit']['variance'] < summary['uniform_audit']['variance']
    # Every method's identical fresh downstream model is represented by p=.5.
    # A single exact-mean update of p is only a synthetic expectation calculation.
    old_utility = sum(reward_by_theta) / 2
    update = F(1, 10)
    new_utilities = {name: old_utility + update * m['mean'] * derivative for name, m in summary.items()}
    expected_audits = {'uniform': F(1, 10), 'adaptive': F(69, 2000)}
    result = {
        'status': 'PASS_EXACT_SCOPED_CHECKS_NOT_BIOLOGICAL_VALIDATION',
        'events': len(rows), 'posterior_identities': posterior_checks,
        'pointwise_candidate_conventional_identities': conventional_checks,
        'true_derivative': derivative, 'moments': summary,
        'expected_exact_posterior_calls_per_trace': expected_audits,
        'source_update_step': update, 'common_fresh_start_p': F(1, 2),
        'old_expected_utility': old_utility, 'one_expected_update_utility': new_utilities,
        'cost_limits': 'Enumerated synthetic law; posterior cost ratios unmeasured. No equal-runtime superiority claimed. Adaptive audit rule is specified, not learned from independent source traces.',
        'git_head': 'ed2e360093d25e577ea02a5011d54d13b32ec8f1',
        'environment': {'python': sys.version, 'executable': sys.executable, 'platform': platform.platform()},
        'code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'random_seed': 'none: exhaustive rational enumeration',
    }
    dump = lambda x: str(x) if isinstance(x, F) else x
    (OUT / 'SYNTHETIC_TRACES.json').write_text(json.dumps(rows, default=dump, indent=2), encoding='utf-8')
    (OUT / 'CHECK_RESULT.json').write_text(json.dumps(result, default=dump, indent=2), encoding='utf-8')
    print(json.dumps(result, default=dump, indent=2))


if __name__ == '__main__':
    main()
