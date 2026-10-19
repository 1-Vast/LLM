"""Kinobeads substitution test (PROTOCOL.md): does Klaeger 2017 binding similarity predict same-annotation substitution
on the Jaaks 2022 interaction endpoint (SYNERGY_DELTA_AUC)?

Reuses the frozen action-substitution phase-2 code (lofo.py, imported, never modified) for cells, reference tables,
drug annotations, implementations and partner-level units. Writes KB_RESULT.json and kb_units.csv (write-once).
Usage: python kb_run.py [--smoke]
  --smoke  execution check only: builds the binding matrix and runs the B0/B5 reproduction gate; prints no metric
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
AS = ROOT / "research/action_substitution_20261019"
KL = ROOT / "data/external/klaeger2017_chembl"
sys.path.insert(0, str(AS))
import cas_data as D  # noqa: E402
import lofo as L  # noqa: E402
import repro as R  # noqa: E402

EP = "SYNERGY_DELTA_AUC"
EPS = 0.03
N_BOOT = 2000
TAU = 0.2           # B5 kernel width (lofo.predict_fold), not re-tuned
JAC_W = 2.0         # B5 annotation factor (lofo.predict_fold), not re-tuned
MIN_COMMON = 30     # minimum shared Klaeger targets for a binding correlation
MIN_IMPL = 10       # minimum mapped evaluable implementations for a primary test
OUT = HERE / "KB_RESULT.json"


# ---------------------------------------------------------------- binding profiles
def binding_matrix():
    """Drug x target pKd (median over records); censored '>' records are set to the censoring value."""
    k = pd.read_csv(KL / "klaeger2017_CHEMBL3991601_kd.csv", low_memory=False)
    k = k[(k.standard_type == "Kd") & (k.standard_units == "nM") & k.standard_value.notna() & (k.standard_value > 0)]
    k = k[k.data_validity_comment.isna()]
    k["pkd"] = 9 - np.log10(k.standard_value.astype(float))
    return k.groupby(["molecule_chembl_id", "target_chembl_id"]).pkd.median().unstack("target_chembl_id")


def binding_corr(bm, mapping):
    """{(jaaks_id_a, jaaks_id_b): Pearson r of pKd over shared targets} for mapped drugs."""
    ids = {did: v["chembl"] for did, v in mapping.items() if v["chembl"] in bm.index}
    sub = bm.loc[list(ids.values())]
    c = sub.T.corr(min_periods=MIN_COMMON)
    out = {}
    for a, ma in ids.items():
        for b, mb in ids.items():
            v = c.at[ma, mb]
            out[(a, b)] = float(v) if np.isfinite(v) else np.nan
    return out, ids


# ---------------------------------------------------------------- predictions
def kernel(o, sims, jac):
    w = np.array([np.exp(-(1 - (s if np.isfinite(s) else 0.0)) / TAU) * (1 + JAC_W * j) for s, j in zip(sims, jac)])
    return float(np.dot(w, [v[0] for v in o.values()]) / w.sum())


def predict(ref, dg, X, test, ckb):
    """Cell-level B0, B5 (exact lofo formula), K (kinobeads kernel), Khyb, plus sibling similarities."""
    excl = {X}
    out = []
    for k, role, line, partner, y in zip(test.key, test.role, test.line, test.partner, test.y):
        o = ref.others(k, excl)
        if not o:
            continue
        sibs = dg.siblings(X, role, o)
        if not sibs:
            continue
        ref_s = float(np.mean([o[s][0] for s in sibs]))
        ds = list(o)
        jac = [dg.jac(X, d) for d in ds]
        cf = [dg.c(role, X, d) for d in ds]
        cb = [ckb.get((X, d), np.nan) for d in ds]
        hyb = [b if np.isfinite(b) else f for b, f in zip(cb, cf)]
        p = dict(B0=ref_s, B5=kernel(o, cf, jac), K=kernel(o, cb, jac), Khyb=kernel(o, hyb, jac))
        skb = [ckb.get((X, s), np.nan) for s in sibs]
        skb = [v for v in skb if np.isfinite(v)]
        sf = [dg.c(role, X, s) for s in sibs]
        sf = [v for v in sf if np.isfinite(v)]
        out.append(dict(X=X, role=role, partner=partner, line=line, y=y, ref=ref_s, **p,
                        sim_kb=float(np.mean(skb)) if skb else np.nan,
                        sim_func=float(np.mean(sf)) if sf else np.nan,
                        jac=float(np.mean([dg.jac(X, s) for s in sibs]))))
    return out


METHODS = ["B0", "B5", "K", "Khyb"]


def units(cellpred):
    c = pd.DataFrame(cellpred)
    c["obs"] = c.y - c.ref
    for m in METHODS:
        c["d_" + m] = c[m] - c.ref
    agg = {"obs": "mean", "line": "nunique", "sim_kb": "mean", "sim_func": "mean", "jac": "mean",
           **{"d_" + m: "mean" for m in METHODS}}
    return c.groupby(["X", "role", "partner"]).agg(agg).reset_index()


# ---------------------------------------------------------------- statistics
def auroc(score, y):
    return L.auroc(np.asarray(score, float), np.asarray(y, bool))


def mse(g, m):
    return float(np.mean((g["d_" + m] - g.obs) ** 2))


def stats(u):
    fail = (u.obs.abs() > EPS).to_numpy()
    s = {f"mse_{m}": mse(u, m) for m in METHODS}
    s["B5_minus_K"] = s["mse_B5"] - s["mse_K"]
    s["B0_minus_K"] = s["mse_B0"] - s["mse_K"]
    s["B5_minus_Khyb"] = s["mse_B5"] - s["mse_Khyb"]
    s["B0_minus_Khyb"] = s["mse_B0"] - s["mse_Khyb"]
    s["failure_rate"] = float(fail.mean())
    for name in ("sim_kb", "sim_func", "jac"):
        ok = u[name].notna().to_numpy()
        s[f"auroc_{name}"] = auroc(-u[name].to_numpy()[ok], fail[ok])
    ok = (u.sim_kb.notna() & u.sim_func.notna()).to_numpy()
    s["auroc_kb_minus_func_common"] = auroc(-u.sim_kb.to_numpy()[ok], fail[ok]) - auroc(-u.sim_func.to_numpy()[ok], fail[ok])
    ok = u.sim_kb.notna().to_numpy()
    s["auroc_kb_minus_jac_common"] = s["auroc_sim_kb"] - auroc(-u.jac.to_numpy()[ok], fail[ok])
    return s


def boot(u, rng):
    groups = {x: g for x, g in u.groupby("X")}
    names = list(groups)
    point = stats(u)
    draws = defaultdict(list)
    for _ in range(N_BOOT):
        g = pd.concat([groups[names[i]] for i in rng.choice(len(names), len(names))], ignore_index=True)
        for k, v in stats(g).items():
            draws[k].append(v)
    ci = {k: [float(np.nanpercentile(v, 2.5)), float(np.nanpercentile(v, 97.5))] for k, v in draws.items()}
    return dict(n_units=int(len(u)), n_impl=len(names), point=point, ci=ci)


def per_impl(u, dg):
    rows = {}
    for x, g in u.groupby("X"):
        rows[dg.name[x]] = dict(n_units=int(len(g)), failure_rate=float((g.obs.abs() > EPS).mean()),
                                sim_kb=float(g.sim_kb.mean()) if g.sim_kb.notna().any() else None,
                                sim_func=float(g.sim_func.mean()), jac=float(g.jac.mean()),
                                **{f"mse_{m}": mse(g, m) for m in METHODS})
    return rows


def spearman(a, b):
    a, b = pd.Series(a).rank(), pd.Series(b).rank()
    return float(np.corrcoef(a, b)[0, 1])


# ---------------------------------------------------------------- main
def main():
    smoke = "--smoke" in sys.argv
    if OUT.exists() and not smoke:
        raise SystemExit(f"{OUT.name} exists (write-once)")
    mapping = json.loads((HERE / "MAPPING.json").read_text(encoding="utf-8"))
    bm = binding_matrix()
    ckb, ids = binding_corr(bm, mapping["mapped"])
    census = json.loads((AS / "CENSUS.json").read_text(encoding="utf-8"))
    df = R.halves(D.full("original"))
    t = L.cells(df, EP)
    ref = L.Ref(t)
    dg = L.Drugs(census, t)
    present = t.groupby("role").drug.agg(set).to_dict()
    impl = sorted({x for role, S in present.items() for x in S if dg.siblings(x, role, S)})
    preds = []
    for X in impl:
        preds += predict(ref, dg, X, t[t.drug == X], ckb)
    u = units(preds)
    # reproduction gate: B0, B5 and obs must equal the frozen phase-2 unit table
    old = pd.read_csv(AS / f"lofo_units_{EP}.csv", dtype={"X": str})
    m = u.merge(old, on=["X", "role", "partner"], suffixes=("", "_old"), how="outer", indicator=True)
    gate = dict(n_new=int(len(u)), n_old=int(len(old)), unmatched=int((m["_merge"] != "both").sum()),
                max_abs_diff={c: float(np.nanmax(np.abs(m[c] - m[c + "_old"]))) for c in ("obs", "d_B0", "d_B5")})
    gate["pass"] = gate["unmatched"] == 0 and all(v < 1e-9 for v in gate["max_abs_diff"].values())
    n_pairs = sum(1 for (a, b), v in ckb.items() if a < b and np.isfinite(v))
    print("binding matrix", bm.shape, "mapped drugs with profile", len(ids), "finite pairs", n_pairs, flush=True)
    print("reproduction gate", json.dumps(gate), flush=True)
    if smoke:
        print("smoke: implementations", u.X.nunique(), "units", len(u), "finite K",
              bool(np.isfinite(u[["d_K", "d_Khyb"]].to_numpy()).all()))
        return
    if not gate["pass"]:
        raise SystemExit("reproduction gate failed; no metric computed")
    profiled = {a for (a, b), v in ckb.items() if a == b and np.isfinite(v)}
    mapped_names = set(mapping["evaluable_mapped"]) & {dg.name[a] for a in profiled}
    prim = u[u.X.map(dg.name).isin(mapped_names)].copy()
    res = dict(protocol="PROTOCOL.md", endpoint=EP, eps=EPS, n_boot=N_BOOT, tau=TAU, jac_w=JAC_W, min_common=MIN_COMMON,
               binding_matrix=dict(drugs=int(bm.shape[0]), targets=int(bm.shape[1]), mapped_with_profile=len(ids),
                                   finite_pairs=n_pairs),
               gate=gate, primary_implementations=sorted(mapped_names))
    if prim.X.nunique() < MIN_IMPL:
        res["verdict"] = "BLOCKED"
        res["reason"] = f"{prim.X.nunique()} mapped evaluable implementations < {MIN_IMPL}"
    else:
        rng = np.random.default_rng(20261019)
        res["primary"] = boot(prim, rng)
        res["secondary_all27"] = boot(u, rng)
        ci, pt = res["primary"]["ci"], res["primary"]["point"]
        t1 = ci["B5_minus_K"][0] > 0 and ci["B0_minus_K"][0] > 0
        t2 = ci["auroc_sim_kb"][0] > 0.5
        res["test1_prediction"] = dict(pass_=t1, B5_minus_K=[pt["B5_minus_K"], ci["B5_minus_K"]],
                                       B0_minus_K=[pt["B0_minus_K"], ci["B0_minus_K"]])
        res["test2_ranking"] = dict(pass_=t2, auroc_sim_kb=[pt["auroc_sim_kb"], ci["auroc_sim_kb"]])
        res["verdict"] = "SUPPORTED" if (t1 and t2) else "NOT_SUPPORTED"
        pi = per_impl(prim, dg)
        res["per_impl"] = pi
        xs = [v for v in pi.values() if v["sim_kb"] is not None]
        res["descriptive_impl_spearman_simkb_vs_failure"] = dict(n=len(xs), rho=spearman([v["sim_kb"] for v in xs],
                                                                                        [v["failure_rate"] for v in xs]))
        res["descriptive_sibling_binding"] = {
            dg.name[a]: {dg.name[b]: ckb.get((a, b)) for b in sorted(ids) if b != a and dg.ts.get(a, frozenset()) & dg.ts.get(b, frozenset())}
            for a in sorted(ids) if dg.name[a] in mapped_names}
    out = u.copy()
    out["name"] = out.X.map(dg.name)
    out.to_csv(HERE / "kb_units.csv", index=False, lineterminator="\n")
    OUT.write_text(json.dumps(res, indent=1, default=float), encoding="utf-8", newline="\n")
    show = {k: res[k] for k in ("verdict", "gate") if k in res}
    for k in ("test1_prediction", "test2_ranking", "descriptive_impl_spearman_simkb_vs_failure"):
        if k in res:
            show[k] = res[k]
    if "primary" in res:
        show["primary_point"] = res["primary"]["point"]
        show["primary_ci"] = res["primary"]["ci"]
        show["n"] = (res["primary"]["n_units"], res["primary"]["n_impl"])
    print(json.dumps(show, indent=1, default=float))


if __name__ == "__main__":
    main()
