"""Exploratory gate on exposed PRISM 19Q4: is structured knowledge real information for unseen compounds?

File summary
- Path: research/knowledge_reality_20261013/develop.py
- Purpose: run DEV_PLAN.md. It covers the T0 arms, stacks, knowledge controls, ablations, T1
  incremental value, calibration and decision utility, and the G1-G3 gate verdicts.
- Core points:
  - Five outer folds by MoA family. Within each, three inner folds by family fit the
    chemical-ridge penalty, the stack weights and the hit calibrator. Test compounds are never read.
  - Every route reads only training outcomes, the query's admissible inputs and basal line state
    (`maestro.information_tier` admission is checked per arm).
  - Controls randomise the whole knowledge graph within fold, twenty seeds each. Progress is
    saved after every seed in tmp/, so an interrupted run resumes.
- Output: DEVELOPMENT.json in this folder.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass, replace

import warnings

import numpy as np
from scipy import sparse

import models as M

warnings.filterwarnings("ignore", message="All-NaN slice")
warnings.filterwarnings("ignore", message="Mean of empty slice")
from sources import CACHE, HERE, ROOT, sha256, write_json

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from maestro.information_tier import InputDeclaration, Tier, require  # noqa: E402
from tools.evaluation.scoring import cluster_signflip_test  # noqa: E402

SEED = 20261013
INNER = 3
CONTROL_SEEDS = 20
CONTROLS = ("degree", "setperm", "relabel")
B_NOMINATE = 200
CAP = 3
VISIBLE_FRACTION = 0.25
CTX_K = 25
PHENO = (10, 2.0, 0.0)
DENSITY_ALPHA = 1.0
HUB, MAPCUR, BINDAGG, BIOCHEM, ENGAGE = range(5)
SOURCE_INDEX = {"curated_hub": HUB, "curated_mechanism": MAPCUR, "binding_aggregate": BINDAGG,
                "assay_biochemical": BIOCHEM, "assay_cell_engagement": ENGAGE}
PARTIAL = CACHE / ("controls_partial_smoke.json" if os.environ.get("KR_SMOKE") else "controls_partial.json")

DECLARED = {d.name: d for d in (
    InputDeclaration("structure", Tier.T0, provenance="chemistry"),
    InputDeclaration("t0_knowledge", Tier.T0, provenance="curated, aggregate binding, biochemical"),
    InputDeclaration("basal_context", Tier.T0, provenance="CCLE 19Q4 expression and mutation of lines"),
    InputDeclaration("training_outcomes", Tier.T0, provenance="other compounds' PRISM responses"),
    InputDeclaration("cell_engagement_edges", Tier.T1, provenance="ChEMBL cell-based target assays"),
    InputDeclaration("own_visible_lines", Tier.T1, provenance="query's own primary-screen values"))}
ARM_INPUTS = {
    "chem_full": ("structure", "training_outcomes"),
    "annot_full": ("structure", "t0_knowledge", "training_outcomes"),
    "rkt_full": ("structure", "t0_knowledge", "training_outcomes"),
    "know_full": ("structure", "t0_knowledge", "basal_context", "training_outcomes"),
    "know_only": ("t0_knowledge", "basal_context", "training_outcomes"),
    "density_full": ("structure", "t0_knowledge", "training_outcomes"),
    "know_full_t1": ("structure", "t0_knowledge", "cell_engagement_edges", "basal_context", "training_outcomes"),
    "t1_base": ("structure", "own_visible_lines", "training_outcomes"),
    "t1_know": ("structure", "own_visible_lines", "t0_knowledge", "basal_context", "training_outcomes"),
}
ARM_TIER = {a: (Tier.T1 if a in ("know_full_t1", "t1_base", "t1_know") else Tier.T0) for a in ARM_INPUTS}


def h(key: str, salt: str) -> int:
    return int(hashlib.sha256(f"{salt}:{key}".encode()).hexdigest(), 16)


@dataclass(frozen=True)
class Edges:
    drug: np.ndarray
    gene: np.ndarray
    rel: np.ndarray
    prov: np.ndarray        # provenance group: 0 curated, 1 measured, 2 cell engagement
    src: np.ndarray         # source index (SOURCE_INDEX)
    moa: np.ndarray         # (k, 2) drug, moa


def true_edges(T: dict) -> Edges:
    return Edges(T["edge_drug"], T["edge_gene"], T["edge_rel"], T["edge_prov"],
                 np.array([SOURCE_INDEX[s] for s in T["edge_source"]], dtype=np.int8), T["moa_pairs"])


def t0_only(E: Edges) -> Edges:
    m = E.prov < 2
    return replace(E, drug=E.drug[m], gene=E.gene[m], rel=E.rel[m], prov=E.prov[m], src=E.src[m])


# ---------------------------------------------------------------- knowledge controls

def curveball(adj: dict, rng: np.random.Generator, sweeps: int = 10) -> dict:
    keys = [k for k in adj if adj[k]]
    out = {k: set(v) for k, v in adj.items()}
    if len(keys) < 2:
        return out
    for _ in range(sweeps * len(keys)):
        a, b = rng.choice(len(keys), 2, replace=False)
        A, B = out[keys[a]], out[keys[b]]
        a_only, b_only = list(A - B), list(B - A)
        if not a_only or not b_only:
            continue
        pool = a_only + b_only
        rng.shuffle(pool)
        na = len(a_only)
        shared = A & B
        out[keys[a]] = shared | set(pool[:na])
        out[keys[b]] = shared | set(pool[na:])
    return out


def control_edges(E: Edges, kind: str, seed: int, T: dict) -> Edges:
    rng = np.random.default_rng(SEED * 1000 + seed + 100 * CONTROLS.index(kind))
    fold = T["fold"]
    strata = [int(f) for f in np.unique(fold)]          # 0-4 in development; the sealed stratum is 5
    if kind == "degree":
        rows = []
        for f in strata:
            for layer in sorted(set(zip(E.rel.tolist(), E.src.tolist()))):
                m = (fold[E.drug] == f) & (E.rel == layer[0]) & (E.src == layer[1])
                adj: dict = {}
                for d, g in zip(E.drug[m], E.gene[m]):
                    adj.setdefault(int(d), set()).add(int(g))
                pg = int(E.prov[m][0]) if m.any() else 0
                for d, gs in curveball(adj, rng).items():
                    rows += [(d, g, layer[0], pg, layer[1]) for g in gs]
        a = np.array(rows, dtype=np.int64).reshape(-1, 5)
        madj: dict = {}
        for d, mo in E.moa:
            madj.setdefault(int(d), set()).add(int(mo))
        moa = []
        for f in strata:
            sub = {d: v for d, v in madj.items() if fold[d] == f}
            moa += [(d, mo) for d, ms in curveball(sub, rng).items() for mo in ms]
        return Edges(a[:, 0].astype(np.int32), a[:, 1].astype(np.int32), a[:, 2].astype(np.int8),
                     a[:, 3].astype(np.int8), a[:, 4].astype(np.int8), np.array(moa, dtype=np.int32).reshape(-1, 2))
    if kind == "setperm":
        n = len(fold)
        cnt = np.bincount(E.drug[E.prov < 2], minlength=n)
        meas = np.bincount(E.drug[E.prov == 1], minlength=n) > 0
        bucket = np.digitize(cnt, [1, 2, 3, 6, 16])
        target = np.arange(n)
        for f in strata:
            for b in np.unique(bucket):
                for mm in (False, True):
                    idx = np.where((fold == f) & (bucket == b) & (meas == mm))[0]
                    if len(idx) > 1:
                        target[idx] = rng.permutation(idx)
        # target[i] = the compound whose bundle compound i receives
        owner = np.empty(n, dtype=np.int64)
        owner[target] = np.arange(n)
        return Edges(owner[E.drug].astype(np.int32), E.gene, E.rel, E.prov, E.src,
                     np.column_stack([owner[E.moa[:, 0]], E.moa[:, 1]]).astype(np.int32))
    if kind == "relabel":
        G = len(T["genes"])
        deg = np.bincount(E.gene[E.prov < 2], minlength=G)
        dbin = np.digitize(deg, [2, 3, 6, 21])
        sdq = np.digitize(T["expr_sd"], np.quantile(T["expr_sd"], [1 / 3, 2 / 3]))
        hot = (T["hotspot"].mean(0) >= 0.01).astype(int)
        stratum = dbin * 100 + sdq * 10 + hot
        perm = np.arange(G)
        for s in np.unique(stratum):
            idx = np.where(stratum == s)[0]
            if len(idx) > 1:
                perm[idx] = rng.permutation(idx)
        return replace(E, gene=perm[E.gene].astype(np.int32))
    raise ValueError(kind)


# ---------------------------------------------------------------- knowledge representations

@dataclass
class Knowledge:
    annot: tuple
    rkt: tuple
    typed: tuple
    F_tc: np.ndarray
    has_tc: np.ndarray
    density: np.ndarray
    extra: dict


def knowledge(E: Edges, T: dict, *, ablations: bool) -> Knowledge:
    n = len(T["cores"])
    moa_rows = [(int(d), f"M:{int(m)}", 1.0) for d, m in E.moa]
    t0 = E.prov < 2
    annot = M.token_matrix(n, [(int(d), f"T:{int(g)}", 1.0) for d, g, s in zip(E.drug, E.gene, E.src) if s == HUB] + moa_rows)
    sign = np.where(E.rel == 1, -1, 1)
    rkt = M.token_matrix(n, [(int(d), f"S:{int(g)}:{int(sg)}", 1.0) for d, g, s, r, sg in zip(E.drug, E.gene, E.src, E.rel, sign)
                             if s == HUB or (s == MAPCUR and r in (0, 1))] + moa_rows)
    typed = M.token_matrix(n, [(int(d), f"T:{int(g)}:{int(r)}:{int(p)}", M.TYPED_WEIGHTS[int(p)])
                               for d, g, r, p in zip(E.drug[t0], E.gene[t0], E.rel[t0], E.prov[t0])] + moa_rows)
    ctx = (T["expr_z"], T["expressed"], T["hotspot"], T["deleterious"])
    F, has = M.tc_features(E.drug, E.gene, E.rel, E.prov, n, *ctx, typed=True, groups=(0, 1))
    deg = np.bincount(E.gene[t0], minlength=len(T["genes"]))
    cnt0 = np.bincount(E.drug[E.prov == 0], minlength=n)
    cnt1 = np.bincount(E.drug[E.prov == 1], minlength=n)
    nm = np.bincount(E.moa[:, 0], minlength=n) if len(E.moa) else np.zeros(n)
    sdeg = np.bincount(E.drug[t0], weights=np.log1p(deg[E.gene[t0]]), minlength=n)
    mdeg = np.where(cnt0 + cnt1 > 0, sdeg / np.maximum(cnt0 + cnt1, 1), 0.0)
    density = np.column_stack([np.log1p(cnt0), np.log1p(cnt1), np.log1p(nm), mdeg, (cnt0 + cnt1 > 0)]).astype(np.float64)
    extra = {}
    if ablations:
        extra["F_untyped"] = lambda: M.tc_features(E.drug, E.gene, E.rel, E.prov, n, *ctx, typed=False, groups=(0, 1))
        extra["F_curated"] = lambda: M.tc_features(E.drug, E.gene, E.rel, E.prov, n, *ctx, typed=True, groups=(0,))
        extra["F_t1"] = lambda: M.tc_features(E.drug, E.gene, E.rel, E.prov, n, *ctx, typed=True, groups=(0, 1, 2))
        extra["typed_t1"] = M.token_matrix(n, [(int(d), f"T:{int(g)}:{int(r)}:{int(p)}", {0: 1.0, 1: 0.5, 2: 0.5}[int(p)])
                                               for d, g, r, p in zip(E.drug, E.gene, E.rel, E.prov)] + moa_rows)
    return Knowledge(annot, rkt, typed, F, has, density, extra)


# ---------------------------------------------------------------- routes per reference/query split

def route_knn_tokens(tok: tuple, qry: np.ndarray, ref: np.ndarray, S: np.ndarray) -> np.ndarray:
    X, w = tok
    sim = M.weighted_jaccard(X, w, qry, ref)
    return M.knn_predict(sim, S[ref], *M.KNOW_PARAMS)


def route_tc(F: np.ndarray, has: np.ndarray, qry: np.ndarray, ref: np.ndarray, S: np.ndarray, G: np.ndarray) -> np.ndarray:
    model = M.TargetContext().fit(F, S, G, ref[has[ref]])
    out = np.full((len(qry), S.shape[1]), np.nan)
    ok = has[qry]
    if ok.any():
        out[ok] = model.predict(F, G, qry[ok])
    return out


def route_density(D: np.ndarray, qry: np.ndarray, ref: np.ndarray, S: np.ndarray) -> np.ndarray:
    mu, sd = D[ref].mean(0), D[ref].std(0)
    sd = np.where(sd > 1e-9, sd, 1.0)
    Xr = np.column_stack([np.ones(len(ref)), (D[ref] - mu) / sd])
    Xq = np.column_stack([np.ones(len(qry)), (D[qry] - mu) / sd])
    Sr = np.where(np.isfinite(S[ref]), S[ref], 0.0)
    B = np.linalg.solve(Xr.T @ Xr + DENSITY_ALPHA * np.eye(Xr.shape[1]), Xr.T @ Sr)
    return Xq @ B


def visible_mask(cores: np.ndarray, L: int) -> np.ndarray:
    V = np.zeros((len(cores), L), dtype=bool)
    k = int(round(VISIBLE_FRACTION * L))
    for i, c in enumerate(cores):
        rng = np.random.default_rng(h(str(c), "visible") % (2 ** 32))
        V[i, rng.choice(L, k, replace=False)] = True
    return V


def route_ctx(S: np.ndarray, qry: np.ndarray, V: np.ndarray, line_sim: np.ndarray) -> np.ndarray:
    out = np.full((len(qry), S.shape[1]), np.nan)
    for i, q in enumerate(qry):
        vis = np.where(V[q] & np.isfinite(S[q]))[0]
        if len(vis) < CTX_K:
            continue
        sim = line_sim[:, vis]
        idx = np.argpartition(-sim, CTX_K, axis=1)[:, :CTX_K]
        w = np.maximum(np.take_along_axis(sim, idx, 1), 0.0)
        vals = S[q, vis][idx]
        out[i] = (w * vals).sum(1) / np.maximum(w.sum(1), 1e-9)
    return out


def route_pheno(S: np.ndarray, qry: np.ndarray, ref: np.ndarray, V: np.ndarray) -> np.ndarray:
    out = np.full((len(qry), S.shape[1]), np.nan)
    Sr = S[ref]
    for i, q in enumerate(qry):
        vis = V[q] & np.isfinite(S[q])
        a = S[q, vis]
        B = Sr[:, vis]
        f = np.isfinite(B)
        B0 = np.where(f, B, 0.0)
        a_c = a - a.mean()
        Bm = (B0.sum(1) / np.maximum(f.sum(1), 1))[:, None]
        Bc = np.where(f, B - Bm, 0.0)
        num = Bc @ a_c
        den = np.sqrt((Bc ** 2).sum(1) * (a_c ** 2).sum())
        r = np.where(den > 0, num / np.maximum(den, 1e-12), 0.0)
        out[i] = M.knn_predict(r[None, :], Sr, *PHENO)[0]
    return out


# ---------------------------------------------------------------- evaluation

def drug_r(P: np.ndarray, S: np.ndarray, G: np.ndarray, lines: np.ndarray | None = None) -> np.ndarray:
    r = np.zeros(len(P))
    for i in range(len(P)):
        f = np.isfinite(P[i]) & np.isfinite(S[i]) & np.isfinite(G)
        if lines is not None:
            f &= lines[i]
        if f.sum() < 20:
            continue
        X = np.column_stack([np.ones(f.sum()), G[f]])
        p = P[i, f] - X @ np.linalg.lstsq(X, P[i, f], rcond=None)[0]
        s = S[i, f]
        den = np.sqrt(((p - p.mean()) ** 2).sum() * ((s - s.mean()) ** 2).sum())
        r[i] = ((p - p.mean()) @ (s - s.mean())) / den if den > 1e-12 else 0.0
    return r


def specificity(P: np.ndarray, S: np.ndarray, G: np.ndarray) -> np.ndarray:
    """Own-profile r minus the mean r with the other compounds' observed profiles."""

    X = np.column_stack([np.ones_like(G), G])
    Pin = np.linalg.pinv(X)
    Pz = np.where(np.isfinite(P), P, 0.0)
    Pz = Pz - (Pz @ Pin.T) @ X.T
    Sz = np.where(np.isfinite(S), S, 0.0)
    Pz = Pz - Pz.mean(1, keepdims=True)
    Sz = Sz - Sz.mean(1, keepdims=True)
    pn = np.linalg.norm(Pz, axis=1)
    sn = np.linalg.norm(Sz, axis=1)
    C = (Pz @ Sz.T) / np.maximum(np.outer(pn, sn), 1e-12)
    C[pn < 1e-12] = 0.0
    n = len(P)
    mism = (C.sum(1) - np.diag(C)) / max(n - 1, 1)
    return np.diag(C) - mism


def robust_z(S: np.ndarray) -> np.ndarray:
    med = np.nanmedian(S, axis=1, keepdims=True)
    mad = np.nanmedian(np.abs(S - med), axis=1, keepdims=True) * 1.4826
    return (S - med) / np.maximum(mad, 1e-6)


TIE: dict = {}


def tie_break(cores: np.ndarray, L: int) -> np.ndarray:
    """A fixed pseudo-random order of (compound, line) pairs, from a salted hash of the compound."""

    out = np.empty((len(cores), L))
    for i, c in enumerate(cores):
        if c not in TIE:
            TIE[c] = np.random.default_rng(h(str(c), "tie") % (2 ** 32)).random(L)
        out[i] = TIE[c]
    return out


def nominate(score: np.ndarray, cores: np.ndarray, budget: int = B_NOMINATE, cap: int = CAP) -> list[tuple[int, int]]:
    n, L = score.shape
    flat = np.where(np.isfinite(score), score, -np.inf) + tie_break(cores, L) * 1e-9
    order = np.argsort(-flat, axis=None)
    picked, per = [], {}
    for k in order:
        i, l = divmod(int(k), L)
        if not np.isfinite(flat[i, l]):
            break
        if per.get(i, 0) >= cap:
            continue
        picked.append((i, l))
        per[i] = per.get(i, 0) + 1
        if len(picked) == budget:
            break
    return picked


def brier_ece(p: np.ndarray, y: np.ndarray, bins: int = 10) -> tuple[float, float]:
    brier = float(np.mean((p - y) ** 2))
    edges = np.quantile(p, np.linspace(0, 1, bins + 1))
    idx = np.clip(np.searchsorted(edges, p, side="right") - 1, 0, bins - 1)
    ece = sum(abs(p[idx == b].mean() - y[idx == b].mean()) * (idx == b).mean() for b in range(bins) if (idx == b).any())
    return brier, float(ece)


def paired(a: np.ndarray, b: np.ndarray, clusters: np.ndarray) -> dict:
    d = a - b
    test = cluster_signflip_test(d.tolist(), clusters.tolist(), draws=10000, seed=SEED)
    rng = np.random.default_rng(SEED)
    names, inv = np.unique(clusters, return_inverse=True)
    sums = np.bincount(inv, weights=d)
    cnts = np.bincount(inv)
    boots = []
    for _ in range(2000):
        pick = rng.integers(0, len(names), len(names))
        boots.append(sums[pick].sum() / cnts[pick].sum())
    return {"mean_a": float(a.mean()), "mean_b": float(b.mean()), "difference": float(d.mean()),
            "ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))],
            "p_greater": float(test["p_greater"]), "favour": int((d > 1e-9).sum()), "oppose": int((d < -1e-9).sum()),
            "units": int(len(d)), "clusters": int(len(names))}


# ---------------------------------------------------------------- one pass over the folds

SMOKE = bool(os.environ.get("KR_SMOKE"))


def fold_setup(T: dict) -> list[dict]:
    Y = T["Y"].astype(np.float64)
    keep = np.array([h(str(c), "smoke") % 8 == 0 for c in T["cores"]]) if SMOKE else np.ones(len(T["cores"]), bool)
    out = []
    for f in range(5):
        train = np.where((T["fold"] != f) & keep)[0]
        test = np.where((T["fold"] == f) & keep)[0]
        G = np.nanmedian(Y[train], axis=0)
        S = M.residualise(Y, G)
        inner = np.array([h(T["family"][i], f"inner{f}") % INNER for i in train])
        out.append({"f": f, "train": train, "test": test, "G": G, "S": S, "inner": inner})
    return out


def chem_routes(T: dict, folds: list[dict], K: np.ndarray, V: np.ndarray, line_sim: np.ndarray) -> list[dict]:
    """Structure and T1 routes, which do not depend on the knowledge graph (computed once)."""

    res = []
    for fs in folds:
        train, test, S, inner = fs["train"], fs["test"], fs["S"], fs["inner"]
        iv = {k: np.full((len(train), S.shape[1]), np.nan, dtype=np.float32) for k in ("chem_knn", "ctx", "pheno")}
        ridge_inner = {a: np.full((len(train), S.shape[1]), np.nan, dtype=np.float32) for a in M.RIDGE_ALPHAS}
        for k in range(INNER):
            q, r = train[inner == k], train[inner != k]
            iv["chem_knn"][inner == k] = M.knn_predict(K[np.ix_(q, r)], S[r], *M.CHEM_PARAMS)
            kr = M.KernelRidge(K[np.ix_(r, r)], S[r])
            for a, pred in kr.predict_many(K[np.ix_(q, r)], M.RIDGE_ALPHAS).items():
                ridge_inner[a][inner == k] = pred
            del kr
            iv["ctx"][inner == k] = route_ctx(S, q, V, line_sim)
            iv["pheno"][inner == k] = route_pheno(S, q, r, V)
        St = S[train]
        mse = {a: float(np.nanmean((np.where(np.isfinite(St), St, np.nan) - p) ** 2)) for a, p in ridge_inner.items()}
        alpha = min(mse, key=mse.get)
        iv["chem_ridge"] = ridge_inner[alpha]
        del ridge_inner
        te = {"chem_knn": M.knn_predict(K[np.ix_(test, train)], S[train], *M.CHEM_PARAMS),
              "chem_ridge": M.KernelRidge(K[np.ix_(train, train)], S[train]).predict(K[np.ix_(test, train)], alpha),
              "ctx": route_ctx(S, test, V, line_sim), "pheno": route_pheno(S, test, train, V)}
        te = {k: v.astype(np.float32) for k, v in te.items()}
        res.append({"inner": iv, "test": te, "alpha": alpha})
        print(f"  chem fold {fs['f']} alpha {alpha}", flush=True)
    return res


def knowledge_routes(T: dict, folds: list[dict], kn: Knowledge, *, ablations: bool) -> list[dict]:
    """Knowledge routes for every fold, route by route, so only one feature tensor is held at a time."""

    res = [{"inner": {}, "test": {}} for _ in folds]

    def run(name, fn):
        for fs, slot in zip(folds, res):
            train, test, inner = fs["train"], fs["test"], fs["inner"]
            iv = np.full((len(train), fs["S"].shape[1]), np.nan, dtype=np.float32)
            for k in range(INNER):
                iv[inner == k] = fn(fs, train[inner == k], train[inner != k])
            slot["inner"][name] = iv
            slot["test"][name] = fn(fs, test, train).astype(np.float32)

    run("kn_typed", lambda fs, q, r: route_knn_tokens(kn.typed, q, r, fs["S"]))
    run("tc", lambda fs, q, r: route_tc(kn.F_tc, kn.has_tc, q, r, fs["S"], fs["G"]))
    run("annot", lambda fs, q, r: route_knn_tokens(kn.annot, q, r, fs["S"]))
    run("rkt_know", lambda fs, q, r: route_knn_tokens(kn.rkt, q, r, fs["S"]))
    run("density", lambda fs, q, r: route_density(kn.density, q, r, fs["S"]))
    if ablations:
        for name, key in (("tc_untyped", "F_untyped"), ("tc_curated", "F_curated"), ("tc_t1", "F_t1")):
            F, has = kn.extra[key]()
            run(name, lambda fs, q, r: route_tc(F, has, q, r, fs["S"], fs["G"]))
            del F, has
        run("kn_typed_t1", lambda fs, q, r: route_knn_tokens(kn.extra["typed_t1"], q, r, fs["S"]))
    return res


STACKS = {
    "chem_full": ("chem_knn", "chem_ridge"),
    "annot_full": ("chem_knn", "chem_ridge", "annot"),
    "rkt_full": ("chem_knn", "chem_ridge", "rkt_know"),
    "know_full": ("chem_knn", "chem_ridge", "kn_typed", "tc"),
    "know_only": ("kn_typed", "tc"),
    "density_full": ("chem_knn", "chem_ridge", "density"),
    "know_untyped": ("chem_knn", "chem_ridge", "kn_typed", "tc_untyped"),
    "know_curated_tc": ("chem_knn", "chem_ridge", "kn_typed", "tc_curated"),
    "know_full_t1": ("chem_knn", "chem_ridge", "kn_typed_t1", "tc_t1"),
    "t1_base": ("chem_knn", "chem_ridge", "ctx", "pheno"),
    "t1_know": ("chem_knn", "chem_ridge", "ctx", "pheno", "kn_typed", "tc"),
}
T1_ARMS = ("t1_base", "t1_know")


def stacked(fs: dict, chem: dict, know: dict, arm: str, V: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    routes = STACKS[arm]
    pool_i = {**chem["inner"], **know["inner"]}
    pool_t = {**chem["test"], **know["test"]}
    S_tr = fs["S"][fs["train"]]
    if arm in T1_ARMS:
        S_fit = np.where(V[fs["train"]], np.nan, S_tr)     # fit on hidden lines only
    else:
        S_fit = S_tr
    w = M.nnls_stack([pool_i[r] for r in routes], S_fit)
    return M.combine([pool_t[r] for r in routes], w), M.combine([pool_i[r] for r in routes], w), w


def evaluate_arms(T: dict, folds: list[dict], chem: list[dict], know: list[dict], arms: tuple, V: np.ndarray,
                  *, detail: bool) -> dict:
    out = {a: {"r": [], "spec": [], "idx": [], "w": []} for a in arms}
    extras = {a: {"brier": [], "ece": [], "hits": 0, "sec_conf": 0, "sec_eval": 0, "nominated": 0} for a in arms} if detail else None
    for fs, ch, kn in zip(folds, chem, know):
        test, S, G, Y = fs["test"], fs["S"], fs["G"], T["Y"]
        Z = robust_z(S)
        event = (Z <= -3) & (Y <= -1)
        active = event[test].sum(1) >= 5
        for a in arms:
            P_test, P_inner, w = stacked(fs, ch, kn, a, V)
            lines = ~V[test] if a in T1_ARMS else None
            r = drug_r(P_test, S[test], G, lines)
            out[a]["r"].append(r)
            out[a]["idx"].append(test)
            out[a]["w"].append(w.tolist())
            act = test[active]
            sp = np.full(len(test), np.nan)
            sp[active] = specificity(P_test[active], S[act], G)
            out[a]["spec"].append(sp)
            if detail and a not in T1_ARMS:
                from sklearn.linear_model import LogisticRegression
                tr = fs["train"]
                ev_tr = event[tr]
                m = np.isfinite(S[tr])
                rng = np.random.default_rng(SEED + fs["f"])
                xs, ys = -P_inner[m], ev_tr[m]
                pick = rng.choice(len(xs), min(300_000, len(xs)), replace=False)
                cal = LogisticRegression(C=1.0).fit(xs[pick, None], ys[pick])
                mt = np.isfinite(S[test])
                p = cal.predict_proba((-P_test[mt])[:, None])[:, 1]
                b, e = brier_ece(p, event[test][mt].astype(float))
                extras[a]["brier"].append(b)
                extras[a]["ece"].append(e)
                picks = nominate(-P_test, T["cores"][test])
                sec = T["secondary"]
                Gs = np.nanmedian(sec[tr], axis=0)
                for i, l in picks:
                    extras[a]["nominated"] += 1
                    extras[a]["hits"] += int(event[test[i], l])
                    row = sec[test[i]]
                    if np.isfinite(row[l]) and np.isfinite(row).sum() >= 50:
                        f = np.isfinite(row) & np.isfinite(Gs)
                        X = np.column_stack([np.ones(f.sum()), Gs[f]])
                        res = row[f] - X @ np.linalg.lstsq(X, row[f], rcond=None)[0]
                        full = np.full(len(row), np.nan)
                        full[f] = res
                        med = np.nanmedian(full)
                        mad = np.nanmedian(np.abs(full - med)) * 1.4826
                        if np.isfinite(full[l]):
                            extras[a]["sec_eval"] += 1
                            extras[a]["sec_conf"] += int((full[l] - med) / max(mad, 1e-6) <= -2)
    summary = {}
    for a in arms:
        summary[a] = {"r": np.concatenate(out[a]["r"]), "spec": np.concatenate(out[a]["spec"]),
                      "idx": np.concatenate(out[a]["idx"]), "weights": out[a]["w"]}
        if detail and a not in T1_ARMS:
            e = extras[a]
            summary[a].update({"brier": float(np.mean(e["brier"])), "ece": float(np.mean(e["ece"])),
                               "nominated": e["nominated"], "hits": e["hits"], "sec_eval": e["sec_eval"],
                               "sec_confirmed": e["sec_conf"]})
    return summary


def zero_arm(T: dict, folds: list[dict]) -> dict:
    hits, sec_eval, nom = 0, 0, 0
    for fs in folds:
        test, S, G, Y = fs["test"], fs["S"], fs["G"], T["Y"]
        event = (robust_z(S) <= -3) & (Y <= -1)
        score = np.tile(-G, (len(test), 1))
        for i, l in nominate(score, T["cores"][test]):
            nom += 1
            hits += int(event[test[i], l])
    return {"nominated": nom, "hits": hits}


def active_mask(T: dict, folds: list[dict], idx: np.ndarray) -> np.ndarray:
    act = np.zeros(len(T["cores"]), dtype=bool)
    for fs in folds:
        ev = (robust_z(fs["S"]) <= -3) & (T["Y"] <= -1)
        act[fs["test"]] = ev[fs["test"]].sum(1) >= 5
    return act[idx]


def main() -> None:
    t_start = time.time()
    plan = sha256(HERE / "DEV_PLAN.md")
    for arm, inputs in ARM_INPUTS.items():
        require([DECLARED[n] for n in inputs], ARM_TIER[arm], DECLARED)
    T = dict(np.load(CACHE / "tables.npz", allow_pickle=False))
    E = true_edges(T)
    E0 = t0_only(E)
    cores = T["cores"]
    L = T["Y"].shape[1]
    print("tables", T["Y"].shape, "edges", len(E.drug), flush=True)
    folds = fold_setup(T)
    K = M.tanimoto(T["fp"], T["fp"])
    V = visible_mask(cores, L)
    Zl = T["expr_z"]
    line_sim = np.corrcoef(Zl)
    np.fill_diagonal(line_sim, -np.inf)
    chem = chem_routes(T, folds, K, V, line_sim)
    print("chem routes", round(time.time() - t_start), "s", flush=True)

    kn_true = knowledge(E, T, ablations=True)
    know_true = knowledge_routes(T, folds, kn_true, ablations=True)
    print("knowledge routes", round(time.time() - t_start), "s", flush=True)
    arms = tuple(STACKS)
    ev = evaluate_arms(T, folds, chem, know_true, arms, V, detail=True)
    idx = ev["chem_full"]["idx"]
    act = active_mask(T, folds, idx)
    fam = T["family"][idx]
    strict = T["strict_new_target"][idx]
    has_t0 = kn_true.has_tc[idx]
    print("evaluated true graph", round(time.time() - t_start), "s; active", int(act.sum()), flush=True)

    def arm_summary(a: str) -> dict:
        e = ev[a]
        d = {"mean_r_active": float(e["r"][act].mean()), "mean_r_all": float(e["r"].mean()),
             "mean_r_active_annotated": float(e["r"][act & has_t0].mean()),
             "mean_r_active_strict_new_target": float(e["r"][act & strict & has_t0].mean()) if (act & strict & has_t0).any() else None,
             "specificity_active": float(np.nanmean(e["spec"][act])), "stack_weights_by_fold": e["weights"],
             "tier": ARM_TIER.get(a, Tier.T0).name}
        for k in ("brier", "ece", "nominated", "hits", "sec_eval", "sec_confirmed"):
            if k in e:
                d[k] = e[k]
        return d

    arms_out = {a: arm_summary(a) for a in arms}
    comparisons = {}
    pairs = [("know_full", "chem_full"), ("know_full", "rkt_full"), ("know_full", "annot_full"), ("rkt_full", "chem_full"),
             ("annot_full", "chem_full"), ("know_full", "density_full"), ("density_full", "chem_full"),
             ("know_full", "know_untyped"), ("know_full", "know_curated_tc"), ("know_full_t1", "know_full"),
             ("know_only", "chem_full"), ("t1_know", "t1_base")]
    for a, b in pairs:
        for name, m in (("active", act), ("active_annotated", act & has_t0), ("active_strict_new_target", act & strict & has_t0)):
            if m.sum() >= 5:
                comparisons[f"{a}-{b}:{name}"] = paired(ev[a]["r"][m], ev[b]["r"][m], fam[m])
    for a, b in [("know_full", "chem_full"), ("rkt_full", "chem_full")]:
        m = act & np.isfinite(ev[a]["spec"]) & np.isfinite(ev[b]["spec"])
        comparisons[f"specificity:{a}-{b}:active"] = paired(ev[a]["spec"][m], ev[b]["spec"][m], fam[m])

    # Single-route diagnostics on annotated active compounds (refusal counted as r = 0).
    single = {}
    for route in ("chem_knn", "chem_ridge", "annot", "rkt_know", "kn_typed", "tc", "tc_untyped", "tc_curated", "density"):
        rs, refused = [], 0
        for fs, ch, kn in zip(folds, chem, know_true):
            P = {**ch["test"], **kn["test"]}[route]
            refused += int((~np.isfinite(P).any(1)).sum())
            rs.append(drug_r(P, fs["S"][fs["test"]], fs["G"]))
        r = np.concatenate(rs)
        single[route] = {"mean_r_active": float(r[act].mean()), "mean_r_active_annotated": float(r[act & has_t0].mean()),
                         "refused_all": refused, "refused_share": refused / len(r)}

    # Controls: twenty seeds of each, whole graph, within fold; resumable.
    partial = json.loads(PARTIAL.read_text(encoding="utf-8")) if PARTIAL.is_file() else {}
    if partial.get("_tables") != sha256(CACHE / "tables.npz") or partial.get("_plan") != plan:
        partial = {"_tables": sha256(CACHE / "tables.npz"), "_plan": plan}
    ctrl_arms = ("know_full", "know_only", "rkt_full", "annot_full", "chem_full")
    n_seeds = 1 if SMOKE else CONTROL_SEEDS
    for kind in CONTROLS:
        for seed in range(n_seeds):
            key = f"{kind}:{seed}"
            if key in partial:
                continue
            Ec = control_edges(E0, kind, seed, T)
            knc = knowledge(Ec, T, ablations=False)
            kr = knowledge_routes(T, folds, knc, ablations=False)
            evc = evaluate_arms(T, folds, chem, kr, ctrl_arms, V, detail=False)
            spec = evc["know_full"]["spec"]
            partial[key] = {
                "know_full": float(evc["know_full"]["r"][act].mean()),
                "know_only": float(evc["know_only"]["r"][act].mean()),
                "rkt_full": float(evc["rkt_full"]["r"][act].mean()),
                "annot_full": float(evc["annot_full"]["r"][act].mean()),
                "know_full_annotated": float(evc["know_full"]["r"][act & has_t0].mean()),
                "tc_gain": float((evc["know_full"]["r"][act] - ev["chem_full"]["r"][act]).mean()),
                "specificity": float(np.nanmean(spec[act])),
            }
            write_json(PARTIAL, partial)
            print(f"  control {key} done ({round(time.time() - t_start)} s)", flush=True)

    true_vals = {"know_full": arms_out["know_full"]["mean_r_active"], "know_only": arms_out["know_only"]["mean_r_active"],
                 "rkt_full": arms_out["rkt_full"]["mean_r_active"], "annot_full": arms_out["annot_full"]["mean_r_active"],
                 "know_full_annotated": arms_out["know_full"]["mean_r_active_annotated"],
                 "tc_gain": float((ev["know_full"]["r"][act] - ev["chem_full"]["r"][act]).mean()),
                 "specificity": arms_out["know_full"]["specificity_active"]}
    controls = {}
    for kind in CONTROLS:
        vals = [partial[f"{kind}:{s}"] for s in range(n_seeds)]
        controls[kind] = {}
        for k, tv in true_vals.items():
            null = np.array([v[k] for v in vals])
            controls[kind][k] = {"true": tv, "null_mean": float(null.mean()), "null_p95": float(np.quantile(null, 0.95)),
                                 "null_max": float(null.max()), "empirical_p": float((1 + (null >= tv).sum()) / (1 + len(null)))}
    g1 = comparisons["know_full-chem_full:active"]
    g1_pass = g1["difference"] > 0 and g1["p_greater"] < 0.05
    g2_pass = all(controls[k]["know_full"]["true"] > controls[k]["know_full"]["null_p95"]
                  and controls[k]["tc_gain"]["true"] > controls[k]["tc_gain"]["null_p95"] for k in CONTROLS)
    g3 = comparisons["specificity:know_full-chem_full:active"]
    g3_pass = g3["difference"] > 0 and g3["p_greater"] < 0.05
    out = {
        "study": "knowledge_reality_20261013", "stage": "exploratory gate on exposed PRISM 19Q4 (not confirmation)",
        "plan_sha256": plan, "tables_sha256": sha256(CACHE / "tables.npz"),
        "population": {"compounds": int(len(idx)), "active": int(act.sum()), "active_annotated": int((act & has_t0).sum()),
                       "active_strict_new_target_annotated": int((act & strict & has_t0).sum()),
                       "annotated_share": float(has_t0.mean()),
                       "active_by_fold": [int(active_mask(T, folds, fs["test"]).sum()) for fs in folds]},
        "chem_ridge_alpha_by_fold": [c["alpha"] for c in chem],
        "arms": arms_out, "zero_arm_decision": zero_arm(T, folds), "single_routes": single,
        "comparisons": comparisons, "controls": controls,
        "time_matched_control": "TIME_STAMPS_UNAVAILABLE: no per-edge dates in PRISM Hub columns or MAP-KG; the Hub "
                                "file (2020-03-24) postdates the PRISM 19Q4 release",
        "gate": {"G1_knowledge_gain": g1_pass, "G2_beats_every_control": g2_pass, "G3_specificity": g3_pass,
                 "verdict": "PASS" if (g1_pass and g2_pass and g3_pass) else "FAIL"},
        "runtime_seconds": round(time.time() - t_start),
    }
    if SMOKE:
        write_json(CACHE / "smoke_development.json", out)
        print("smoke run completed", flush=True)
        return
    write_json(HERE / "DEVELOPMENT.json", out)
    print(json.dumps(out["gate"]), flush=True)


if __name__ == "__main__":
    main()
