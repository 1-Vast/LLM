"""E1: predictive validity of the cross-condition backend, by information regime, under strict nested validation.

File summary
- Path: research/dual_core/e1.py
- Purpose: run and analyse protocol.json's E1 on SciPlex3 and L1000.
- Core points:
  - Outer folds are the registered folds 0-4 (checked by `splits.check_folds`). Every model is fitted
    on the outer training compounds with inner group CV (`transfer.py`). A held-out shift enters
    only as a truth to score against, or as the held-out compound's own prompt (A1, A2).
  - Items per regime:
    - A0: held-out compound x target condition.
    - A1: x prompt condition x target.
    - A2: x target x an unordered pair of prompt conditions; up to 10 pairs per (compound, target),
      seeded.
    All arms of a regime score identical items.
  - Controls for `rrt_q` (A1):
    - `rrt_q_shuffled`: another held-out compound's prompt at the same condition, from a seeded
      derangement.
    - `rrt_q_wrong_target`: the transition fitted for a different, seeded target condition.
  - Metrics per item:
    - direction: centred cosine at the target's training mean;
    - Pearson delta;
    - MSE;
    - discrimination: State's normalised rank of the item's own truth among all held-out truths at
      the target, Manhattan distance;
    - effect score: the predicted norm;
    - gene-set Spearman: Hallmark set means;
    - phenocopy@5 among training references.
  - Provenance per A1/A2 item: prompt conditions, rows, batches, measured quality and detection.
- Interfaces: `run_dataset`, `run_one`, `analyse`; CLI `python -m research.dual_core.e1 run [--workers N] | analyse`
- Depends on: transfer.py, splits.py, research/incontext_world/metrics.py, research/protocol_v2 loaders
"""
from __future__ import annotations

import argparse
import gzip
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from research.incontext_world import metrics as M

from . import splits as SP
from . import transfer as TF

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/dual_core_20260927/e1"
SEED = 20260927
DRAWS = 10_000
A2_PAIRS = 10
GMT = ROOT / "data/external/msigdb/h.all.v2024.1.Hs.symbols.gmt"
L1000_GENE_INFO = ROOT / "data/external/lincs_l1000_phase1/GSE92742_Broad_LINCS_gene_info.txt.gz"


def _stable(*parts) -> int:
    import hashlib
    return int(hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()[:8], 16)


def gene_sets(dataset: str, data) -> list:
    """Index arrays of Hallmark sets with at least 5 members in the dataset's fixed feature space."""
    if dataset == "sciplex3":
        symbols = data.genes.symbol.astype(str).tolist()
        sets = {k: v for k, v in data.gene_sets.items()}
    else:
        ids = np.load(ROOT / "outputs/sequence_audit_20260926/l1000/prepared/shifts.npz")["gene_id"].astype(str)
        info = pd.read_csv(L1000_GENE_INFO, sep="\t", dtype=str)
        sym = dict(zip(info.pr_gene_id, info.pr_gene_symbol))
        symbols = [sym.get(i, "") for i in ids]
        sets = {}
        for line in GMT.read_text(encoding="utf-8").splitlines():
            parts = line.split("\t")
            sets[parts[0]] = parts[2:]
    pos = {s: i for i, s in enumerate(symbols) if s}
    out = []
    for name in sorted(sets):
        idx = np.asarray(sorted({pos[g] for g in sets[name] if g in pos}), dtype=int)
        if len(idx) >= 5:
            out.append(idx)
    return out


def _dataset(dataset: str):
    from research.belief_planning import arms as BA
    from research.protocol_v2 import tasks_v21 as TV
    C, LP = TV.C, TV.LP
    frame, data = SP.dataset_frame(dataset)
    if dataset == "sciplex3":
        spec = C.load_protocol()
        detected = C.detected_flags(data, C.detection_null(data, spec))
        tiers = C.tiers(data, spec)
        keys = tuple(sorted(set(tiers["A"].keys) | set(tiers["B"].keys)))
        if "smiles" not in data.compounds.columns:
            raise ValueError("SciPlex3 compounds carry no SMILES")
        batch = data.conditions.plate_rep1.astype(str).to_numpy()
    else:
        from research.belief_planning import tasks as T
        detected = data.conditions.detected.to_numpy(bool)
        keys = tuple(LP.TIERS["LT"]["keys"])
        smiles = T.l1000_smiles()
        data.compounds["smiles"] = [smiles.get(c) for c in data.compounds.compound]
        batch = data.conditions.batch.astype(str).to_numpy()
    qc = np.array([C.qc_passed(data, i) for i in range(len(data.conditions))])
    fp, pos = BA.fingerprints(data.compounds)
    quality = np.clip(np.nan_to_num(np.asarray(data.agreement, dtype=np.float64), nan=0.0), 0.0, 1.0)
    return frame, data, detected, keys, qc, fp, pos, quality, batch


def _relation(p, c) -> str:
    if p[0] != c[0]:
        return "line"
    if p[1] != c[1]:
        return "time"
    return "dose"


class _Scorer:
    """Metrics of predictions at one target in one outer fold."""

    def __init__(self, truths: np.ndarray, truth_names: list, centre: np.ndarray, refs: np.ndarray, sets: list):
        self.truths, self.index = truths, {n: i for i, n in enumerate(truth_names)}
        self.centre, self.sets = centre, sets
        u = M._unit(refs.sum(0)) if len(refs) else None
        P = refs - np.outer(refs @ u, u) if u is not None else refs
        self.u = u
        self.Rn = P / np.maximum(np.linalg.norm(P, axis=1, keepdims=True), 1e-12)
        self._nn = {}

    def nearest(self, v, k=5):
        vp = v - (v @ self.u) * self.u if self.u is not None else v
        n = float(np.linalg.norm(vp))
        if n < 1e-12 or len(self.Rn) < k:
            return set()
        return set(np.argsort(-(self.Rn @ (vp / n)), kind="stable")[:k].tolist())

    def gene_set_scores(self, v):
        return np.asarray([v[idx].mean() for idx in self.sets])

    def score(self, names: list, preds: np.ndarray) -> list:
        preds = np.atleast_2d(preds)
        dist = np.abs(preds[:, None, :] - self.truths[None, :, :]).sum(-1)
        out = []
        T = len(self.truths)
        for i, name in enumerate(names):
            j = self.index[name]
            y = self.truths[j]
            own = dist[i, j]
            closer = int((dist[i] < own - 1e-12).sum())
            ties = int((np.abs(dist[i] - own) <= 1e-12).sum()) - 1
            disc = 1.0 - 2.0 * (closer + 0.5 * ties) / (T - 1) if T > 1 else np.nan
            if name not in self._nn:
                self._nn[name] = (self.nearest(y), self.gene_set_scores(y))
            nn_true, gs_true = self._nn[name]
            gs_pred = self.gene_set_scores(preds[i])
            gs = float(pd.Series(gs_pred).corr(pd.Series(gs_true), method="spearman")) if len(gs_true) > 2 else np.nan
            out.append({"centred_cosine": M.centred_cosine(preds[i], y, self.centre),
                        "pearson_delta": M.pearson_delta(preds[i], y), "mse": M.mse(preds[i], y),
                        "discrimination": disc, "norm": float(np.linalg.norm(preds[i])),
                        "gs_spearman": gs if np.isfinite(gs) else 0.0,
                        "phenocopy5": len(self.nearest(preds[i]) & nn_true) / 5 if nn_true else np.nan})
        return out


def run_dataset(dataset: str, folds=SP.FOLDS) -> dict:
    folds = SP.check_folds(folds)
    frame, data, detected, keys, qc, fp, pos, quality, batch = _dataset(dataset)
    sets = gene_sets(dataset, data)
    compounds = list(frame.index)
    rows = {"A0": [], "A1": [], "A2": []}
    fits = []
    for fold in folds:
        train = [c for c in compounds if frame.fold[c] != fold]
        held = [c for c in compounds if frame.fold[c] == fold]
        measured = {k: {c: r for c, r in data.index.get(k, {}).items() if qc[r]} for k in keys}
        train_rows = [r for k in keys for c, r in measured[k].items() if c in set(train)]
        global_mean = data.shift[train_rows].astype(np.float64).mean(0)
        fpq = {c: fp[pos[c]] if c in pos else None for c in compounds}
        scorers, target_models = {}, {}
        for c_key in keys:
            names = [n for n in train if n in measured[c_key]]
            Y = data.shift[[measured[c_key][n] for n in names]].astype(np.float64)
            F = np.stack([fpq[n] if fpq[n] is not None else np.zeros(fp.shape[1]) for n in names])
            tm = TF.fit_target(c_key, F, Y, [frame.unit[n] for n in names], global_mean)
            target_models[c_key] = tm
            hnames = [h for h in held if h in measured[c_key]]
            truths = data.shift[[measured[c_key][h] for h in hnames]].astype(np.float64)
            scorers[c_key] = _Scorer(truths, hnames, tm.mean, Y, sets)
            fits.append({"fold": fold, "target": list(c_key), "kind": "A0", "references": tm.references,
                         "krr": tm.krr, "knn": tm.knn})
            if not hnames:
                continue
            for arm in TF.A0_ARMS:
                preds = np.stack([tm.predict(fpq[h], arm) for h in hnames])
                for h, m in zip(hnames, scorers[c_key].score(hnames, preds)):
                    rows["A0"].append({"fold": fold, "compound": h, "unit": frame.unit[h], "target": _id(c_key),
                                       "arm": arm, "target_detected": bool(detected[measured[c_key][h]]),
                                       "true_norm": float(np.linalg.norm(data.shift[measured[c_key][h]])), **m})
        pair_models = {}
        for c_key in keys:
            for p_key in keys:
                if p_key == c_key:
                    continue
                names = [n for n in train if n in measured[c_key] and n in measured[p_key]]
                X = data.shift[[measured[p_key][n] for n in names]]
                Y = data.shift[[measured[c_key][n] for n in names]]
                q = quality[[measured[p_key][n] for n in names]]
                pm = TF.fit_pair(p_key, c_key, X, Y, q, [frame.unit[n] for n in names])
                pair_models[(p_key, c_key)] = pm
                fits.append({"fold": fold, "prompt": list(p_key), "target": list(c_key), "kind": "A1",
                             "references": pm.references, "k": pm.k, "lambda_mult": pm.mult,
                             "gamma_const": pm.gamma_const, "gamma0": pm.gamma0, "inner_mse": pm.inner_mse})
        # A1 scoring (after all pairs exist, so the wrong-target control can borrow another pair's transition)
        for (p_key, c_key), pm in pair_models.items():
            items = [h for h in held if h in measured[p_key] and h in measured[c_key]]
            if not items:
                continue
            others = [c for c in keys if c not in (p_key, c_key)]
            wrong = others[_stable(dataset, fold, _id(p_key), _id(c_key)) % len(others)] if others else None
            rng = np.random.default_rng([SEED, fold, _stable(_id(p_key), _id(c_key))])
            order = rng.permutation(len(items))
            partner = {items[order[i]]: items[order[(i + 1) % len(order)]] for i in range(len(order))}
            x = {h: data.shift[measured[p_key][h]].astype(np.float64) for h in items}
            qh = {h: quality[measured[p_key][h]] for h in items}
            tm = target_models[c_key]
            predictions = {arm: np.stack([pm.predict(x[h], qh[h], arm) for h in items]) for arm in TF.A1_ARMS}
            predictions["chem_ridge"] = np.stack([tm.predict(fpq[h], "chem_ridge") for h in items])
            predictions["context_mean"] = np.stack([tm.mean for _ in items])
            predictions["rrt_q_shuffled"] = np.stack([pm.predict(x[partner[h]], qh[partner[h]], "rrt_q")
                                                      if len(items) > 1 else np.full_like(tm.mean, np.nan) for h in items])
            if wrong is not None and (p_key, wrong) in pair_models:
                wm = pair_models[(p_key, wrong)]
                predictions["rrt_q_wrong_target"] = np.stack([wm.predict(x[h], qh[h], "rrt_q") for h in items])
            for arm, preds in predictions.items():
                if not np.isfinite(preds).all():
                    continue
                for h, m in zip(items, scorers[c_key].score(items, preds)):
                    rp = measured[p_key][h]
                    rows["A1"].append({"fold": fold, "compound": h, "unit": frame.unit[h], "prompt": _id(p_key),
                                       "target": _id(c_key), "relation": _relation(p_key, c_key), "arm": arm,
                                       "prompt_row": int(rp), "prompt_batch": batch[rp], "prompt_quality": float(qh[h]),
                                       "prompt_detected": bool(detected[rp]),
                                       "target_detected": bool(detected[measured[c_key][h]]),
                                       "true_norm": float(np.linalg.norm(data.shift[measured[c_key][h]])), **m})
        # A2: pairs of prompts per (held-out compound, target)
        for c_key in keys:
            tm = target_models[c_key]
            for h in held:
                if h not in measured[c_key]:
                    continue
                prompts = [p for p in keys if p != c_key and h in measured[p]]
                pairs = [(a, b) for i, a in enumerate(prompts) for b in prompts[i + 1:]]
                if not pairs:
                    continue
                pick = np.random.default_rng([SEED, fold, _stable(h, _id(c_key))])
                chosen = [pairs[i] for i in sorted(pick.choice(len(pairs), size=min(A2_PAIRS, len(pairs)), replace=False))]
                for pa in chosen:
                    per = {p: pair_models[(p, c_key)] for p in pa}
                    xs = {p: data.shift[measured[p][h]].astype(np.float64) for p in pa}
                    qs = {p: quality[measured[p][h]] for p in pa}
                    err = [per[p].inner_mse.get("rrt_q", np.inf) for p in pa]
                    rrt = [per[p].predict(xs[p], qs[p], "rrt_q") for p in pa]
                    preds, weights = {}, {}
                    preds["prompt_mean"], _ = TF.aggregate([xs[p] for p in pa], err, "prompt_mean")
                    preds["additive_mean"], _ = TF.aggregate([per[p].predict(xs[p], qs[p], "additive") for p in pa],
                                                             err, "additive_mean")
                    for arm in ("rrt_mean", "rrt_best_single", "rrt_precision"):
                        preds[arm], weights[arm] = TF.aggregate(rrt, err, arm)
                    preds["chem_ridge"] = tm.predict(fpq[h], "chem_ridge")
                    arms = list(preds)
                    scored = scorers[c_key].score([h] * len(arms), np.stack([preds[a] for a in arms]))
                    for arm, m in zip(arms, scored):
                        rows["A2"].append({"fold": fold, "compound": h, "unit": frame.unit[h], "target": _id(c_key),
                                           "prompts": "+".join(_id(p) for p in pa), "arm": arm,
                                           "prompt_quality_min": float(min(qs.values())),
                                           "prompts_detected": int(sum(bool(detected[measured[p][h]]) for p in pa)),
                                           "precision_weight_max": float(np.max(weights["rrt_precision"]))
                                           if arm == "rrt_precision" else np.nan,
                                           "target_detected": bool(detected[measured[c_key][h]]),
                                           "true_norm": float(np.linalg.norm(data.shift[measured[c_key][h]])), **m})
    spanning = set(json.loads((ROOT / "outputs/dual_core_20260927/split_manifest.json").read_text())["datasets"]
                   [dataset]["murcko_scaffolds_spanning_folds"])
    out = {}
    for regime, rs in rows.items():
        df = pd.DataFrame(rs)
        df["dataset"] = dataset
        df["scaffold_spans_folds"] = df.compound.map(frame.scaffold).isin(spanning)
        out[regime] = df
    out["fits"] = fits
    return out


def _id(key) -> str:
    return f"{key[0]}|{float(key[1]):g}|{float(key[2]):g}"


# ------------------------------------------------------------------------------------ analysis
KEYS = {"A0": ["fold", "compound", "target"], "A1": ["fold", "compound", "prompt", "target"],
        "A2": ["fold", "compound", "target", "prompts"]}


def _load(out: Path, dataset: str, regime: str) -> pd.DataFrame:
    paths = sorted(out.glob(f"{dataset}_{regime}_fold*.parquet"))
    return pd.concat([pd.read_parquet(p) for p in paths], ignore_index=True)


def paired(frame: pd.DataFrame, a: str, b: str, metric: str, key, *, weighting: str = "unit") -> dict:
    """a - b on identical items; unit mean (each unit's items averaged first) or item-weighted, unit bootstrap."""
    wide = frame.pivot_table(index=list(key) + ["unit"], columns="arm", values=metric, aggfunc="first")
    if a not in wide or b not in wide:
        return {"missing": True}
    d = (wide[a] - wide[b]).dropna().reset_index()
    d.columns = list(key) + ["unit", "d"]
    g = d.groupby(d.unit.astype(str)).d.agg(["sum", "size", "mean"]).sort_index()
    rng = np.random.default_rng(SEED)
    index = rng.integers(len(g), size=(DRAWS, len(g)))
    if weighting == "unit":
        values = g["mean"].to_numpy()
        est, boot = float(values.mean()), values[index].mean(1)
    else:
        s, n = g["sum"].to_numpy(), g["size"].to_numpy()
        est, boot = float(s.sum() / n.sum()), s[index].sum(1) / n[index].sum(1)
    return {"difference": est, "ci": np.quantile(boot, [0.025, 0.975]).tolist(), "units": int(len(g)),
            "items": int(len(d)), "weighting": weighting}


def arm_means(frame: pd.DataFrame, metric: str) -> dict:
    return {a: float(g.groupby(g.unit.astype(str))[metric].mean().mean()) for a, g in frame.groupby("arm")}


def analyse(out: Path = OUT) -> dict:
    spec = json.loads((ROOT / "research/dual_core/protocol.json").read_text(encoding="utf-8"))["E1"]
    result = {"spec": "research/dual_core/protocol.json#E1", "datasets": {}}
    for dataset in ("sciplex3", "l1000"):
        if not list(out.glob(f"{dataset}_A1_fold*.parquet")):
            continue
        present = sorted(int(p.stem.split("fold")[-1]) for p in out.glob(f"{dataset}_A1_fold*.parquet"))
        if tuple(present) != SP.FOLDS:
            raise SP.SplitError(f"{dataset}: records for folds {present}, expected {list(SP.FOLDS)}")
        entry = {}
        A0, A1, A2 = (_load(out, dataset, r) for r in ("A0", "A1", "A2"))
        for name, df in (("A0", A0), ("A1", A1), ("A2", A2)):
            SP.duplicated_records(df, KEYS[name] + ["arm"])
        d0, d1, d2 = A0[A0.target_detected], A1[A1.target_detected], A2[A2.target_detected]
        metrics = ("centred_cosine", "discrimination", "pearson_delta", "gs_spearman", "phenocopy5")
        entry["A0_arms"] = {m: arm_means(d0, m) for m in metrics}
        entry["A1_arms"] = {m: arm_means(d1, m) for m in metrics} | {"mse_all": arm_means(A1, "mse")}
        entry["A2_arms"] = {m: arm_means(d2, m) for m in metrics}
        k1, k2 = KEYS["A1"], KEYS["A2"]
        primary = {
            "A1_discrimination_rrt_q-ridge_st": paired(d1, "rrt_q", "ridge_st", "discrimination", k1),
            "A1_direction_rrt_q-ridge_st": paired(d1, "rrt_q", "ridge_st", "centred_cosine", k1),
            "A2_direction_precision-mean": paired(d2, "rrt_precision", "rrt_mean", "centred_cosine", k2),
            "A2_discrimination_precision-mean": paired(d2, "rrt_precision", "rrt_mean", "discrimination", k2),
        }
        margin = spec["noninferiority_margin"]
        a1 = primary["A1_discrimination_rrt_q-ridge_st"]["ci"][0] > 0 and \
            primary["A1_direction_rrt_q-ridge_st"]["ci"][0] > -margin
        a2 = primary["A2_direction_precision-mean"]["ci"][0] > 0 and \
            primary["A2_discrimination_precision-mean"]["ci"][0] > -margin
        entry["primary"] = primary
        entry["verdict"] = {"A1_keep_rrt_q": bool(a1), "A2_keep_precision": bool(a2)}
        entry["secondary"] = {
            "item_weighted": {k: paired(d1 if k.startswith("A1") else d2, *v, k1 if k.startswith("A1") else k2,
                                        weighting="item")
                              for k, v in {"A1_discrimination_rrt_q-ridge_st": ("rrt_q", "ridge_st", "discrimination"),
                                           "A1_direction_rrt_q-ridge_st": ("rrt_q", "ridge_st", "centred_cosine"),
                                           "A2_direction_precision-mean": ("rrt_precision", "rrt_mean", "centred_cosine")}.items()},
            "quality_awareness": {m: paired(d1, "rrt_q", "rrt_const", m, k1) for m in ("discrimination", "centred_cosine")},
            "vs_additive": {m: paired(d1, "rrt_q", "additive", m, k1) for m in ("discrimination", "centred_cosine")},
            "vs_prompt_copy": {m: paired(d1, "rrt_q", "prompt_copy", m, k1) for m in ("discrimination", "centred_cosine")},
            "controls": {f"{c}": {m: paired(d1, "rrt_q", c, m, k1) for m in ("discrimination", "centred_cosine")}
                         for c in ("rrt_q_shuffled", "rrt_q_wrong_target", "context_mean", "chem_ridge")},
            "A0_vs_context_mean": {a: paired(d0, a, "context_mean", "centred_cosine", KEYS["A0"])
                                   for a in ("chem_ridge", "chem_knn")},
            "A2_vs_best_single": paired(d2, "rrt_precision", "rrt_best_single", "centred_cosine", k2),
            "strata_A1_discrimination": {
                **{f"relation={r}": paired(g, "rrt_q", "ridge_st", "discrimination", k1) for r, g in d1.groupby("relation")},
                **{f"prompt_detected={p}": paired(g, "rrt_q", "ridge_st", "discrimination", k1)
                   for p, g in d1.groupby("prompt_detected")},
                "scaffold_not_spanning": paired(d1[~d1.scaffold_spans_folds], "rrt_q", "ridge_st", "discrimination", k1),
            },
            "effect_tertile_A1_discrimination": {},
        }
        ref = d1[d1.arm == "ridge_st"][k1 + ["true_norm"]]
        cuts = np.quantile(ref.true_norm, [1 / 3, 2 / 3])
        d1t = d1.assign(tertile=np.digitize(d1.true_norm, cuts))
        entry["secondary"]["effect_tertile_A1_discrimination"] = {
            int(t): paired(g, "rrt_q", "ridge_st", "discrimination", k1) for t, g in d1t.groupby("tertile")}
        entry["effect_auroc"] = {"A0": effect_auroc_table(A0), "A1": effect_auroc_table(A1)}
        entry["counts"] = {r: {"items": int(len(df) // max(df.arm.nunique(), 1)), "units": int(df.unit.nunique())}
                           for r, df in (("A0", A0), ("A1", A1), ("A2", A2))}
        result["datasets"][dataset] = entry
    (out / "analysis.json").write_text(json.dumps(result, indent=1, default=float), encoding="utf-8")
    return result


def effect_auroc_table(frame: pd.DataFrame) -> dict:
    """PRESAGE effect stage: AUROC of the predicted norm for target detection, per arm (all items)."""
    return {arm: M.effect_auroc(g.norm.to_numpy(), g.target_detected.to_numpy(bool)) for arm, g in frame.groupby("arm")}


def run_one(task) -> str:
    """One (dataset, fold): write-once record files."""
    from threadpoolctl import threadpool_limits
    dataset, fold = task
    paths = [OUT / f"{dataset}_{r}_fold{fold}.parquet" for r in ("A0", "A1", "A2")]
    if any(p.exists() for p in paths):
        return f"{dataset} fold {fold}: records exist, skipped (write-once)"
    started = time.time()
    with threadpool_limits(limits=2):
        res = run_dataset(dataset, (fold,))
    for regime, path in zip(("A0", "A1", "A2"), paths):
        res[regime].to_parquet(path, index=False)
    with gzip.open(OUT / f"{dataset}_fits_fold{fold}.json.gz", "wt", encoding="utf-8") as f:
        json.dump(res["fits"], f, default=float)
    return f"{dataset} fold {fold}: {dict((r, len(res[r])) for r in ('A0', 'A1', 'A2'))} {time.time() - started:.0f}s"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("run", "analyse"))
    parser.add_argument("--workers", type=int, default=5)
    args = parser.parse_args()
    if args.command == "run":
        import multiprocessing as mp
        OUT.mkdir(parents=True, exist_ok=True)
        tasks = [(d, f) for d in ("sciplex3", "l1000") for f in SP.FOLDS]
        with mp.get_context("spawn").Pool(args.workers) as pool:
            for line in pool.imap_unordered(run_one, tasks):
                print(line, flush=True)
    print(json.dumps(analyse(), indent=1, default=float)[:5000])


if __name__ == "__main__":
    main()
