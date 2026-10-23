"""Exact candidate-vs-KKT reduction and limits of rectangle certificates."""
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/post_almanac_mechanism/root'


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def solve(matrix, rhs):
    n = len(rhs)
    a = [[F(v) for v in row] + [F(b)] for row, b in zip(matrix, rhs)]
    for j in range(n):
        pivot = next(i for i in range(j, n) if a[i][j])
        a[j], a[pivot] = a[pivot], a[j]
        scale = a[j][j]
        a[j] = [v / scale for v in a[j]]
        for i in range(n):
            if i != j:
                scale = a[i][j]
                a[i] = [v - scale * w for v, w in zip(a[i], a[j])]
    return [row[-1] for row in a]


def rectangles(height, width):
    rows = []
    for i in range(height - 1):
        for j in range(width - 1):
            row = [F(0)] * (height * width)
            for a, b, sign in ((i, j, 1), (i + 1, j, -1), (i, j + 1, -1), (i + 1, j + 1, 1)):
                row[a * width + b] = F(sign)
            rows.append(row)
    return rows


def candidate(a, r0, b):
    residual = [target - dot(row, r0) for row, target in zip(a, b)]
    gram = [[dot(x, y) for y in a] for x in a]
    weights = solve(gram, residual)
    return [v + sum(a[j][i] * weights[j] for j in range(len(a))) for i, v in enumerate(r0)]


def ordinary_kkt(a, r0, b):
    n, m = len(r0), len(a)
    matrix = [[F(i == j) for j in range(n)] + [a[k][i] for k in range(m)] for i in range(n)]
    matrix += [row + [F(0)] * m for row in a]
    solution = solve(matrix, r0 + b)
    return solution[:n], solution[n:]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    assert not (OUT / 'EXACT_PROJECTION.json').exists()
    cases, assertions = 0, 0
    for height, width in ((2, 2), (2, 3), (3, 3)):
        a = rectangles(height, width)
        n, m = height * width, len(a)
        for seed in range(1, 8):
            r0 = [F(((i + 2) * seed) % 11 - 5, seed + 1) for i in range(n)]
            b = [F((j + 1) * seed - 4, seed + 2) for j in range(m)]
            c = candidate(a, r0, b)
            k, multipliers = ordinary_kkt(a, r0, b)
            assert c == k
            assert [dot(row, c) for row in a] == b
            assert all(c[i] - r0[i] + sum(a[j][i] * multipliers[j] for j in range(m)) == 0 for i in range(n))
            cases += 1
            assertions += 3
    d = [F(1), F(-1), F(-1), F(1)]
    slabs = 0
    for seed in range(1, 8):
        r0 = [F(seed * (i - 1), seed + 1) for i in range(4)]
        for b in (F(-2), F(0), F(3, 2)):
            for epsilon in (F(0), F(1, 3), F(2)):
                before = dot(d, r0)
                projected = min(max(before, b - epsilon), b + epsilon)
                shift = (projected - before) / dot(d, d)
                after = [v + shift * w for v, w in zip(r0, d)]
                assert abs(dot(d, after) - b) <= epsilon
                if b - epsilon <= before <= b + epsilon:
                    assert after == r0
                else:
                    assert dot(d, after) in (b - epsilon, b + epsilon)
                    assert all(after[i] - r0[i] == shift * d[i] for i in range(4))
                slabs += 1
    truth = [F(0), F(1), F(2), F(4)]
    witnesses = []
    for scale in (F(-100), F(10), F(100)):
        nuisance = [F(0), scale, F(0), scale]
        prediction = [x + z for x, z in zip(truth, nuisance)]
        assert dot(d, prediction) == dot(d, truth)
        squared_error = sum((x - y) ** 2 for x, y in zip(prediction, truth)) / 4
        witnesses.append({'main_effect_shift': str(scale), 'certificate_error': '0',
                          'mean_squared_error': str(squared_error),
                          'single_action_ranking_matches': (prediction[1] < prediction[2]) == (truth[1] < truth[2])})
    # With three known corners and a known contrast, the fourth is identified.
    recovered = dot(d, truth) - truth[0] + truth[1] + truth[2]
    assert recovered == truth[3]
    assert sum(v * v for v in d) == 4 and sum(d) == 0
    result = {'status': 'PASS', 'equality_projection_cases': cases, 'equality_assertions': assertions,
              'single_rectangle_slab_cases': slabs, 'nullspace_witnesses': witnesses,
              'matching_marginals_and_contrast_identify_fourth_corner': True,
              'independent_equal_variance_noise_multiplier': '4', 'common_offset_cancels': True,
              'scope': 'Exact rational checks for linear prediction constraints; no biological fits, no advantage claimed',
              'protocol_sha256': hashlib.sha256((OUT.parent / 'ROOT_MATH_PROTOCOL.md').read_bytes()).hexdigest(),
              'code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (OUT / 'EXACT_PROJECTION.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
