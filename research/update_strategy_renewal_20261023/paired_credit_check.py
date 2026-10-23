"""Exact finite population moments; not biological responses or policy training."""
from fractions import Fraction as F
from itertools import product
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261023/update_strategy_renewal'


def moments(values):
    count = len(values)
    mean = sum(values, F(0))/count
    variance = sum((v-mean)**2 for v in values)/count
    return dict(mean=str(mean), variance=str(variance), states=count, evaluation_cost_units=2)


if __name__ == '__main__':
    target = OUT/'PAIRED_CREDIT_RESULT.json'
    assert not target.exists()
    freeze = json.loads((OUT/'PAIRED_CREDIT_FREEZE.json').read_text())
    for filename, expected in freeze['files'].items():
        assert hashlib.sha256((ROOT/filename).read_bytes()).hexdigest() == expected
    rows = []
    for amplitude in (0, 2):
        paired = []
        for e, m, noise, base_noise in product((-1, 1), repeat=4):
            reward = F(e+amplitude*m+noise)
            reference = F(amplitude*m+base_noise)
            paired.append((reward-reference)*e)
        independent = []
        for e1, m1, n1, e2, m2, n2 in product((-1, 1), repeat=6):
            independent.append(F((e1+amplitude*m1+n1)*e1+(e2+amplitude*m2+n2)*e2, 2))
        antithetic = []
        for m, plus_noise, minus_noise in product((-1, 1), repeat=3):
            plus = F(1+amplitude*m+plus_noise)
            minus = F(-1+amplitude*m+minus_noise)
            antithetic.append((plus-minus)/2)
        result = dict(task_variance=amplitude**2, paired=moments(paired),
                      independent=moments(independent), antithetic=moments(antithetic))
        assert result['paired']['variance']=='2'
        assert result['independent']['variance']==str(F(amplitude**2+1,2))
        assert result['antithetic']['variance']=='1/2'
        assert all(result[k]['mean']=='1' for k in ('paired','independent','antithetic'))
        rows.append(result)
    common_paired, common_anti = [], []
    for e, m, noise in product((-1, 1), repeat=3):
        common_paired.append(F((e+2*m+noise)-(2*m+noise))*e)
        common_anti.append(F((1+2*m+noise)-(-1+2*m+noise),2))
    biased = moments([F((e-e)*e) for e in (-1,1)])
    assert biased['mean']=='0'
    report = dict(independent_noise=rows,
                  common_noise=dict(paired=moments(common_paired), antithetic=moments(common_anti)),
                  action_dependent_baseline_counterexample=dict(true_gradient='1', estimate=biased),
                  decision='NO_PAIRED_CREDIT_ADVANTAGE_OVER_ORDINARY_ANTITHETIC_IN_THIS_TOY',
                  scope='Exact stipulated reward/action/noise/cost model; no biological experiment, learned updater or RSI claim')
    assert report['common_noise']['paired']['variance']=='0'
    assert report['common_noise']['antithetic']['variance']=='0'
    target.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
