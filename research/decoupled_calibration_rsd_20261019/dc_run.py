"""Decoupled calibration layer for the replicate-identified Virtual Cell posterior (RSD): stage runner.

Usage (maestro environment, from the repository root or this folder):
  python -B dc_run.py dev <tag> <block>   -> dev/<tag>_2p5uM_<block>.json (development dose 2.5 uM; write-once)
  python -B dc_run.py devread             -> DEV_RESULT.json (requires FREEZE.json; pre-registered development readout on
                                             the exposed 0.625 and 10 uM reads (primary) and 2.5 uM (secondary); write-once)
  python -B dc_run.py confirm             -> refuses: no unopened arena is authorised (PROTOCOL.md section 9)

The layer under test ("dec"): decisions D1 and D2 rank by the frozen Gaussian RSD posterior mean, and the claimed value
of a chosen pair stays that mean; only the noise term of its predictive interval for a new read is replaced by the
compound's posterior noise scale under the compound-level Student-t model of the heavy-tail study
(`ht_core.ht_posterior(level="compound")`), fitted to the same read A. Nothing here changes a decision or a claim.

Arms per (dose, query block); one read A (20 pool wells per compound) unless stated:
  raw          selective read A; interval: flat-prior replicate noise, T - A ~ N(0, 2 n1) (zero-method arm)
  raw2         mean of reads A and B (40 wells); interval T - mean ~ N(0, 1.5 n1) (0.5 n1 + n1 when B is missing: n1 + n1)
  shrink       read A x per-tier replicate reliability r_k; interval N(r_k sA, (1 + r_k) n1)
               (n1 and r_k from the fixed-definition VC q = 0, rho = 0, prior off: independent of every inner choice)
  rsd          frozen Gaussian RSD posterior (own frozen inner selection); its Gaussian predictive
  ht_compound  compound-level Student-t posterior (heavy-tail `ht_compound` rule: geometry from the frozen Gaussian inner
               choice, nu = best compound candidate by the frozen reference-only utility, scale s by reference ML); ranks
               and claims with its own posterior
  dec          ranks and claims with rsd; predictive = rsd's Gaussian signal posterior plus ht_compound's compound noise
               scale for the new read (method under test)
  dec_full     ranks with rsd; claims and intervals from ht_compound's own predictive (centre and spread; secondary)
  dec_ml       as dec, with the compound noise scale from the compound-level model at nu = nu_ML (reference likelihood)
  rsd_wm       width-matched control: ranks and claims with rsd; rsd's Gaussian predictive with its SD scaled per unit by
               one constant so that its mean SD over rsd's D2 picks equals dec's (uses no outcome)
Policies read only A (and B for raw2) through the frozen Acquisition; only the frozen Evaluator holds T.
Reads come only from the heavy-tail study's existing read caches; this module refuses to run if a cache is missing and
checks that the cache folder is unchanged afterwards (it never writes outside this folder). No LLM or paid call.
"""
from __future__ import annotations

import datetime
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.stats import norm

HERE = Path(__file__).resolve().parent
HT = HERE.parent / "heavy_tail_rsd_20261019"
RSD = HERE.parent / "replicate_decisions_20261019"
for p in (HT, RSD):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import ht_core as H  # noqa: E402  (frozen heavy-tail; imported, never modified)
import ht_data as HD  # noqa: E402  (frozen heavy-tail; imported, never modified)
import ht_run as HR  # noqa: E402  (frozen heavy-tail; imported, never modified)
import rsd_core as C  # noqa: E402  (frozen RSD; imported, never modified)
import rsd_data as D  # noqa: E402  (frozen RSD; imported, never modified)
import rsd_run as R  # noqa: E402  (frozen RSD; imported, never modified)

BLOCKS = ("search", "selection", "evaluation")
PRIMARY_DOSES = (0.625, 10.0)          # pre-registered development readout (exposed by the heavy-tail test stage)
SECONDARY_DOSES = (2.5,)               # development dose (exposed by RSD; this study's smoke run used its search block)
ARMS = ("raw", "raw2", "shrink", "rsd", "ht_compound", "dec", "dec_full", "dec_ml", "rsd_wm")
RANK_BY = dict(raw="raw", raw2="raw2", shrink="shrink", rsd="rsd", ht_compound="ht_compound",
               dec="rsd", dec_full="rsd", dec_ml="rsd", rsd_wm="rsd")
DECOUPLED = ("dec", "dec_full", "dec_ml", "rsd_wm")
CONTRASTS = (("rsd", "raw"), ("raw2", "raw"), ("shrink", "raw"), ("ht_compound", "raw"), ("ht_compound", "rsd"),
             ("dec", "raw"), ("dec", "rsd"), ("dec", "ht_compound"), ("dec", "raw2"))
COV_CONTRASTS = (("dec", "rsd"), ("dec", "rsd_wm"), ("dec", "dec_full"), ("dec", "ht_compound"), ("dec_full", "rsd"),
                 ("dec_ml", "rsd"), ("ht_compound", "rsd"))
LEVELS = (0.5, 0.8, 0.9)
LEVEL = 0.8
N_BOOT = 4000
SEED = 20261019
WELLS_PER_READ = R.WELLS_PER_READ
COMPOUND_CANDS = tuple(c for c in HR.CANDS if c[0] == "compound")
# pre-registered thresholds (also written into FREEZE.json)
THRESHOLDS = dict(alpha_holm=0.05, coverage_selected_band=[0.70, 0.90], optimism_abs_max=0.15,
                  coverage_all_band=[0.75, 0.85], delta_rule="0.5 x pooled (raw2 - raw) estimate per decision, same data")


# ----------------------------------------------------------------------------- read-cache guard
def cache_snapshot():
    return {p.name: (p.stat().st_size, p.stat().st_mtime_ns) for p in sorted(HD.CACHE.glob("*"))}


def require_cache(dose):
    """Only already-opened reads: the heavy-tail study's cache for this dose must exist (no LFC parse, no write)."""
    tag = str(dose).replace(".", "p")
    hits = sorted(HD.CACHE.glob(f"reads_{tag}uM_*.npz"))
    if not hits:
        raise PermissionError(f"no existing read cache for {dose} uM in {HD.CACHE}; this study only reads opened reads")
    return [h.name for h in hits]


def setup(blk, dose):
    before = cache_snapshot()
    require_cache(dose)
    S = HD.setup(blk, dose)
    if cache_snapshot() != before:
        raise RuntimeError("the heavy-tail read cache changed while loading reads")
    return S


# ----------------------------------------------------------------------------- intervals
def noise1(vc, tier):
    """Per-pair noise variance of one read under a VC (the frozen posterior's noise1 formula)."""
    return vc.beta[tier][:, None] * np.diag(vc.N0)[None, :]


def coverage_rows(F, cid, n_cl):
    out = {}
    for lv in LEVELS:
        out[f"cov{int(round(lv * 100))}"] = HR._bin(cid, np.abs(F - 0.5) <= lv / 2, n_cl)
    return out


def scores_gaussian(y, m, var, level=LEVEL):
    """Proper scores of a Gaussian predictive N(m, var) for outcome y: the central-interval score at `level` (width plus
    2 / alpha times the miss distance; Gneiting and Raftery 2007; lower is better) and the log predictive density."""
    alpha = 1.0 - level
    sd = np.sqrt(var)
    half = norm.ppf(1.0 - alpha / 2) * sd
    lo, hi = m - half, m + half
    iscore = (hi - lo) + (2 / alpha) * np.clip(lo - y, 0, None) + (2 / alpha) * np.clip(y - hi, 0, None)
    return iscore, norm.logpdf(y, m, sd)


# ----------------------------------------------------------------------------- one (dose, block)
def run_block(blk, dose):
    t0 = time.time()
    S = setup(blk, dose)
    q, ref = S["q"], S["ref"]
    cl_ref = S["t"].cluster.to_numpy()[ref]
    cfg, inner_g = C.inner_select(S["Tsim"], ref, cl_ref, S["E"], S["A"], S["B"], S["T"], S["pools"], R.GRID, R.PCA_GRID)
    acq = R.Acquisition(S["A"][q], S["B"][q])
    A = acq.read_A()
    vc = R.build_vc(S, cfg)
    cluster_q = S["t"].cluster.to_numpy()[q]
    ev = C.Evaluator(S["T"][q], None, vc.g, cluster_q)
    clusters, inv = np.unique(cluster_q, return_inverse=True)
    n_cl = len(clusters)
    tier = C.tier_of(A)
    one = np.ones(len(q))
    keep_ref = np.arange(len(ref))
    # frozen Gaussian RSD
    mu = vc.prior(q, keep_ref)
    m_g, v_g, n1_g = vc.posterior(mu, A, one, tier)
    # two reads (B bought for every query through the interface)
    acq2 = R.Acquisition(S["A"][q], S["B"][q])
    Bq = acq2.buy_B(np.arange(len(q)))
    Y2 = np.nanmean(np.stack([A, Bq]), 0)
    # fixed-definition baselines (independent of every inner choice)
    vc_s = R.build_vc(S, dict(q=0, rho=0.0, use_prior=False))
    rel = R.reliability(vc_s)
    n1_s = noise1(vc_s, tier)
    sA = C.raw_score(A, vc.g)
    s2 = C.raw_score(Y2, vc.g)
    shr = C.scalar_shrink(A, vc.g, rel, tier)
    both = np.isfinite(C.selective(A, vc.g)) & np.isfinite(C.selective(Bq, vc.g))
    # compound-level Student-t interval model (heavy-tail ht_compound rule), and the nu_ML variant
    fvc = H.build_factor_vc(S, cfg["q"], cfg["use_prior"])
    Zref = H.standardized_differences(fvc, S["A"], S["B"], S["T"], ref, matrix=True)
    tail = H.fit_tail_compound(Zref)
    _, inner_h = H.ht_inner_select(S, cfg["q"], cfg["use_prior"], COMPOUND_CANDS)
    best = max(COMPOUND_CANDS, key=lambda c: (inner_h["score"][H.cand_key(c)], c[1], c[2]))
    nu_c, s_c = best[1], tail["profile"][best[1]]["s"]
    nu_ml, s_ml = tail["nu_ml"], tail["profile"][tail["nu_ml"]]["s"]
    mu_f = fvc.prior(q, keep_ref)
    p_c = H.ht_posterior(fvc, mu_f, A, tier, nu_c, s_c, level="compound")
    p_ml = H.ht_posterior(fvc, mu_f, A, tier, nu_ml, s_ml, level="compound")
    scores = dict(raw=sA, raw2=s2, shrink=shr, rsd=m_g, ht_compound=p_c["mean"])
    # width-matched control: one per-unit constant on rsd's predictive SD, matching dec's mean SD over rsd's D2 picks
    ch_g = C.d2_choose(m_g)
    li_g = np.tile(np.arange(m_g.shape[1]), (ch_g.shape[0], 1))
    sd_dec = np.sqrt(v_g + p_c["pred_sig2"])[ch_g, li_g]
    sd_rsd = np.sqrt(v_g + n1_g)[ch_g, li_g]
    wm = float(np.mean(sd_dec) / np.mean(sd_rsd))
    # predictive for the truth read T: (centre, signal variance, new-read noise scale^2, noise tail)
    pred = dict(
        raw=(sA, n1_s, n1_s, np.inf),
        raw2=(s2, np.where(both, 0.5, 1.0) * n1_s, n1_s, np.inf),
        shrink=(shr, rel[tier][:, None] * n1_s, n1_s, np.inf),
        rsd=(m_g, v_g, n1_g, np.inf),
        ht_compound=(p_c["mean"], p_c["var"], p_c["pred_sig2"], p_c["pred_nu"]),
        dec=(m_g, v_g, p_c["pred_sig2"], p_c["pred_nu"]),
        dec_full=(p_c["mean"], p_c["var"], p_c["pred_sig2"], p_c["pred_nu"]),
        dec_ml=(m_g, v_g, p_ml["pred_sig2"], p_ml["pred_nu"]),
        rsd_wm=(m_g, wm * wm * v_g, wm * wm * n1_g, np.inf),
    )
    sT = ev._sT                                                   # evaluator-side grading only
    L = sT.shape[1]
    rec = dict(block=blk, dose=dose, n_queries=int(len(q)), n_reference=int(len(ref)), n_absent_queries=S["n_absent_queries"],
               n_absent_references=S["n_absent_references"], n_clusters=int(n_cl), clusters=[str(c) for c in clusters],
               compound_cluster=inv.tolist(), cfg_gauss=cfg, inner_gauss=inner_g,
               tail_compound={k: v for k, v in tail.items()}, inner_ht_compound=inner_h,
               interval_model=dict(ht_compound=dict(level="compound", nu=nu_c, s=s_c),
                                   dec_ml=dict(level="compound", nu=nu_ml, s=s_ml), rsd_wm_sd_factor=wm),
               reliability_shrink=rel.tolist(), alpha=vc.alpha.tolist(), beta=vc.beta.tolist(),
               tier_counts_query=np.bincount(tier, minlength=3).tolist(),
               reads=dict(one_read=int(acq.reads), two_reads=int(acq.reads + acq2.reads)),
               wells=dict(one_read=int(acq.reads) * WELLS_PER_READ, two_reads=int(acq.reads + acq2.reads) * WELLS_PER_READ))
    rec["d1"], rec["d2"] = {}, {}
    for a in ARMS:
        sc = scores[RANK_BY[a]]
        r1 = ev.d1(C.d1_choose(sc))
        rec["d1"][a] = dict(util=HR._l(r1["util"]), hit=HR._l(r1["hit"]), fp=HR._l(r1["fp"]), unknown=int(r1["unknown"]))
        c2 = R.d2_contrib(ev, sc, inv, n_cl)
        rec["d2"][a] = dict(num=HR._l(c2["num"]), den=HR._l(c2["den"]), hit=HR._l(c2["hit"]), fp=HR._l(c2["fp"]),
                            unknown=int(c2["unknown"]))
    rec["calibration"], rec["optimism"] = {}, {}
    rows = np.broadcast_to(np.arange(len(q))[:, None], sT.shape)
    for a in ARMS:
        m, v, sg2, nu = pred[a]
        ch = C.d2_choose(scores[RANK_BY[a]])                      # the arm's own D2 picks
        li = np.tile(np.arange(L), (ch.shape[0], 1))
        e, ok = sT[ch, li] - m[ch, li], np.isfinite(sT[ch, li]) & np.isfinite(m[ch, li])
        Fs = H.predictive_cdf(e[ok], v[ch, li][ok], sg2[ch, li][ok], nu)
        cid_s = inv[ch[ok]]
        c1 = C.d1_choose(scores[RANK_BY[a]])                      # the arm's own D1 picks
        r1 = np.broadcast_to(np.arange(len(q))[:, None], c1.shape)
        e1, ok1 = sT[r1, c1] - m[r1, c1], np.isfinite(sT[r1, c1]) & np.isfinite(m[r1, c1])
        F1 = H.predictive_cdf(e1[ok1], v[r1, c1][ok1], sg2[r1, c1][ok1], nu)
        ok_all = np.isfinite(sT) & np.isfinite(m)                 # pairs with a known truth read and a defined claim
        ii_all = rows[ok_all]
        Fa = H.predictive_cdf((sT - m)[ok_all], v[ok_all], sg2[ok_all], nu)
        if np.isfinite(nu):
            raise ValueError("proper scores are implemented for Gaussian predictives only")
        isc, lpd = scores_gaussian(sT[ch, li][ok], m[ch, li][ok], v[ch, li][ok] + sg2[ch, li][ok])
        rec["calibration"][a] = dict(
            **{k + "_sel": x for k, x in coverage_rows(Fs, cid_s, n_cl).items()},
            n_sel=HR._bin(cid_s, np.ones(ok.sum()), n_cl),
            z_sel=HR._bin(cid_s, norm.ppf(np.clip(Fs, 1e-12, 1 - 1e-12)), n_cl),
            width80_sel=HR._bin(cid_s, 2 * norm.ppf(0.9) * np.sqrt(v[ch, li][ok] + sg2[ch, li][ok]), n_cl),
            iscore80_sel=HR._bin(cid_s, isc, n_cl), logscore_sel=HR._bin(cid_s, lpd, n_cl),
            cov80_d1=HR._bin(inv[r1[ok1]], np.abs(F1 - 0.5) <= LEVEL / 2, n_cl),
            n_d1=HR._bin(inv[r1[ok1]], np.ones(ok1.sum()), n_cl),
            cov80_all=HR._bin(inv[ii_all], np.abs(Fa - 0.5) <= LEVEL / 2, n_cl),
            n_all=HR._bin(inv[ii_all], np.ones(ok_all.sum()), n_cl))
        cl_, ob = -m[ch, li], -sT[ch, li]
        okc = np.isfinite(cl_) & np.isfinite(ob)
        cid = inv[ch[okc]]
        rec["optimism"][a] = dict(claimed=HR._bin(cid, cl_[okc], n_cl), observed=HR._bin(cid, ob[okc], n_cl),
                                  n=HR._bin(cid, np.ones(okc.sum()), n_cl))
    ch_g, ch_c = C.d2_choose(m_g), C.d2_choose(p_c["mean"])
    li = np.tile(np.arange(L), (ch_g.shape[0], 1))
    rec["checks"] = dict(
        dec_picks_equal_rsd=bool(all(np.array_equal(C.d2_choose(scores[RANK_BY[a]]), ch_g)
                                     and np.array_equal(C.d1_choose(scores[RANK_BY[a]]), C.d1_choose(m_g)) for a in DECOUPLED)),
        d2_pick_overlap_ht_compound_rsd=float(np.mean([len(set(ch_c[:, j]) & set(ch_g[:, j])) / ch_g.shape[0] for j in range(L)])),
        mean_lambda_all=float(np.mean(p_c["lam"][:, 0])),
        mean_lambda_rsd_selected=float(np.mean(p_c["lam"][ch_g, li])),
        mean_lambda_ht_compound_selected=float(np.mean(p_c["lam"][ch_c, li])),
        iterations=dict(ht_compound=int(p_c["iters"]), dec_ml=int(p_ml["iters"])))
    rec["seconds"] = round(time.time() - t0, 1)
    return rec


# ----------------------------------------------------------------------------- pooling and bootstrap
def boot_weights(keys, n_boot, seed):
    """Cluster multinomial stratified by block (the construction of the frozen heavy-tail pool)."""
    index = {k: i for i, k in enumerate(keys)}
    rng = np.random.default_rng(seed)
    W = np.zeros((n_boot, len(keys)))
    for blk in sorted({k[0] for k in keys}):
        cols = [index[k] for k in keys if k[0] == blk]
        W[:, cols] = rng.multinomial(len(cols), np.full(len(cols), 1 / len(cols)), size=n_boot)
    return W, index


def pool(records, n_boot=N_BOOT, seed=SEED, th=THRESHOLDS):
    """Pool (dose, block) records: per-cluster sums over doses; one bootstrap draw shared by every dose (a compound's reads
    at several doses are not independent). Returns aggregates, contrasts, calibration, optimism and the primary tests."""
    keys = sorted({(r["block"], c) for r in records for c in r["clusters"]})
    W, index = boot_weights(keys, n_boot, seed)
    n = len(keys)

    def gidx(r):
        return np.array([index[(r["block"], c)] for c in r["clusters"]])

    def sums(section, arm, fields):
        out = {f: np.zeros(n) for f in fields}
        for r in records:
            g = gidx(r)
            for f in fields:
                np.add.at(out[f], g, np.asarray(r[section][arm][f], float))
        return out

    def ratio(numv, denv):
        return float(numv.sum() / denv.sum()), (W @ numv) / np.maximum(W @ denv, 1e-12)

    def summ(est, bs, null=0.0):
        lo, hi = np.nanpercentile(bs, [2.5, 97.5])
        return dict(estimate=est, ci95=[float(lo), float(hi)], p_one_sided=p_le(bs, null))

    def d1_contrast(a, b):
        num, den = np.zeros(n), np.zeros(n)
        for r in records:
            g = gidx(r)[np.asarray(r["compound_cluster"])]
            d = HR._arr(r["d1"][a]["util"]) - HR._arr(r["d1"][b]["util"])
            ok = np.isfinite(d)
            np.add.at(num, g[ok], d[ok]); np.add.at(den, g[ok], 1.0)
        return float(num.sum() / den.sum()), (W @ num) / np.maximum(W @ den, 1e-12)

    out = dict(n_records=len(records), n_clusters=n, n_compound_doses=int(sum(r["n_queries"] for r in records)),
               doses=sorted({r["dose"] for r in records}), blocks=sorted({r["block"] for r in records}),
               wells=dict(one_read=int(sum(r["wells"]["one_read"] for r in records)),
                          two_reads=int(sum(r["wells"]["two_reads"] for r in records)), calibration_layer=0))
    arms = {}
    for a in ARMS:
        s2 = sums("d2", a, ("num", "den", "hit", "fp"))
        u1 = [x for r in records for x in HR._arr(r["d1"][a]["util"]) if np.isfinite(x)]
        h1 = [x for r in records for x in HR._arr(r["d1"][a]["hit"]) if np.isfinite(x)]
        f1 = [x for r in records for x in HR._arr(r["d1"][a]["fp"]) if np.isfinite(x)]
        arms[a] = dict(wells_per_compound=2 * WELLS_PER_READ if a == "raw2" else WELLS_PER_READ,
                       D1=dict(util=float(np.mean(u1)), hit=float(np.mean(h1)), false_progression=float(np.mean(f1))),
                       D2=dict(util=float(s2["num"].sum() / s2["den"].sum()), hit=float(s2["hit"].sum() / s2["den"].sum()),
                               false_progression=float(s2["fp"].sum() / s2["den"].sum())))
    out["arms"] = arms
    con = {}
    for a, b in CONTRASTS:
        e1, b1 = d1_contrast(a, b)
        sa, sb = sums("d2", a, ("num", "den")), sums("d2", b, ("num", "den"))
        ea, ba = ratio(sa["num"], sa["den"])
        eb, bb = ratio(sb["num"], sb["den"])
        con[f"{a}-{b}"] = dict(D1=summ(e1, b1), D2=summ(ea - eb, ba - bb))
    out["contrasts"] = con
    cal, draws, sdraws = {}, {}, {}
    for a in ARMS:
        s = sums("calibration", a, ("cov50_sel", "cov80_sel", "cov90_sel", "n_sel", "z_sel", "width80_sel",
                                    "iscore80_sel", "logscore_sel", "cov80_d1", "n_d1", "cov80_all", "n_all"))
        e80, b80 = ratio(s["cov80_sel"], s["n_sel"])
        ed1, bd1 = ratio(s["cov80_d1"], s["n_d1"])
        eal, bal = ratio(s["cov80_all"], s["n_all"])
        eis, bis = ratio(s["iscore80_sel"], s["n_sel"])
        els, bls = ratio(s["logscore_sel"], s["n_sel"])
        draws[a] = b80
        sdraws[a] = dict(iscore80=(eis, bis), logscore=(els, bls))
        cal[a] = dict(coverage80_selected=dict(estimate=e80, ci95=_ci(b80)),
                      coverage50_selected=float(s["cov50_sel"].sum() / s["n_sel"].sum()),
                      coverage90_selected=float(s["cov90_sel"].sum() / s["n_sel"].sum()),
                      coverage80_d1_selected=dict(estimate=ed1, ci95=_ci(bd1)),
                      coverage80_all=dict(estimate=eal, ci95=_ci(bal)),
                      mean_pit_z_selected=float(s["z_sel"].sum() / s["n_sel"].sum()),
                      mean_width80_selected=float(s["width80_sel"].sum() / s["n_sel"].sum()),
                      interval_score80_selected=dict(estimate=eis, ci95=_ci(bis)),
                      log_score_selected=dict(estimate=els, ci95=_ci(bls)),
                      n_selected=int(s["n_sel"].sum()))
    cov_con, score_con = {}, {}
    for a, b in COV_CONTRASTS:
        cov_con[f"{a}-{b}"] = summ(cal[a]["coverage80_selected"]["estimate"] - cal[b]["coverage80_selected"]["estimate"],
                                   draws[a] - draws[b])
        score_con[f"{a}-{b}"] = {k: summ(sdraws[a][k][0] - sdraws[b][k][0], sdraws[a][k][1] - sdraws[b][k][1])
                                 for k in ("iscore80", "logscore")}
    out["calibration"] = cal
    out["coverage_contrasts"] = cov_con
    out["score_contrasts"] = score_con
    opt, odraws = {}, {}
    for a in ARMS:
        s = sums("optimism", a, ("claimed", "observed", "n"))
        e, bs = ratio(s["claimed"] - s["observed"], s["n"])
        odraws[a] = bs
        opt[a] = dict(claimed=float(s["claimed"].sum() / s["n"].sum()), observed=float(s["observed"].sum() / s["n"].sum()),
                      optimism=e, optimism_ci95=_ci(bs))
    out["selected_optimism_D2"] = opt
    # primary tests (PROTOCOL.md section 6): one-sided percentile-bootstrap p values
    lo_c, hi_c = th["coverage_selected_band"]
    om = th["optimism_abs_max"]
    out["tests"] = dict(
        P1=dict(statistic="coverage80_selected(dec) - coverage80_selected(rsd)", estimate=cov_con["dec-rsd"]["estimate"],
                ci95=cov_con["dec-rsd"]["ci95"], p_one_sided=p_le(draws["dec"] - draws["rsd"], 0.0)),
        P2=dict(statistic=f"coverage80_selected(dec) in [{lo_c}, {hi_c}] (two one-sided tests)",
                estimate=cal["dec"]["coverage80_selected"]["estimate"], ci95=cal["dec"]["coverage80_selected"]["ci95"],
                p_lower=p_le(draws["dec"], lo_c), p_upper=p_ge(draws["dec"], hi_c),
                p_one_sided=max(p_le(draws["dec"], lo_c), p_ge(draws["dec"], hi_c))),
        P3=dict(statistic=f"selected optimism(dec) in [-{om}, {om}] (two one-sided tests)",
                estimate=opt["dec"]["optimism"], ci95=opt["dec"]["optimism_ci95"],
                p_lower=p_le(odraws["dec"], -om), p_upper=p_ge(odraws["dec"], om),
                p_one_sided=max(p_le(odraws["dec"], -om), p_ge(odraws["dec"], om))))
    return out


def p_le(bs, x):
    """One-sided percentile-bootstrap p for H0: statistic <= x (the frozen RSD definition, shifted to x)."""
    bs = np.asarray(bs, float)
    return float((np.sum(bs <= x) + 1) / (len(bs) + 1))


def p_ge(bs, x):
    bs = np.asarray(bs, float)
    return float((np.sum(bs >= x) + 1) / (len(bs) + 1))


def _ci(bs):
    lo, hi = np.nanpercentile(bs, [2.5, 97.5])
    return [float(lo), float(hi)]


def holm(p):
    order = sorted(p, key=p.get)
    out, run = {}, 0.0
    for i, h in enumerate(order):
        run = max(run, min(1.0, (len(order) - i) * p[h]))
        out[h] = run
    return out


def verdict(agg, decisions_identical, th=THRESHOLDS):
    """Pre-registered rule (PROTOCOL.md section 6). Development-grade labels on exposed data."""
    tests = agg["tests"]
    p = {h: tests[h]["p_one_sided"] for h in ("P1", "P2", "P3")}
    ph = holm(p)
    lab = {h: ("SUPPORTED" if ph[h] < th["alpha_holm"] else "NOT_SUPPORTED") for h in p}
    cs = agg["calibration"]["dec"]["coverage80_selected"]["estimate"]
    ca = agg["calibration"]["dec"]["coverage80_all"]["estimate"]
    op = agg["selected_optimism_D2"]["dec"]["optimism"]
    lo_c, hi_c = th["coverage_selected_band"]
    point = dict(coverage_selected_in_band=bool(lo_c <= cs <= hi_c), optimism_within=bool(abs(op) <= th["optimism_abs_max"]),
                 coverage_all_in_band=bool(th["coverage_all_band"][0] <= ca <= th["coverage_all_band"][1]))
    c = agg["contrasts"]
    keep = dict(K1_decisions_identical=bool(decisions_identical),
                dec_minus_rsd_D1=c["dec-rsd"]["D1"]["estimate"], dec_minus_rsd_D2=c["dec-rsd"]["D2"]["estimate"])
    if not decisions_identical or keep["dec_minus_rsd_D1"] != 0.0 or keep["dec_minus_rsd_D2"] != 0.0:
        overall = "DEFECT_DECISIONS_CHANGED"
    elif all(v == "SUPPORTED" for v in lab.values()):
        overall = "DECOUPLED_CALIBRATION_HOLDS"
    elif not (point["coverage_selected_in_band"] and point["optimism_within"]):
        overall = "DECOUPLED_CALIBRATION_FAILS"
    else:
        overall = "PARTIAL"
    return dict(grade="DEVELOPMENT_ONLY", overall=overall,
                hypotheses={h: dict(statistic=tests[h]["statistic"], estimate=tests[h]["estimate"], ci95=tests[h]["ci95"],
                                    p_one_sided=p[h], p_holm=ph[h], label=lab[h]) for h in p},
                decisions=keep, point_criteria=point,
                values=dict(coverage80_selected=cs, coverage80_all=ca, optimism=op,
                            rsd_coverage80_selected=agg["calibration"]["rsd"]["coverage80_selected"]["estimate"]),
                not_met=[h for h in lab if lab[h] != "SUPPORTED"] + [k for k, v in point.items() if not v])


# ----------------------------------------------------------------------------- reproduction of the frozen heavy-tail records
def reproduction(records):
    """Max absolute difference between this study's rsd / ht_compound per-unit sums and the heavy-tail RESULT.json records
    (same frozen code, same reads): checks that the imported pipeline is reproduced."""
    ht = json.loads((HT / "RESULT.json").read_text(encoding="utf-8"))
    by = {(r["dose"], r["block"]): r for r in ht["records"]}
    out = {}
    for r in records:
        h = by.get((r["dose"], r["block"]))
        if h is None:
            continue
        diffs = []
        for a in ("raw", "raw2", "shrink", "rsd", "ht_compound"):
            for f in ("num", "den"):
                diffs.append(np.nanmax(np.abs(HR._arr(r["d2"][a][f]) - HR._arr(h["d2"][a][f]))))
            diffs.append(np.nanmax(np.abs(HR._arr(r["d1"][a]["util"]) - HR._arr(h["d1"][a]["util"]))))
            for f in ("claimed", "observed", "n"):
                diffs.append(np.nanmax(np.abs(np.asarray(r["optimism"][a][f]) - np.asarray(h["optimism"][a][f]))))
        for a in ("rsd", "ht_compound"):
            for mine, theirs in (("cov80_sel", "cov_sel"), ("n_sel", "n_sel"), ("cov80_all", "cov_all"), ("n_all", "n_all")):
                diffs.append(np.nanmax(np.abs(np.asarray(r["calibration"][a][mine]) - np.asarray(h["calibration"][a][theirs]))))
        out[f"{r['dose']}|{r['block']}"] = dict(
            max_abs_diff=float(max(diffs)), cfg_equal=r["cfg_gauss"] == h["cfg_gauss"],
            nu_equal=r["interval_model"]["ht_compound"]["nu"] == h["chosen"]["ht_compound"]["nu"],
            s_abs_diff=abs(r["interval_model"]["ht_compound"]["s"] - h["chosen"]["ht_compound"]["s"]))
    return out


# ----------------------------------------------------------------------------- stages
def write_once(path, obj):
    if path.exists():
        raise SystemExit(f"refusing to overwrite {path.name}")
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, default=float), encoding="utf-8", newline="\n")


def code_hashes():
    return {f: D.sha256_text(HERE / f) for f in ("dc_run.py",)}


def stage_dev(tag, blk):
    path = HERE / "dev" / f"{tag}_2p5uM_{blk}.json"
    if path.exists():
        raise SystemExit(f"{path.name} exists (write-once)")
    hashes = code_hashes()
    rec = run_block(blk, 2.5)
    agg = pool([rec])
    write_once(path, dict(note="DEVELOPMENT (2.5 uM, exposed by RSD); not evidence", code_sha256=hashes, record=rec,
                          aggregate=agg, rule_for_illustration=verdict(agg, rec["checks"]["dec_picks_equal_rsd"])))


def frozen():
    fz = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    for rel, h in fz["sha256_text"].items():
        if D.sha256_text(HERE / rel) != h:
            raise SystemExit(f"FREEZE mismatch: {rel}")
    for rel, h in fz["imported_frozen_sha256_text"].items():
        if D.sha256_text(HERE.parent / rel) != h:
            raise SystemExit(f"imported frozen file changed: {rel}")
    for rel, h in fz["read_cache_sha256"].items():
        if D.sha256(HD.CACHE / rel) != h:
            raise SystemExit(f"read cache changed: {rel}")
    return fz


def stage_devread():
    fz = frozen()
    path = HERE / "DEV_RESULT.json"
    if path.exists():
        raise SystemExit("DEV_RESULT.json exists (write-once)")
    t0 = time.time()
    started = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    hashes = code_hashes()
    recs = []
    for dose in PRIMARY_DOSES + SECONDARY_DOSES:
        for blk in BLOCKS:
            recs.append(run_block(blk, dose))
            print(f"done dose {dose} block {blk} ({recs[-1]['seconds']} s)", flush=True)
    prim = [r for r in recs if r["dose"] in PRIMARY_DOSES]
    sec = [r for r in recs if r["dose"] in SECONDARY_DOSES]
    agg = pool(prim, fz["n_boot"], fz["seed"], fz["thresholds"])
    agg_sec = pool(sec, fz["n_boot"], fz["seed"], fz["thresholds"])
    same = all(r["checks"]["dec_picks_equal_rsd"] for r in prim)
    out = dict(grade="DEVELOPMENT_ONLY",
               note="Development-only readout on exposed HTS002 reads (0.625 and 10 uM opened by the heavy-tail test stage; "
                    "2.5 uM by RSD). Pre-registered in the frozen PROTOCOL.md; not a confirmation. Confirmatory stage "
                    "BLOCKED: no unopened arena is authorised.",
               frozen_utc=fz["frozen_utc"], started_utc=started, code_sha256=hashes, records=recs,
               primary=dict(doses=list(PRIMARY_DOSES), aggregate=agg, verdict=verdict(agg, same, fz["thresholds"])),
               per_dose={str(d): pool([r for r in recs if r["dose"] == d], fz["n_boot"], fz["seed"], fz["thresholds"])
                         for d in PRIMARY_DOSES + SECONDARY_DOSES},
               secondary_2p5uM=dict(aggregate=agg_sec,
                                    verdict=verdict(agg_sec, all(r["checks"]["dec_picks_equal_rsd"] for r in sec),
                                                    fz["thresholds"])),
               reproduction_of_heavy_tail=reproduction(recs),
               confirmatory=dict(status="BLOCKED_NO_AUTHORISED_UNOPENED_ARENA"),
               seconds=round(time.time() - t0, 1))
    write_once(path, out)
    print(json.dumps(out["primary"]["verdict"], indent=1))


def stage_confirm():
    raise SystemExit("BLOCKED: no unopened arena is authorised. An independent tier (e.g. PRISM 24Q2) needs the owner's "
                     "authorisation and a protocol amendment frozen before it is opened (PROTOCOL.md section 9).")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "dev":
        stage_dev(sys.argv[2], sys.argv[3])
    elif cmd == "devread":
        stage_devread()
    elif cmd == "confirm":
        stage_confirm()
    else:
        raise SystemExit(f"unknown stage {cmd}")
