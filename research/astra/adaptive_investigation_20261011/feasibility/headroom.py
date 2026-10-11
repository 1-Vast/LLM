"""Feasibility F1 (exploratory, open drugs only, no model calls): does adaptive evidence acquisition have headroom?

Units:
* killers among the 982 open block-N drugs (reference + development roles);
* novel-class regime: same-class drugs leave the pool;
* actions are real recorded observations (``environment.py``).

Policies, each scored at budgets 2, 4, 8 and 16:
* ``fixed_L``, ``fixed_V``, ``fixed_LV``: L1000 options in a learned order, viability lines from a
  fixed discriminative panel, or half of each.
  * Orders, panel, tau and sigma are learned on reference-role queries only.
  * Scored on development-role killers, and on all open killers for context.
* ``random``: uniform random affordable actions (seeded).
* ``adaptive``: greedy expected reduction of posterior predictive variance on test lines per
  unit cost.
  * Viability lines: Gaussian preposterior.
  * L1000 options: library-sampled preposterior, 32 pseudo-outcomes.
* ``adaptive_V``: the same planner restricted to viability (no transcriptional evidence).

Bounds:
* ``full_info``: all options plus all discovery lines.
* ``oracle5``: the 5 pool drugs best correlated with the truth on test lines; not achievable.

Output: feasibility/headroom.json and headroom_rows.csv.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import environment as EN  # noqa: E402

sys.path.insert(0, str(EN.BLOCK_N))
import predictors as PR  # noqa: E402

sys.path.insert(0, str(EN.BLOCK_N.parent / "mechanism_falsification_20261010"))
import intervals as IV  # noqa: E402

BUDGETS = (2, 4, 8, 16)
SEED = 20261011
M_SAMPLES = 32


def killers(lib):
    return [i for i in range(len(lib.P)) if np.nanmean(lib.P[i] < -1) >= 0.05]


def menu(lib, i):
    opts = [int(o) for o in np.where(lib.have[i])[0]]
    lines = [int(l) for l in lib.disc if np.isfinite(lib.P[i, l])]
    return opts, lines


def adaptive_step(post: EN.Posterior, opts_left, lines_left, use_l1000=True, use_viab=True, m_samples=12):
    """Greedy expected reduction of the selective test-line posterior variance per unit cost."""
    lib = post.lib
    w = post.weights()
    Qb = post.test_projector()
    best, gain_best = None, -np.inf
    if use_viab and lines_left:
        c = np.array(lines_left)
        _, Ft = post.factors(w, lib.test)
        Ftp = post._project(Ft.T, Qb)                      # (n_test, k)
        _, Fc = post.factors(w, c)                         # (k, n_c)
        Ktc = Ftp @ Fc
        vc = (Fc ** 2).sum(axis=0)
        if post.lines:
            S, yS, muS, FS, A = post._solve_parts(w)
            KtS, KcS = Ftp @ FS, Fc.T @ FS
            Ktc = Ktc - KtS @ np.linalg.solve(A, KcS.T)
            vc = vc - np.sum(KcS * np.linalg.solve(A, KcS.T).T, axis=1)
        g = (Ktc ** 2).sum(axis=0) / (vc + post.sigma ** 2)
        k = int(np.argmax(g))
        best, gain_best = ("viability", int(c[k])), float(g[k])
    if use_l1000 and opts_left:
        top = np.argsort(-w)[:m_samples]
        pw = w[top] / w[top].sum()
        k_now = len(post.options)
        s_old = post.l1000_sim()
        base = post.test_trace(w, Qb)
        for o in opts_left:
            Xo, no = lib.X[post.pool, o], lib.norm[post.pool, o]
            hv = lib.have[post.pool, o] & (no > 0)
            S = (Xo @ Xo[top].T) / np.maximum(np.outer(no, no[top]), 1e-12)   # (J, m)
            S = np.where(hv[:, None] & hv[top][None], S, np.nan)
            fill = np.nanmin(S) if np.isfinite(S).any() else 0.0
            S = np.where(np.isfinite(S), S, fill)
            exp_tr = 0.0
            for m in range(len(top)):
                s_new = (k_now * s_old + S[:, m]) / (k_now + 1)
                exp_tr += pw[m] * post.test_trace(post.weights(s_new), Qb)
            g = base - exp_tr
            if g > gain_best:
                best, gain_best = ("l1000", int(o)), g
    return best


def run_policy(lib, i, policy, cfg, rng):
    pool = lib.pool(i)
    post = EN.Posterior(lib, i, pool, tau_l=cfg["tau_l"], sigma=cfg["sigma"], alpha=cfg["alpha"])
    opts, lines = menu(lib, i)
    out = {}
    spent = 0
    plan = None
    if policy.startswith("fixed"):
        o_order = [o for o in cfg["option_order"] if o in opts]
        l_order = [l for l in cfg["panel"] if l in lines]
        if policy == "fixed_L":
            plan = [("l1000", o) for o in o_order] + [("viability", l) for l in l_order]
        elif policy == "fixed_V":
            plan = [("viability", l) for l in l_order]
        else:  # alternate, starting with L1000
            plan = []
            for k in range(max(len(o_order), len(l_order))):
                if k < len(o_order):
                    plan.append(("l1000", o_order[k]))
                if k < len(l_order):
                    plan.append(("viability", l_order[k]))
    for step in range(1, max(BUDGETS) + 1):
        if policy == "random":
            acts = [("l1000", o) for o in opts if o not in post.options] + \
                   [("viability", l) for l in lines if l not in post.lines]
            a = acts[rng.integers(len(acts))] if acts else None
        elif plan is not None:
            a = plan[step - 1] if step - 1 < len(plan) else None
        else:
            a = adaptive_step(post, [o for o in opts if o not in post.options], [l for l in lines if l not in post.lines],
                              use_l1000=(policy == "adaptive"), use_viab=True)
        if a is not None:
            if a[0] == "l1000":
                post.options.append(a[1])
            else:
                post.lines[a[1]] = float(lib.P[i, a[1]])
            spent += 1
        if step in BUDGETS:
            s = EN.score(lib, i, post.predict())
            s["n_l1000"] = len(post.options)
            out[step] = s
    return out


def cfg_opts(lib, i):
    return [int(o) for o in np.where(lib.have[i])[0]]


def learn_config(lib, train):
    """Option order, discriminative panel, tau and sigma from reference-role queries only."""
    # discriminative panel: discovery lines with the largest variance of reference selective profiles
    R = np.stack([PR.residual(lib.P[j], lib.G) for j in train])
    v = np.nanvar(R[:, lib.disc], axis=0)
    panel = [int(l) for l in lib.disc[np.argsort(-v)]]
    best = None
    for tau in (0.02, 0.05, 0.1):
        rs = []
        for i in train[:150]:
            post = EN.Posterior(lib, i, lib.pool(i), tau_l=tau)
            post.options = [int(o) for o in np.where(lib.have[i])[0]]
            rs.append(EN.score(lib, i, post.predict())["r"])
        m = float(np.mean(rs))
        if best is None or m > best[1]:
            best = (tau, m)
    tau = best[0]
    gains = np.zeros(lib.have.shape[1])
    counts = np.zeros(lib.have.shape[1])
    for i in train[:150]:
        for o in np.where(lib.have[i])[0]:
            post = EN.Posterior(lib, i, lib.pool(i), tau_l=tau)
            post.options = [int(o)]
            gains[o] += EN.score(lib, i, post.predict())["r"]
            counts[o] += 1
    order = [int(o) for o in np.argsort(-(gains / np.maximum(counts, 1)))]
    best_s = None
    for sigma in (0.3, 0.5, 0.8):
        for alpha in (0.05, 0.2, 0.5):
            rs = []
            for i in train[:100]:
                for n_lines in (8, 32):
                    post = EN.Posterior(lib, i, lib.pool(i), tau_l=tau, sigma=sigma, alpha=alpha)
                    post.options = [int(o) for o in cfg_opts(lib, i)[:2]]
                    for l in panel[:n_lines]:
                        if np.isfinite(lib.P[i, l]):
                            post.lines[l] = float(lib.P[i, l])
                    rs.append(EN.score(lib, i, post.predict())["r"])
            m = float(np.mean(rs))
            if best_s is None or m > best_s[2]:
                best_s = (sigma, alpha, m)
    return {"tau_l": tau, "sigma": best_s[0], "alpha": best_s[1], "option_order": order, "panel": panel[:64],
            "option_mean_r": (gains / np.maximum(counts, 1)).round(4).tolist(), "tau_fit_r": best[1], "sigma_alpha_fit_r": best_s[2]}


def bounds(lib, i, cfg):
    pool = lib.pool(i)
    post = EN.Posterior(lib, i, pool, tau_l=cfg["tau_l"], sigma=cfg["sigma"], alpha=cfg["alpha"])
    opts, lines = menu(lib, i)
    post.options = opts
    s_vc = EN.score(lib, i, post.predict())
    post.lines = {l: float(lib.P[i, l]) for l in lines}
    s_full = EN.score(lib, i, post.predict())
    y = PR.residual(lib.P[i], lib.G)
    t = lib.test[np.isfinite(y[lib.test])]
    R = np.stack([PR.residual(lib.P[j], lib.G) for j in pool])
    rr = np.array([PR.pearson(R[k, t], y[t], 30) for k in range(len(pool))])
    top = pool[np.argsort(-np.nan_to_num(rr, nan=-1))[:5]]
    s_or = EN.score(lib, i, np.nanmean(lib.P[top], axis=0))
    return {"vc_all_options": s_vc, "full_info": s_full, "oracle5": s_or}


def main(max_units=None):
    t0 = time.time()
    lib = EN.Library.open()
    K = killers(lib)
    role = lib.world.role
    train = [i for i in range(len(lib.P)) if role[i] == "reference"]
    cfg = learn_config(lib, train)
    units = [i for i in K][:max_units]
    rng = np.random.default_rng(SEED)
    rows = []
    for n, i in enumerate(units):
        row = {"drug": lib.world.drug[i], "moa": lib.world.moa[i], "role": role[i]}
        for pol in ("fixed_L", "fixed_V", "fixed_LV", "random", "adaptive", "adaptive_V"):
            res = run_policy(lib, i, pol, cfg, rng)
            for b, s in res.items():
                row[f"{pol}@{b}:r"] = s["r"]
                row[f"{pol}@{b}:p10"] = s["p10"]
                row[f"{pol}@{b}:nL"] = s["n_l1000"]
        for k, s in bounds(lib, i, cfg).items():
            row[f"{k}:r"] = s["r"]
            row[f"{k}:p10"] = s["p10"]
        rows.append(row)
        if n % 20 == 0:
            print(n, len(units), round(time.time() - t0), flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(HERE / "feasibility" / "headroom_rows.csv", index=False)
    res = {"n_units": len(df), "n_dev_role": int((df.role == "development").sum()), "config": {k: v for k, v in cfg.items() if k != "panel"},
           "seconds": round(time.time() - t0, 1), "summary": {}}
    for scope, sub in (("development_role", df[df.role == "development"]), ("all_open_killers", df)):
        cl = sub["moa"].to_numpy()
        S = {}
        for c in sub.columns:
            if c.endswith(":r") or c.endswith(":p10"):
                est, lo, hi = IV.cluster_bootstrap(sub[c].to_numpy(float), cl, n_boot=1000, seed=SEED)
                S[c] = [round(est, 4), round(lo, 4), round(hi, 4)]
        for b in BUDGETS:
            for a, bb in (("adaptive", "fixed_L"), ("adaptive", "fixed_LV"), ("adaptive", "fixed_V"), ("adaptive", "random"),
                          ("adaptive", "adaptive_V")):
                for m in ("r", "p10"):
                    d = IV.paired_difference(sub[f"{a}@{b}:{m}"].to_numpy(float), sub[f"{bb}@{b}:{m}"].to_numpy(float), cl,
                                             n_boot=1000, seed=SEED)
                    S[f"{a}-{bb}@{b}:{m}"] = [round(d["mean_difference"], 4), round(d["ci95"][0], 4), round(d["ci95"][1], 4)]
        res["summary"][scope] = S
    (HERE / "feasibility" / "headroom.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    return res


if __name__ == "__main__":
    mx = int(sys.argv[1]) if len(sys.argv) > 1 else None
    r = main(mx)
    print(json.dumps(r["summary"]["development_role"], indent=0)[:3000])
