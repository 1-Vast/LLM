"""Scientific input-isolation and formula checks on synthetic data only."""
import json
import numpy as np
from models import MENU, expectation, predict_catalog, select
from prepare import OUT


def main():
    rng = np.random.default_rng(20261022)
    solo = rng.uniform(-.2, 1.2, (12, 3, 6))
    y = expectation(solo) + rng.normal(0, .1, (12, 3, 9))
    source, target = slice(0, 8), slice(8, 12)
    counts = 0
    for budget in (0, 1):
        preds = {}
        for name in MENU:
            anchor = y[target, :, 8].copy() if budget else None
            pred, _ = predict_catalog(name, budget, solo[source], y[source], solo[target], anchor)
            altered = y.copy()
            altered[target, :, :8] += 10000
            if budget == 0:
                altered[target, :, 8] -= 10000
            again, _ = predict_catalog(name, budget, solo[source], altered[source], solo[target], altered[target, :, 8] if budget else None)
            np.testing.assert_array_equal(pred, again)
            # Changing another target pair cannot change this pair's predictions.
            changed_solo = solo[target].copy()
            changed_solo[:, 1] += 100
            changed_anchor = None if anchor is None else anchor.copy()
            if changed_anchor is not None:
                changed_anchor[:, 1] += 100
            cross, _ = predict_catalog(name, budget, solo[source], y[source], changed_solo, changed_anchor)
            np.testing.assert_array_equal(pred[:, 0], cross[:, 0])
            assert pred.shape == (4, 3, 8) and np.isfinite(pred).all()
            preds[name] = pred
            counts += 1
        # Finite selection on the supplied synthetic tuning set; full run order is statically reviewed.
        selected, risks = select(preds, y[target])
        assert selected in preds and all(np.isfinite(v) for v in risks.values())
    values = np.array([[-.2, .5, 1.2, .4, .8, 1.1]])
    np.testing.assert_allclose(expectation(values), [[-.2, -.2, -.2, .2, .4, .5, .4, .8, 1]])
    (OUT / 'SYNTHETIC_TESTS.json').write_text(json.dumps({'status': 'PASS', 'models_budgets_checked': counts,
        'checks': ['NCI negative/min and positive capped product', 'query/anchor isolation',
                   'no cross-target-pair input dependence', 'finite common eight-query outputs',
                   'finite source-menu selection; not full-pipeline selection perturbation'], 'seed': 20261022}, indent=2), encoding='utf-8')
    print('Synthetic input-isolation checks PASS')


if __name__ == '__main__':
    main()
