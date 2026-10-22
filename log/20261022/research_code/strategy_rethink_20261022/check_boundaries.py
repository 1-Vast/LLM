"""Small meaningful prefreeze checks of prediction and scoring boundaries."""
import json

import numpy as np

from screen import OUT, fit_solver, predict, score, write


def main():
    rng = np.random.default_rng(11)
    n = 30
    pack = {'comp': np.repeat(np.arange(10), 3), 'line': np.tile(np.arange(3), 10),
            'truth': rng.normal(size=(n, 6)), 'pred': rng.normal(size=(n, 4, 6)),
            'available': np.ones((n, 4), dtype=bool),
            'support': [rng.normal(size=(n, k)) for k in (3, 5, 5, 5)]}
    results = []
    for program in range(12):
        solver = fit_solver(pack, program)
        original = predict(pack, solver)
        poisoned = dict(pack)
        poisoned['truth'] = np.full((n, 6), np.nan)
        assert np.array_equal(original, predict(poisoned, solver))
    results.append('all12 program predictions invariant to target-truth NaN sentinel')
    toy = {'comp': np.array([0, 0, 1]), 'truth': np.array([[1.], [0.], [1.]])}
    assert score(toy, np.ones((3, 1)))[0] == .75
    results.append('compound-weighted score .75 differs correctly from row-weighted2/3')
    manifest = json.loads((OUT / 'EPISODE_MANIFEST.json').read_text())
    seen = set()
    for phase in manifest['episodes'].values():
        for episode in phase:
            for split, size in (('calibration', 16), ('development', 16), ('evaluation', 32)):
                ids = episode[split]
                assert len(ids) == len(set(ids)) == size
                assert not seen.intersection(ids)
                seen.update(ids)
                assert episode['row_indices'][split]
    results.append('all1024 compound IDs disjoint across source/later and all splits')
    write('BOUNDARY_CHECKS.json', {'checks': results, 'status': 'PASS', 'synthetic_only': True})
    print(json.dumps({'checks': len(results), 'status': 'PASS'}))


if __name__ == '__main__':
    main()
