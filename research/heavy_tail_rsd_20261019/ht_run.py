"""Heavy-tail RSD stage runner.

Usage (maestro environment, from the repository root or this folder):
  python -B ht_run.py dev <tag> <block>     -> dev/<tag>_2p5uM_<block>.json  (development dose 2.5 uM, already exposed)
  python -B ht_run.py dev_pool <tag>        -> dev/<tag>_2p5uM_pooled.json   (pooled development record + rule applied)
  python -B ht_run.py evaluation            -> RESULT.json (requires FREEZE.json; test doses 0.625 and 10 uM; write-once)

Arms per (dose, query block), all on one read A per compound except raw2:
  raw      selective read A
  raw2     mean of reads A and B (two reads, 40 wells; value of a second read, sets the practical threshold)
  shrink   read A scaled by its per-tier replicate reliability (fixed definition: q = 0, rho = 0, prior off; independent
           of every inner choice)
  rsd      frozen Gaussian RSD posterior with its own frozen inner selection (rsd_core.inner_select, frozen grid)
  ht       Student-t noise; geometry (q, prior) = the frozen Gaussian inner choice, rho = 0; noise model (level, nu)
           chosen from CANDS inside the reference set by the frozen replicate-split utility (ht_core.ht_inner_select);
           noise scale s fitted by ML from the reference replicate differences at that (level, nu)
  ht_pair, ht_compound  best candidate within each model class by the same reference-only score (secondary)
  ht_fit   the selected class with nu = nu_ML of the reference replicate differences (no utility selection; secondary)
  gauss_rho0  ht's geometry with Gaussian noise (nu = inf, s = 1); equals rsd whenever rsd's inner choice has rho = 0
Policies read only A (and B for raw2) through the frozen Acquisition; only the frozen Evaluator holds T.
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
sys.path.insert(0, str(HERE))
import ht_core as H  # noqa: E402
import ht_data as HD  # noqa: E402
import rsd_core as C  # noqa: E402  (frozen)
import rsd_data as D  # noqa: E402  (frozen)
import rsd_run as R  # noqa: E402  (frozen)

BLOCKS = ("search", "selection", "evaluation")
# pre-registered noise-model candidates for the reference-only inner selection: (level, nu, nu_s)
CANDS = tuple(H.candidates(("pair", "compound"), H.NU_GRID, (np.inf,)))
ARMS = ("raw", "raw2", "shrink", "rsd", "ht", "ht_pair", "ht_compound", "ht_fit", "gauss_rho0")
CAL_ARMS = ("rsd", "ht", "ht_pair", "ht_compound", "ht_fit", "gauss_rho0")
OPT_ARMS = ("raw", "raw2", "shrink", "rsd", "ht", "ht_pair", "ht_compound", "ht_fit")
CONTRASTS = (("ht", "raw"), ("ht", "rsd"), ("rsd", "raw"), ("raw2", "raw"), ("ht", "raw2"), ("ht", "shrink"),
             ("ht_pair", "rsd"), ("ht_compound", "rsd"), ("ht_fit", "rsd"), ("shrink", "raw"), ("ht", "ht_fit"))
N_BOOT = 4000
SEED = 20261019
LEVEL = 0.8
# pre-registered thresholds (also written into FREEZE.json)
THRESHOLDS = dict(alpha_holm=0.05, delta_rule="0.5 x pooled (raw2 - raw) estimate per decision, same doses and queries",
                  ni_margin_rule="0.5 x delta_D1", coverage_selected_band=[0.70, 0.90], coverage_all_band=[0.75, 0.85],
                  optimism_abs_max=0.15)


# ----------------------------------------------------------------------------- one (dose, block)
def run_block(blk, dose):
    t0 = time.time()
    S = HD.setup(blk, dose)
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
    Y2 = np.nanmean(np.stack([A, acq2.buy_B(np.arange(len(q)))]), 0)
    # scalar shrinkage: fixed definition, independent of every inner choice
    vc_s = R.build_vc(S, dict(q=0, rho=0.0, use_prior=False))
    rel = R.reliability(vc_s)
    # heavy tail: noise scale fitted by ML on the reference replicate differences, model chosen by reference-only utility
    fvc = H.build_factor_vc(S, cfg["q"], cfg["use_prior"])
    Zref = H.standardized_differences(fvc, S["A"], S["B"], S["T"], ref, matrix=True)
    tails = dict(pair=H.fit_tail(Zref.ravel()), compound=H.fit_tail_compound(Zref))
    sel, inner_h = H.ht_inner_select(S, cfg["q"], cfg["use_prior"], CANDS)
    mu_f = fvc.prior(q, keep_ref)
    chosen = {"ht": (sel["level"], sel["nu"], sel["nu_s"])}
    for lv in sorted({c[0] for c in CANDS}):                    # best candidate within each model class (secondary)
        cl_c = [c for c in CANDS if c[0] == lv]
        chosen[f"ht_{lv}"] = max(cl_c, key=lambda c: (inner_h["score"][H.cand_key(c)], c[1], c[2]))
    chosen["ht_fit"] = (sel["level"], tails[sel["level"]]["nu_ml"], sel["nu_s"])
    post = {k: H.ht_posterior(fvc, mu_f, A, tier, c[1], tails[c[0]]["profile"][c[1]]["s"], level=c[0], nu_s=c[2])
            for k, c in chosen.items()}
    post["gauss_rho0"] = H.ht_posterior(fvc, mu_f, A, tier, np.inf, 1.0)
    scores = dict(raw=C.raw_score(A, vc.g), raw2=C.raw_score(Y2, vc.g), shrink=C.scalar_shrink(A, vc.g, rel, tier), rsd=m_g)
    scores |= {k: p["mean"] for k, p in post.items()}
    pred = dict(rsd=(m_g, v_g, n1_g, np.inf))
    pred |= {k: (p["mean"], p["var"], p["pred_sig2"], p["pred_nu"]) for k, p in post.items()}
    sT = ev._sT                                                   # evaluator-side grading only
    L = sT.shape[1]
    rec = dict(block=blk, dose=dose, n_queries=int(len(q)), n_reference=int(len(ref)), n_absent_queries=S["n_absent_queries"],
               n_absent_references=S["n_absent_references"], n_clusters=int(n_cl), clusters=[str(c) for c in clusters],
               compound_cluster=inv.tolist(), cfg_gauss=cfg, inner_gauss=inner_g,
               tail_fit={lv: {k: v for k, v in t.items()} for lv, t in tails.items()},
               selected=sel, chosen={k: dict(level=c[0], nu=c[1], nu_s=c[2], s=tails[c[0]]["profile"][c[1]]["s"]) for k, c in chosen.items()},
               inner_ht=inner_h, reliability_shrink=rel.tolist(),
               alpha=vc.alpha.tolist(), beta=vc.beta.tolist(), tier_counts_query=np.bincount(tier, minlength=3).tolist(),
               reads=dict(one_read=int(acq.reads), two_reads=int(acq.reads + acq2.reads)))
    rec["d1"], rec["d2"] = {}, {}
    for a in ARMS:
        r1 = ev.d1(C.d1_choose(scores[a]))
        rec["d1"][a] = dict(util=_l(r1["util"]), hit=_l(r1["hit"]), fp=_l(r1["fp"]), unknown=int(r1["unknown"]))
        c2 = R.d2_contrib(ev, scores[a], inv, n_cl)
        rec["d2"][a] = dict(num=_l(c2["num"]), den=_l(c2["den"]), hit=_l(c2["hit"]), fp=_l(c2["fp"]), unknown=int(c2["unknown"]))
    rec["calibration"] = {}
    ok_all = np.isfinite(sT)
    ii_all = np.broadcast_to(np.arange(len(q))[:, None], sT.shape)[ok_all]
    for a in CAL_ARMS:
        m, v, s2, nu = pred[a]
        ch = C.d2_choose(m)
        li = np.tile(np.arange(L), (ch.shape[0], 1))
        e, ok = sT[ch, li] - m[ch, li], np.isfinite(sT[ch, li])
        Fs = H.predictive_cdf(e[ok], v[ch, li][ok], s2[ch, li][ok], nu)
        cs = np.abs(Fs - 0.5) <= LEVEL / 2
        zs = norm.ppf(np.clip(Fs, 1e-12, 1 - 1e-12))
        Fa = H.predictive_cdf((sT - m)[ok_all], v[ok_all], s2[ok_all], nu)
        ca = np.abs(Fa - 0.5) <= LEVEL / 2
        cid_s = inv[ch[ok]]
        rec["calibration"][a] = dict(cov_sel=_bin(cid_s, cs, n_cl), n_sel=_bin(cid_s, np.ones_like(cs), n_cl),
                                     z_sel=_bin(cid_s, zs, n_cl), cov_all=_bin(inv[ii_all], ca, n_cl),
                                     n_all=_bin(inv[ii_all], np.ones_like(ca), n_cl))
    rec["optimism"] = {}
    for a in OPT_ARMS:
        ch = C.d2_choose(scores[a])
        li = np.tile(np.arange(L), (ch.shape[0], 1))
        cl_, ob = -scores[a][ch, li], -sT[ch, li]
        ok = np.isfinite(cl_) & np.isfinite(ob)
        cid = inv[ch[ok]]
        rec["optimism"][a] = dict(claimed=_bin(cid, cl_[ok], n_cl), observed=_bin(cid, ob[ok], n_cl), n=_bin(cid, np.ones(ok.sum()), n_cl))
    ch_h, ch_g = C.d2_choose(scores["ht"]), C.d2_choose(scores["rsd"])
    li = np.tile(np.arange(L), (ch_h.shape[0], 1))
    p_ht = post["ht"]
    rec["checks"] = dict(
        gauss_rho0_max_abs_diff_rsd=float(np.nanmax(np.abs(post["gauss_rho0"]["mean"] - m_g))) if cfg["rho"] == 0 else None,
        iterations={k: int(p["iters"]) for k, p in post.items()},
        mean_lambda_all_ht=float(np.mean(p_ht["lam"][np.isfinite(A)])),
        mean_lambda_ht_selected=float(np.mean(p_ht["lam"][ch_h, li])), mean_lambda_rsd_selected_under_ht=float(np.mean(p_ht["lam"][ch_g, li])),
        d2_pick_overlap_ht_rsd=float(np.mean([len(set(ch_h[:, j]) & set(ch_g[:, j])) / ch_h.shape[0] for j in range(L)])))
    rec["seconds"] = round(time.time() - t0, 1)
    return rec


def _l(x):
    return [None if not np.isfinite(v) else float(v) for v in np.asarray(x, float)]


def _bin(cid, x, n):
    out = np.zeros(n)
    np.add.at(out, cid, np.asarray(x, float))
    return out.tolist()


# ----------------------------------------------------------------------------- pooling and bootstrap
def _arr(x):
    return np.array([np.nan if v is None else v for v in x], float)


def pool(records, n_boot=N_BOOT, seed=SEED):
    """Pool (dose, block) records: per-cluster sums over doses; bootstrap = cluster multinomial stratified by block, the
    same draw for every dose (a compound's reads at two doses are not independent)."""
    keys = sorted({(r["block"], c) for r in records for c in r["clusters"]})
    index = {k: i for i, k in enumerate(keys)}
    n = len(keys)
    rng = np.random.default_rng(seed)
    W = np.zeros((n_boot, n))
    for blk in sorted({k[0] for k in keys}):
        cols = [index[k] for k in keys if k[0] == blk]
        W[:, cols] = rng.multinomial(len(cols), np.full(len(cols), 1 / len(cols)), size=n_boot)

    def gidx(r):
        return np.array([index[(r["block"], c)] for c in r["clusters"]])

    def d1_contrast(a, b):
        num, den = np.zeros(n), np.zeros(n)
        for r in records:
            g = gidx(r)[np.asarray(r["compound_cluster"])]
            d = _arr(r["d1"][a]["util"]) - _arr(r["d1"][b]["util"])
            ok = np.isfinite(d)
            np.add.at(num, g[ok], d[ok]); np.add.at(den, g[ok], 1.0)
        return float(num.sum() / den.sum()), (W @ num) / np.maximum(W @ den, 1e-12)

    def sums(section, arm, fields):
        out = {f: np.zeros(n) for f in fields}
        for r in records:
            g = gidx(r)
            for f in fields:
                np.add.at(out[f], g, np.asarray(r[section][arm][f], float))
        return out

    def ratio(numv, denv):
        return float(numv.sum() / denv.sum()), (W @ numv) / np.maximum(W @ denv, 1e-12)

    def summ(est, bs):
        lo, hi = np.nanpercentile(bs, [2.5, 97.5])
        return dict(estimate=est, ci95=[float(lo), float(hi)], p_one_sided=float((np.sum(bs <= 0) + 1) / (len(bs) + 1)))

    out = dict(n_records=len(records), n_clusters=n, n_compound_doses=int(sum(r["n_queries"] for r in records)),
               doses=sorted({r["dose"] for r in records}), blocks=sorted({r["block"] for r in records}))
    arms = {}
    for a in ARMS:
        s2 = sums("d2", a, ("num", "den", "hit", "fp"))
        u1 = [x for r in records for x in _arr(r["d1"][a]["util"]) if np.isfinite(x)]
        h1 = [x for r in records for x in _arr(r["d1"][a]["hit"]) if np.isfinite(x)]
        f1 = [x for r in records for x in _arr(r["d1"][a]["fp"]) if np.isfinite(x)]
        arms[a] = dict(D1=dict(util=float(np.mean(u1)), hit=float(np.mean(h1)), false_progression=float(np.mean(f1))),
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
    cal = {}
    for a in CAL_ARMS:
        s = sums("calibration", a, ("cov_sel", "n_sel", "z_sel", "cov_all", "n_all"))
        es, bs = ratio(s["cov_sel"], s["n_sel"])
        ea, ba = ratio(s["cov_all"], s["n_all"])
        cal[a] = dict(coverage_selected=summ(es, bs), coverage_all=summ(ea, ba),
                      mean_pit_z_selected=float(s["z_sel"].sum() / s["n_sel"].sum()), n_selected=int(s["n_sel"].sum()))
        cal[a]["coverage_selected"].pop("p_one_sided"); cal[a]["coverage_all"].pop("p_one_sided")
        cal[a]["_bs_sel"] = bs
    d = cal["ht"]["_bs_sel"] - cal["rsd"]["_bs_sel"]
    cal["ht-rsd_coverage_selected"] = summ(cal["ht"]["coverage_selected"]["estimate"] - cal["rsd"]["coverage_selected"]["estimate"], d)
    for a in CAL_ARMS:
        cal[a].pop("_bs_sel")
    out["calibration"] = cal
    opt = {}
    for a in OPT_ARMS:
        s = sums("optimism", a, ("claimed", "observed", "n"))
        e, bs = ratio(s["claimed"] - s["observed"], s["n"])
        lo, hi = np.nanpercentile(bs, [2.5, 97.5])
        opt[a] = dict(claimed=float(s["claimed"].sum() / s["n"].sum()), observed=float(s["observed"].sum() / s["n"].sum()),
                      optimism=e, optimism_ci95=[float(lo), float(hi)])
    out["selected_optimism_D2"] = opt
    return out


def verdict(agg, th=THRESHOLDS):
    """Pre-registered rule (PROTOCOL.md section 5)."""
    c = agg["contrasts"]
    delta = {d: 0.5 * c["raw2-raw"][d]["estimate"] for d in ("D1", "D2")}
    headroom = {d: c["raw2-raw"][d]["ci95"][0] > 0 for d in ("D1", "D2")}
    tests = dict(H1=("ht-raw", "D2"), H2=("ht-rsd", "D2"), H3=("ht-raw", "D1"))
    p = {h: c[k][d]["p_one_sided"] for h, (k, d) in tests.items()}
    order = sorted(p, key=p.get)
    holm, run = {}, 0.0
    for i, h in enumerate(order):
        run = max(run, min(1.0, (len(order) - i) * p[h]))
        holm[h] = run
    lab = {}
    for h, (k, d) in tests.items():
        est = c[k][d]["estimate"]
        if not headroom[d]:
            lab[h] = "UNINFORMATIVE_NO_HEADROOM"
        elif h == "H2":
            lab[h] = "SUPPORTED" if holm[h] < th["alpha_holm"] else "NOT_SUPPORTED"
        elif holm[h] < th["alpha_holm"] and est >= delta[d]:
            lab[h] = "SUPPORTED"
        elif holm[h] < th["alpha_holm"]:
            lab[h] = "SIGNIFICANT_BELOW_PRACTICAL"
        else:
            lab[h] = "NOT_SUPPORTED"
    ni_margin = 0.5 * delta["D1"]
    ni = c["ht-rsd"]["D1"]["ci95"][0] > -ni_margin
    cs = agg["calibration"]["ht"]["coverage_selected"]["estimate"]
    ca = agg["calibration"]["ht"]["coverage_all"]["estimate"]
    op = agg["selected_optimism_D2"]["ht"]["optimism"]
    crit = dict(C1_coverage_selected=bool(th["coverage_selected_band"][0] <= cs <= th["coverage_selected_band"][1]),
                C2_coverage_all=bool(th["coverage_all_band"][0] <= ca <= th["coverage_all_band"][1]),
                C3_optimism=bool(abs(op) <= th["optimism_abs_max"]), NI_D1_vs_rsd=bool(ni))
    d2_fixed = lab["H1"] == "SUPPORTED" and lab["H2"] == "SUPPORTED"
    d1_kept = lab["H3"] == "SUPPORTED" and crit["NI_D1_vs_rsd"]
    if d2_fixed and d1_kept and crit["C1_coverage_selected"]:
        overall = "ADVANCE_TO_INDEPENDENT_TEST"
    elif lab["H2"] != "SUPPORTED":
        overall = "HEAVY_TAIL_DOES_NOT_FIX_D2"
    else:
        overall = "PARTIAL"
    failed = [h for h in ("H1", "H2", "H3") if lab[h] != "SUPPORTED"] + [k for k, v in crit.items() if not v]
    return dict(delta=delta, headroom_lower_bound_positive=headroom, ni_margin=ni_margin,
                hypotheses={h: dict(contrast=k, decision=d, estimate=c[k][d]["estimate"], ci95=c[k][d]["ci95"],
                                    p_one_sided=p[h], p_holm=holm[h], label=lab[h]) for h, (k, d) in tests.items()},
                criteria=crit, values=dict(coverage_selected=cs, coverage_all=ca, optimism=op,
                                           ht_minus_rsd_D1_ci95=c["ht-rsd"]["D1"]["ci95"]),
                overall=overall, not_met=failed)


# ----------------------------------------------------------------------------- stages
def write_once(path, obj):
    if path.exists():
        raise SystemExit(f"refusing to overwrite {path.name}")
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, default=float), encoding="utf-8", newline="\n")


def code_hashes():
    return {f: D.sha256_text(HERE / f) for f in ("ht_core.py", "ht_data.py", "ht_run.py")}


def stage_dev(tag, blk):
    path = HERE / "dev" / f"{tag}_2p5uM_{blk}.json"
    if path.exists():
        raise SystemExit(f"{path.name} exists (write-once)")
    hashes = code_hashes()                                         # hashes of the code as launched
    rec = run_block(blk, HD.DEV_DOSE)
    write_once(path, dict(note="DEVELOPMENT (2.5 uM, exposed by the RSD study); not evidence", code_sha256=hashes, record=rec))


def stage_dev_pool(tag):
    path = HERE / "dev" / f"{tag}_2p5uM_pooled.json"
    if path.exists():
        raise SystemExit(f"{path.name} exists (write-once)")
    recs = [json.loads((HERE / "dev" / f"{tag}_2p5uM_{b}.json").read_text(encoding="utf-8"))["record"] for b in BLOCKS
            if (HERE / "dev" / f"{tag}_2p5uM_{b}.json").exists()]
    agg = pool(recs)
    write_once(path, dict(note="DEVELOPMENT (2.5 uM, exposed by the RSD study); rule applied for illustration only",
                          blocks=[r["block"] for r in recs], aggregate=agg, rule=verdict(agg)))


def frozen():
    fz = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    for rel, h in fz["sha256_text"].items():
        if D.sha256_text(HERE / rel) != h:
            raise SystemExit(f"FREEZE mismatch: {rel}")
    for rel, h in fz["rsd_frozen_sha256_text"].items():
        if D.sha256_text(HD.RSD / rel) != h:
            raise SystemExit(f"frozen RSD file changed: {rel}")
    for rel, h in fz["data_sha256"].items():
        if D.sha256(D.ROOT / rel) != h:
            raise SystemExit(f"FREEZE data mismatch: {rel}")
    return fz


def stage_evaluation():
    fz = frozen()
    path = HERE / "RESULT.json"
    if path.exists():
        raise SystemExit("RESULT.json exists (write-once)")
    t0 = time.time()
    started = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    hashes = code_hashes()
    recs = []
    for dose in HD.TEST_DOSES:
        for blk in BLOCKS:
            recs.append(run_block(blk, dose))
            print(f"done dose {dose} block {blk} ({recs[-1]['seconds']} s)", flush=True)
    agg = pool(recs, fz["n_boot"], fz["seed"])
    per_dose = {str(d): pool([r for r in recs if r["dose"] == d], fz["n_boot"], fz["seed"]) for d in HD.TEST_DOSES}
    out = dict(note="Development-grade: same PRISM 19Q4 compounds as the RSD study (exposed), doses 0.625 and 10 uM opened "
                    "once by this stage after FREEZE.json", frozen_utc=fz["frozen_utc"], started_utc=started,
               code_sha256=hashes,
               records=recs, aggregate=agg, per_dose=per_dose, verdict=verdict(agg, fz["thresholds"]),
               seconds=round(time.time() - t0, 1))
    write_once(path, out)
    print(json.dumps(out["verdict"], indent=1))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "dev":
        stage_dev(sys.argv[2], sys.argv[3])
    elif cmd == "dev_pool":
        stage_dev_pool(sys.argv[2])
    elif cmd == "evaluation":
        stage_evaluation()
    else:
        raise SystemExit(f"unknown stage {cmd}")
