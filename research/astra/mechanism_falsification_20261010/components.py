"""Component-level tests of the agent's hypotheses (claims, not whole mechanisms).

The hypotheses were written before any L1000 value was read, so every measured drug can test them.
For each class with at least ``min_drugs`` drugs in the tier, the observed class mean signature per
option is compared with three kinds of claim:

* gene direction: each listed gene's sign at the matching time (mean over lines whose EMH level is
  not "none"), scored as accuracy over genes whose observed mean |z| >= 1 (otherwise undecided);
* line response: Spearman correlation between the EMH line levels and the observed per-line
  response norm at 24 h;
* kinetics: the EMH kinetic call against the observed 6 h / 24 h norm ratio.

Controls: the same EMH fields permuted across classes (seeded), which keeps the agent's marginal
habits (for example, "cell-cycle genes go down") and removes class specificity.
"""
from __future__ import annotations

import numpy as np

import knowledge as KN

RANK = KN.RANK


def class_means(X: np.ndarray, labels: np.ndarray, mask: np.ndarray, min_drugs: int) -> dict[str, np.ndarray]:
    out = {}
    for c in np.unique(labels[mask]):
        idx = np.where(mask & (labels == c))[0]
        if len(idx) >= min_drugs:
            with np.errstate(invalid="ignore"):
                out[str(c)] = np.nanmean(X[idx], axis=0)  # (n_opt, G)
    return out


def direction_accuracy(emh: dict, mean: np.ndarray, genes: list[str], options: list[str], min_abs: float = 1.0) -> tuple[int, int]:
    pos = {g: i for i, g in enumerate(genes)}
    lines_on = {o.split("|")[0] for o in options if RANK.get(emh["line_response"].get(o.split("|")[0], "none"), 0) > 0}
    correct = total = 0
    for t_label, keys in (("6 h", ("proximal_up", "proximal_down")), ("24 h", ("proximal_up", "proximal_down", "late_up", "late_down"))):
        cols = [j for j, o in enumerate(options) if o.endswith(t_label) and (o.split("|")[0] in lines_on or not lines_on)]
        if not cols:
            continue
        with np.errstate(invalid="ignore"):
            m = np.nanmean(mean[cols], axis=0)
        for key in keys:
            sign = 1 if key.endswith("up") else -1
            for g in emh.get(key, []):
                v = m[pos[g]] if g in pos else np.nan
                if np.isfinite(v) and abs(v) >= min_abs:
                    total += 1
                    correct += int(np.sign(v) == sign)
    return correct, total


def line_spearman(emh: dict, mean: np.ndarray, options: list[str], scale: np.ndarray | None = None) -> float:
    """``scale`` (n_opt,) divides each option's norm (for example the option's median class-mean
    norm), so that line-specific noise levels do not drive the correlation."""
    lines = sorted({o.split("|")[0] for o in options})
    obs, pred = [], []
    for ln in lines:
        j = options.index(f"{ln}|24 h") if f"{ln}|24 h" in options else None
        if j is None or np.isnan(mean[j]).all():
            continue
        obs.append(float(np.linalg.norm(np.nan_to_num(mean[j]))) / (1.0 if scale is None else float(scale[j])))
        pred.append(RANK.get(emh["line_response"].get(ln, "none"), 0))
    if len(obs) < 4 or len(set(pred)) < 2:
        return float("nan")
    ro = np.argsort(np.argsort(obs)).astype(float)
    rp = np.argsort(np.argsort(pred)).astype(float)
    return float(np.corrcoef(ro, rp)[0, 1])


def kinetic_ratio(mean: np.ndarray, options: list[str]) -> float:
    n6 = [np.linalg.norm(np.nan_to_num(mean[j])) for j, o in enumerate(options) if o.endswith("6 h") and not np.isnan(mean[j]).all()]
    n24 = [np.linalg.norm(np.nan_to_num(mean[j])) for j, o in enumerate(options) if o.endswith("24 h") and not np.isnan(mean[j]).all()]
    if not n6 or not n24:
        return float("nan")
    return float(np.mean(n6) / np.mean(n24))


def audit(emhs: dict[str, dict], means: dict[str, np.ndarray], genes: list[str], options: list[str], seed: int = 0) -> dict:
    classes = sorted(c for c in means if c in emhs)
    # per-option scale: median over classes of the class-mean norm (the option's typical response)
    norms = np.array([[np.linalg.norm(np.nan_to_num(means[c][j])) if not np.isnan(means[c][j]).all() else np.nan
                       for j in range(len(options))] for c in means])
    scale = np.nanmedian(norms, axis=0)
    rng = np.random.default_rng(seed)
    perm = [classes[i] for i in rng.permutation(len(classes))]
    res = {}
    for label, source in (("emh", {c: emhs[c] for c in classes}), ("permuted", {c: emhs[p] for c, p in zip(classes, perm)})):
        corr = tot = 0
        rhos, rhos_n, kin = [], [], {"fast": [], "slow": [], "sustained": [], "none": []}
        for c in classes:
            e = source[c]
            a, b = direction_accuracy(e, means[c], genes, options)
            corr += a
            tot += b
            r = line_spearman(e, means[c], options)
            if np.isfinite(r):
                rhos.append(r)
            rn = line_spearman(e, means[c], options, scale)
            if np.isfinite(rn):
                rhos_n.append(rn)
            kr = kinetic_ratio(means[c], options)
            if np.isfinite(kr):
                kin.setdefault(e.get("kinetics", "none"), []).append(kr)
        res[label] = {"direction_correct": corr, "direction_total": tot,
                      "direction_accuracy": corr / tot if tot else float("nan"),
                      "line_spearman_mean": float(np.mean(rhos)) if rhos else float("nan"),
                      "line_spearman_n": len(rhos),
                      "line_spearman_scaled_mean": float(np.mean(rhos_n)) if rhos_n else float("nan"),
                      "kinetic_ratio_by_call": {k: (float(np.median(v)) if v else None, len(v)) for k, v in kin.items()}}
    res["n_classes"] = len(classes)
    return res
