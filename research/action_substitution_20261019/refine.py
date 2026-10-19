"""Phase 3 (PROTOCOL_P3.md): counterexample refinement of substitution contrasts, partner-specific vs generic.

Writes REFINE_<endpoint>.json (write-once). Usage: python refine.py [SYNERGY_DELTA_AUC|SYNERGY_OBS_AUC] [--smoke]
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

import cas_data as D
import repro as R
from lofo import Drugs, Ref, cells

HERE = Path(__file__).resolve().parent
N_BOOT = 2000
EPS = 0.03
RNG = np.random.default_rng(20261019)


def sibling_swaps(ref, dg):
    rows = []
    for k, o in ref.by_key.items():
        role, partner, line = k.split("|", 2)
        ds = sorted(o)
        for i, s in enumerate(ds):
            for x in ds[i + 1:]:
                if dg.ts.get(s, frozenset()) & dg.ts.get(x, frozenset()):
                    rows.append((s, x, role, partner, ref.pdrug[k], line, o[x][0] - o[s][0], o[x][1] - o[s][1]))
    return pd.DataFrame(rows, columns=["s", "x", "role", "partner", "pdrug", "line", "d", "f1"])


def variance_parts(sw):
    g = sw.groupby(["s", "x", "role", "partner"]).d
    n = g.size()
    keep = n[n >= 2].index
    gg = sw.set_index(["s", "x", "role", "partner"]).loc[keep].groupby(level=[0, 1, 2, 3]).d
    sw2 = float((gg.var(ddof=1) * (gg.size() - 1)).sum() / (gg.size() - 1).sum())
    means = g.mean()
    tau2 = max(float(means.var()) - float(np.mean(sw2 / n)), 0.0)
    pm = sw.groupby(["s", "x", "role"]).d.agg(["mean", "size"])
    tauX2 = max(float(pm["mean"].var()) - float(np.mean((tau2 + sw2) / pm["size"])), 0.0)
    return tau2, sw2, tauX2


def fold(ref, dg, X, sw_all, t):
    sw = sw_all[(sw_all.s != X) & (sw_all.x != X) & (sw_all.pdrug != X)]
    beta = {}
    for role in ("L", "A"):
        s = sw[sw.role == role]
        beta[role] = float(np.polyfit(s.f1, s.d, 1)[0]) if len(s) > 20 else 0.0
    tau2, sw2, tauX2 = variance_parts(sw)
    units = defaultdict(list)
    for k, role, partner, line, y, m in zip(t.key, t.role, t.partner, t.line, t.y, t.m):
        o = ref.others(k, {X})
        sibs = dg.siblings(X, role, o)
        if not sibs:
            continue
        obs = y - np.mean([o[s][0] for s in sibs])
        p2 = float(np.mean([beta[role] * (m - o[s][1]) for s in sibs]))
        units[(role, partner)].append((line, obs, 0.0, p2))
    units = {u: sorted(v) for u, v in units.items()}
    return units, dict(beta=beta, tau2=tau2, sigma_w2=sw2, tauX2=tauX2)


def arms_for_x(units, par, prior_ix):
    """Per-unit MSE (averaged over probe lines) for R0-R3 and decision accuracy."""
    w = par["tau2"] / (par["tau2"] + par["sigma_w2"]) if par["tau2"] + par["sigma_w2"] > 0 else 0.0
    out = []
    by_role = defaultdict(list)
    for (role, p), v in units.items():
        by_role[role].append(((role, p), v))
    for role, lst in by_role.items():
        # residuals of every cell, and first-line probe residual, per unit (for R2 / R3)
        res_cells = {u: np.array([c[1] - c[prior_ix] for c in v]) for u, v in lst}
        first = {u: v[0][1] - v[0][prior_ix] for u, v in lst}
        for u, v in lst:
            if len(v) < 3:
                continue
            others = np.concatenate([res_cells[o] for o, _ in lst if o != u]) if len(lst) > 1 else np.array([])
            oth_first = np.array([first[o] for o, _ in lst if o != u])
            n_p = len(oth_first)
            wX = par["tauX2"] / (par["tauX2"] + (par["tau2"] + par["sigma_w2"]) / n_p) if n_p and par["tauX2"] > 0 else 0.0
            obs = np.array([c[1] for c in v])
            pri = np.array([c[prior_ix] for c in v])
            acc = defaultdict(list)
            for i in range(len(v)):
                rest = np.arange(len(v)) != i
                T = obs[rest].mean()
                a = pri[rest].mean()
                r1 = a + w * (obs[i] - pri[i])
                acc["R0"].append((a - T) ** 2)
                acc["R1"].append((r1 - T) ** 2)
                if len(others):
                    acc["R2"].append((a - T) ** 2 + 2 * w * (a - T) * others.mean() + w ** 2 * np.mean(others ** 2))
                    acc["R3"].append((a + wX * oth_first.mean() - T) ** 2)
                fail = abs(T) > EPS
                acc["dec_R0"].append(float((abs(a) > EPS) == fail))
                acc["dec_R1"].append(float((abs(r1) > EPS) == fail))
                acc["flip_good"].append(float(((abs(r1) > EPS) != (abs(a) > EPS)) and ((abs(r1) > EPS) == fail)))
                acc["flip_bad"].append(float(((abs(r1) > EPS) != (abs(a) > EPS)) and ((abs(r1) > EPS) != fail)))
            if "R2" not in acc:
                continue
            out.append(dict(role=role, partner=u[1], n_lines=len(v), **{k: float(np.mean(x)) for k, x in acc.items()}))
    return out, w


def design_for_x(units, par, prior_ix, rng):
    """Budgeted probing: ambiguity designer vs random; decision accuracy over all of X's units (fixed probe line l0)."""
    w = par["tau2"] / (par["tau2"] + par["sigma_w2"]) if par["tau2"] + par["sigma_w2"] > 0 else 0.0
    U = [(u, v) for u, v in units.items() if len(v) >= 2]
    if len(U) < 2:
        return None
    rows = []
    for u, v in U:
        obs = np.array([c[1] for c in v])
        pri = np.array([c[prior_ix] for c in v])
        T, a = obs[1:].mean(), pri[1:].mean()
        rows.append((abs(T) > EPS, a, a + w * (obs[0] - pri[0])))
    fail = np.array([r[0] for r in rows])
    a = np.array([r[1] for r in rows])
    r1 = np.array([r[2] for r in rows])
    K = max(1, int(round(0.25 * len(U))))
    sd = np.sqrt(par["tau2"]) if par["tau2"] > 0 else 1e-3

    def acc(sel):
        pred = np.where(sel, r1, a)
        return float(np.mean((np.abs(pred) > EPS) == fail))
    amb = np.argsort(np.abs(np.abs(a) - EPS) / sd)[:K]
    sel = np.zeros(len(U), bool)
    sel[amb] = True
    rnd = []
    for _ in range(200):
        s = np.zeros(len(U), bool)
        s[rng.choice(len(U), K, replace=False)] = True
        rnd.append(acc(s))
    return dict(n_units=len(U), K=K, none=acc(np.zeros(len(U), bool)), ambiguity=acc(sel), random=float(np.mean(rnd)),
                all=acc(np.ones(len(U), bool)))


def summarise(per_unit):
    u = pd.DataFrame(per_unit)
    arms = ["R0", "R1", "R2", "R3"]
    point = {a: float(u[a].mean()) for a in arms}
    groups = {x: g for x, g in u.groupby("X")}
    names = list(groups)
    bs = defaultdict(list)
    for _ in range(N_BOOT):
        g = pd.concat([groups[names[i]] for i in RNG.choice(len(names), len(names))], ignore_index=True)
        m = {a: g[a].mean() for a in arms}
        bs["C1"].append(m["R0"] - m["R1"])
        bs["C2"].append(m["R2"] - m["R1"])
        bs["C3"].append(m["R3"] - m["R1"])
        bs["dec_gain"].append(g.dec_R1.mean() - g.dec_R0.mean())
    ci = {k: [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))] for k, v in bs.items()}
    if ci["C1"][0] > 0 and ci["C2"][0] > 0 and ci["C3"][0] > 0:
        label = "PARTNER_SPECIFIC_REFINEMENT"
    elif ci["C1"][0] > 0:
        label = "GENERIC_REFINEMENT_ONLY"
    else:
        label = "NO_REFINEMENT_VALUE"
    return dict(n_units=int(len(u)), n_impl=len(names), mse=point, ci=ci, label=label,
                decision=dict(acc_R0=float(u.dec_R0.mean()), acc_R1=float(u.dec_R1.mean()),
                              flip_good=float(u.flip_good.mean()), flip_bad=float(u.flip_bad.mean())))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    ep = args[0] if args else "SYNERGY_DELTA_AUC"
    out_path = HERE / f"REFINE_{ep}.json"
    if out_path.exists():
        raise SystemExit(f"{out_path.name} exists (write-once)")
    census = json.loads((HERE / "CENSUS.json").read_text(encoding="utf-8"))
    df = R.halves(D.full("original"))
    t = cells(df, ep)
    ref = Ref(t)
    dg = Drugs(census, t)
    present = t.groupby("role").drug.agg(set).to_dict()
    impl = sorted({x for role, S in present.items() for x in S if dg.siblings(x, role, S)})
    sw_all = sibling_swaps(ref, dg)
    res = dict(endpoint=ep, protocol="PROTOCOL_P3.md", eps=EPS, n_boot=N_BOOT, folds={})
    for prior_name, ix in (("B0", 2), ("B2", 3)):
        per_unit, designs = [], []
        rng = np.random.default_rng(7)
        for X in (impl[:3] if "--smoke" in sys.argv else impl):
            units, par = fold(ref, dg, X, sw_all, t[t.drug == X])
            pu, w = arms_for_x(units, par, ix)
            per_unit += [dict(X=dg.name[X], **r) for r in pu]
            dz = design_for_x(units, par, ix, rng)
            if dz:
                designs.append(dict(X=dg.name[X], **dz))
            if prior_name == "B0":
                res["folds"][dg.name[X]] = dict(units=len(units), units_ge3=len(pu), w=w, **par)
        if "--smoke" in sys.argv:
            ok = all(np.isfinite(v) for r in per_unit for k, v in r.items() if isinstance(v, float))
            print("smoke", prior_name, len(per_unit), len(designs), "finite" if ok else "NONFINITE")
            continue
        s = summarise(per_unit) if len({r['X'] for r in per_unit}) >= 3 else dict(n_units=len(per_unit))
        dz = pd.DataFrame(designs)
        if len(dz):
            wts = dz.n_units / dz.n_units.sum()
            s["design"] = dict(n_impl=int(len(dz)), n_units=int(dz.n_units.sum()),
                               **{k: float((dz[k] * wts).sum()) for k in ("none", "random", "ambiguity", "all")})
        res[f"prior_{prior_name}"] = s
    if "--smoke" in sys.argv:
        return
    out_path.write_text(json.dumps(res, indent=1, default=float), encoding="utf-8", newline="\n")
    for k in ("prior_B0", "prior_B2"):
        r = res[k]
        print(k, r.get("label"), r.get("n_units"), r.get("n_impl"), {a: round(v, 6) for a, v in r.get("mse", {}).items()})
        print("   ci", r.get("ci"))
        print("   decision", r.get("decision"), "design", r.get("design"))


if __name__ == "__main__":
    main()
