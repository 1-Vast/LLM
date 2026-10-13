"""Development-only check: is cross-platform reliability of a line or lineage learnable from past outcomes?

File summary
- Path: research/selective_hit_triage_20261013/dev_explore3.py
- Purpose: decide what the memory arms may learn from qualified outcomes.
- Method:
  - Fit reliability out of fold, grouped by family.
  - For each line (and each lineage), take the validation rate among selective primary hits
    (z_r <= -2) of other-fold compounds.
  - Shrink it to the pooled rate with a Beta prior of strength 20, then take the log-odds.
  - Add it to the MAESTRO context score with weight lambda in {0.5, 1}. The same is done with
    fold-shuffled labels.
- Output: DEV_EXPLORE3.json.
"""
from __future__ import annotations

import hashlib
import json

import numpy as np

from arms import load_table
from census import HERE, SPLIT_SALT
from dev import FOLDS, campaigns, labels, run_arm
from outcomes import qualified_outcomes

PRIOR = 20.0


def reliability(keys: np.ndarray, y: np.ndarray, use: np.ndarray, target_keys: np.ndarray) -> np.ndarray:
    pooled = y[use].mean()
    n, s = {}, {}
    for k, v in zip(keys[use], y[use]):
        n[k] = n.get(k, 0) + 1
        s[k] = s.get(k, 0) + int(v)
    rate = np.array([(s.get(k, 0) + PRIOR * pooled) / (n.get(k, 0) + PRIOR) for k in target_keys])
    return np.log(rate / (1 - rate)) - np.log(pooled / (1 - pooled))


def main() -> None:
    t = load_table()
    split = json.loads((HERE / "SPLIT.json").read_text(encoding="utf-8"))
    cores = split["development"]
    rows = np.flatnonzero(t["role"] == "development")
    y, ev, pan = labels(t, rows, qualified_outcomes("development"))
    core, line, lineage = t["core"][rows], t["line"][rows], t["lineage"][rows]
    fam = np.array([split["family"][c] for c in core])
    sizes, folds = np.zeros(FOLDS), {}
    for f in sorted(set(fam), key=lambda f: (-(fam == f).sum(), hashlib.sha256(f"{SPLIT_SALT}:fold:{f}".encode()).hexdigest())):
        k = int(np.argmin(sizes)); folds[f] = k; sizes[k] += (fam == f).sum()
    fold = np.array([folds[f] for f in fam])
    zr = t["z_r"][rows]
    ctx = np.where(np.isfinite(t["ctx_pred"][rows]), t["ctx_pred"][rows], 0.0)
    base = -(zr + ctx) / np.sqrt(2)
    sel = (zr <= -2) & ev
    rng = np.random.default_rng(20261013)
    camps = campaigns(cores)
    out = {"label": "DEVELOPMENT exploration 3 (outcomes opened)", "selective_hit_rate": float(y[sel].mean()), "results": {}}
    for level, keys in (("line", line), ("lineage", lineage)):
        rel, rel_shuf = np.zeros(len(rows)), np.zeros(len(rows))
        for k in range(FOLDS):
            tr, te = (fold != k) & sel, fold == k
            rel[te] = reliability(keys, y, tr, keys[te])
            perm = y.copy()
            idx = np.flatnonzero(tr)
            perm[idx] = y[idx][rng.permutation(len(idx))]
            rel_shuf[te] = reliability(keys, perm, tr, keys[te])
        for lam in (0.5, 1.0):
            for name, r in (("memory", rel), ("shuffled", rel_shuf)):
                s = base + lam * r
                out["results"][f"{level}_{name}_lambda{lam}"] = {str(b): int(y[run_arm(s, t, rows, camps, b)].sum()) for b in (0.5, 1.0, 2.0)}
        out[f"{level}_reliability_spread"] = [float(np.percentile(rel, 5)), float(np.percentile(rel, 95))]
    out["results"]["no_memory"] = {str(b): int(y[run_arm(base, t, rows, camps, b)].sum()) for b in (0.5, 1.0, 2.0)}
    (HERE / "DEV_EXPLORE3.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
