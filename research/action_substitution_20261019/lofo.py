"""Phase 2 (PROTOCOL_P2.md): leave-one-implementation-out prediction of partner-specific substitution contrasts.

Writes LOFO_<endpoint>.json (write-once). Usage: python lofo.py [SYNERGY_DELTA_AUC|SYNERGY_OBS_AUC]
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

import cas_data as D
import repro as R

HERE = Path(__file__).resolve().parent
N_BOOT = 2000
N_SWAPS = 300_000
N_B4 = 200_000
EPS = 0.03
RNG = np.random.default_rng(20261019)


# ---------------------------------------------------------------- cell tables
def conc_rank(df):
    rank = {}
    for aid, g in df.groupby("ANCHOR_ID"):
        cs = sorted(g.ANCHOR_CONC.unique(), key=lambda s: float(str(s).split("|")[0]))
        for i, c in enumerate(cs):
            rank[(aid, c)] = i
    return np.array([rank[(a, c)] for a, c in zip(df.ANCHOR_ID, df.ANCHOR_CONC)])


def cells(df, ep, half=None):
    df = df[~df.ANCHOR_NAME.str.contains(r"\|") & ~df.LIBRARY_NAME.str.contains(r"\|")].copy()
    if half is not None:
        df = df[df.half == half]
    df["rk"] = conc_rank(df)
    lib = df.groupby(["LIBRARY_ID", "ANCHOR_ID", "ANCHOR_CONC", "CELL_LINE_NAME"]).agg(
        y=(ep, "mean"), m=("LIBRARY_AUC", "mean"), mp=("ANCHOR_VIABILITY", "mean")).reset_index()
    lib = pd.DataFrame(dict(drug=lib.LIBRARY_ID, role="L", partner="A" + lib.ANCHOR_ID + "@" + lib.ANCHOR_CONC,
                            pdrug=lib.ANCHOR_ID, line=lib.CELL_LINE_NAME, y=lib.y, m=lib.m, mp=lib.mp))
    anc = df.groupby(["ANCHOR_ID", "LIBRARY_ID", "rk", "CELL_LINE_NAME"]).agg(
        y=(ep, "mean"), m=("ANCHOR_VIABILITY", "mean"), mp=("LIBRARY_AUC", "mean")).reset_index()
    anc = pd.DataFrame(dict(drug=anc.ANCHOR_ID, role="A", partner="L" + anc.LIBRARY_ID + "#r" + anc.rk.astype(str),
                            pdrug=anc.LIBRARY_ID, line=anc.CELL_LINE_NAME, y=anc.y, m=anc.m, mp=anc.mp))
    t = pd.concat([lib, anc], ignore_index=True).dropna(subset=["y", "m"])
    t["key"] = t.role + "|" + t.partner + "|" + t.line
    return t.reset_index(drop=True)


class Ref:
    """Reference cells indexed by key; per-fold exclusion of one drug (as drug or partner)."""

    def __init__(self, t):
        self.t = t
        self.by_key = defaultdict(dict)
        for k, d, y, m in zip(t.key, t.drug, t.y, t.m):
            self.by_key[k][d] = (y, m)
        self.pdrug = dict(zip(t.key, t.pdrug))
        self.mp = t.groupby("key").mp.mean().to_dict()
        self.sum = t.groupby("key").y.sum().to_dict()
        self.cnt = t.groupby("key").y.size().to_dict()

    def others(self, key, excl):
        """{drug: (y, m)} at key excluding drugs in excl; empty if the partner is excluded."""
        if self.pdrug.get(key) in excl:
            return {}
        return {d: v for d, v in self.by_key.get(key, {}).items() if d not in excl}


# ---------------------------------------------------------------- drug annotations
class Drugs:
    def __init__(self, census, t_profile):
        dr = census["drugs"]
        self.ids = sorted(dr)
        self.ts = {i: D.target_set(dr[i]["target"]) for i in self.ids}
        self.pw = {i: dr[i]["pathway"] for i in self.ids}
        self.name = {i: dr[i]["name"] for i in self.ids}
        prof = t_profile.groupby(["drug", "role", "line"]).m.mean().unstack("line")
        self.prof = prof
        self.mean_m = prof.mean(axis=1).to_dict()
        self.corr = {}
        for role in ("L", "A"):
            p = prof.xs(role, level="role")
            c = p.T.corr(min_periods=10)
            self.corr[role] = c

    def jac(self, a, b):
        x, y = self.ts.get(a, frozenset()), self.ts.get(b, frozenset())
        return len(x & y) / len(x | y) if x | y else 0.0

    def same_pw(self, a, b):
        return float(self.pw.get(a) is not None and self.pw.get(a) == self.pw.get(b))

    def c(self, role, a, b):
        try:
            v = self.corr[role].at[a, b]
        except KeyError:
            return np.nan
        return v

    def siblings(self, x, role, present):
        return [s for s in present if s != x and self.ts.get(s, frozenset()) & self.ts.get(x, frozenset())]


# ---------------------------------------------------------------- ridge
def ridge_fit(F, y, alpha=1.0):
    mu, sd = F.mean(0), F.std(0)
    sd[sd == 0] = 1
    Z = (F - mu) / sd
    Z = np.c_[np.ones(len(Z)), Z]
    P = alpha * np.eye(Z.shape[1])
    P[0, 0] = 0
    w = np.linalg.solve(Z.T @ Z + P, Z.T @ y)
    return mu, sd, w


def ridge_pred(model, F):
    mu, sd, w = model
    return np.c_[np.ones(len(F)), (F - mu) / sd] @ w


# ---------------------------------------------------------------- features
def swap_feats(dg, role, s, x, yS, mS, mX, mp, b1, pd_):
    f1 = mX - mS
    f2 = dg.mean_m.get((x, role), np.nan) - dg.mean_m.get((s, role), np.nan)
    cc = dg.c(role, s, x)
    f3 = 1 - (cc if np.isfinite(cc) else 0.0)
    return [f1, f2 if np.isfinite(f2) else 0.0, f3, dg.jac(x, s), dg.same_pw(x, s), f1 * mp,
            dg.same_pw(x, pd_) - dg.same_pw(s, pd_), dg.jac(x, pd_) - dg.jac(s, pd_), yS - b1, b1, float(role == "A")]


P_FEATS = [5, 6, 7]


def b4_feats(dg, role, x, mX, mp, b1, pd_, ppm):
    mm = dg.mean_m.get((x, role), np.nan)
    return [b1, mX, mm if np.isfinite(mm) else 0.0, mp, dg.same_pw(x, pd_), dg.jac(x, pd_), ppm, float(role == "A")]


def pp_table(t, dg):
    """Sum/count of y by (pathway of drug, pathway of partner) and by (drug, partner pathway) for leave-drug-out means."""
    pwd = t.drug.map(dg.pw).fillna("?")
    pwp = t.pdrug.map(dg.pw).fillna("?")
    g = t.groupby([pwd, pwp]).y.agg(["sum", "size"])
    gd = t.groupby([t.drug, pwp]).y.agg(["sum", "size"])
    return g["sum"].to_dict(), g["size"].to_dict(), gd["sum"].to_dict(), gd["size"].to_dict()


def ppm_of(pp, dg, d, pdrug, gm):
    S, N, SD, ND = pp
    a, b = dg.pw.get(d, "?"), dg.pw.get(pdrug, "?")
    s = S.get((a, b), 0.0) - SD.get((d, b), 0.0)
    n = N.get((a, b), 0) - ND.get((d, b), 0)
    return s / n if n > 0 else gm


# ---------------------------------------------------------------- fold fitting
def fit_fold(ref, dg, X, swap_sample):
    """Fit beta (B2), ridge M / M-noP, ridge B4 on the training table without X."""
    excl = {X}
    # swap training set for M and B2
    F, Y, sib_f1, sib_y = [], [], [], []
    for k, s, x in swap_sample:
        if s == X or x == X:
            continue
        o = ref.others(k, excl)
        if s not in o or x not in o:
            continue
        role = k[0]
        (yS, mS), (yX, mX) = o[s], o[x]
        n = len(o)
        if n < 3:
            continue
        b1 = (sum(v[0] for v in o.values()) - yS - yX) / (n - 2)
        f = swap_feats(dg, role, s, x, yS, mS, mX, ref.mp[k], b1, ref.pdrug[k])
        F.append(f)
        Y.append(yX - yS)
        if dg.ts.get(s, frozenset()) & dg.ts.get(x, frozenset()):
            sib_f1.append((role, mX - mS))
            sib_y.append(yX - yS)
    F, Y = np.array(F, float), np.array(Y, float)
    m_full = ridge_fit(F, Y)
    keep = [i for i in range(F.shape[1]) if i not in P_FEATS]
    m_nop = (ridge_fit(F[:, keep], Y), keep)
    beta = {}
    for role in ("L", "A"):
        xs = np.array([f for r, f in sib_f1 if r == role])
        ys = np.array([y for (r, _), y in zip(sib_f1, sib_y) if r == role])
        beta[role] = float(np.polyfit(xs, ys, 1)[0]) if len(xs) > 20 else 0.0
    # B4 cold-start regression on training cells
    tt = ref.t[(ref.t.drug != X) & (ref.t.pdrug != X)]
    if len(tt) > N_B4:
        tt = tt.sample(N_B4, random_state=1)
    pp = pp_table(ref.t[(ref.t.drug != X) & (ref.t.pdrug != X)], dg)
    gm = float(tt.y.mean())
    FB, YB = [], []
    for k, d, y, m, pd_ in zip(tt.key, tt.drug, tt.y, tt.m, tt.pdrug):
        o = ref.others(k, excl)
        n = len(o)
        if n < 2:
            continue
        b1 = (sum(v[0] for v in o.values()) - y) / (n - 1)
        FB.append(b4_feats(dg, k[0], d, m, ref.mp[k], b1, pd_, ppm_of(pp, dg, d, pd_, gm)))
        YB.append(y)
    m_b4 = ridge_fit(np.array(FB, float), np.array(YB, float))
    return dict(M=m_full, MnoP=m_nop, beta=beta, B4=m_b4, pp=pp, gm=gm)


def predict_fold(ref, dg, X, fit, test):
    """Cell-level predictions for X's test cells (rows of `test` with drug == X) using reference `ref` without X."""
    excl = {X}
    out = []
    for k, role, line, partner, pd_, y, m in zip(test.key, test.role, test.line, test.partner, test.pdrug, test.y, test.m):
        o = ref.others(k, excl)
        if not o:
            continue
        sibs = dg.siblings(X, role, o)
        if not sibs:
            continue
        mp = ref.mp.get(k, np.nan)
        b1_all = float(np.mean([v[0] for v in o.values()]))
        ref_s = float(np.mean([o[s][0] for s in sibs]))
        p = dict(B0=ref_s, B1=b1_all)
        same = [v[0] for d, v in o.items() if dg.same_pw(d, X)]
        p["B1p"] = float(np.mean(same)) if same else b1_all
        p["B2"] = float(np.mean([o[s][0] + fit["beta"][role] * (m - o[s][1]) for s in sibs]))
        cands = [(dg.c(role, X, d), d) for d in o]
        cands = [(c, d) for c, d in cands if np.isfinite(c)]
        p["B3"] = o[max(cands)[1]][0] if cands else b1_all
        n = len(o)
        f4 = b4_feats(dg, role, X, m, mp, b1_all, pd_, ppm_of(fit["pp"], dg, X, pd_, fit["gm"]))
        p["B4"] = float(ridge_pred(fit["B4"], np.array([f4]))[0])
        w = np.array([np.exp(-(1 - (dg.c(role, X, d) if np.isfinite(dg.c(role, X, d)) else 0.0)) / 0.2) * (1 + 2 * dg.jac(X, d)) for d in o])
        p["B5"] = float(np.dot(w, [v[0] for v in o.values()]) / w.sum())
        ms, mn = [], []
        for s in sibs:
            yS, mS = o[s]
            b1 = (sum(v[0] for v in o.values()) - yS) / (n - 1) if n > 1 else b1_all
            f = np.array([swap_feats(dg, role, s, X, yS, mS, m, mp, b1, pd_)], float)
            ms.append(yS + ridge_pred(fit["M"], f)[0])
            mn.append(yS + ridge_pred(fit["MnoP"][0], f[:, fit["MnoP"][1]])[0])
        p["M"], p["MnoP"] = float(np.mean(ms)), float(np.mean(mn))
        out.append(dict(X=X, role=role, partner=partner, line=line, y=y, ref=ref_s, **p))
    return out


METHODS = ["B0", "B1", "B1p", "B2", "B3", "B4", "B5", "M", "MnoP"]
BASELINES = ["B0", "B1", "B1p", "B2", "B3", "B4", "B5"]


def partner_units(cellpred):
    c = pd.DataFrame(cellpred)
    c["obs"] = c.y - c.ref
    for m in METHODS:
        c["d_" + m] = c[m] - c.ref
    agg = {"obs": "mean", "line": "nunique", **{"d_" + m: "mean" for m in METHODS}}
    return c.groupby(["X", "role", "partner"]).agg(agg).reset_index()


def evaluate(u):
    def mses(g):
        return {m: float(np.mean((g["d_" + m] - g.obs) ** 2)) for m in METHODS}
    base = mses(u)
    best = min(BASELINES, key=lambda m: base[m])
    groups = {x: g for x, g in u.groupby("X")}
    names = list(groups)
    bs = defaultdict(list)
    for _ in range(N_BOOT):
        g = pd.concat([groups[names[i]] for i in RNG.choice(len(names), len(names))], ignore_index=True)
        s = mses(g)
        bs["best_minus_M"].append(s[best] - s["M"])
        bs["rel"].append((s[best] - s["M"]) / s[best])
        bs["MnoP_minus_M"].append(s["MnoP"] - s["M"])
        bs["B0_minus_M"].append(s["B0"] - s["M"])
        bs["B2_minus_M"].append(s["B2"] - s["M"])
    ci = {k: [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))] for k, v in bs.items()}
    fail = (u.obs.abs() > EPS).to_numpy()
    eq = {}
    for m in METHODS:
        s = u["d_" + m].abs().to_numpy()
        eq[m] = dict(auroc=auroc(s, fail), acc=float(np.mean((s > EPS) == fail)))
    rel = (base[best] - base["M"]) / base[best]
    lo, hi = ci["rel"]
    label = "LEARNABLE" if ci["best_minus_M"][0] > 0 and rel >= 0.05 else ("NOT_BEYOND_BASELINE" if hi < 0.05 else "INCONCLUSIVE")
    return dict(n_units=int(len(u)), n_impl=len(names), mse=base, best_baseline=best, rel_reduction=float(rel), ci=ci,
                failure_rate=float(fail.mean()), equivalence=eq, label=label,
                var_obs=float(np.var(u.obs)), mse_zero=float(np.mean(u.obs ** 2)))


def auroc(score, y):
    y = np.asarray(y, bool)
    if y.all() or (~y).all():
        return float("nan")
    r = pd.Series(score).rank().to_numpy()
    return float((r[y].sum() - y.sum() * (y.sum() + 1) / 2) / (y.sum() * (~y).sum()))


def noise_ceiling(df, ep, dg, units):
    """Half-split reliability of partner-level Delta_obs for evaluable units (descriptive)."""
    want = set(zip(units.X, units.role, units.partner))
    res = {}
    for h in (1, 2):
        t = cells(df, ep, half=h)
        ref = Ref(t)
        vals = defaultdict(list)
        for k, d, role, partner, y in zip(t.key, t.drug, t.role, t.partner, t.y):
            if (d, role, partner) not in want:
                continue
            o = ref.others(k, {d})
            sibs = dg.siblings(d, role, o)
            if sibs:
                vals[(d, role, partner)].append(y - np.mean([o[s][0] for s in sibs]))
        res[h] = {k: np.mean(v) for k, v in vals.items()}
    common = sorted(set(res[1]) & set(res[2]))
    if len(common) < 10:
        return dict(n=len(common))
    a = np.array([res[1][k] for k in common])
    b = np.array([res[2][k] for k in common])
    return dict(n=len(common), r=float(np.corrcoef(a, b)[0, 1]), repro_var=float(np.cov(a, b)[0, 1]),
                noise_var_half=float(np.var(a - b) / 2))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    ep = args[0] if args else "SYNERGY_DELTA_AUC"
    out_path = HERE / f"LOFO_{ep}.json"
    if out_path.exists():
        raise SystemExit(f"{out_path.name} exists (write-once)")
    census = json.loads((HERE / "CENSUS.json").read_text(encoding="utf-8"))
    df = R.halves(D.full("original"))
    t = cells(df, ep)
    ref = Ref(t)
    dg = Drugs(census, t)
    # held-out implementations: drugs with a target-overlap sibling in the same role
    present = t.groupby("role").drug.agg(set).to_dict()
    impl = sorted({(x) for role, S in present.items() for x in S if dg.siblings(x, role, S)})
    # global swap sample (same role, partner, line); fold-specific exclusion happens in fit_fold
    keys = list(ref.by_key)
    swap_sample = []
    while len(swap_sample) < N_SWAPS:
        k = keys[RNG.integers(len(keys))]
        ds = list(ref.by_key[k])
        if len(ds) < 3:
            continue
        s, x = RNG.choice(len(ds), 2, replace=False)
        swap_sample.append((k, ds[s], ds[x]))
    val = D.full("validation")
    val["half"] = 0
    tv = cells(val, ep)
    refv = Ref(tv)
    preds, preds_v, folds = [], [], {}
    if "--smoke" in sys.argv:
        # execution check only: two folds, counts and finiteness, no metric
        for X in impl[:2]:
            fit = fit_fold(ref, dg, X, swap_sample[:20000])
            pr = predict_fold(ref, dg, X, fit, t[t.drug == X])
            pv = predict_fold(refv, dg, X, fit, tv[tv.drug == X])
            ok = all(np.isfinite(r[m]) for r in pr + pv for m in METHODS)
            print("smoke", dg.name[X], len(pr), len(pv), "finite" if ok else "NONFINITE", flush=True)
        print("implementations:", len(impl), [dg.name[x] for x in impl])
        return
    for i, X in enumerate(impl):
        fit = fit_fold(ref, dg, X, swap_sample)
        pr = predict_fold(ref, dg, X, fit, t[t.drug == X])
        pv = predict_fold(refv, dg, X, fit, tv[tv.drug == X])
        preds += pr
        preds_v += pv
        folds[dg.name[X]] = dict(cells=len(pr), cells_val=len(pv), beta=fit["beta"])
        print(f"[{i + 1}/{len(impl)}] {dg.name[X]}: {len(pr)} cells, {len(pv)} validation cells", flush=True)
    u = partner_units(preds)
    res = dict(endpoint=ep, protocol="PROTOCOL_P2.md", eps=EPS, n_boot=N_BOOT, implementations=[dg.name[x] for x in impl],
               folds=folds, primary=evaluate(u), noise_ceiling=noise_ceiling(df, ep, dg, u))
    # partner-conditioning check restricted to units with >= 3 lines (less noisy targets)
    u3 = u[u.line >= 3]
    res["primary_ge3_lines"] = evaluate(u3) if u3.X.nunique() >= 5 else dict(n_units=int(len(u3)))
    if preds_v:
        uv = partner_units(preds_v)
        res["validation_screen"] = evaluate(uv) if uv.X.nunique() >= 3 else dict(n_units=int(len(uv)))
    res["per_impl"] = {dg.name[x]: dict(n=int(len(g)), mse={m: float(np.mean((g["d_" + m] - g.obs) ** 2)) for m in ("B0", "B2", "B4", "M")})
                       for x, g in u.groupby("X")}
    u.to_csv(HERE / f"lofo_units_{ep}.csv", index=False, lineterminator="\n")
    out_path.write_text(json.dumps(res, indent=1, default=float), encoding="utf-8", newline="\n")
    p = res["primary"]
    print(json.dumps(dict(label=p["label"], n_units=p["n_units"], n_impl=p["n_impl"], best=p["best_baseline"],
                          rel=p["rel_reduction"], mse=p["mse"], ci=p["ci"], eq={m: p["equivalence"][m] for m in ("B0", "B2", "M")},
                          noise=res["noise_ceiling"]), indent=1, default=float))
    for k in ("primary_ge3_lines", "validation_screen"):
        if k in res and "label" in res[k]:
            r = res[k]
            print(k, r["label"], r["n_units"], r["best_baseline"], round(r["rel_reduction"], 4), r["ci"]["best_minus_M"], r["ci"]["MnoP_minus_M"])


if __name__ == "__main__":
    main()
