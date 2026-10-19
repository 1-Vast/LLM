"""P0 Biological Residual Information Gate (PROTOCOL.md). Writes P0_RESULT.json and p0_units_*.csv (write-once).

Usage: python p0.py [--smoke]
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.preprocessing import StandardScaler

HERE = Path(__file__).resolve().parent
AS = HERE.parent / "action_substitution_20261019"
sys.path.insert(0, str(AS))
import cas_data as D  # noqa: E402
import repro as R  # noqa: E402
from lofo import Drugs, Ref, cells  # noqa: E402

EPS = 0.03
N_BOOT = 2000
N_PERM = 200
MIN_GAIN = 0.02
RNG = np.random.default_rng(20261019)
SMOKE = "--smoke" in sys.argv


# ---------------------------------------------------------------- helpers
def families(dg, ids):
    parent = {i: i for i in ids}

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for a in ids:
        for b in ids:
            if a < b and dg.ts.get(a, frozenset()) & dg.ts.get(b, frozenset()):
                parent[find(a)] = find(b)
    return {i: find(i) for i in ids}


def rho(dg, role, a, b):
    c = dg.c(role, a, b)
    return c if np.isfinite(c) else 0.0


def jac_mat(ts, ids):
    n = len(ids)
    J = np.zeros((n, n))
    for i, a in enumerate(ids):
        for j, b in enumerate(ids):
            u = ts[a] | ts[b]
            J[i, j] = len(ts[a] & ts[b]) / len(u) if u else 0.0
    return J


def cluster_boot(df, group, stat, n=N_BOOT, rng=RNG):
    groups = {g: x for g, x in df.groupby(group)}
    names = list(groups)
    vals = []
    for _ in range(n):
        b = pd.concat([groups[names[i]] for i in rng.choice(len(names), len(names))], ignore_index=True)
        vals.append(stat(b))
    v = np.array(vals, float)
    return [float(np.nanpercentile(v, 2.5)), float(np.nanpercentile(v, 97.5))]


def auroc(score, y):
    y = np.asarray(y, bool)
    if y.all() or (~y).all():
        return float("nan")
    r = pd.Series(np.asarray(score, float)).rank().to_numpy()
    return float((r[y].sum() - y.sum() * (y.sum() + 1) / 2) / (y.sum() * (~y).sum()))


def dec_metrics(obs, pred):
    fail = np.abs(obs) > EPS
    p = np.abs(pred) > EPS
    sens = (p & fail).sum() / max(fail.sum(), 1)
    spec = (~p & ~fail).sum() / max((~fail).sum(), 1)
    slope = float(np.polyfit(pred, obs, 1)[0]) if np.var(pred) > 0 else float("nan")
    return dict(mse=float(np.mean((pred - obs) ** 2)), auroc=auroc(np.abs(pred), fail), sens=float(sens), spec=float(spec),
                bal_acc=float(0.5 * (sens + spec)), acc=float(np.mean(p == fail)), calib_slope=slope)


# ---------------------------------------------------------------- P0-A cell table
def test_cells(t, ref, dg, impl, ids):
    """Per held-out cell: reference drugs (ids index), their y, F weight; sibling reference mean. Also B1, B1p, B0."""
    idx = {d: i for i, d in enumerate(ids)}
    rows = []
    for X in impl:
        for k, role, partner, line, y, m in zip(*[t[t.drug == X][c] for c in ("key", "role", "partner", "line", "y", "m")]):
            o = ref.others(k, {X})
            if not o:
                continue
            sibs = dg.siblings(X, role, o)
            if not sibs:
                continue
            ds = [d for d in o if d in idx]
            yv = np.array([o[d][0] for d in ds])
            fw = np.array([np.exp(-(1 - rho(dg, role, X, d)) / 0.2) for d in ds])
            same = [o[d][0] for d in ds if dg.same_pw(d, X)]
            rows.append(dict(X=X, role=role, partner=partner, line=line, key=k, y=y, m=m,
                             ref=float(np.mean([o[s][0] for s in sibs])), sibs=sibs,
                             xi=idx[X], di=np.array([idx[d] for d in ds]), yv=yv, fw=fw,
                             B1=float(yv.mean()), B1p=float(np.mean(same)) if same else float(yv.mean())))
    return rows


def kernel_preds(rows, J, use_f=True, use_t=True):
    out = np.empty(len(rows))
    for i, r in enumerate(rows):
        w = (r["fw"] if use_f else 1.0) * ((1 + 2 * J[r["xi"], r["di"]]) if use_t else 1.0)
        w = w * np.ones(len(r["yv"]))
        out[i] = np.dot(w, r["yv"]) / w.sum()
    return out


def to_units(rows, preds):
    c = pd.DataFrame([{k: r[k] for k in ("X", "role", "partner", "line", "y", "ref")} for r in rows])
    c["obs"] = c.y - c.ref
    for name, p in preds.items():
        c["d_" + name] = np.asarray(p) - c.ref
    agg = {"obs": "mean", "line": "nunique", **{"d_" + n: "mean" for n in preds}}
    return c, c.groupby(["X", "role", "partner"]).agg(agg).reset_index()


def permute_targets(dg, ids, rng, within_pathway):
    ts = dict(dg.ts)
    if within_pathway:
        groups = defaultdict(list)
        for i in ids:
            groups[dg.pw.get(i)].append(i)
    else:
        groups = {"all": list(ids)}
    for g in groups.values():
        perm = rng.permutation(len(g))
        sets = [dg.ts.get(i, frozenset()) for i in g]
        for i, p in zip(g, perm):
            ts[i] = sets[p]
    return ts


def p0a(ep, t, ref, dg, impl, ids, fam):
    rows = test_cells(t, ref, dg, impl, ids)
    J = jac_mat({i: dg.ts.get(i, frozenset()) for i in ids}, ids)
    preds = dict(F=kernel_preds(rows, J, True, False), T=kernel_preds(rows, J, False, True), FT=kernel_preds(rows, J, True, True),
                 B1=[r["B1"] for r in rows], B1p=[r["B1p"] for r in rows], B0=[r["ref"] for r in rows])
    cell, u = to_units(rows, preds)
    u["family"] = u.X.map(fam)
    res = dict(n_units=int(len(u)), n_impl=int(u.X.nunique()), n_families=int(u.family.nunique()))
    res["families"] = {dg.name[f]: sorted(dg.name[x] for x in u[u.family == f].X.unique()) for f in u.family.unique()}
    res["arms"] = {a: dec_metrics(u.obs.to_numpy(), u["d_" + a].to_numpy()) for a in preds}
    # reproduction of historical B5
    hist = pd.read_csv(AS / f"lofo_units_{ep}.csv", dtype={"X": str})
    mg = u.merge(hist[["X", "role", "partner", "d_B5"]], on=["X", "role", "partner"], how="inner")
    res["b5_reproduction"] = dict(n_matched=int(len(mg)), n_hist=int(len(hist)), max_abs_diff=float(np.abs(mg.d_FT - mg.d_B5).max()))
    # contrasts
    def mse(g, a):
        return float(np.mean((g["d_" + a] - g.obs) ** 2))
    f_ft = mse(u, "F") - mse(u, "FT")
    res["F_minus_FT"] = dict(point=f_ft, rel=f_ft / mse(u, "F"),
                             ci_family=cluster_boot(u, "family", lambda g: mse(g, "F") - mse(g, "FT")),
                             ci_impl=cluster_boot(u, "X", lambda g: mse(g, "F") - mse(g, "FT")),
                             rel_ci_family=cluster_boot(u, "family", lambda g: (mse(g, "F") - mse(g, "FT")) / mse(g, "F")))
    for a, b in (("B0", "T"), ("B1", "T"), ("T", "FT"), ("B1", "F")):
        res[f"{a}_minus_{b}"] = dict(point=mse(u, a) - mse(u, b), ci_family=cluster_boot(u, "family", lambda g: mse(g, a) - mse(g, b)))
    # shuffles
    perm = {}
    for name, within in (("pathway", True), ("global", False)):
        vals = []
        prng = np.random.default_rng(11 if within else 12)
        for _ in range(5 if SMOKE else N_PERM):
            Jp = jac_mat(permute_targets(dg, ids, prng, within), ids)
            p = kernel_preds(rows, Jp, True, True)
            _, up = to_units(rows, {"P": p})
            vals.append(float(np.mean((up.d_P - up.obs) ** 2)))
        vals = np.array(vals)
        perm[name] = dict(mean=float(vals.mean()), p5=float(np.percentile(vals, 5)), p95=float(np.percentile(vals, 95)),
                          p_value=float((np.sum(vals <= mse(u, "FT")) + 1) / (len(vals) + 1)))
    res["shuffle"] = perm
    res["per_family_mse"] = {dg.name[f]: {a: mse(g, a) for a in ("B0", "B1", "T", "F", "FT")} | {"n": int(len(g))}
                             for f, g in u.groupby("family")}
    # gate 1
    n_fam = res["n_families"]
    lo, hi = res["F_minus_FT"]["rel_ci_family"]
    if n_fam < 8:
        g1 = "UNDERPOWERED"
    elif (res["F_minus_FT"]["rel"] >= 0.05 and res["F_minus_FT"]["ci_family"][0] > 0 and perm["pathway"]["p_value"] < 0.05
          and res["arms"]["FT"]["bal_acc"] >= res["arms"]["F"]["bal_acc"]):
        g1 = "PASS"
    elif lo <= 0 <= hi and lo <= 0.05 <= hi:
        g1 = "UNDERPOWERED"
    else:
        g1 = "FAIL"
    res["gate1"] = g1
    return res, rows, cell, u


# ---------------------------------------------------------------- P0-B
def p0b(u, rows, dg, fam):
    hist = pd.read_csv(AS / "lofo_units_SYNERGY_DELTA_AUC.csv", dtype={"X": str})
    feats = defaultdict(lambda: defaultdict(list))
    for r in rows:
        X, role = r["X"], r["role"]
        key = (X, role, r["partner"])
        for s in r["sibs"]:
            j = dg.jac(X, s)
            feats[key]["one_minus_j"].append(1 - j)
            feats[key]["exact"].append(float(bool(dg.ts.get(X)) and dg.ts.get(X) == dg.ts.get(s)))
            feats[key]["primary"].append(float(bool(dg.primary.get(X)) and dg.primary.get(X) == dg.primary.get(s)))
            feats[key]["rho"].append(rho(dg, role, X, s))
            feats[key]["fs_td"].append(rho(dg, role, X, s) * (1 - j))
            mx, ms = dg.mean_m.get((X, role), np.nan), dg.mean_m.get((s, role), np.nan)
            feats[key]["potency_mismatch"].append(abs(mx - ms) if np.isfinite(mx) and np.isfinite(ms) else 0.0)
        ww = r["fw"]
        feats[key]["n_eff"].append(ww.sum() ** 2 / np.sum(ww ** 2))
    rows_out = []
    for (X, role, p), f in feats.items():
        rows_out.append(dict(X=X, role=role, partner=p, one_minus_j=np.mean(f["one_minus_j"]), exact=max(f["exact"]),
                             primary_shared=max(f["primary"]), fs_td=max(f["fs_td"]), rho=np.mean(f["rho"]),
                             potency_mismatch=np.mean(f["potency_mismatch"]), n_eff=np.mean(f["n_eff"])))
    F = pd.DataFrame(rows_out)
    d = u.merge(F, on=["X", "role", "partner"]).merge(hist[["X", "role", "partner", "d_B4"]], on=["X", "role", "partner"], how="left")
    d["dis_b1"] = (d.d_FT - d.d_B1).abs()
    d["dis_b4"] = (d.d_FT - d.d_B4.fillna(d.d_FT)).abs()
    d["partner_same_pw"] = [float(dg.same_pw(x, p[1:].split("@")[0].split("#")[0])) for x, p in zip(d.X, d.partner)]
    d["is_anchor"] = (d.role == "A").astype(float)
    d["e"] = d.obs - d.d_FT
    d["cons"] = ((d.obs.abs() > EPS) != (d.d_FT.abs() > EPS)).astype(int)
    d["family"] = d.X.map(fam)
    sets = dict(generic=["rho", "potency_mismatch", "n_eff", "dis_b1", "dis_b4", "partner_same_pw", "is_anchor"],
                bio=["one_minus_j", "exact", "primary_shared", "fs_td"])
    sets["both"] = sets["generic"] + sets["bio"]
    for name, cols in sets.items():
        p_cons = np.full(len(d), np.nan)
        g_hat = np.full(len(d), np.nan)
        for f in d.family.unique():
            tr, te = d.family != f, d.family == f
            sc = StandardScaler().fit(d.loc[tr, cols])
            Xtr, Xte = sc.transform(d.loc[tr, cols]), sc.transform(d.loc[te, cols])
            if d.loc[tr, "cons"].nunique() == 2:
                p_cons[te.to_numpy()] = LogisticRegression(C=1.0, max_iter=1000).fit(Xtr, d.loc[tr, "cons"]).predict_proba(Xte)[:, 1]
            g_hat[te.to_numpy()] = Ridge(alpha=1.0).fit(Xtr, d.loc[tr, "e"]).predict(Xte)
        d["p_" + name] = p_cons
        d["g_" + name] = g_hat
    res = dict(n_units=int(len(d)), n_families=int(d.family.nunique()), cons_rate=float(d.cons.mean()),
               auroc={n: auroc(d["p_" + n], d.cons) for n in sets})
    res["auroc_both_minus_generic"] = dict(point=res["auroc"]["both"] - res["auroc"]["generic"],
                                           ci_family=cluster_boot(d, "family", lambda g: auroc(g.p_both, g.cons) - auroc(g.p_generic, g.cons)))
    d["d_corr"] = d.d_FT + d.g_both
    res["corrected"] = dict(b5=dec_metrics(d.obs.to_numpy(), d.d_FT.to_numpy()), corr=dec_metrics(d.obs.to_numpy(), d.d_corr.to_numpy()),
                            mse_gain_ci_family=cluster_boot(d, "family", lambda g: np.mean((g.d_FT - g.obs) ** 2) - np.mean((g.d_corr - g.obs) ** 2)))
    res["univariate_assoc_abs_e"] = {c: float(np.corrcoef(d[c], d.e.abs())[0, 1]) for c in sets["both"] if np.var(d[c]) > 0}
    if res["n_families"] < 8:
        g2 = "UNDERPOWERED"
    elif (res["auroc_both_minus_generic"]["point"] >= 0.05 and res["auroc_both_minus_generic"]["ci_family"][0] > 0
          and res["corrected"]["mse_gain_ci_family"][0] > 0 and res["corrected"]["corr"]["bal_acc"] >= res["corrected"]["b5"]["bal_acc"]):
        g2 = "PASS"
    else:
        lo, hi = res["auroc_both_minus_generic"]["ci_family"]
        g2 = "UNDERPOWERED" if lo <= 0 and hi >= 0.05 else "FAIL"
    res["gate2"] = g2
    return res, d


# ---------------------------------------------------------------- P0-C
def choice_sets(tE, refE, dg, fam, ids):
    idx = set(ids)
    J = {}
    out = []
    for k, o in refE.by_key.items():
        role = k[0]
        pd_ = refE.pdrug[k]
        mem = defaultdict(list)
        for d in o:
            if d in idx:
                mem[fam[d]].append(d)
        for f, M in mem.items():
            if len(M) < 3:
                continue
            for A in M:
                alts = [x for x in M if x != A]
                oref = {d: v for d, v in o.items() if d not in alts and d != pd_}
                yv = np.array([v[0] for v in oref.values()])
                ds = list(oref)
                mp = refE.mp[k]
                for X in alts:
                    fw = np.array([np.exp(-(1 - rho(dg, role, X, d)) / 0.2) for d in ds])
                    tw = np.array([1 + 2 * dg.jac(X, d) for d in ds])
                    p = dict(F=np.dot(fw, yv) / fw.sum(), T=np.dot(tw, yv) / tw.sum(), FT=np.dot(fw * tw, yv) / (fw * tw).sum(),
                             B1=yv.mean(), B0=o[A][0])
                    yX, mX = o[X]
                    out.append(dict(key=k, A=A, X=X, family=f, role=role, mX=mX, mp=mp, yE=yX, **{"p_" + a: v for a, v in p.items()}))
    return pd.DataFrame(out)


def p0c(df_raw, cs, dg):
    cs = cs.copy()
    cs["ecb_obs"] = np.minimum(cs.mX, cs.mp) - cs.yE
    for a in ("F", "T", "FT", "B1", "B0"):
        cs["ecb_" + a] = np.minimum(cs.mX, cs.mp) - cs["p_" + a]
    g = cs.groupby(["key", "A"])
    sets = []
    for (k, A), s in g:
        row = dict(key=k, A=A, family=s.family.iloc[0], n_alt=len(s), random=s.ecb_obs.mean(), oracle=s.ecb_obs.max(),
                   eff_random=-s.yE.mean())
        for a in ("F", "T", "FT", "B1", "B0"):
            sc = s["ecb_" + a].to_numpy()
            best = np.flatnonzero(sc == sc.max())
            row[a] = float(s.ecb_obs.to_numpy()[best].mean())  # ties -> expected value of random tie-break
            row["wrong_" + a] = float(np.mean([(s.ecb_obs.iloc[b] <= 0) and (s.ecb_obs.max() > 0.02) for b in best]))
            ef = -s["p_" + a].to_numpy()
            bb = np.flatnonzero(ef == ef.max())
            row["eff_" + a] = float(-s.yE.to_numpy()[bb].mean())
        sets.append(row)
    S = pd.DataFrame(sets)
    res = dict(n_sets=int(len(S)), n_keys=int(S.key.nunique()), n_families=int(S.family.nunique()),
               families={dg.name[f]: int((S.family == f).sum()) for f in S.family.unique()},
               mean_alternatives=float(S.n_alt.mean()), oracle_opportunity=float((S.oracle - S.random).mean()),
               share_sets_any_alt_ecb_gt_0_02=float((S.oracle > 0.02).mean()))
    res["gain_over_random"] = {a: float((S[a] - S.random).mean()) for a in ("F", "T", "FT", "B1", "B0")}
    res["gain_ci_family"] = {a: cluster_boot(S, "family", lambda x, a=a: (x[a] - x.random).mean()) for a in ("F", "T", "FT", "B1")}
    res["FT_minus_F"] = dict(point=float((S.FT - S.F).mean()), ci_family=cluster_boot(S, "family", lambda x: (x.FT - x.F).mean()))
    res["wrong_advancement"] = {a: float(S["wrong_" + a].mean()) for a in ("F", "T", "FT", "B1", "B0")}
    res["efficacy_gain_over_random"] = {a: float((S["eff_" + a] - S.eff_random).mean()) for a in ("F", "T", "FT", "B1", "B0")}
    return res, S


def reproducible_opportunity(df, dg, fam, ids):
    tabs = {h: cells(df, "SYNERGY_OBS_AUC", half=h) for h in (1, 2)}
    val = {}
    for h, t in tabs.items():
        val[h] = {(k, d): min(m, mp) - y for k, d, m, mp, y in zip(t.key, t.drug, t.m, t.mp, t.y)}
    keys = defaultdict(set)
    for (k, d) in val[1]:
        if (k, d) in val[2] and d in fam:
            keys[k].add(d)
    gains, fams = [], []
    for k, ds in keys.items():
        mem = defaultdict(list)
        for d in ds:
            mem[fam[d]].append(d)
        for f, M in mem.items():
            if len(M) < 3:
                continue
            for A in M:
                alts = [x for x in M if x != A]
                v1 = np.array([val[1][(k, x)] for x in alts])
                v2 = np.array([val[2][(k, x)] for x in alts])
                b = np.flatnonzero(v1 == v1.max())
                gains.append(v2[b].mean() - v2.mean())
                fams.append(f)
    G = pd.DataFrame(dict(gain=gains, family=fams))
    if len(G) == 0:
        return dict(n_sets=0)
    return dict(n_sets=int(len(G)), n_families=int(G.family.nunique()), reproducible_opportunity=float(G.gain.mean()),
                ci_family=cluster_boot(G, "family", lambda x: x.gain.mean()))


# ---------------------------------------------------------------- feedback vs B5
def feedback(cell, dg):
    ref = json.loads((AS / "REFINE_SYNERGY_DELTA_AUC.json").read_text(encoding="utf-8"))
    wmap = {k: v["w"] for k, v in ref["folds"].items()}
    out = defaultdict(list)
    c = cell.copy()
    c["fam"] = 0
    for (X, role, partner), g in c.groupby(["X", "role", "partner"]):
        g = g.sort_values("line")
        if len(g) < 3:
            continue
        w = wmap[dg.name[X]]
        obs = g.obs.to_numpy()
        for pname, pri in (("B0", np.zeros(len(g))), ("B5", g.d_FT.to_numpy())):
            for i in range(len(g)):
                rest = np.arange(len(g)) != i
                T, a = obs[rest].mean(), pri[rest].mean()
                r1 = a + w * (obs[i] - pri[i])
                out[pname].append((X, T, a, r1))
    res = {}
    for pname, lst in out.items():
        a = pd.DataFrame(lst, columns=["X", "T", "R0", "R1"])
        res[pname] = dict(n=int(len(a)), R0=dec_metrics(a["T"].to_numpy(), a.R0.to_numpy()), R1=dec_metrics(a["T"].to_numpy(), a.R1.to_numpy()))
    return res


def main():
    out_path = HERE / "P0_RESULT.json"
    if out_path.exists() and not SMOKE:
        raise SystemExit("P0_RESULT.json exists (write-once)")
    census = json.loads((AS / "CENSUS.json").read_text(encoding="utf-8"))
    df = R.halves(D.full("original"))
    res = dict(protocol="PROTOCOL.md", n_boot=N_BOOT, n_perm=N_PERM)
    tS = cells(df, "SYNERGY_DELTA_AUC")
    refS = Ref(tS)
    dg = Drugs(census, tS)
    dg.primary = {i: (census["drugs"][i]["target"].split(",")[0].strip().upper() if isinstance(census["drugs"][i]["target"], str) else "")
                  for i in dg.ids}
    ids = [i for i in dg.ids if "|" not in dg.name[i]]
    fam = families(dg, ids)
    present = tS.groupby("role").drug.agg(set).to_dict()
    impl = sorted({x for role, S in present.items() for x in S if dg.siblings(x, role, S)})
    if SMOKE:
        impl = impl[:6]
    resS, rowsS, cellS, uS = p0a("SYNERGY_DELTA_AUC", tS, refS, dg, impl, ids, fam)
    if resS["b5_reproduction"]["max_abs_diff"] > 1e-9 and not SMOKE:
        raise SystemExit(f"B5 reproduction failed: {resS['b5_reproduction']}")
    res["P0A_S"] = resS
    tE = cells(df, "SYNERGY_OBS_AUC")
    refE = Ref(tE)
    dgE = Drugs(census, tE)
    dgE.primary = dg.primary
    resE, rowsE, cellE, uE = p0a("SYNERGY_OBS_AUC", tE, refE, dgE, impl, ids, fam)
    res["P0A_E"] = resE
    resB, dB = p0b(uS, rowsS, dg, fam)
    res["P0B_S"] = resB
    cs = choice_sets(tE, refE, dgE, fam, ids)
    resC, SC = p0c(df, cs, dgE)
    resC["reproducible"] = reproducible_opportunity(df, dgE, fam, ids)
    ro = resC["reproducible"].get("reproducible_opportunity", 0.0)
    g3 = ("PASS" if ro >= MIN_GAIN and resC["gain_over_random"]["FT"] >= MIN_GAIN and resC["gain_ci_family"]["FT"][0] > 0
          and resC["FT_minus_F"]["ci_family"][0] > 0 else "FAIL")
    resC["gate3"] = g3
    res["P0C"] = resC
    res["feedback_vs_B5"] = feedback(cellS, dg)
    gates = [resS["gate1"], resB["gate2"], g3]
    if all(g == "PASS" for g in gates):
        dec = "GO"
    elif any(g == "PASS" for g in gates):
        dec = "NARROW"
    elif "UNDERPOWERED" in gates[:2]:
        dec = "UNDERPOWERED"
    else:
        dec = "STOP"
    res["decision"] = dict(gates=dict(gate1=gates[0], gate2=gates[1], gate3=gates[2]), label=dec)
    if SMOKE:
        print("smoke ok", resS["n_units"], resS["b5_reproduction"], resB["n_units"], resC["n_sets"])
        return
    uS.to_csv(HERE / "p0_units_S.csv", index=False, lineterminator="\n")
    dB.to_csv(HERE / "p0b_units.csv", index=False, lineterminator="\n")
    SC.to_csv(HERE / "p0c_sets.csv", index=False, lineterminator="\n")
    out_path.write_text(json.dumps(res, indent=1, default=float), encoding="utf-8", newline="\n")
    print(json.dumps(res["decision"], indent=1))


if __name__ == "__main__":
    main()
