"""Independent attaining-measure audit of the peer's finite moment witness."""
from fractions import Fraction as Q
from pathlib import Path
import json
import hashlib


def moment(atoms, power):
    return sum(weight * point ** power for point, weight in atoms)


def extremizers(first, second):
    upper_node = (first - second) / (1 - first)
    upper_one_weight = (first - upper_node) / (1 - upper_node)
    return ([(Q(0), 1 - first * first / second), (second / first, first * first / second)],
            [(upper_node, 1 - upper_one_weight), (Q(1), upper_one_weight)])


def audit_atoms(atoms, first, second):
    assert sum(w for _, w in atoms) == 1
    assert all(0 <= x <= 1 and 0 <= w <= 1 for x, w in atoms)
    assert moment(atoms, 1) == first
    assert moment(atoms, 2) == second


checks = 0
for n in range(1, 10):
    first = Q(n, 10)
    for level in range(5):
        second = first ** 2 + Q(level, 4) * (first - first ** 2)
        lower, upper = extremizers(first, second)
        audit_atoms(lower, first, second)
        audit_atoms(upper, first, second)
        assert moment(lower, 4) == second ** 3 / first ** 2
        assert moment(lower, 4) <= moment(upper, 4)
        checks += 1

firsts = [Q(1, 2), Q(3, 5), Q(99, 100)]
seconds = [Q(3, 8), Q(9, 25), Q(9801, 10000)]
b = [Q(1, 3)] * 3
c1 = sum(w * x for w, x in zip(b, firsts))
c2 = sum(w * x for w, x in zip(b, seconds))
r1 = [x / c1 for x in firsts]
r2 = [x / c2 for x in seconds]
assert sum(w * r for w, r in zip(b, r1)) == 1
assert sum(w * r for w, r in zip(b, r2)) == 1
lo = max(x * x / r for x, r in zip(firsts, r2))
hi = min(x / r for x, r in zip(firsts, r2))
for scale in (lo, (lo + hi) / 2, hi):
    reconstructed = []
    for first, relative in zip(firsts, r2):
        low_atoms, _ = extremizers(first, relative * scale)
        audit_atoms(low_atoms, first, relative * scale)
        reconstructed.append(moment(low_atoms, 2))
    assert sum(w * x for w, x in zip(b, reconstructed)) == scale
    assert [x / scale for x in reconstructed] == r2

cert_lower = moment(extremizers(firsts[0], r2[0] * lo)[0], 4)
cert_upper = moment(extremizers(firsts[1], r2[1] * hi)[1], 4)
assert (cert_lower, cert_upper) == (Q(27, 128), Q(753, 5324))
assert cert_lower > cert_upper
other_firsts = [x / 10 for x in firsts]
other_seconds = [x / 50 for x in seconds]
other_a = extremizers(other_firsts[0], other_seconds[0])[0]
other_b = extremizers(other_firsts[1], other_seconds[1])[1]
audit_atoms(other_a, other_firsts[0], other_seconds[0])
audit_atoms(other_b, other_firsts[1], other_seconds[1])
assert moment(other_a, 4) < moment(other_b, 4)

result = {'status': 'PASS_INDEPENDENT_EXACT_MEASURE_RECONSTRUCTION',
          'first_second_pairs_checked': checks,
          'attaining_probability_measures_checked': 2 * checks,
          'pooled_feasible_scales_reconstructed': 3,
          'anchored_rank_values': [str(cert_lower), str(cert_upper)],
          'unanchored_reverse_values': [str(moment(other_a, 4)), str(moment(other_b, 4))],
          'code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'scope': 'Synthetic law only. No biological likelihood, utility or novel-computation gain.'}
Path('log/20261022/operator_renewal/recursive/INDEPENDENT_ANCHOR_CHECK.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
