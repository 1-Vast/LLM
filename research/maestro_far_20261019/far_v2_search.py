"""Search-only development of the expected-benefit model (FAR-v2): gradient-boosted regression of the realised benefit of measuring a compound
on pre-assay features. Cross-fit inside the search folds (0 -> 1, 1 -> 0) is the only check used; the model for select/test is fit on both.
Writes VALUE_MODEL.pkl and V2_SEARCH.json."""
import json, pickle, sys
from pathlib import Path
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import far_core as fc
from far_run import build, SEED


def table(c, rng, tau, n_lines=120):
    lines = rng.choice(c.lines, min(n_lines, len(c.lines)), replace=False)
    X, y = [], []
    for j in lines:
        X.append(fc.value_features(c, j)[c.has_sig]); y.append(fc.benefit(c, j, "fuse", tau)[c.has_sig])
    return np.vstack(X), np.concatenate(y)


def main():
    if (HERE / "VALUE_MODEL.pkl").exists() or (HERE / "V2_SEARCH.json").exists():
        raise SystemExit("write-once: value model or search records exist")
    D, folds = build("search")
    rng = np.random.default_rng(SEED)
    model = json.loads((HERE / "MODEL.json").read_text(encoding="utf-8")); tau = model["tau"]
    camps = {f: fc.Campaign(D, f, r) for f, r in folds.items()}
    tab = {f: table(c, rng, tau) for f, c in camps.items()}
    res = {"tau": tau}
    for a, b in ((0, 1), (1, 0)):
        m = HistGradientBoostingRegressor(max_depth=3, max_iter=150, learning_rate=0.05, min_samples_leaf=200, random_state=0).fit(*tab[a])
        p = m.predict(tab[b][0]); y = tab[b][1]
        res[f"crossfit_{a}_to_{b}"] = {"corr": float(np.corrcoef(p, y)[0, 1]), "n": int(len(y)), "mean_benefit": float(y.mean()),
                                       "top_decile_mean_benefit": float(y[p >= np.quantile(p, 0.9)].mean()), "bottom_half_mean_benefit": float(y[p <= np.median(p)].mean())}
    X = np.vstack([tab[f][0] for f in tab]); y = np.concatenate([tab[f][1] for f in tab])
    m = HistGradientBoostingRegressor(max_depth=3, max_iter=150, learning_rate=0.05, min_samples_leaf=200, random_state=0).fit(X, y)
    pickle.dump(m, open(HERE / "VALUE_MODEL.pkl", "wb"))
    (HERE / "V2_SEARCH.json").write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(res, indent=1))

if __name__ == "__main__":
    main()
