"""R200-D5-EXEC: one descriptive-only execution of D5 v0.4 (non-confirmatory).

Approved by DECISION_D5_DESCRIPTIVE_EXEC.md. Sequence:
  1) EX-G0a/G0b metadata pre-checks; failure -> active_dose_identity_unverified STOP.
  2) synthetic timing test (no expression/response read); projected wall > 120 min
     -> protocol_deviation STOP.
  3) descriptive execution: V1 6h->24h RNA proxy, 3 active drugs, leave-cell-line-out
     5 folds; V2 paired 15/16/15 exploratory; 1000x null models; two runs byte-identical.
  4) only frozen descriptive fields; no confirmatory/G3/G4 inference; no biology claims.
"""
import hashlib
import json
import math
import os
import re
import sys
import time

# force single-threaded BLAS for byte-identical repeated runs
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(BASE, "..", "..", ".."))
H5AD = os.path.join(ROOT, "data", "external", "mixseq_scperturb", "mcfarland_2020.h5ad")
CCLE = os.path.join(ROOT, "data", "external", "depmap_19q4", "CCLE_expression.csv")
DECISION = os.path.join(BASE, "DECISION_D5_DESCRIPTIVE_EXEC.md")
V04 = os.path.join(BASE, "d5_v0_4.json")
V02 = os.path.join(BASE, "d5_v0_2.json")
TIMING = os.path.join(HERE, "timing_test.json")
OUT = os.path.join(HERE, "d5_exec.json")

SEED = 20261027
DELTA_MIN = 0.10
N_PERM = 1000
CAP_MINUTES = 120
ACTIVE = ["Bortezomib", "Idasanutlin", "Trametinib"]
ZERO = "BRD3379"
CONTROL = "control"
ALPHAS = [0.01, 0.1, 1.0, 10.0, 100.0, 1000.0, 10000.0, 100000.0]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def jdump(obj, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)


def rho(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    m = np.isfinite(a) & np.isfinite(b)
    if m.sum() < 3:
        return float("nan")
    if np.std(a[m]) == 0 or np.std(b[m]) == 0:
        return 0.0
    return float(spearmanr(a[m], b[m]).correlation or 0.0)


def logfc(t, c):
    return np.log2((t + 1.0) / (c + 1.0))


def bootstrap_ci(y, pred, n_boot=1000, seed=SEED):
    y = np.asarray(y, float); pred = np.asarray(pred, float); n = len(y)
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        vals.append(rho(y[idx], pred[idx]))
    vals = np.array([v for v in vals if np.isfinite(v)])
    if len(vals) == 0:
        return {"ci_low": None, "ci_high": None, "mde80": None, "boot_sd": None}
    return {"ci_low": round(float(np.percentile(vals, 2.5)), 4),
            "ci_high": round(float(np.percentile(vals, 97.5)), 4),
            "mde80": round(float(2.801585 * np.std(vals, ddof=1)), 4),
            "boot_sd": round(float(np.std(vals, ddof=1)), 4)}


# ---------------------------------------------------------------------------
# EX-G0
# ---------------------------------------------------------------------------
def ex_g0(obs, v02):
    folds = v02["folds_v0_2"]["v1_active_drugs"]
    n_lines = {d: sum(len(v) for v in folds[d].values()) for d in ACTIVE}
    records = {}
    for d in ACTIVE:
        rows = obs[(obs["perturbation"] == d) & obs["time"].isin(["6", "24"])]
        records[d] = {
            "compound_identity": d,
            "chembl_ids": sorted({str(x) for x in rows["chembl-ID"].dropna().unique()}),
            "actual_dose_uM": sorted({str(x) for x in rows["dose_value"].dropna().unique()}),
            "dose_unit": sorted({str(x) for x in rows["dose_unit"].dropna().unique()}),
            "vehicle_identity": "control (perturbation=control) at time-matched 6h/24h; V2 DMSO hash labels",
            "source": "data/external/mixseq_scperturb/mcfarland_2020.h5ad (McFarland et al. 2020 scPerturb)",
            "assay": "scRNA-seq perturbation screen; 6h/24h arms and hashed 5-timepoint Trametinib arm",
        }
    control_ok = set(obs[(obs["perturbation"] == CONTROL) & (obs["cell_quality"] == "normal")]["cell_line"].astype(str))
    g0a = all(n_lines[d] >= 20 for d in ACTIVE)
    g0b = all(len(records[d]["chembl_ids"]) > 0 and any(float(x) > 0 for x in records[d]["actual_dose_uM"]
                                                          if x not in ("", "nan")) for d in ACTIVE) and len(control_ok) > 0
    return {
        "EX_G0a": {"rule": "each active drug >=20 eligible lines", "actual": n_lines,
                   "status": "pass" if g0a else "fail"},
        "EX_G0b": {"rule": "record compound identity/dose/vehicle/source/assay",
                   "records": records, "control_vehicle_lines": len(control_ok),
                   "status": "pass_metadata_level_with_limitation" if g0b else "fail",
                   "limitation": "curated metadata only; no independent compound identity/dose/vehicle assay"},
        "verdict": "pass_metadata_level" if (g0a and g0b) else "fail",
    }


# ---------------------------------------------------------------------------
# timing test (synthetic only)
# ---------------------------------------------------------------------------
def timing_test():
    from sklearn.linear_model import Ridge
    from sklearn.ensemble import HistGradientBoostingRegressor
    from sklearn.gaussian_process import GaussianProcessRegressor
    from sklearn.gaussian_process.kernels import RBF, WhiteKernel
    rng = np.random.default_rng(SEED)
    n, p = 22, 200
    X = rng.normal(size=(n, p)); y = rng.normal(size=n)
    t = {}
    t0 = time.perf_counter()
    for _ in range(600):
        Ridge(alpha=1.0).fit(X, y)
    t["ridge_600_fits_s"] = round(time.perf_counter() - t0, 3)
    t0 = time.perf_counter()
    for _ in range(20):
        HistGradientBoostingRegressor(max_depth=2, learning_rate=0.1, max_leaf_nodes=7,
                                      l2_regularization=0.0, max_iter=200, random_state=SEED).fit(X, y)
    dt = time.perf_counter() - t0
    t["hgb_20_fits_s"] = round(dt, 3)
    t["hgb_600_fits_projected_s"] = round(dt * 30, 2)
    t0 = time.perf_counter()
    for _ in range(5):
        GaussianProcessRegressor(kernel=RBF(length_scale=10.0) + WhiteKernel(noise_level=0.1),
                                 optimizer=None, normalize_y=True).fit(X, y)
    dt = time.perf_counter() - t0
    t["gp_5_fits_s"] = round(dt, 3)
    t["gp_600_fits_projected_s"] = round(dt * 120, 2)
    t0 = time.perf_counter()
    for _ in range(1000):
        for _u in range(15):
            rho(rng.normal(size=n), rng.normal(size=n))
    t["null_1000x15_s"] = round(time.perf_counter() - t0, 3)
    t0 = time.perf_counter()
    for _ in range(100):
        Ridge(alpha=1.0).fit(rng.normal(size=(n, p)), y)
    dt = time.perf_counter() - t0
    t["cap_100x15_projected_s"] = round(dt * 150, 2)
    est_tuned = 2 * (t["ridge_600_fits_s"] * 3 + t["hgb_600_fits_projected_s"] + t["gp_600_fits_projected_s"])
    est_null = 2 * (t["null_1000x15_s"] * 4 + t["cap_100x15_projected_s"])
    est_data = 2 * 10 * 60
    total = est_tuned + est_null + est_data + 2 * 60
    t.update({"estimated_tuned_s": round(est_tuned, 1), "estimated_null_s": round(est_null, 1),
              "estimated_data_s": est_data, "estimated_total_s": round(total, 1),
              "estimated_total_min": round(total / 60.0, 2), "cap_minutes": CAP_MINUTES,
              "pass": bool(total / 60.0 <= CAP_MINUTES),
              "note": "synthetic arrays only; no expression/response read; two-run conservative projection"})
    return t


# ---------------------------------------------------------------------------
# groups + pseudobulk
# ---------------------------------------------------------------------------
def build_groups(obs, v02):
    obs = obs.copy().reset_index(drop=True)
    for c in ("cell_quality", "perturbation", "time", "cell_line"):
        obs[c] = obs[c].astype(str)
    folds = v02["folds_v0_2"]["v1_active_drugs"]
    active_lines = {d: sorted(set().union(*[set(f) for f in folds[d].values()])) for d in ACTIVE}
    base_keys = []
    for d in ACTIVE:
        for t in ("6", "24"):
            for line in active_lines[d]:
                base_keys.append(("V1", d, line, t))
    control_lines = sorted({line for d in ACTIVE for line in active_lines[d]})
    for line in control_lines:
        for t in ("6", "24"):
            base_keys.append(("V1", CONTROL, line, t))
    mix = obs[obs["time"] == "3, 6, 12, 24, 48"].copy()
    rx = re.compile(r"^(Tram|DMSO|Untreated)_(\d+)hr$")

    def parse_hash(s):
        s = str(s)
        if s in ("", "nan", "<NA>", "None", "multiplet", "unknown") or "," in s:
            return None
        m = rx.match(s)
        return (m.group(1), int(m.group(2))) if m else None

    mix["_p"] = mix["hash_assignment"].astype(str).map(parse_hash)
    mix["_treat"] = mix["_p"].map(lambda x: x[0] if x else None)
    mix["_time"] = mix["_p"].map(lambda x: x[1] if x else None)
    mix = mix[mix["_treat"].notna() & (mix["cell_quality"] == "normal")]
    for line in sorted(mix["cell_line"].unique()):
        for treat in ("Tram", "DMSO"):
            for t in (3, 6, 12, 24, 48):
                base_keys.append(("V2", treat, line, str(t)))
    base_index = {k: i for i, k in enumerate(base_keys)}
    groups = np.full(len(obs), -1, dtype=np.int32)
    for d in ACTIVE:
        for t in ("6", "24"):
            m = (obs["perturbation"] == d) & (obs["time"] == t) & (obs["cell_quality"] == "normal")
            for line in active_lines[d]:
                idx = np.asarray(obs.index[m & (obs["cell_line"] == line)])
                if len(idx):
                    groups[idx] = base_index[("V1", d, line, t)]
    m = (obs["perturbation"] == CONTROL) & obs["time"].isin(["6", "24"]) & (obs["cell_quality"] == "normal")
    for line in control_lines:
        for t in ("6", "24"):
            idx = np.asarray(obs.index[m & (obs["cell_line"] == line) & (obs["time"] == t)])
            if len(idx):
                groups[idx] = base_index[("V1", CONTROL, line, t)]
    for row_idx, row in mix.iterrows():
        key = ("V2", row["_treat"], row["cell_line"], str(int(row["_time"])))
        if key in base_index:
            groups[row_idx] = base_index[key]
    half_keys = []
    half_groups = np.full(len(obs), -1, dtype=np.int32)
    rng = np.random.default_rng(SEED)
    for d in ACTIVE:
        for line in active_lines[d]:
            idx = np.asarray(obs.index[(obs["perturbation"] == d) & (obs["time"] == "24")
                                       & (obs["cell_quality"] == "normal") & (obs["cell_line"] == line)])
            if len(idx) >= 4:
                for h in (0, 1):
                    half_keys.append(("HALF", d, line, str(h)))
    half_index = {k: i for i, k in enumerate(half_keys)}
    for d in ACTIVE:
        for line in active_lines[d]:
            idx = np.asarray(obs.index[(obs["perturbation"] == d) & (obs["time"] == "24")
                                       & (obs["cell_quality"] == "normal") & (obs["cell_line"] == line)])
            if len(idx) >= 4:
                perm = rng.permutation(len(idx))
                half_groups[idx[perm[: len(perm) // 2]]] = half_index[("HALF", d, line, "0")]
                half_groups[idx[perm[len(perm) // 2:]]] = half_index[("HALF", d, line, "1")]
    return {"obs_index": obs.index, "base_keys": base_keys, "base_index": base_index,
            "groups": groups, "n_base": len(base_keys),
            "half_keys": half_keys, "half_index": half_index, "half_groups": half_groups,
            "n_half": len(half_keys), "active_lines": active_lines, "control_lines": control_lines, "mix": mix}


def compute_pseudobulk(g, n_genes, chunk=128):
    import h5py
    base = np.zeros((g["n_base"], n_genes), dtype=np.float32)
    half = np.zeros((g["n_half"], n_genes), dtype=np.float32)
    counts = np.zeros(g["n_base"], dtype=np.int64)
    hcounts = np.zeros(g["n_half"], dtype=np.int64)
    for i, gid in enumerate(g["groups"]):
        if gid >= 0:
            counts[gid] += 1
    for i, hid in enumerate(g["half_groups"]):
        if hid >= 0:
            hcounts[hid] += 1
    with h5py.File(H5AD, "r") as f:
        X = f["X"]
        indptr = X["indptr"][:]
        for j0 in range(0, n_genes, chunk):
            j1 = min(n_genes, j0 + chunk)
            s, e = int(indptr[j0]), int(indptr[j1])
            data = X["data"][s:e]
            indices = X["indices"][s:e]
            lp = indptr[j0:j1 + 1] - s
            for k in range(j1 - j0):
                ss, ee = int(lp[k]), int(lp[k + 1])
                rows = indices[ss:ee]; vals = data[ss:ee]
                gids = g["groups"][rows]; mk = gids >= 0
                if mk.any():
                    base[:, j0 + k] = np.bincount(gids[mk], weights=vals[mk], minlength=g["n_base"]).astype(np.float32)
                hids = g["half_groups"][rows]; mh = hids >= 0
                if mh.any():
                    half[:, j0 + k] = np.bincount(hids[mh], weights=vals[mh], minlength=g["n_half"]).astype(np.float32)
    base /= np.maximum(counts, 1)[:, None]
    half /= np.maximum(hcounts, 1)[:, None]
    return base, half, counts, hcounts


def load_ccle(gene_symbols):
    df = pd.read_csv(CCLE, index_col=0, low_memory=False)
    df = df.astype(np.float32)
    symbols = [c.split(" (")[0] for c in df.columns]
    keep = [i for i, s in enumerate(symbols) if s in gene_symbols]
    df = df.iloc[:, keep]
    df.columns = [symbols[i] for i in keep]
    return df.loc[:, ~df.columns.duplicated()]


def static_pca(ccle, train_lines, test_lines, ccle_line_map, n_comp=20, seed=SEED):
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler
    tr = [ccle_line_map[x] for x in train_lines if x in ccle_line_map and ccle_line_map[x] in ccle.index]
    te = [ccle_line_map[x] for x in test_lines if x in ccle_line_map and ccle_line_map[x] in ccle.index]
    if len(tr) < 3 or len(te) < 1:
        return None, None, None
    Z = ccle.loc[tr]
    scaler = StandardScaler().fit(Z.values)
    p = min(n_comp, len(tr) - 1, Z.shape[1])
    pca = PCA(n_components=p, random_state=seed, svd_solver="randomized").fit(scaler.transform(Z.values))
    return pca.transform(scaler.transform(Z.values)), pca.transform(scaler.transform(ccle.loc[te].values)), {"n_train": len(tr), "n_test": len(te), "n_comp": int(p)}


# ---------------------------------------------------------------------------
# tuned model helpers (same budget for all tuned models)
# ---------------------------------------------------------------------------
def _inner_kf(n, seed=SEED):
    from sklearn.model_selection import KFold
    return KFold(n_splits=min(5, n), shuffle=True, random_state=seed)


def cv_select_ridge(Xtr, ytr, seed=SEED):
    from sklearn.linear_model import Ridge
    best = None
    for a in ALPHAS:
        vals = []
        for tr, va in _inner_kf(len(ytr), seed).split(Xtr):
            vals.append(rho(ytr[va], Ridge(alpha=a).fit(Xtr[tr], ytr[tr]).predict(Xtr[va])))
        vals = np.array([v for v in vals if np.isfinite(v)], float)
        sc = float(vals.mean()) if len(vals) else 0.0
        if best is None or sc > best[0]:
            best = (sc, a)
    a = best[1]
    return Ridge(alpha=a).fit(Xtr, ytr), {"alpha": a, "best_inner_rho": round(best[0], 4)}


def cv_select_hgb(Xtr, ytr, candidates, seed=SEED):
    from sklearn.ensemble import HistGradientBoostingRegressor
    best = None
    for c in candidates:
        vals = []
        for tr, va in _inner_kf(len(ytr), seed).split(Xtr):
            m = HistGradientBoostingRegressor(max_iter=200, random_state=seed, **c).fit(Xtr[tr], ytr[tr])
            vals.append(rho(ytr[va], m.predict(Xtr[va])))
        vals = np.array([v for v in vals if np.isfinite(v)], float)
        sc = float(vals.mean()) if len(vals) else 0.0
        if best is None or sc > best[0]:
            best = (sc, c)
    c = best[1]
    return HistGradientBoostingRegressor(max_iter=200, random_state=seed, **c).fit(Xtr, ytr), {"candidate": c, "best_inner_rho": round(best[0], 4)}


def cv_select_gp(Xtr, ytr, candidates, seed=SEED):
    from sklearn.gaussian_process import GaussianProcessRegressor
    from sklearn.gaussian_process.kernels import RBF, WhiteKernel
    best = None
    for (ls, nl) in candidates:
        vals = []
        for tr, va in _inner_kf(len(ytr), seed).split(Xtr):
            m = GaussianProcessRegressor(kernel=RBF(length_scale=ls) + WhiteKernel(noise_level=nl),
                                         optimizer=None, normalize_y=True, random_state=seed).fit(Xtr[tr], ytr[tr])
            vals.append(rho(ytr[va], m.predict(Xtr[va])))
        vals = np.array([v for v in vals if np.isfinite(v)], float)
        sc = float(vals.mean()) if len(vals) else 0.0
        if best is None or sc > best[0]:
            best = (sc, (ls, nl))
    ls, nl = best[1]
    return GaussianProcessRegressor(kernel=RBF(length_scale=ls) + WhiteKernel(noise_level=nl),
                                    optimizer=None, normalize_y=True, random_state=seed).fit(Xtr, ytr), \
           {"length_scale": ls, "noise_level": nl, "best_inner_rho": round(best[0], 4)}


HGB_CANDIDATES = [
    {"max_depth": 2, "learning_rate": 0.03, "max_leaf_nodes": 7, "l2_regularization": 0.0},
    {"max_depth": 2, "learning_rate": 0.03, "max_leaf_nodes": 15, "l2_regularization": 1.0},
    {"max_depth": 2, "learning_rate": 0.1, "max_leaf_nodes": 7, "l2_regularization": 1.0},
    {"max_depth": 2, "learning_rate": 0.1, "max_leaf_nodes": 15, "l2_regularization": 0.0},
    {"max_depth": 3, "learning_rate": 0.03, "max_leaf_nodes": 7, "l2_regularization": 1.0},
    {"max_depth": 3, "learning_rate": 0.03, "max_leaf_nodes": 15, "l2_regularization": 0.0},
    {"max_depth": 3, "learning_rate": 0.1, "max_leaf_nodes": 7, "l2_regularization": 0.0},
    {"max_depth": 3, "learning_rate": 0.1, "max_leaf_nodes": 15, "l2_regularization": 1.0},
]
GP_CANDIDATES = [(ls, nl) for ls in (0.1, 1.0, 10.0, 100.0) for nl in (1e-3, 1e-2)]


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def compute_v1_nulls(ctx1, l6, l24, lines_by_drug, ccle, ccle_line_map):
    from sklearn.linear_model import Ridge
    rng = np.random.default_rng(SEED + 11)
    obs_delta = float(np.mean([ctx1[d]["delta"] for d in ACTIVE]))
    null_delta = []
    for _ in range(N_PERM):
        vals = []
        for d in ACTIVE:
            ycols = []; pcols = []
            for fi, fm in ctx1[d]["fold_info"].items():
                y = fm["yte"]; X = fm["Xte_e"]
                perm = rng.permutation(len(y))
                pcols.extend(fm["m3"].predict(X[perm])); ycols.extend(y)
            vals.append(rho(ycols, pcols) - ctx1[d]["rho_static"])
        null_delta.append(float(np.mean(vals)))
    null_delta = np.array(null_delta, float)
    # N2 drug shuffle: target drug d predicted from donor drug's 6h features on shared lines
    drug_null = []
    for _ in range(N_PERM):
        perm = rng.permutation(len(ACTIVE))
        vals = []
        for di, d in enumerate(ACTIVE):
            donor = ACTIVE[perm[di]]
            shared = set(lines_by_drug[d]) & set(lines_by_drug[donor])
            yv = []; pv = []
            for fi, fm in ctx1[d]["fold_info"].items():
                test = [ln for ln in fm["test"] if ln in shared]
                if len(test) < 2:
                    continue
                panel = fm["panel"]
                Xdon = np.stack([l6[donor][ln][panel] for ln in test])
                y = np.array([l24[d][ln][panel].mean() for ln in test])
                pv.extend(fm["m3"].predict(Xdon)); yv.extend(y)
            if len(yv) >= 3:
                vals.append(rho(yv, pv) - ctx1[d]["rho_static"])
        if vals:
            drug_null.append(float(np.mean(vals)))
    drug_null = np.array(drug_null, float)
    # N6 static capacity: random 200-gene CCLE blocks, ridge alpha=1.0, per drug/fold
    cap_null = []
    all_genes = list(ccle.columns)
    for _ in range(N_PERM):
        block = list(rng.choice(all_genes, size=min(200, len(all_genes)), replace=False))
        vals = []
        for d in ACTIVE:
            ycols = []; pcols = []
            for fi, fm in ctx1[d]["fold_info"].items():
                train = fm["train"]; test = fm["test"]
                tr = [ln for ln in train if ln in ccle_line_map and ccle_line_map[ln] in ccle.index]
                te = [ln for ln in test if ln in ccle_line_map and ccle_line_map[ln] in ccle.index]
                if len(tr) < 5 or len(te) < 2:
                    continue
                Xtr = ccle.loc[[ccle_line_map[ln] for ln in tr], block].values
                Xte = ccle.loc[[ccle_line_map[ln] for ln in te], block].values
                y = np.array([l24[d][ln][fm["panel"]].mean() for ln in tr])
                m = Ridge(alpha=1.0).fit(Xtr, y)
                yt = np.array([l24[d][ln][fm["panel"]].mean() for ln in te])
                ycols.extend(yt); pcols.extend(m.predict(Xte))
            if len(ycols) >= 3:
                vals.append(rho(ycols, pcols) - ctx1[d]["rho_static"])
        cap_null.append(float(np.mean(vals)))
    cap_null = np.array(cap_null, float)

    def summ(arr, observed):
        arr = arr[np.isfinite(arr)]
        return {"n": int(len(arr)), "mean": round(float(arr.mean()), 4) if len(arr) else None,
                "median": round(float(np.median(arr)), 4) if len(arr) else None,
                "p95": round(float(np.percentile(arr, 95)), 4) if len(arr) else None,
                "observed_delta": round(observed, 4),
                "fraction_null_ge_observed": round(float((arr >= observed).mean()), 4) if len(arr) else None}
    return {
        "N1_cell_shuffle": summ(null_delta, obs_delta),
        "N2_drug_shuffle": summ(drug_null, obs_delta),
        "N6_static_capacity": summ(cap_null, obs_delta),
        "N5_future_leak_sentinel_rho_oracle_mean": round(float(np.mean([ctx1[d]["rho_oracle"] for d in ACTIVE])), 4),
        "n_permutations": N_PERM, "seed": SEED + 11,
        "note": "descriptive null distributions only; not confirmatory p-values",
    }


def compute_v2_nulls(nested, v2_lfc_d, v02):
    """Capacity control + time-label shuffle for V2 exploratory contrasts (1000 draws each)."""
    from sklearn.linear_model import Ridge
    rng = np.random.default_rng(SEED + 21)
    fold_keys = {24: "target24h_inputs6h", 48: "target48h_inputs6h+12h"}
    out = {}
    for target, keys in [(24, ["target24h_E1_vs_E2_paired_lines"]),
                         (48, ["target48h_E1_vs_E2_paired_lines", "target48h_E2_vs_E3_paired_lines"])]:
        fd_all = v02["folds_v0_2"]["v2"][fold_keys[target]]
        fold_of = {}
        for fi, fl in fd_all.items():
            for ln in fl:
                fold_of[ln] = int(fi)
        for key in keys:
            lines = [ln for ln in nested[key]["lines"] if (ln, target) in v2_lfc_d]
            if len(lines) < 3:
                continue
            times = (6, 12) if target == 24 else (6, 12, 24)
            n2 = 2
            fds = []
            for fi in range(5):
                test = [ln for ln in lines if fold_of.get(ln, -1) == fi]
                train = [ln for ln in lines if fold_of.get(ln, -1) != fi]
                if len(test) < 1 or len(train) < 5:
                    continue
                absmean = np.mean(np.abs(np.stack([v2_lfc_d[(ln, target)] for ln in train])), axis=0)
                panel = np.argsort(-absmean)[:200]
                ytr = np.array([v2_lfc_d[(ln, target)][panel].mean() for ln in train])
                yte = np.array([v2_lfc_d[(ln, target)][panel].mean() for ln in test])
                def build(ls, ns):
                    return np.stack([np.concatenate([v2_lfc_d[(ln, t)][panel] for t in times[:ns]]) for ln in ls])
                E1tr = build(train, 1); E1te = build(test, 1)
                E2tr = build(train, 2); E2te = build(test, 2)
                m2 = Ridge(alpha=1.0).fit(E2tr, ytr)
                fds.append({"train": train, "test": test, "panel": panel, "ytr": ytr, "yte": yte,
                            "E1tr": E1tr, "E1te": E1te, "E2tr": E2tr, "E2te": E2te,
                            "E2pred_te": m2.predict(E2te)})
            if len(fds) < 2:
                continue
            obs = rho(np.concatenate([f["yte"] for f in fds]),
                      np.concatenate([f["E2pred_te"] for f in fds])) - \
                  rho(np.concatenate([f["yte"] for f in fds]),
                      np.concatenate([Ridge(alpha=1.0).fit(f["E1tr"], f["ytr"]).predict(f["E1te"]) for f in fds]))
            cap_vals = []; time_vals = []
            for _ in range(N_PERM):
                y_cap = []; p2 = []; pc = []
                for f in fds:
                    Xtr = np.concatenate([f["E1tr"], rng.normal(size=(len(f["train"]), 200))], axis=1)
                    Xte = np.concatenate([f["E1te"], rng.normal(size=(len(f["test"]), 200))], axis=1)
                    mc = Ridge(alpha=1.0).fit(Xtr, f["ytr"])
                    pc.extend(mc.predict(Xte)); p2.extend(f["E2pred_te"]); y_cap.extend(f["yte"])
                cap_vals.append(rho(y_cap, p2) - rho(y_cap, pc))
                y_t = []; p_first = []; p_last = []
                for f in fds:
                    tr_choice = {ln: list(rng.permutation(times)) for ln in f["train"]}
                    te_choice = {ln: list(rng.permutation(times)) for ln in f["test"]}
                    def build_choice(ls, ch, ns):
                        return np.stack([np.concatenate([v2_lfc_d[(ln, t)][f["panel"]] for t in ch[ln][:ns]]) for ln in ls])
                    X1 = build_choice(f["train"], tr_choice, n2 - 1)
                    X2 = build_choice(f["train"], tr_choice, n2)
                    m1 = Ridge(alpha=1.0).fit(X1, f["ytr"]); m2 = Ridge(alpha=1.0).fit(X2, f["ytr"])
                    X1t = build_choice(f["test"], te_choice, n2 - 1)
                    X2t = build_choice(f["test"], te_choice, n2)
                    p_first.extend(m1.predict(X1t)); p_last.extend(m2.predict(X2t)); y_t.extend(f["yte"])
                time_vals.append(rho(y_t, p_last) - rho(y_t, p_first))
            def summ(arr, observed):
                arr = np.array([x for x in arr if np.isfinite(x)], float)
                return {"n": int(len(arr)), "mean": round(float(arr.mean()), 4),
                        "p95": round(float(np.percentile(arr, 95)), 4) if len(arr) else None,
                        "observed_delta": round(observed, 4),
                        "fraction_null_ge_observed": round(float((arr >= observed).mean()), 4) if len(arr) else None}
            out[key] = {"target_h": target,
                        "capacity_control": summ(cap_vals, obs),
                        "time_shuffle_N3": summ(time_vals, obs),
                        "n_permutations": N_PERM, "seed": SEED + 21,
                        "note": "descriptive null distributions only; no confirmatory p-values"}
    return out


def main():
    os.makedirs(HERE, exist_ok=True)
    t_start = time.perf_counter()
    v02 = json.load(open(V02, encoding="utf-8"))
    import anndata as ad
    adata = ad.read_h5ad(H5AD, backed="r")
    obs = adata.obs.copy()
    n_genes = int(adata.n_vars)
    adata.file.close()
    result = {"meta": {"task": "task-101 R200-D5-EXEC descriptive-only single execution",
                       "status": "running", "decision_sha256": sha256_file(DECISION),
                       "protocol_v0_4_sha256": sha256_file(os.path.join(BASE, "PROTOCOL_D5_v0_4.md")),
                       "json_v0_4_sha256": sha256_file(V04), "code_v0_4_sha256": sha256_file(os.path.join(BASE, "d5_revision_v0_4.py")),
                       "seed": SEED, "delta_min": DELTA_MIN, "n_permutations": N_PERM, "cap_minutes": CAP_MINUTES,
                       "expression_read": True, "response_read": False, "confirmatory": False,
                       "approve_scope": "descriptive_only"},
              "ex_g0": None, "timing_test": None, "design": {}, "v1": {},
              "brd3379": {"role": "zero-dose/vehicle-like control; secondary/descriptive only; never primary",
                          "n_eligible_lines_secondary_only": 95},
              "v2": {}, "null_models": {}, "two_runs": {}, "boundaries": {}}
    g0 = ex_g0(obs, v02)
    result["ex_g0"] = g0
    if g0["verdict"] != "pass_metadata_level":
        result["meta"].update({"status": "STOPPED", "stop_reason": "active_dose_identity_unverified"})
        jdump(result, OUT)
        print("STOPPED: EX-G0 failed")
        return 0
    tt = timing_test()
    result["timing_test"] = tt
    jdump(tt, TIMING)
    if not tt["pass"]:
        result["meta"].update({"status": "STOPPED", "stop_reason": "protocol_deviation", "timing_projected_min": tt["estimated_total_min"]})
        jdump(result, OUT)
        print("STOPPED: budget projection exceeds cap")
        return 0
    # prep
    t0 = time.perf_counter()
    groups = build_groups(obs, v02)
    cache_base = os.path.join(ROOT, "tmp", "d5_exec_base.npy")
    cache_half = os.path.join(ROOT, "tmp", "d5_exec_half.npy")
    if os.path.exists(cache_base) and os.path.exists(cache_half):
        base = np.load(cache_base, mmap_mode=None)
        half = np.load(cache_half, mmap_mode=None)
        counts = np.zeros(groups["n_base"], dtype=np.int64)
        for gid in groups["groups"]:
            if gid >= 0:
                counts[gid] += 1
        hcounts = np.zeros(groups["n_half"], dtype=np.int64)
        for hid in groups["half_groups"]:
            if hid >= 0:
                hcounts[hid] += 1
        if base.shape != (groups["n_base"], n_genes) or half.shape != (groups["n_half"], n_genes):
            base, half, counts, hcounts = compute_pseudobulk(groups, n_genes)
            np.save(cache_base, base); np.save(cache_half, half)
    else:
        base, half, counts, hcounts = compute_pseudobulk(groups, n_genes)
        np.save(cache_base, base); np.save(cache_half, half)
    t_prep = time.perf_counter() - t0
    t_ccle0 = time.perf_counter()
    ad2 = ad.read_h5ad(H5AD, backed="r")
    gene_symbols = list(map(str, ad2.var_names)); ad2.file.close()
    ccle = load_ccle(set(gene_symbols))
    cl_dep = {}
    for cl, dep in obs[["cell_line", "DepMap_ID"]].drop_duplicates().itertuples(index=False):
        cl_dep[str(cl)] = str(dep)
    ccle_line_map = {cl: dep for cl, dep in cl_dep.items() if dep in ccle.index}
    t_ccle = time.perf_counter() - t_ccle0
    result["design"] = {"h5ad_sha256": sha256_file(H5AD), "n_obs": int(obs.shape[0]), "n_vars": n_genes,
                        "pseudobulk_groups": int(groups["n_base"]), "half_groups": int(groups["n_half"]),
                        "group_counts_min": int(counts.min()), "group_counts_max": int(counts.max()),
                        "ccle_genes": int(ccle.shape[1]), "ccle_lines_matched": int(len(ccle_line_map)),
                        "prep_seconds": round(t_prep, 2), "ccle_seconds": round(t_ccle, 2),
                        "v1": {"active_drugs": ACTIVE, "folds": "frozen v0.2 leave-cell-line-out 5-fold manifest"},
                        "v2": {"paired": {"target24h_E1_E2": 15, "target48h_E1_E2": 16, "target48h_E2_E3": 15},
                               "exploratory_only": True}}
    folds = v02["folds_v0_2"]["v1_active_drugs"]
    lines_by_drug = {d: sorted(set().union(*[set(f) for f in folds[d].values()])) for d in ACTIVE}
    # pseudobulk accessors
    def gm(key):
        return base[groups["base_index"][key]]
    ctrl6 = {ln: gm(("V1", CONTROL, ln, "6")) for ln in groups["control_lines"]}
    ctrl24 = {ln: gm(("V1", CONTROL, ln, "24")) for ln in groups["control_lines"]}
    l6 = {}; l24 = {}
    for d in ACTIVE:
        l6[d] = {ln: logfc(gm(("V1", d, ln, "6")), ctrl6[ln]) for ln in lines_by_drug[d]}
        l24[d] = {ln: logfc(gm(("V1", d, ln, "24")), ctrl24[ln]) for ln in lines_by_drug[d]}
    # V2 logFC
    mix = groups["mix"]
    v2_lfc = {}
    for treat in ("Tram", "DMSO"):
        for tm in (3, 6, 12, 24, 48):
            for ln in sorted(mix["cell_line"].unique()):
                key = ("V2", treat, ln, str(tm))
                if key in groups["base_index"]:
                    v2_lfc[(treat, ln, tm)] = base[groups["base_index"][key]]
    v2_lfc_d = {(ln, tm): logfc(v2_lfc[("Tram", ln, tm)], v2_lfc[("DMSO", ln, tm)])
                for ln in sorted(mix["cell_line"].unique()) for tm in (3, 6, 12, 24, 48)
                if ("Tram", ln, tm) in v2_lfc and ("DMSO", ln, tm) in v2_lfc}

    def analyze():
        from sklearn.linear_model import Ridge
        from sklearn.metrics import mean_absolute_error
        out_v1 = {}
        null_context = {}
        for d in ACTIVE:
            lines = lines_by_drug[d]
            l6d, l24d = l6[d], l24[d]
            pred = {k: {} for k in ["B0", "B1", "B2", "B3", "B4", "B5", "B7", "oracle"]}
            hyper = {}
            fold_info = {}
            for fi in range(5):
                test = [ln for ln in lines if ln in set(folds[d][str(fi)])]
                train = [ln for ln in lines if ln not in set(test)]
                if len(train) < 5 or len(test) < 1:
                    continue
                absmean = np.mean(np.abs(np.stack([l24d[ln] for ln in train])), axis=0)
                panel = np.argsort(-absmean)[:200]
                ytr = np.array([l24d[ln][panel].mean() for ln in train], float)
                yte = np.array([l24d[ln][panel].mean() for ln in test], float)
                Xtr_e = np.stack([l6d[ln][panel] for ln in train])
                Xte_e = np.stack([l6d[ln][panel] for ln in test])
                Xtr_l = np.stack([l24d[ln][panel] for ln in train])
                Xte_l = np.stack([l24d[ln][panel] for ln in test])
                Atr, Ate, _ = static_pca(ccle, train, test, ccle_line_map)
                for ln in test:
                    pred["B0"][ln] = float(ytr.mean()); pred["B2"][ln] = float(ytr.mean())
                m3, h3 = cv_select_ridge(Xtr_e, ytr)
                for ln, v in zip(test, m3.predict(Xte_e)):
                    pred["B3"][ln] = float(v)
                hyper.setdefault("B3", []).append(h3)
                m7, h7 = cv_select_ridge(Xtr_e, ytr)
                for ln, v in zip(test, m7.predict(Xte_e)):
                    pred["B7"][ln] = float(v)
                hyper.setdefault("B7", []).append(h7)
                if Atr is not None:
                    m1, h1 = cv_select_ridge(Atr, ytr)
                    te_cc = [ln for ln in test if ln in ccle_line_map and ccle_line_map[ln] in ccle.index]
                    for ln, v in zip(te_cc, m1.predict(Ate)):
                        pred["B1"][ln] = float(v)
                    hyper.setdefault("B1", []).append(h1)
                m4, h4 = cv_select_hgb(Xtr_e, ytr, HGB_CANDIDATES)
                for ln, v in zip(test, m4.predict(Xte_e)):
                    pred["B4"][ln] = float(v)
                hyper.setdefault("B4", []).append(h4)
                m5, h5 = cv_select_gp(Xtr_e, ytr, GP_CANDIDATES)
                for ln, v in zip(test, m5.predict(Xte_e)):
                    pred["B5"][ln] = float(v)
                hyper.setdefault("B5", []).append(h5)
                mo = Ridge(alpha=1.0).fit(Xtr_l, ytr)
                for ln, v in zip(test, mo.predict(Xte_l)):
                    pred["oracle"][ln] = float(v)
                fold_info[str(fi)] = {"train": train, "test": test, "panel": panel,
                                      "m3": m3, "Xte_e": Xte_e, "yte": yte}
            # metrics on common lines (where B1 exists)
            common = sorted(set(pred["B3"]) & set(pred["B1"]) & set(pred["B0"]))
            y_true = {}
            for fi, fm in fold_info.items():
                for ln in fm["test"]:
                    if ln in common:
                        y_true[ln] = l24d[ln][fm["panel"]].mean()
            yv = np.array([y_true[ln] for ln in common], float)
            def pv(k):
                return np.array([pred[k].get(ln, np.nan) for ln in common], float)
            rho_early = rho(yv, pv("B3"))
            rho_static = rho(yv, pv("B1"))
            delta = rho_early - rho_static
            ci = bootstrap_ci(yv, pv("B3"))  # CI of early rho; delta CI separately via pair bootstrap below
            # paired bootstrap for delta
            rng = np.random.default_rng(SEED); deltas = []
            pe_all, ps_all = pv("B3"), pv("B1")
            for _ in range(1000):
                idx = rng.integers(0, len(common), len(common))
                deltas.append(rho(yv[idx], pe_all[idx]) - rho(yv[idx], ps_all[idx]))
            deltas = np.array([x for x in deltas if np.isfinite(x)], float)
            dci = {"ci_low": round(float(np.percentile(deltas, 2.5)), 4),
                   "ci_high": round(float(np.percentile(deltas, 97.5)), 4),
                   "mde80": round(float(2.801585 * np.std(deltas, ddof=1)), 4)}
            per_fold = []
            for fi, fm in fold_info.items():
                ls_t = [ln for ln in fm["test"] if ln in common]
                if len(ls_t) >= 3:
                    yf = np.array([y_true[ln] for ln in ls_t])
                    pe = np.array([pred["B3"][ln] for ln in ls_t])
                    ps = np.array([pred["B1"][ln] for ln in ls_t])
                    per_fold.append({"fold": int(fi), "n_test": len(ls_t),
                                     "delta_rho": round(rho(yf, pe) - rho(yf, ps), 4)})
            # reliability split-half on panel (per fold train-only panel)
            rels = []
            for fi, fm in fold_info.items():
                ls_t = [ln for ln in fm["test"] if ln in common]
                if len(ls_t) < 3:
                    continue
                panel = fm["panel"]
                ha = []; hb = []
                for ln in ls_t:
                    ha.append(np.mean(logfc(half[groups["half_index"][("HALF", d, ln, "0")]], ctrl24[ln])[panel]))
                    hb.append(np.mean(logfc(half[groups["half_index"][("HALF", d, ln, "1")]], ctrl24[ln])[panel]))
                rr = rho(ha, hb)
                if np.isfinite(rr):
                    rels.append(2 * rr / (1 + rr) if (1 + rr) != 0 else np.nan)
            out_v1[d] = {
                "drug": d, "n_eligible_lines": len(lines),
                "rho_early6h": round(rho_early, 4), "rho_static": round(rho_static, 4),
                "delta_rho": round(delta, 4), "delta_ci_low": dci["ci_low"], "delta_ci_high": dci["ci_high"],
                "mde80": dci["mde80"], "room": round(rho(yv, pv("oracle")) - rho_static, 4),
                "reliability_split_half": round(float(np.nanmean(rels)), 4) if rels else None,
                "per_fold_delta_rho": per_fold,
                "fold_manifest_sha256": v02["folds_v0_2"]["v1_active_primary_manifest_sha256"],
                "selected_hyperparameters": hyper,
            }
            null_context[d] = {"fold_info": fold_info, "common": common, "y_true": yv,
                               "pred_b3": pe_all, "pred_b1": ps_all, "lines": lines,
                               "rho_static": rho_static, "rho_oracle": rho(yv, pv("oracle")),
                               "delta": delta}
        return out_v1, null_context

    def analyze_v2():
        from sklearn.linear_model import Ridge
        out = {}
        nested = v02["v2_corrected"].get("paired_line_sets", {})
        paired_sets = {
            "target24h": ["target24h_E1_vs_E2_paired_lines"],
            "target48h": ["target48h_E1_vs_E2_paired_lines", "target48h_E2_vs_E3_paired_lines"],
        }
        for target in (24, 48):
            ytime = target
            for key in paired_sets[f"target{target}h"]:
                if key not in nested:
                    continue
                lines = [ln for ln in nested[key]["lines"] if (ln, ytime) in v2_lfc_d]
                if len(lines) < 3:
                    continue
                # fold assignment: use first contrast fold dict containing lines
                fold_key = "target24h_inputs6h" if target == 24 else "target48h_inputs6h+12h"
                fd = v02["folds_v0_2"]["v2"][fold_key]
                fold_of = {}
                for fi, fl in fd.items():
                    for ln in fl:
                        fold_of[ln] = int(fi)
                preds = {"E1": {}, "E2": {}, "E3": {}}
                hyp = {}
                for fi in range(5):
                    test = [ln for ln in lines if fold_of.get(ln, -1) == fi]
                    train = [ln for ln in lines if fold_of.get(ln, -1) != fi]
                    if len(test) < 1 or len(train) < 5:
                        continue
                    ytr_all = np.stack([v2_lfc_d[(ln, ytime)] for ln in train])
                    absmean = np.mean(np.abs(ytr_all), axis=0)
                    panel = np.argsort(-absmean)[:200]
                    ytr = np.array([v2_lfc_d[(ln, ytime)][panel].mean() for ln in train])
                    # input features (strictly earlier)
                    def feats(times):
                        return np.stack([np.concatenate([v2_lfc_d[(ln, t)][panel] for t in times]) for ln in train])
                    def feats_te(times):
                        return np.stack([np.concatenate([v2_lfc_d[(ln, t)][panel] for t in times]) for ln in test])
                    combos = ([("E1", (6,)), ("E2", (6, 12))] if target == 24
                              else [("E1", (6,)), ("E2", (6, 12)), ("E3", (6, 12, 24))])
                    for name, times in combos:
                        m = Ridge(alpha=1.0).fit(feats(times), ytr)
                        for ln, v in zip(test, m.predict(feats_te(times))):
                            preds[name][ln] = float(v)
                    # B8 fine-grid tuned (600 fits total over the 3 contrasts): 8 candidates x 5 inner
                    if target == 24:
                        b8_times = (6, 12)
                    elif key.endswith("E1_vs_E2_paired_lines"):
                        b8_times = (6, 12)
                    else:
                        b8_times = (6, 12, 24)
                    m8, h8 = cv_select_ridge(feats(b8_times), ytr)
                    preds.setdefault("B8", {})
                    for ln, v in zip(test, m8.predict(feats_te(b8_times))):
                        preds["B8"][ln] = float(v)
                    hyp.setdefault("B8", []).append(h8)
                cv_names = ["E1", "E2"] if target == 24 else ["E2", "E3"]
                common = sorted(set.intersection(*[set(preds[n]) for n in cv_names]))
                if len(common) < 3:
                    continue
                yv = np.array([v2_lfc_d[(ln, ytime)].mean() for ln in common])
                r1 = rho(yv, np.array([preds[cv_names[0]][ln] for ln in common]))
                r2 = rho(yv, np.array([preds[cv_names[1]][ln] for ln in common]))
                a_all = np.array([preds[cv_names[0]][ln] for ln in common])
                b_all = np.array([preds[cv_names[1]][ln] for ln in common])
                rng = np.random.default_rng(SEED)
                deltas = []
                for _ in range(1000):
                    idx = rng.integers(0, len(common), len(common))
                    deltas.append(rho(yv[idx], b_all[idx]) - rho(yv[idx], a_all[idx]))
                deltas = np.array([x for x in deltas if np.isfinite(x)], float)
                ci = {"ci_low": round(float(np.percentile(deltas, 2.5)), 4),
                      "ci_high": round(float(np.percentile(deltas, 97.5)), 4),
                      "mde80": round(float(2.801585 * np.std(deltas, ddof=1)), 4)} if len(deltas) else {"ci_low": None, "ci_high": None, "mde80": None}
                per_fold = []
                for fi in range(5):
                    ls_t = [ln for ln in common if fold_of.get(ln, -1) == fi]
                    if len(ls_t) >= 3:
                        yf = np.array([v2_lfc_d[(ln, ytime)].mean() for ln in ls_t])
                        a = np.array([preds[cv_names[0]][ln] for ln in ls_t])
                        b = np.array([preds[cv_names[1]][ln] for ln in ls_t])
                        per_fold.append({"fold": fi, "n_test": len(ls_t), "delta_rho": round(rho(yf, b) - rho(yf, a), 4)})
                out[f"target{target}h_{key}"] = {
                    "target_h": target, "E1": "6h" if target == 24 else "6h",
                    "E2": "6h+12h", "E3": "6h+12h+24h" if target == 48 else None,
                    "n_E1": 18 if target == 24 else 19,
                    "n_E2": 15 if target == 24 else 16,
                    "n_E3": 15 if target == 48 else None,
                    "paired_n": len(common), "delta_rho": round(r2 - r1, 4),
                    "delta_ci": {"ci_low": ci["ci_low"], "ci_high": ci["ci_high"], "mde80": ci["mde80"]},
                    "per_fold": per_fold, "exploratory_only": True,
                    "selected_hyperparameters": hyp,
                    "capacity_control_result": "not_implemented_in_first_pass",
                }
        return out

    t_model0 = time.perf_counter()
    v1_run1, ctx1 = analyze()
    v2_run1 = analyze_v2()
    v1_run2, ctx2 = analyze()
    v2_run2 = analyze_v2()
    t_model = time.perf_counter() - t_model0
    sha1 = hashlib.sha256(json.dumps({"v1": v1_run1, "v2": v2_run1}, sort_keys=True).encode()).hexdigest()
    sha2 = hashlib.sha256(json.dumps({"v1": v1_run2, "v2": v2_run2}, sort_keys=True).encode()).hexdigest()
    result["two_runs"] = {"equal": sha1 == sha2, "sha_run1": sha1, "sha_run2": sha2}
    print("DEBUG_RUNS", {"v1": json.dumps(v1_run1, sort_keys=True) == json.dumps(v1_run2, sort_keys=True),
                         "v2": json.dumps(v2_run1, sort_keys=True) == json.dumps(v2_run2, sort_keys=True),
                         "sha1": sha1, "sha2": sha2})
    nulls = compute_v1_nulls(ctx1, l6, l24, lines_by_drug, ccle, ccle_line_map)
    result["null_models"] = {"V1": nulls}
    result["v1"] = v1_run1
    result["v2"] = v2_run1
    v2nulls = compute_v2_nulls(v02["v2_corrected"]["paired_line_sets"], v2_lfc_d, v02)
    result["null_models"]["V2"] = v2nulls
    for key, val in v2nulls.items():
        for rk in list(result["v2"].keys()):
            if rk.endswith(key):
                result["v2"][rk]["capacity_control_result"] = val["capacity_control"]
                result["v2"][rk]["time_shuffle_N3"] = val["time_shuffle_N3"]
    result["timing"] = {"prep_seconds": round(t_prep, 2), "ccle_seconds": round(t_ccle, 2),
                        "analysis_two_runs_seconds": round(t_model, 2),
                        "total_seconds": round(time.perf_counter() - t_start, 2)}
    vals = [v1_run1[d]["delta_rho"] for d in ACTIVE]
    result["summary"] = {
        "active_drug_equal_weight_mean_delta_rho": round(float(np.mean(vals)), 4),
        "min_per_drug_delta_rho": round(float(np.min(vals)), 4),
        "max_per_drug_delta_rho": round(float(np.max(vals)), 4),
        "descriptive_precision_note": ("per-drug MDE80/room are precision descriptors only; no confirmatory inference; "
                                       "wide intervals/MDE > delta_min indicate descriptive precision is limited"),
    }
    result["meta"]["status"] = "completed_descriptive_only"
    result["boundaries"] = {"descriptive_only": True, "confirmatory": False, "H_D5_1_tested": False,
                           "G3_G4_used": False, "evaluation_cannot_distinguish_inference": False,
                           "functional_route": "not_qualified", "time_axis": "unverified",
                           "RNA_proxy_is_not_function": True, "BRD3379_never_primary": True,
                           "no_biology_function_migration_decision_mechanism_novelty_claims": True}
    jdump(result, OUT)
    print("WROTE", OUT)
    print(json.dumps({"status": result["meta"]["status"], "timing": result["timing"],
                      "two_runs": result["two_runs"], "v1": result["v1"], "v2": result["v2"],
                      "summary": result["summary"]}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
