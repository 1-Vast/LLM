"""Independent A1 arithmetic/access fixtures. Synthetic values only, stdlib only.

This file never imports the experiment or opens a real count/matrix file.
Expectations were fixed before reading the root implementation.
"""
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
from statistics import median

HERE = Path(__file__).parent
NTC = tuple(f'N{i:02d}' for i in range(13))
GENES = {'A': ('A1', 'A2'), 'B': ('B1', 'B2'), 'C': ('C1', 'C2')}
GUIDE_GENE = {guide: gene for gene, guides in GENES.items() for guide in guides}
GUIDES = tuple(GUIDE_GENE) + NTC


def fold(a, b):
    a, b = sorted((a, b))
    key = f'MAESTRO-EGI-A1|{a}|{b}'.encode()
    return int(hashlib.sha256(key).hexdigest()[:8], 16) % 10


def constructs(a, b):
    return tuple((x, y) for x in GENES[a] for y in GENES[b]) + tuple((y, x) for x in GENES[a] for y in GENES[b])


def q(log_ratios, a, b, mask=None):
    ok = (lambda pair: True) if mask is None else (lambda pair: pair in mask)
    return (log_ratios[a, b]
            - median(log_ratios[a, n] for n in NTC if ok((a, n)))
            - median(log_ratios[n, b] for n in NTC if ok((n, b)))
            + median(log_ratios[n, m] for n in NTC for m in NTC if ok((n, m))))


def ratios(culture, x, y):
    return {pair: math.log2((culture[x][pair] + 1) / (culture[y][pair] + 1)) for pair in culture[x]}


def make_culture():
    result = {c: {} for c in ('T0', 'UT', 'DRUG')}
    singles = {'A1': 1, 'A2': 2, 'B1': 1, 'B2': 2, 'C1': 0, 'C2': 1}
    change = {'A1': 0, 'A2': 1, 'B1': 1, 'B2': 0, 'C1': 1, 'C2': 0}
    for a in GUIDES:
        for b in GUIDES:
            genes = tuple(sorted((GUIDE_GENE.get(a, 'NTC'), GUIDE_GENE.get(b, 'NTC'))))
            interaction = int('NTC' not in genes and genes[0] != genes[1])
            delta = 2 if genes == ('A', 'C') else -1 if genes == ('A', 'B') else 0
            base = 12 + singles.get(a, 0) + singles.get(b, 0) + interaction
            result['T0'][a, b] = 2**12 - 1
            result['UT'][a, b] = 2**base - 1
            result['DRUG'][a, b] = 2**(base + 3 + change.get(a, 0) + change.get(b, 0) + delta) - 1
    return result


class SourceReadGuard:
    """Prediction can read only the source culture and source training doubles."""
    def __init__(self, source):
        self.source = source
        self.reads = []

    def get(self, condition, a, b, culture='source'):
        if culture != 'source':
            raise PermissionError('Target culture cannot supply predictor values')
        if condition == 'DRUG' and a in GUIDE_GENE and b in GUIDE_GENE:
            ga, gb = GUIDE_GENE[a], GUIDE_GENE[b]
            if ga == gb or fold(ga, gb) >= 7:
                raise PermissionError('Held double DRUG count cannot supply predictor values')
        self.reads.append((culture, condition, a, b))
        return self.source[condition][a, b]


def source_prediction_inputs(view):
    # Collect a dependency witness, not a scientific prediction/model.
    allowed = []
    for a in GUIDES:
        for b in GUIDES:
            conditions = ['T0', 'UT']
            control = a in NTC or b in NTC
            anchor = a in GUIDE_GENE and b in GUIDE_GENE and GUIDE_GENE[a] != GUIDE_GENE[b] and fold(GUIDE_GENE[a], GUIDE_GENE[b]) <= 6
            if control or anchor:
                conditions.append('DRUG')
            allowed.extend(view.get(c, a, b) for c in conditions)
    return tuple(allowed)


def check():
    expected = json.loads((HERE / 'a_arithmetic_expectations_v1.json').read_text())['expected']
    culture = make_culture()
    baseline = ratios(culture, 'UT', 'T0')
    delta = ratios(culture, 'DRUG', 'UT')
    assert median(q(baseline, a, b) for a, b in constructs('A', 'C')) == expected['Q_UT_T0_for_A_C']
    assert median(q(delta, a, b) for a, b in constructs('A', 'C')) == expected['Q_DRUG_UT_for_A_C']
    shifted = {pair: value + 3 for pair, value in delta.items()}
    assert q(shifted, 'A1', 'C1') == expected['Q_after_common_L_offset_plus_3']
    masked = set(delta)
    outliers = dict(delta)
    for n in NTC[5:]:
        masked.remove(('A1', n))
        outliers['A1', n] += 100
    assert sum(('A1', n) in masked for n in NTC) == 5
    assert sum((n, m) in masked for n in NTC for m in NTC) >= 25
    assert q(outliers, 'A1', 'C1', masked) == expected['Q_after_eight_excluded_control_outliers']
    assert q(outliers, 'A1', 'C1') != expected['Q_after_eight_excluded_control_outliers']
    assert len(set(constructs('A', 'C'))) == expected['ordered_constructs_for_two_guides_each_distinct_gene_pair']
    assert set(constructs('A', 'C')) == set(constructs('C', 'A'))
    assert median(range(8)) == expected['median_of_eight_ordered_values_0_through_7']
    ab, ba = constructs('A', 'C')[:4], constructs('A', 'C')[4:]
    pair_eligible = lambda keep: len(keep) >= 4 and any(p in keep for p in ab) and any(p in keep for p in ba)
    assert pair_eligible(set(ab[:3] + ba[:1]))
    assert not pair_eligible(set(ab))
    for a, b in [('A', 'B'), ('A', 'C'), ('B', 'C')]:
        assert fold(a, b) == fold(b, a) == expected[f'fold_{a}_{b}']
        assert {fold(GUIDE_GENE[x], GUIDE_GENE[y]) for x, y in constructs(a, b)} == {fold(a, b)}

    # Median subtraction does not commute: 9 zero/4 hundred vs 4 zero/9 hundred.
    lx = {pair: 0 for pair in delta}
    ly = dict(lx)
    for i, n in enumerate(NTC):
        lx['A1', n] = 0 if i < 9 else 100
        ly['A1', n] = 0 if i < 4 else 100
    difference = {pair: ly[pair] - lx[pair] for pair in lx}
    assert q(difference, 'A1', 'C1') == expected['median_noncommutation_direct_Q_DRUG_UT']
    assert q(ly, 'A1', 'C1') - q(lx, 'A1', 'C1') == expected['median_noncommutation_Q_DRUG_T0_minus_Q_UT_T0']

    # T0 threshold is inclusive and shared-mask eligibility uses both cultures.
    target = deepcopy(culture)
    culture['T0']['A1', 'C1'] = 30
    target['T0']['A1', 'C1'] = 30
    shared = lambda: {p for p in culture['T0'] if culture['T0'][p] >= 30 and target['T0'][p] >= 30}
    assert ('A1', 'C1') in shared()
    target['T0']['A1', 'C1'] = 29
    assert ('A1', 'C1') not in shared()

    view = SourceReadGuard(culture)
    inputs = source_prediction_inputs(view)
    changed = deepcopy(culture)
    for pair in constructs('A', 'C'):
        changed['DRUG'][pair] = 2**30 - 1
    assert source_prediction_inputs(SourceReadGuard(changed)) == inputs
    # Arbitrarily changing target values cannot alter a source-only view.
    target = {c: {p: -123 for p in values} for c, values in target.items()}
    assert source_prediction_inputs(SourceReadGuard(culture)) == inputs
    for kwargs in [{'condition': 'DRUG', 'a': 'A1', 'b': 'C1'}, {'condition': 'UT', 'a': 'A1', 'b': 'C1', 'culture': 'target'}]:
        try:
            view.get(**kwargs)
        except PermissionError:
            pass
        else:
            raise AssertionError('Forbidden read was accepted')
    return {'synthetic_arithmetic': 'PASS', 'independent_access_partition_fixture': 'PASS', 'implementation_integration_checked': False, 'v1_protocol_clarifications': ['Joint T0 eligibility is an explicit target-baseline dependency and needs a declared exception or repair', 'T0 cancellation is per-construct L before medians, not subtraction of aggregate Q'], 'real_count_or_GI_values_accessed': False}


if __name__ == '__main__':
    result = check()
    print(json.dumps(result, indent=2))
