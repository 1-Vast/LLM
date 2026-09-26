"""One-step population transition arms: time (24 h to 72 h), dose and context transfer.

File summary
- Path: research/dynamic_world_model/transition.py
- Purpose: evaluate, on held-out compounds (the frozen skeleton folds), whether anything learned
  predicts a compound's shift at a target condition from its measured shift at a source condition
  better than predicting no change or carrying the source over; and provide the fitted forecasts
  that the `dyn_model` policy uses at step 2.
- Core points:
  - Every fit sees only training-fold compounds measured (QC-passed) at both conditions.
  - The latent is a 20-component PCA fitted on those training profiles; the latent arms predict
    the latent *change* and add it to the source profile, so they nest persistence.
  - Ridge penalties are chosen by inner grouped cross-validation on training compounds only.
  - A 24 h to 72 h pair is two matched populations measured in different wells; nothing here is
    a cell trajectory, and no arm is asked to predict a time that was not measured.
- Run: python research/dynamic_world_model/transition.py
- Depends on: common.py, numpy, scikit-learn
"""
from __future__ import annotations

import hashlib
import json
import time
import warnings
from pathlib import Path

import numpy as np

import common as C

LAMBDAS = (0.01, 0.1, 1.0, 10.0)
ARMS = ("zero", "persistence", "scaled_persistence", "latent_ridge_residual", "gene_ridge", "mlp_latent_residual",
        "retrieval_k3", "retrieval_residual_k3")
LEARNED = ARMS[2:]


# ------------------------------------------------------------------------------ fitting
def _ridge_dual(K: np.ndarray, T: np.ndarray, lam: float) -> np.ndarray:
    n = K.shape[0]
    return np.linalg.solve(K + lam * np.eye(n), T)


def _choose_lambda(Xs: np.ndarray, Yt: np.ndarray, groups: np.ndarray, target_fn) -> float:
    """Inner grouped CV over the lambda grid (scaled by the kernel's mean diagonal)."""
    unique = np.unique(groups)
    if len(unique) < 4:
        return LAMBDAS[2]
    rng = np.random.default_rng(C.SEED)
    assign = dict(zip(unique, rng.permutation(len(unique)) % 4))
    split = np.array([assign[g] for g in groups])
    best, best_err = LAMBDAS[2], np.inf
    for lam in LAMBDAS:
        err = 0.0
        for k in range(4):
            tr, te = split != k, split == k
            if tr.sum() < 3 or te.sum() == 0:
                continue
            pred = target_fn(Xs[tr], Yt[tr], Xs[te], lam)
            err += float(((pred - Yt[te]) ** 2).sum())
        if err < best_err:
            best, best_err = lam, err
    return best


def _gene_ridge(Xtr, Ytr, Xte, lam):
    K = Xtr @ Xtr.T
    scale = float(np.mean(np.diag(K))) or 1.0
    A = _ridge_dual(K, Ytr, lam * scale)
    return (Xte @ Xtr.T) @ A


def _pca(stack: np.ndarray, k: int = 20):
    mu = stack.mean(0)
    U, s, Vt = np.linalg.svd(stack - mu, full_matrices=False)
    return mu, Vt[:min(k, Vt.shape[0])]


class Transfer:
    """Fitted arms for one (fold, source key, target key)."""

    def __init__(self, Ys: np.ndarray, Yt: np.ndarray, groups: np.ndarray, seed: int = C.SEED):
        self.Ys, self.Yt, self.groups = Ys.astype(np.float64), Yt.astype(np.float64), groups
        denom = float((self.Ys ** 2).sum())
        self.alpha = float((self.Ys * self.Yt).sum()) / denom if denom > 0 else 0.0
        self.mu, self.P = _pca(np.vstack([self.Ys, self.Yt]))
        Zs = (self.Ys - self.mu) @ self.P.T
        Zt = (self.Yt - self.mu) @ self.P.T
        self.Zs_aug = np.hstack([Zs, np.ones((len(Zs), 1))])
        D = Zt - Zs

        def latent_fn(Xtr, Ytr, Xte, lam):
            return Xte @ np.linalg.solve(Xtr.T @ Xtr + lam * np.eye(Xtr.shape[1]) * max(np.mean(np.diag(Xtr.T @ Xtr)), 1e-9), Xtr.T @ Ytr)

        self.lat_lambda = _choose_lambda(self.Zs_aug, D, groups, latent_fn)
        X = self.Zs_aug
        self.R = np.linalg.solve(X.T @ X + self.lat_lambda * np.eye(X.shape[1]) * max(np.mean(np.diag(X.T @ X)), 1e-9), X.T @ D)
        self.gene_lambda = _choose_lambda(self.Ys, self.Yt, groups, _gene_ridge)
        K = self.Ys @ self.Ys.T
        self.gene_A = _ridge_dual(K, self.Yt, self.gene_lambda * (float(np.mean(np.diag(K))) or 1.0))
        self.mlp = None
        if len(Zs) >= 10:
            from sklearn.neural_network import MLPRegressor
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                self.mlp = MLPRegressor(hidden_layer_sizes=(64,), alpha=1e-3, early_stopping=True, validation_fraction=0.15,
                                        max_iter=2000, random_state=seed).fit(Zs, D)
        norms = np.linalg.norm(self.Ys, axis=1)
        self.Ys_unit = self.Ys / np.maximum(norms, 1e-12)[:, None]

    def predict(self, arm: str, y: np.ndarray) -> np.ndarray:
        y = y.astype(np.float64)
        if arm == "zero":
            return np.zeros_like(y)
        if arm == "persistence":
            return y.copy()
        if arm == "scaled_persistence":
            return self.alpha * y
        z = (y - self.mu) @ self.P.T
        if arm == "latent_ridge_residual":
            return y + (np.append(z, 1.0) @ self.R) @ self.P
        if arm == "gene_ridge":
            return (y @ self.Ys.T) @ self.gene_A
        if arm == "mlp_latent_residual":
            if self.mlp is None:
                return y.copy()
            return y + self.mlp.predict(z[None])[0] @ self.P
        sims = self.Ys_unit @ (y / max(np.linalg.norm(y), 1e-12))
        nearest = np.argsort(-sims)[:3]
        if arm == "retrieval_k3":
            return self.Yt[nearest].mean(0)
        if arm == "retrieval_residual_k3":
            return y + (self.Yt[nearest] - self.Ys[nearest]).mean(0)
        raise ValueError(arm)


def training_pairs(data: C.Data, fold: int, key_s, key_t):
    comp = data.compounds.drop_duplicates("compound").set_index("compound")
    rows_s, rows_t, names = [], [], []
    for c, rs in data.index.get(key_s, {}).items():
        rt = data.index.get(key_t, {}).get(c)
        if rt is None or comp.fold.get(c) == fold:
            continue
        if C.qc_passed(data, rs) and C.qc_passed(data, rt):
            rows_s.append(rs); rows_t.append(rt); names.append(c)
    return rows_s, rows_t, names


_FITS: dict = {}


def fitted(data: C.Data, fold: int, key_s, key_t) -> Transfer | None:
    cache_key = (fold, key_s, key_t)
    if cache_key not in _FITS:
        rs, rt, names = training_pairs(data, fold, key_s, key_t)
        comp = data.compounds.drop_duplicates("compound").set_index("compound")
        _FITS[cache_key] = (Transfer(data.shift[rs], data.shift[rt], np.array([comp.skeleton[c] for c in names]))
                            if len(rs) >= 6 else None)
    return _FITS[cache_key]


# ------------------------------------------------------------------------------ evaluation
def cosine(a, b) -> float:
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    return float(a @ b / (na * nb)) if na > 0 and nb > 0 else 0.0


def families(data: C.Data) -> dict:
    lines, doses = ("A549", "K562", "MCF7"), (10.0, 100.0, 1000.0, 10000.0)
    fam = {"T2_time": [(("A549", 24.0, d), ("A549", 72.0, d)) for d in doses],
           "T4_context": [((a, 24.0, d), (b, 24.0, d)) for a in lines for b in lines if a != b for d in doses],
           "dose_single_source": []}
    for line, t in [(l, 24.0) for l in lines] + [("A549", 72.0)]:
        for i in range(3):
            fam["dose_single_source"].append(((line, t, doses[i]), (line, t, doses[i + 1])))
            fam["dose_single_source"].append(((line, t, doses[i + 1]), (line, t, doses[i])))
    return fam


def evaluate_family(data: C.Data, pairs, detected: np.ndarray, templates=None) -> list[dict]:
    comp = data.compounds.drop_duplicates("compound").set_index("compound")
    rows = []
    for key_s, key_t in pairs:
        for c, rs in data.index.get(key_s, {}).items():
            rt = data.index.get(key_t, {}).get(c)
            if rt is None or not (C.qc_passed(data, rs) and C.qc_passed(data, rt)):
                continue
            fold = int(comp.fold[c])
            model = fitted(data, fold, key_s, key_t)
            if model is None:
                continue
            y_s, y_t = data.shift[rs].astype(np.float64), data.shift[rt].astype(np.float64)
            rec = {"compound": c, "skeleton": comp.skeleton[c], "fold": fold, "klass": comp.klass.get(c),
                   "source": list(key_s), "target": list(key_t), "target_detected": bool(detected[rt]),
                   "ceiling": cosine(data.rep1[rt], data.rep2[rt])}
            for arm in ARMS:
                pred = model.predict(arm, y_s)
                rec[f"cos:{arm}"] = cosine(pred, y_t) if arm != "zero" else 0.0
                rec[f"r2:{arm}"] = 1.0 - float(((y_t - pred) ** 2).sum()) / max(float((y_t ** 2).sum()), 1e-12)
                if templates is not None:
                    rec[f"class:{arm}"] = templates(fold, key_t, pred) if arm != "zero" else None
            if templates is not None:
                rec["class:observed"] = templates(fold, key_t, y_t)
            rows.append(rec)
    return rows


def evaluate_t3(data: C.Data, detected: np.ndarray) -> list[dict]:
    """Two-neighbour dose transfer (interpolation) and 10 uM extrapolation, as registered."""
    comp = data.compounds.drop_duplicates("compound").set_index("compound")
    doses = (10.0, 100.0, 1000.0, 10000.0)
    tasks = [((10.0, 1000.0), 100.0, "interpolation"), ((100.0, 10000.0), 1000.0, "interpolation"),
             ((100.0, 1000.0), 10000.0, "extrapolation")]
    rows = []
    for line, t in [(l, 24.0) for l in ("A549", "K562", "MCF7")] + [("A549", 72.0)]:
        for (lo, hi), target, kind in tasks:
            k_lo, k_hi, k_t = (line, t, lo), (line, t, hi), (line, t, target)
            names = [c for c in data.index.get(k_t, {}) if all(
                c in data.index.get(k, {}) and C.qc_passed(data, data.index[k][c]) for k in (k_lo, k_hi, k_t))]
            by_fold = {}
            for c in names:
                by_fold.setdefault(int(comp.fold[c]), []).append(c)
            for fold, held in by_fold.items():
                train = [c for c in names if int(comp.fold[c]) != fold]
                X = np.hstack([data.shift[[data.index[k_lo][c] for c in train]], data.shift[[data.index[k_hi][c] for c in train]]]).astype(np.float64)
                Y = data.shift[[data.index[k_t][c] for c in train]].astype(np.float64)
                groups = np.array([comp.skeleton[c] for c in train])
                lam = _choose_lambda(X, Y, groups, _gene_ridge)
                for c in held:
                    a = data.shift[data.index[k_lo][c]].astype(np.float64)
                    b = data.shift[data.index[k_hi][c]].astype(np.float64)
                    y = data.shift[data.index[k_t][c]].astype(np.float64)
                    if kind == "interpolation":
                        nearest, interp = b, 0.5 * (a + b)          # equal log spacing; ties go to the higher dose
                    else:
                        nearest, interp = b, b + (b - a)            # one decade of log-linear extrapolation
                    ridge = _gene_ridge(X, Y, np.hstack([a, b])[None], lam)[0]
                    rec = {"compound": c, "skeleton": comp.skeleton[c], "fold": fold, "line": line, "time": t,
                           "target_dose": target, "kind": kind, "target_detected": bool(detected[data.index[k_t][c]]),
                           "ceiling": cosine(data.rep1[data.index[k_t][c]], data.rep2[data.index[k_t][c]])}
                    for arm, pred in (("zero", np.zeros_like(y)), ("nearest_dose", nearest),
                                      ("log_dose_interpolation", interp), ("ridge_neighbours", ridge)):
                        rec[f"cos:{arm}"] = cosine(pred, y) if arm != "zero" else 0.0
                        rec[f"r2:{arm}"] = 1.0 - float(((y - pred) ** 2).sum()) / max(float((y ** 2).sum()), 1e-12)
                    rows.append(rec)
    return rows


def main() -> None:
    started = time.time()
    protocol = C.load_protocol()
    data = C.load()
    null = C.detection_null(data, protocol)
    detected = C.detected_flags(data, null)
    tiers = C.tiers(data, protocol)
    tables = {}

    def templates(fold, key, profile):
        """Class of the nearest detected training template (projected cosine), tier-A pool at 72 h, tier-B pool at 24 h."""
        tier = tiers["A"] if key[1] == 72.0 else tiers["B"]
        cache_key = (tier.name, fold)
        if cache_key not in tables:
            tables[cache_key] = C.build_fold_tables(data, tier, fold, detected)
        ft = tables[cache_key]
        if key not in ft.tables:
            return None
        scores = C.heldout_class_scores(ft.tables[key], profile, ft.classes)
        return ft.classes[int(np.argmax(scores))] if np.isfinite(scores).any() else None

    out = C.OUTPUTS / "transition"
    out.mkdir(parents=True, exist_ok=True)
    results = {}
    for name, pairs in families(data).items():
        rows = evaluate_family(data, pairs, detected, templates if name in ("T2_time", "T4_context") else None)
        results[name] = rows
        print(f"{name}: {len(rows)} held-out pairs, {time.time() - started:.0f}s", flush=True)
    results["T3_dose"] = evaluate_t3(data, detected)
    print(f"T3_dose: {len(results['T3_dose'])} held-out targets, {time.time() - started:.0f}s", flush=True)
    for name, rows in results.items():
        with (out / f"{name}.jsonl").open("w", encoding="utf-8") as stream:
            for r in rows:
                stream.write(json.dumps(C.clean(r)) + chr(10))
    C.write_json(out / "manifest.json", {"protocol_hashes": C.frozen_hashes(), "seconds": round(time.time() - started, 1),
                                         "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                                         "pairs": {k: len(v) for k, v in results.items()}})


if __name__ == "__main__":
    main()
