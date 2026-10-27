"""ON3 reference implementation (DRAFT v0.2 semantics; no effect run).

Pure-numpy components for:
  - deterministic member-block mask selection (8/38 drugs, SHA256 key + seed)
  - unit/context static fixture encoding (generic arrays, no response values read here)
  - B2 static strong baseline (cell-blind partner x member-pair lookup + backoff)
  - B4 hierarchical + low-rank conditional model (static effects, pair factors V by ALS,
    held-out cell c_cell/U_cell from NON-masked context only)
  - metrics (Spearman, MAE, top-k appendix), paired-by-cell bootstrap
  - B6 null calibration (two frozen semantics: refit_cu_only vs full_refit)
  - model-free symbolic reconstruction audit (DSU on g(c,pair) nodes of unmasked units)
  - context-ablation diagnostic (DESCRIPTIVE only; not a binary leakage gate)
  - pure cold-cell sensitivity (all held-out units masked; no context)
  - output schema validator

This module is used by tests/budget/selfcheck only; it does NOT implement the ON3 effect run.
All functions are deterministic given inputs/seed.
"""
from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

import numpy as np

SEED_MASK = "20261130"
MASK_FRAC_DRUGS = 0.20
MDE80 = 0.0287644381
DELTA_MIN = 0.10
N_PERM = 1000
BOOT_B = 5000
ALS_MAX_ITER = 25
ALS_TOL = 1e-6


# ---------------------------------------------------------------- mask
def normalize(name: str) -> str:
    import unicodedata
    return "".join(ch for ch in unicodedata.normalize("NFKC", str(name)).casefold() if ch.isalnum())


def select_masked_members(drugs: Sequence[str], seed: str = SEED_MASK, frac: float = MASK_FRAC_DRUGS) -> List[str]:
    """Frozen member selection: SHA256('ON3v0.2|M|seed|norm') ascending, first ceil(frac*n)."""
    ds = sorted(set(normalize(d) for d in drugs))
    k = int(math.ceil(frac * len(ds)))
    ranked = sorted(ds, key=lambda g: hashlib.sha256(("ON3v0.2|M|%s|%s" % (seed, g)).encode()).hexdigest())
    return sorted(ranked[:k])


def unit_is_masked(partner: str, a: str, ap: str, M: Sequence[str]) -> bool:
    S = set(M)
    return (normalize(partner) in S) or (normalize(a) in S) or (normalize(ap) in S)


def build_mask(partners: np.ndarray, a: np.ndarray, ap: np.ndarray, M: Sequence[str]) -> np.ndarray:
    S = set(normalize(x) for x in M)
    return np.array([(normalize(partners[i]) in S) or (normalize(a[i]) in S) or (normalize(ap[i]) in S)
                     for i in range(len(partners))], dtype=bool)


# ---------------------------------------------------------------- symbolic reconstruction audit
class DSU:
    def __init__(self):
        self.p = {}

    def find(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[ra] = rb


def reconstruction_audit(cells, partners, a, ap, masked) -> Dict[str, int]:
    """Model-free audit: nodes g(cell,{x,y}); unmasked units are edges (same partner).
    Masked unit reconstructable iff its two endpoint pair-nodes are in same DSU component of
    the unmasked-edge graph.  Returns counts/denominator (denominator = number of masked units).
    """
    dsu = DSU()
    for c, p, x, y, m in zip(cells, partners, a, ap, masked):
        if m:
            continue
        n1 = (c, tuple(sorted((normalize(x), normalize(p)))))
        n2 = (c, tuple(sorted((normalize(y), normalize(p)))))
        dsu.union(n1, n2)
    total = int(np.sum(masked))
    recon = 0
    for c, p, x, y, m in zip(cells, partners, a, ap, masked):
        if not m:
            continue
        n1 = (c, tuple(sorted((normalize(x), normalize(p)))))
        n2 = (c, tuple(sorted((normalize(y), normalize(p)))))
        if n1 in dsu.p and n2 in dsu.p and dsu.find(n1) == dsu.find(n2):
            recon += 1
    return {"masked_units": total, "reconstructable_units": recon,
            "reconstruction_rate": (recon / total) if total else None}


# ---------------------------------------------------------------- fixture encoding
def encode_fixture(units: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
    """Add compact integer codes: pair_id = sorted(normalized member pair), partner_id, role_id."""
    def key(x, y):
        return tuple(sorted((normalize(x), normalize(y))))
    pair_keys = [key(units["a"][i], units["ap"][i]) for i in range(len(units["a"]))]
    uniq = {k: i for i, k in enumerate(sorted(set(pair_keys)))}
    part = {k: i for i, k in enumerate(sorted(set(normalize(x) for x in units["partner"])))}
    out = dict(units)
    out["pair_id"] = np.array([uniq[k] for k in pair_keys], dtype=np.int64)
    out["partner_id"] = np.array([part[normalize(x)] for x in units["partner"]], dtype=np.int64)
    out["role_id"] = np.array([0 if normalize(r) == "a" else 1 for r in units["role"]], dtype=np.int64)
    out["pair_keys"] = pair_keys
    out["n_pairs"] = len(uniq)
    return out


# ---------------------------------------------------------------- B2 static strong baseline
def fit_b2(train: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
    """cell-blind partner x member-pair means + backoff (role x partner -> global)."""
    y = np.asarray(train["y"], dtype=float)
    pair = train["pair_id"]
    part = train["partner_id"]
    role = train["role_id"]
    g = float(y.mean())
    # role x partner means
    rp = {}
    for p in range(int(part.max()) + 1):
        for r in range(2):
            m = (part == p) & (role == r)
            rp[(p, r)] = float(y[m].mean()) if m.any() else None
    # partner x pair means
    pp = {}
    for p, q in zip(part, pair):
        pp.setdefault((p, q), []).append(1)
    pp_sum = {}
    counts = {}
    for yi, p, q in zip(y, part, pair):
        pp_sum[(p, q)] = pp_sum.get((p, q), 0.0) + float(yi)
        counts[(p, q)] = counts.get((p, q), 0) + 1
    return {"global": g, "rp": rp, "pair_partner_sum": pp_sum, "pair_partner_n": counts}


def predict_b2(model: Dict[str, np.ndarray], units: Dict[str, np.ndarray]) -> np.ndarray:
    out = np.empty(len(units["pair_id"]), dtype=float)
    for i, (p, q, r) in enumerate(zip(units["partner_id"], units["pair_id"], units["role_id"])):
        n = model["pair_partner_n"].get((p, q), 0)
        if n:
            out[i] = model["pair_partner_sum"][(p, q)] / n
        else:
            v = model["rp"].get((int(p), int(r)))
            out[i] = v if v is not None else model["global"]
    return out


# ---------------------------------------------------------------- B4 hierarchical + low-rank
def _ridge_solve(A: np.ndarray, b: np.ndarray, lam: float) -> np.ndarray:
    d = A.shape[1]
    return np.linalg.solve(A.T @ A + lam * np.eye(d), A.T @ b)


def fit_pair_factors(resid_matrix: np.ndarray, obs_mask: np.ndarray, rank: int, lam: float,
                     seed: int = int(SEED_MASK)) -> Tuple[np.ndarray, np.ndarray]:
    """ALS on cells x pairs residual matrix (obs_mask bool). Returns U (cells x rank), V (pairs x rank)."""
    n_cells, n_pairs = resid_matrix.shape
    rng = np.random.default_rng(seed)
    U = rng.normal(0, 0.01, (n_cells, rank))
    V = rng.normal(0, 0.01, (n_pairs, rank))
    for _ in range(ALS_MAX_ITER):
        # solve U rows
        for c in range(n_cells):
            m = obs_mask[c]
            if m.sum() >= rank + 2:
                U[c] = _ridge_solve(V[m], resid_matrix[c, m], lam)
        for q in range(n_pairs):
            m = obs_mask[:, q]
            if m.sum() >= rank + 2:
                V[q] = _ridge_solve(U[m], resid_matrix[m, q], lam)
    return U, V


def build_training_matrix(train: Dict[str, np.ndarray], b2: Dict, rank: int, lam: float) -> Dict[str, np.ndarray]:
    """Residual matrix cells x pairs from training units after B2 static prediction."""
    y = np.asarray(train["y"], dtype=float)
    pred = predict_b2(b2, train)
    resid = y - pred
    cell_ids = train["cell_id"]
    pair = train["pair_id"]
    n_cells = int(cell_ids.max()) + 1
    n_pairs = int(pair.max()) + 1
    mat = np.zeros((n_cells, n_pairs))
    cnt = np.zeros((n_cells, n_pairs))
    np.add.at(mat, (cell_ids, pair), resid)
    np.add.at(cnt, (cell_ids, pair), 1.0)
    mask = cnt > 0
    mat = np.divide(mat, cnt, out=np.zeros_like(mat), where=mask)
    return {"matrix": mat, "mask": mask}


def fit_b4(train: Dict[str, np.ndarray], rank: int, lam: float, refit_factors: bool = True) -> Dict:
    b2 = fit_b2(train)
    tm = build_training_matrix(train, b2, rank, lam)
    if refit_factors:
        U, V = fit_pair_factors(tm["matrix"], tm["mask"], rank, lam)
    else:
        # frozen factors supplied by caller
        U, V = tm.get("U0"), tm.get("V0")
    return {"b2": b2, "U": U, "V": V, "rank": rank, "lam": lam}


def fit_context_factors(units: Dict[str, np.ndarray], b4: Dict, lam: float) -> Tuple[np.ndarray, np.ndarray]:
    """Estimate per-cell c_cell, U_cell (cells x rank) from NON-masked units only."""
    y = np.asarray(units["y"], dtype=float)
    base = predict_b2(b4["b2"], units)
    resid = y - base
    V = b4["V"]
    cells = units["cell_id"]
    pair = units["pair_id"]
    n_cells = int(cells.max()) + 1
    rank = V.shape[1]
    c = np.zeros(n_cells)
    U = np.zeros((n_cells, rank))
    for k in range(n_cells):
        m = cells == k
        if m.sum() == 0:
            continue
        A = np.hstack([np.ones((int(m.sum()), 1)), V[pair[m]]])
        coef = _ridge_solve(A, resid[m], lam)
        c[k] = coef[0]
        U[k] = coef[1:]
    return c, U


def predict_b4(units: Dict[str, np.ndarray], b4: Dict, c: np.ndarray, U: np.ndarray) -> np.ndarray:
    base = predict_b2(b4["b2"], units)
    V = b4["V"]
    return base + c[units["cell_id"]] + np.sum(U[units["cell_id"]] * V[units["pair_id"]], axis=1)


# ---------------------------------------------------------------- metrics
def spearman(a: np.ndarray, b: np.ndarray) -> float:
    from scipy.stats import spearmanr
    r = spearmanr(a, b).correlation
    return float(r) if np.isfinite(r) else 0.0


def mae(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.mean(np.abs(np.asarray(a, float) - np.asarray(b, float))))


def topk_overlap(pred, obs, groups, k=3) -> Dict[str, float]:
    """Appendix-only descriptive measure; groups = context ids for masked units."""
    import collections
    hits = 0.0
    total = 0
    for g, idx in _group_indices(groups):
        if len(idx) < k:
            continue
        p = pred[idx]
        o = obs[idx]
        top_p = set(np.argsort(-p, kind="stable")[:k])
        top_o = set(np.argsort(-o, kind="stable")[:k])
        hits += len(top_p & top_o) / k
        total += 1
    return {"precision_at_k": (hits / total) if total else None, "n_contexts": total}


def _group_indices(groups):
    import collections
    d = collections.defaultdict(list)
    for i, g in enumerate(groups):
        d[g].append(i)
    return d.items()


def paired_bootstrap_delta(pred_a, pred_b, obs, cells, n_boot=BOOT_B, seed=int(SEED_MASK)) -> Dict[str, float]:
    """Paired-by-held-out-cell bootstrap of rho(a)-rho(b) and MAE(b)-MAE(a); predictions fixed."""
    rng = np.random.default_rng(seed)
    uniq = np.unique(cells)
    by_cell = {c: np.where(cells == c)[0] for c in uniq}
    da, db = [], []
    for _ in range(n_boot):
        picks = rng.choice(uniq, size=len(uniq), replace=True)
        idx = np.concatenate([by_cell[c] for c in picks])
        da.append(spearman(pred_a[idx], obs[idx]) - spearman(pred_b[idx], obs[idx]))
        db.append(mae(pred_a[idx], obs[idx]) - mae(pred_b[idx], obs[idx]))
    da = np.asarray(da); db = np.asarray(db)
    return {"delta_rho_mean": float(da.mean()),
            "delta_rho_ci025": float(np.percentile(da, 2.5)), "delta_rho_ci975": float(np.percentile(da, 97.5)),
            "delta_rho_one_sided_lower95": float(np.percentile(da, 5)),
            "delta_mae_mean": float(db.mean()),
            "delta_mae_ci025": float(np.percentile(db, 2.5)), "delta_mae_ci975": float(np.percentile(db, 97.5))}


# ---------------------------------------------------------------- B6 null
def b6_null(fold_data: List[Dict], b4_models: List[Dict], n_perm: int = N_PERM,
            semantics: str = "refit_cu_only", seed: int = int(SEED_MASK)) -> Dict:
    """B6: permute held-out cell NON-masked context across cells (stratified by partner/role),
    re-estimate c/U per cell; semantics:
      - 'refit_cu_only' (frozen default): training structure fixed; re-estimate c/U on permuted context.
      - 'full_refit': also re-fit B4 pair factors U,V on training cells each permutation (not recommended).
    Returns null distributions of rho(B4_null) and delta_rho = rho(B4_null)-rho(B2) per fold.
    """
    rng = np.random.default_rng(seed)
    out = {"semantics": semantics, "n_perm": n_perm, "rho_null": [], "delta_rho_null": [], "fold_rho_null": {}}
    for f, fd in enumerate(fold_data):
        obs = fd["obs_y"]
        rho_list, drho_list = [], []
        for p in range(n_perm):
            perm = fd["unmasked_units"].copy()
            # stratified permutation of cell assignment within (partner, role)
            perm["cell_id"] = _permute_cell_within_strata(perm, rng)
            base_model = b4_models[f]
            if semantics == "full_refit":
                # re-fit training factors with permutation-seeded init on the same training matrix
                b4p = fit_b4(fd["train"], base_model["rank"], base_model["lam"], refit_factors=True)
            else:
                b4p = base_model
            c, U = fit_context_factors(perm, b4p, base_model["lam"])
            pred = predict_b4(fd["masked_units"], b4p, c, U)
            rho = spearman(pred, fd["masked_y"])
            rho_b2 = b2_fold_rho(fd)
            rho_list.append(rho)
            drho_list.append(rho - rho_b2)
        out["fold_rho_null"][str(f)] = rho_list
        out["rho_null"].extend(rho_list)
        out["delta_rho_null"].extend(drho_list)
    out["rho_null"] = np.asarray(out["rho_null"])
    out["delta_rho_null"] = np.asarray(out["delta_rho_null"])
    out["q95_rho"] = float(np.percentile(out["rho_null"], 95))
    out["q95_delta_rho"] = float(np.percentile(out["delta_rho_null"], 95))
    out["p_one_sided"] = lambda observed: float(np.mean(out["delta_rho_null"] >= observed))
    return out


def b2_fold_rho(fd: Dict) -> float:
    return spearman(fd["pred_b2"], fd["masked_y"])


def _permute_cell_within_strata(units: Dict, rng) -> np.ndarray:
    cells = units["cell_id"]
    strata = units.get("stratum")
    if strata is None:
        return rng.permutation(cells)
    new = cells.copy()
    for s in np.unique(strata):
        m = strata == s
        new[m] = rng.permutation(cells[m])
    return new


# ---------------------------------------------------------------- context ablation & pure cold
def context_ablation(units: Dict, b4: Dict, c, U) -> Dict[str, float]:
    pred_ctx = predict_b4(units, b4, c, U)
    pred_abl = predict_b4(units, b4, np.zeros_like(c), np.zeros_like(U))
    obs = np.asarray(units["y"], float)
    return {"rho_with_context": spearman(pred_ctx, obs), "rho_ablated_context": spearman(pred_abl, obs),
            "delta_rho_context": spearman(pred_ctx, obs) - spearman(pred_abl, obs)}


def pure_cold_eval(units: Dict, b4: Dict) -> Dict[str, float]:
    """Pure cold-cell sensitivity: no context; predictions = static structure only (B2)."""
    obs = np.asarray(units["y"], float)
    pred = predict_b2(b4["b2"], units)
    return {"rho": spearman(pred, obs), "mae": mae(pred, obs), "n_units": int(len(obs))}


# ---------------------------------------------------------------- B5 target encoding (train-only, cross-fitted)
def cross_fit_target_encoding(y, pair_id, n_folds: int = 5, seed: int = int(SEED_MASK)) -> np.ndarray:
    """5-fold cross-fitted member-pair target encoding computed ONLY from the passed training arrays.

    No masked-unit responses are accepted/used: the function signature has no masked argument and
    validation-fold encodings are produced from the other folds only (unseen pair -> global mean).
    Frozen: n_folds=5, seed=20261130, global-mean backoff.
    """
    y = np.asarray(y, dtype=float)
    pair_id = np.asarray(pair_id, dtype=np.int64)
    rng = np.random.default_rng(seed)
    uniq = np.unique(pair_id)
    order = rng.permutation(len(uniq))
    fold_of = {int(q): int(order[i] % n_folds) for i, q in enumerate(uniq)}
    folds = np.array([fold_of[int(q)] for q in pair_id], dtype=np.int64)
    out = np.empty(len(y), dtype=float)
    for f in range(n_folds):
        tr = folds != f
        val = ~tr
        gmean = float(y[tr].mean()) if tr.any() else float(y.mean())
        sums = {}
        cnts = {}
        for yi, q in zip(y[tr], pair_id[tr]):
            sums[int(q)] = sums.get(int(q), 0.0) + float(yi)
            cnts[int(q)] = cnts.get(int(q), 0) + 1
        for idx in np.where(val)[0]:
            q = int(pair_id[idx])
            out[idx] = sums[q] / cnts[q] if q in sums else gmean
    return out


# ---------------------------------------------------------------- schema
EXEC_REQUIRED_KEYS = {
    "task", "protocol", "inputs", "mask", "coverage", "results", "primary",
    "null", "bootstrap", "context_ablation", "pure_cold_cell", "gates",
    "verdict", "failure_categories", "attestation", "determinism",
}


def validate_exec_schema(obj: Dict) -> Tuple[bool, List[str]]:
    missing = sorted(EXEC_REQUIRED_KEYS - set(obj.keys()))
    return (len(missing) == 0), missing


def null_calibration_gate(values, mean_abs_max: float = 0.05, field_prefix: str = "delta_rho") -> Dict:
    """B6 null-calibration gate (binary): 2.5-97.5 percentile must cover 0 AND mean|values|<=mean_abs_max.

    v1.1 (AMEND-001): the frozen gate object is delta_rho_null = rho(B4_null)-rho(B2);
    the function is generic but the execution call uses field_prefix='delta_rho' so the output keys
    are p2_5_delta_rho / p97_5_delta_rho / mean_abs_delta_rho (no rho-named gate fields).
    """
    arr = np.asarray(values, dtype=float)
    lo, hi = np.percentile(arr, 2.5), np.percentile(arr, 97.5)
    mean_abs = float(np.mean(np.abs(arr)))
    cover = bool(lo <= 0.0 <= hi)
    return {"pass": bool(cover and mean_abs <= mean_abs_max),
            "p2_5_%s" % field_prefix: float(lo), "p97_5_%s" % field_prefix: float(hi),
            "mean_abs_%s" % field_prefix: mean_abs, "covers_zero": cover,
            "mean_abs_threshold": mean_abs_max, "gate_object": field_prefix}


def validate_null_gate_schema(gate: Dict) -> Tuple[bool, List[str]]:
    """v1.1 schema: null gate must carry delta_rho-named fields (not rho-named)."""
    required = {"pass", "p2_5_delta_rho", "p97_5_delta_rho", "mean_abs_delta_rho"}
    missing = sorted(required - set(gate.keys()))
    return (len(missing) == 0), missing


def sha256_json(obj) -> str:
    import json
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest().upper()
