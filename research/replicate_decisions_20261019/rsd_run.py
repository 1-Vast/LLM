"""RSD stage runner: search (headroom gate + small grid), selection (go/no-go), evaluation (read once).

Usage (from this folder, maestro environment):
  python -B rsd_run.py search        -> SEARCH.json (write-once; headroom gate + full procedure on the search block)
  python -B rsd_run.py selection     -> SELECTION.json (requires FREEZE.json; write-once)
  python -B rsd_run.py evaluation    -> EVALUATION.json (requires FREEZE.json and a GO in SELECTION.json; write-once)
Policies obtain reads only through Acquisition; only Evaluator holds truth reads T and the primary-screen run.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

import rsd_core as C
import rsd_data as D

HERE = Path(__file__).resolve().parent
N_BOOT = 4000
ESC_FRAC = 0.25
WELLS_PER_READ = 20          # one well per HTS002 pool plate per compound-dose-replicate


class Acquisition:
    """Query-side access to purchased reads. A is bought for every query; B only on request (counted)."""

    def __init__(self, A, B):
        self._A, self._B = A, B
        self.reads = 0

    def read_A(self):
        self.reads += len(self._A)
        return self._A.copy()

    def buy_B(self, idx):
        idx = np.asarray(idx, int)
        self.reads += len(idx)
        out = np.full_like(self._A, np.nan)
        out[idx] = self._B[idx]
        return out


def setup(blk, cache={}):
    if "arena" not in cache:
        t, lines, Tsim, audit, E = D.build_arena()
        A, B, T = D.load_reads(t, lines)
        P = D.load_primary(t, lines)
        cache["arena"] = (t, lines, Tsim, audit, E, A, B, T, P)
    t, lines, Tsim, audit, E, A, B, T, P = cache["arena"]
    purged = set(t.attrs["purged"][blk])
    ref = np.array([i for i in np.where(t.role == "reference")[0] if t.core[i] not in purged])
    q = np.where(t.role == blk)[0]
    pools = np.unique(lines.pool_id.astype(str), return_inverse=True)[1]
    return dict(t=t, lines=lines, Tsim=Tsim, E=E, A=A, B=B, T=T, P=P, ref=ref, q=q, pools=pools)


def build_vc(S, cfg, **over):
    kw = dict(q=cfg["q"], rho=cfg["rho"], tiers=True, use_prior=cfg.get("use_prior", True), noise_model="pool", geometry="replicate") | over
    return C.VirtualCell(S["Tsim"], S["ref"], S["t"].cluster.to_numpy()[S["ref"]], S["E"], S["A"], S["B"], S["T"], S["pools"], **kw)


def reliability(vc):
    s = vc.alpha * np.trace(vc.S0)
    return s / (s + vc.beta * np.trace(vc.N0))


def arms_single(S, cfg, acq_A, vc_cache=None):
    """All one-read arms (plus VC-only with zero reads). Returns dict arm -> score matrix (queries x lines)."""
    q, ref = S["q"], S["ref"]
    keep_ref = np.arange(len(ref))
    vc = build_vc(S, cfg)
    vc_alt = build_vc(S, cfg, use_prior=not cfg.get("use_prior", True))      # also the prior-flip ablation
    # baselines keep their own definitions whatever the inner choice: VC-only and fusion use the chemistry prior,
    # scalar shrinkage uses the reliability of the read around zero
    vc_chem, vc_zero = (vc, vc_alt) if cfg.get("use_prior", True) else (vc_alt, vc)
    tier = C.tier_of(acq_A)
    mu = vc.prior(q, keep_ref)
    mu_chem = vc_chem.prior(q, keep_ref)
    one = np.ones(len(q))
    out = {}
    out["raw"] = C.raw_score(acq_A, vc.g)
    out["vc_only"] = mu_chem
    out["shrink"] = C.scalar_shrink(acq_A, vc.g, reliability(vc_zero), tier)
    out["fusion"] = C.fusion(acq_A, vc.g, mu_chem, reliability(vc_chem), tier)
    sA_ref = C.selective(S["A"][ref], vc.g)
    out["pca"] = C.pca_denoise(acq_A, vc.g, sA_ref, cfg["q_pca"])
    m, v, n1 = vc.posterior(mu, acq_A, one, tier)
    out["rsd"] = m
    post = dict(mean=m, var=v, noise1=n1, vc=vc, mu=mu, tier=tier)
    abl = {}
    abl["rsd_priorflip"] = vc_alt
    abl["rsd_poolflip"] = build_vc(S, cfg, rho=(1.0 if cfg["rho"] == 0 else 0.0))
    abl["rsd_notier"] = build_vc(S, cfg, tiers=False)
    abl["rsd_totalgeom"] = build_vc(S, cfg, geometry="total")
    for name, v2 in abl.items():
        mu2 = v2.prior(q, keep_ref)
        out[name] = v2.posterior(mu2, acq_A, one, tier)[0]
    return out, post


def boot_weights(cluster, n_boot, seed):
    u, inv = np.unique(cluster, return_inverse=True)
    rng = np.random.default_rng(seed)
    W = rng.multinomial(len(u), np.full(len(u), 1 / len(u)), size=n_boot).astype(float)
    return W, inv


def d1_table(ev, scores, W, inv, truth="T"):
    res = {}
    per = {}
    for a, sc in scores.items():
        r = ev.d1(C.d1_choose(sc), truth)
        per[a] = r["util"]
        res[a] = dict(util=float(np.nanmean(r["util"])), hit=float(np.nanmean(r["hit"])), false_progression=float(np.nanmean(r["fp"])), unknown_pairs=int(r["unknown"]))
    return res, per


def boot_d1(per, a, b, W, inv):
    d = per[a] - per[b]
    ok = np.isfinite(d)
    num = np.zeros(W.shape[1]); den = np.zeros(W.shape[1])
    np.add.at(num, inv[ok], d[ok]); np.add.at(den, inv[ok], 1.0)
    bs = (W @ num) / np.maximum(W @ den, 1e-9)
    est = float(np.nansum(d) / ok.sum())
    return est, bs


def d2_contrib(ev, sc, inv, n_cl, truth="T"):
    di, li, u = ev.d2_pairs(C.d2_choose(sc), truth)
    ok = np.isfinite(u)
    num = np.zeros(n_cl); den = np.zeros(n_cl)
    np.add.at(num, inv[di[ok]], u[ok]); np.add.at(den, inv[di[ok]], 1.0)
    hit = np.zeros(n_cl); np.add.at(hit, inv[di[ok]], (u[ok] >= 1.0).astype(float))
    fp = np.zeros(n_cl); np.add.at(fp, inv[di[ok]], (u[ok] < 0).astype(float))
    return dict(num=num, den=den, hit=hit, fp=fp, unknown=int((~ok).sum()))


def d2_table(ev, scores, inv, n_cl, truth="T"):
    res, con = {}, {}
    for a, sc in scores.items():
        c = d2_contrib(ev, sc, inv, n_cl, truth)
        con[a] = c
        res[a] = dict(util=float(c["num"].sum() / c["den"].sum()), hit=float(c["hit"].sum() / c["den"].sum()),
                      false_progression=float(c["fp"].sum() / c["den"].sum()), unknown_pairs=c["unknown"])
    return res, con


def boot_d2(con, a, b, W):
    ua = (W @ con[a]["num"]) / (W @ con[a]["den"])
    ub = (W @ con[b]["num"]) / (W @ con[b]["den"])
    est = con[a]["num"].sum() / con[a]["den"].sum() - con[b]["num"].sum() / con[b]["den"].sum()
    return float(est), ua - ub


def summ(est, bs, delta=0.0):
    lo, hi = np.nanpercentile(bs, [2.5, 97.5])
    return dict(estimate=est, ci95=[float(lo), float(hi)], p_one_sided=float((np.sum(bs <= delta) + 1) / (len(bs) + 1)))


def escalation(S, cfg, post, acqB_fn, A, ev, inv, n_cl, seed):
    """D3: the agent buys B for ESC_FRAC of the block's compounds under several policies, then decides D2 on the posterior."""
    vc, mu, tier, mean, var = post["vc"], post["mu"], post["tier"], post["mean"], post["var"]
    n = len(mean)
    nb = int(round(ESC_FRAC * n))
    two = np.full(n, 2.0)
    # posterior variance after a second read (does not depend on the read value)
    _, var2, _ = vc.posterior(mu, A, two, tier)
    pol = {}
    rng = np.random.default_rng(seed)
    pol["random"] = rng.choice(n, nb, replace=False)
    inside = (mean <= np.sort(mean, axis=0)[C.K_DRUGS - 1][None, :])
    pol["exploit_first"] = np.argsort(-(inside.sum(1) + 1e-6 * -mean.min(1)))[:nb]
    pol["uncertainty"] = np.argsort(-(var - var2).sum(1))[:nb]
    pol["voi_kg"] = np.argsort(-C.kg_scores(mean, var, var2))[:nb]
    scores, reads = {"none": mean}, {"none": n}
    checks = {}
    for name, idx in pol.items():
        Bb = acqB_fn(idx)
        Y = A.copy()
        nr = np.ones(n)
        Y[idx] = np.nanmean(np.stack([A[idx], Bb[idx]]), 0)
        nr[idx] = 2.0
        m2, _, _ = vc.posterior(mu, Y, nr, tier)
        scores[name] = m2
        reads[name] = n + len(idx)
        # agent verification: posterior-predictive check of the purchased read B against the A-only posterior
        sB = C.selective(Bb[idx], vc.g)
        pv = var[idx] + post["noise1"][idx]
        z2 = (sB - mean[idx]) ** 2 / pv
        checks[name] = float(np.nanmean(z2))
    # conventional workflow: raw reads, exploit-first escalation on raw ranking
    raw = C.raw_score(A, vc.g)
    inside_r = (np.where(np.isfinite(raw), raw, np.inf) <= np.sort(np.where(np.isfinite(raw), raw, np.inf), axis=0)[C.K_DRUGS - 1][None, :])
    idx = np.argsort(-inside_r.sum(1))[:nb]
    Bb = acqB_fn(idx)
    Y = A.copy(); Y[idx] = np.nanmean(np.stack([A[idx], Bb[idx]]), 0)
    scores["raw_exploit_first"] = C.raw_score(Y, vc.g)
    reads["raw_exploit_first"] = n + nb
    res, con = d2_table(ev, scores, inv, n_cl)
    for k in res:
        res[k]["reads"] = int(reads[k]); res[k]["wells"] = int(reads[k] * WELLS_PER_READ)
    return res, con, checks


def calibration(post, ev, chosen_d2=None, level=0.8):
    """Coverage of central predictive intervals for the truth read T (signal posterior + one-read noise)."""
    sT = ev._sT
    m, pv = post["mean"], post["var"] + post["noise1"]
    z = norm_ppf(0.5 + level / 2)
    ok = np.isfinite(sT)
    cov_all = float(np.mean((np.abs(sT - m) <= z * np.sqrt(pv))[ok]))
    out = dict(level=level, coverage_all=cov_all, mean_z2_all=float(np.mean(((sT - m) ** 2 / pv)[ok])))
    if chosen_d2 is not None:
        k, L = chosen_d2.shape
        li = np.tile(np.arange(L), (k, 1))
        sel = (chosen_d2.ravel(), li.ravel())
        e, mm, vv = sT[sel], m[sel], pv[sel]
        ok2 = np.isfinite(e)
        out.update(coverage_selected=float(np.mean((np.abs(e - mm) <= z * np.sqrt(vv))[ok2])),
                   mean_pred_selected=float(np.mean(-mm[ok2])), mean_truth_selected=float(np.mean(-e[ok2])),
                   mean_z_selected=float(np.mean(((e - mm) / np.sqrt(vv))[ok2])))
    return out


def reselect_d2(ev, sa, sb, n_draw, seed):
    """Selection-variability bootstrap for D2: resample clusters, rebuild the pool (with duplicates), re-choose top-K per line."""
    rng = np.random.default_rng(seed)
    u, inv = np.unique(ev.cluster, return_inverse=True)
    members = [np.where(inv == k)[0] for k in range(len(u))]
    out = np.empty(n_draw)
    L = sa.shape[1]
    for b in range(n_draw):
        cl = rng.integers(0, len(u), len(u))
        idx = np.concatenate([members[c] for c in cl])
        vals = []
        for sc in (sa, sb):
            ch = C.d2_choose(sc[idx])
            v = ev._sT[idx[ch], np.tile(np.arange(L), (ch.shape[0], 1))]
            vals.append(np.nanmean(-v))
        out[b] = vals[0] - vals[1]
    return out


def fit_variability(S, cfg, A, ev, n_refit, seed, frac=0.8):
    """Training variability: refit the VC on 80% subsamples of reference clusters, drawn without replacement (duplicated
    references would fill the kNN neighbour sets of the prior); report rsd - raw with the primary D1/D2 metrics."""
    rng = np.random.default_rng(seed)
    ref0 = S["ref"].copy()
    cl = S["t"].cluster.to_numpy()[ref0]
    u = np.unique(cl)
    tier = C.tier_of(A)
    rows = []
    for b in range(n_refit):
        pick = rng.choice(u, int(round(frac * len(u))), replace=False)
        ref_b = ref0[np.isin(cl, pick)]
        vc = build_vc(dict(S, ref=ref_b), cfg)
        mu = vc.prior(S["q"], np.arange(len(ref_b)))
        m = vc.posterior(mu, A, np.ones(len(A)), tier)[0]
        raw = C.raw_score(A, vc.g)
        d1 = float(np.nanmean(ev.d1(C.d1_choose(m))["util"]) - np.nanmean(ev.d1(C.d1_choose(raw))["util"]))
        d2 = float(np.nanmean(ev.d2_pairs(C.d2_choose(m))[2]) - np.nanmean(ev.d2_pairs(C.d2_choose(raw))[2]))
        rows.append(dict(D1=d1, D2=d2))
    return dict(n_refit=n_refit, frac_clusters=frac, D1=[r["D1"] for r in rows], D2=[r["D2"] for r in rows],
                D1_sd=float(np.std([r["D1"] for r in rows])), D2_sd=float(np.std([r["D2"] for r in rows])))


def norm_ppf(p):
    from scipy.stats import norm
    return float(norm.ppf(p))


def run_block(blk, cfg=None, n_boot=N_BOOT, seed=20261019, do_escalation=True, do_primary=True, do_sensitivity=False):
    """cfg=None: the configuration is chosen by reference-internal replicate-split selection (no query outcome used)."""
    t0 = time.time()
    S = setup(blk)
    q = S["q"]
    inner = None
    if cfg is None:
        cfg, inner = C.inner_select(S["Tsim"], S["ref"], S["t"].cluster.to_numpy()[S["ref"]], S["E"], S["A"], S["B"], S["T"],
                                    S["pools"], GRID, PCA_GRID)
    acq = Acquisition(S["A"][q], S["B"][q])
    A = acq.read_A()
    vc0 = build_vc(S, cfg)
    ev = C.Evaluator(S["T"][q], S["P"][q], vc0.g, S["t"].cluster.to_numpy()[q])
    W, inv = boot_weights(ev.cluster, n_boot, seed)
    n_cl = W.shape[1]
    scores, post = arms_single(S, cfg, A)
    # two-read references (double read cost); B purchased for every query through the interface
    acq2 = Acquisition(S["A"][q], S["B"][q])
    B_all = acq2.buy_B(np.arange(len(q)))
    Y2 = np.nanmean(np.stack([A, B_all]), 0)
    scores["raw2"] = C.raw_score(Y2, vc0.g)
    scores["rsd2"] = post["vc"].posterior(post["mu"], Y2, np.full(len(q), 2.0), post["tier"])[0]
    out = dict(block=blk, n_queries=int(len(q)), n_reference=int(len(S["ref"])), n_clusters=int(n_cl),
               tier_counts_reference=post["vc"].tier_counts.tolist(), alpha=post["vc"].alpha.tolist(), beta=post["vc"].beta.tolist(),
               reliability_by_tier=reliability(post["vc"]).tolist(), cfg=cfg, inner_selection=inner)
    for truth in (["T", "P"] if do_primary else ["T"]):
        r1, per1 = d1_table(ev, scores, W, inv, truth)
        r2, con2 = d2_table(ev, scores, inv, n_cl, truth)
        con_d = {}
        pairs = [("rsd", "raw"), ("raw2", "raw"), ("rsd", "fusion"), ("rsd", "pca"), ("rsd", "shrink"), ("rsd", "vc_only"),
                 ("rsd", "rsd_priorflip"), ("rsd", "rsd_poolflip"), ("rsd", "rsd_notier"), ("rsd", "rsd_totalgeom"),
                 ("rsd", "raw2"), ("rsd2", "raw2"), ("fusion", "raw"), ("pca", "raw")]
        for a, b in pairs:
            e1, b1 = boot_d1(per1, a, b, W, inv)
            e2, b2 = boot_d2(con2, a, b, W)
            con_d[f"{a}-{b}"] = dict(D1=summ(e1, b1), D2=summ(e2, b2))
        # halfway contrast: rsd - 0.5*raw2 - 0.5*raw
        e1a, b1a = boot_d1(per1, "rsd", "raw", W, inv); e1b, b1b = boot_d1(per1, "raw2", "raw", W, inv)
        e2a, b2a = boot_d2(con2, "rsd", "raw", W); e2b, b2b = boot_d2(con2, "raw2", "raw", W)
        con_d["halfway"] = dict(D1=summ(e1a - 0.5 * e1b, b1a - 0.5 * b1b), D2=summ(e2a - 0.5 * e2b, b2a - 0.5 * b2b))
        # identity tiers (descriptive): strict = component-isolated non-giant queries, purged = edge-purged giant queries
        giant = S["t"].giant.to_numpy()[q]
        tiers_d1 = {}
        for name, msk in (("strict", ~giant), ("purged", giant)):
            per_t = {k: np.where(msk, v, np.nan) for k, v in per1.items()}
            e, bs = boot_d1(per_t, "rsd", "raw", W, inv)
            tiers_d1[name] = dict(n_queries=int(msk.sum()), rsd_minus_raw=summ(e, bs))
        con_d["identity_tier_D1"] = tiers_d1
        out[f"truth_{truth}"] = dict(D1=r1, D2=r2, contrasts=con_d)
    out["calibration"] = calibration(post, ev, C.d2_choose(post["mean"]))
    opt = {}
    L = len(S["lines"])
    for a in ("raw", "shrink", "fusion", "pca", "rsd", "raw2", "rsd2"):
        ch = C.d2_choose(scores[a])
        li = np.tile(np.arange(L), (ch.shape[0], 1))
        claimed, truth = -scores[a][ch, li], -ev._sT[ch, li]
        ok = np.isfinite(truth) & np.isfinite(claimed)
        opt[a] = dict(claimed=float(claimed[ok].mean()), observed=float(truth[ok].mean()), optimism=float((claimed[ok] - truth[ok]).mean()))
    out["selected_optimism_D2"] = opt
    if do_escalation:
        acq3 = Acquisition(S["A"][q], S["B"][q])
        res3, con3, checks = escalation(S, cfg, post, acq3.buy_B, A, ev, inv, n_cl, seed + 1)
        c3 = {}
        for a, b in [("voi_kg", "exploit_first"), ("voi_kg", "random"), ("voi_kg", "none"), ("exploit_first", "none"),
                     ("uncertainty", "exploit_first"), ("exploit_first", "raw_exploit_first"), ("voi_kg", "raw_exploit_first")]:
            e, bs = boot_d2(con3, a, b, W)
            c3[f"{a}-{b}"] = summ(e, bs)
        out["D3"] = dict(arms=res3, contrasts=c3, posterior_predictive_mean_z2=checks)
    if do_sensitivity:
        rb = reselect_d2(ev, scores["rsd"], scores["raw"], 1000, seed + 2)
        lo, hi = np.percentile(rb, [2.5, 97.5])
        out["sensitivity"] = dict(reselection_D2_rsd_minus_raw=dict(mean=float(rb.mean()), ci95=[float(lo), float(hi)], n_draw=1000),
                                  fit_variability=fit_variability(S, cfg, A, ev, 10, seed + 3))
    out["reads_one_read_arms"] = int(len(q)); out["wells_per_read"] = WELLS_PER_READ
    out["seconds"] = round(time.time() - t0, 1)
    return out


GRID = [dict(q=qq, rho=r, use_prior=u) for qq in (0, 1, 2, 3, 5, 10) for r in (0.0, 1.0) for u in (True, False)]
PCA_GRID = (2, 5, 10, 20, 40, 80)


def write_once(path, obj):
    if path.exists():
        raise SystemExit(f"refusing to overwrite {path.name}")
    path.write_text(json.dumps(obj, indent=1, default=float), encoding="utf-8", newline="\n")


def stage_search():
    """Headroom gate (value of a second replicate read) and one run of the complete procedure on the search block."""
    path = HERE / "SEARCH.json"
    if path.exists():
        raise SystemExit("SEARCH.json exists (write-once)")
    r = run_block("search", None, do_escalation=True, do_primary=True)
    head = r["truth_T"]["contrasts"]["raw2-raw"]
    gate = any(head[d]["ci95"][0] > 0 for d in ("D1", "D2"))
    res = dict(headroom=head, headroom_gate_pass=bool(gate), practical_threshold={d: 0.5 * head[d]["estimate"] for d in ("D1", "D2")},
               run=r, decision="CONTINUE_TO_FREEZE" if gate else "STOP_NO_REPLICATE_HEADROOM")
    write_once(path, res)


def stage_search2():
    """Final procedure (extended inner grid) on the search block; SEARCH.json (first pass) is kept unchanged."""
    path = HERE / "SEARCH_v2.json"
    if path.exists():
        raise SystemExit("SEARCH_v2.json exists (write-once)")
    write_once(path, run_block("search", None, do_escalation=True, do_primary=True))


def frozen():
    fz = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    for rel, h in fz["sha256_text"].items():
        if D.sha256_text(HERE / rel) != h:
            raise SystemExit(f"FREEZE mismatch: {rel}")
    for rel, h in fz["data_sha256"].items():
        if D.sha256(D.ROOT / rel) != h:
            raise SystemExit(f"FREEZE data mismatch: {rel}")
    return fz


def stage_selection():
    fz = frozen()
    path = HERE / "SELECTION.json"
    if path.exists():
        raise SystemExit("SELECTION.json exists (write-once)")
    a = run_block("selection", None, do_escalation=True, do_primary=True)
    ca = a["truth_T"]["contrasts"]["rsd-raw"]
    go = ca["D1"]["estimate"] > 0 or ca["D2"]["estimate"] > 0
    write_once(path, dict(run=a, decision="GO" if go else "STOP_SELECTION_NONPOSITIVE"))


def stage_evaluation():
    fz = frozen()
    sel = json.loads((HERE / "SELECTION.json").read_text(encoding="utf-8"))
    if sel["decision"] != "GO":
        raise SystemExit("selection gate did not pass; evaluation not run")
    path = HERE / "EVALUATION.json"
    if path.exists():
        raise SystemExit("EVALUATION.json exists (write-once)")
    r = run_block("evaluation", None, do_escalation=True, do_primary=True, do_sensitivity=True)
    r["verdict"] = verdict(r, fz["practical_threshold"])
    write_once(path, r)


def verdict(r, delta):
    """Pre-specified primary rule: Holm over {H1-D1, H1-D2} (one-sided bootstrap p) and estimate >= delta_D."""
    con = r["truth_T"]["contrasts"]["rsd-raw"]
    p = {d: con[d]["p_one_sided"] for d in ("D1", "D2")}
    order = sorted(p, key=p.get)
    holm, run = {}, 0.0
    for i, d in enumerate(order):
        run = max(run, min(1.0, (len(order) - i) * p[d]))
        holm[d] = run
    out = {}
    for d in ("D1", "D2"):
        est = con[d]["estimate"]
        if holm[d] < 0.05 and est >= delta[d]:
            lab = "SUPPORTED"
        elif holm[d] < 0.05:
            lab = "SIGNIFICANT_BELOW_PRACTICAL"
        else:
            lab = "NOT_SUPPORTED"
        out[d] = dict(estimate=est, ci95=con[d]["ci95"], p_one_sided=p[d], p_holm=holm[d], delta=delta[d], label=lab)
    return out


if __name__ == "__main__":
    {"search": stage_search, "search2": stage_search2, "selection": stage_selection, "evaluation": stage_evaluation}[sys.argv[1]]()
