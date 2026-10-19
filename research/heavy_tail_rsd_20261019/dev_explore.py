"""DEVELOPMENT exploration on the exposed 2.5 uM reads (not part of the frozen procedure; informs the design only).

python -B dev_explore.py <tag> [signal]   -> dev/explore_<tag>.json (write-once)
                                           (signal: candidates with Student-t line-specific signal, nu_s in {2, 4, 10})

Uses the Gaussian configuration each RSD block record already chose (SEARCH_v2 / SELECTION / EVALUATION.json) to skip the
slow Gaussian inner selection. For both noise-model levels (pair, compound) and every nu of the grid, plus the Gaussian:
the reference-only inner scores (the quantity the frozen procedure would select on) and point estimates on the block's
queries of D1 and D2 utility minus raw, D2-selected 80% coverage, all-pair coverage and selected-pair optimism.
Point estimates only; no bootstrap.
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ht_core as H  # noqa: E402
import ht_data as HD  # noqa: E402
import rsd_core as C  # noqa: E402

RSD_CFG = {"search": "SEARCH_v2.json", "selection": "SELECTION.json", "evaluation": "EVALUATION.json"}
LEVELS = ("pair", "compound")


def cfg_of(blk):
    r = json.loads((HD.RSD / RSD_CFG[blk]).read_text(encoding="utf-8"))
    return r.get("run", r)["cfg"]


def evaluate(fvc, mu, A, sT, tier, nu, s, level, nu_s=np.inf):
    p = H.ht_posterior(fvc, mu, A, tier, nu, s, level=level, nu_s=nu_s)
    m = p["mean"]
    raw = C.raw_score(A, fvc.g)
    L = sT.shape[1]
    ch = C.d2_choose(m)
    li = np.tile(np.arange(L), (ch.shape[0], 1))
    e = sT[ch, li] - m[ch, li]
    ok = np.isfinite(e)
    cov = float(np.mean(H.covered(e[ok], p["var"][ch, li][ok], p["pred_sig2"][ch, li][ok], p["pred_nu"])))
    okall = np.isfinite(sT)
    cov_all = float(np.mean(H.covered((sT - m)[okall], p["var"][okall], p["pred_sig2"][okall], p["pred_nu"])))
    opt = float(np.mean((-m[ch, li] + sT[ch, li])[ok]))
    return dict(D1=C._u1(m, sT) - C._u1(raw, sT), D2=C._u2(m, sT) - C._u2(raw, sT), cov_sel=cov, cov_all=cov_all,
                optimism=opt, iters=int(p["iters"]))


def main(tag):
    path = HERE / "dev" / f"explore_{tag}.json"
    if path.exists():
        raise SystemExit(f"{path.name} exists (write-once)")
    out = {}
    for blk in ("search", "selection", "evaluation"):
        cfg = cfg_of(blk)
        S = HD.setup(blk, HD.DEV_DOSE)
        q, ref = S["q"], S["ref"]
        fvc = H.build_factor_vc(S, cfg["q"], cfg["use_prior"])
        Z = H.standardized_differences(fvc, S["A"], S["B"], S["T"], ref, matrix=True)
        tails = dict(pair=H.fit_tail(Z.ravel()), compound=H.fit_tail_compound(Z))
        if "signal" in sys.argv[2:]:
            cands = H.candidates(("pair",), (4.0, 10.0, 20.0), (2.0, 4.0, 10.0)) + H.candidates(("compound",), (10.0,), (2.0, 4.0, 10.0))
        else:
            cands = H.candidates(LEVELS)
        best, inner = H.ht_inner_select(S, cfg["q"], cfg["use_prior"], cands)
        A = S["A"][q]
        tier = C.tier_of(A)
        sT = C.selective(S["T"][q], fvc.g)
        mu = fvc.prior(q, np.arange(len(ref)))
        rows = {H.cand_key(("gauss", np.inf, np.inf)): evaluate(fvc, mu, A, sT, tier, np.inf, 1.0, "pair")}
        for c in cands:
            rows[H.cand_key(c)] = evaluate(fvc, mu, A, sT, tier, c[1], tails[c[0]]["profile"][c[1]]["s"], c[0], c[2])
        out[blk] = dict(cfg=cfg, inner_best=best, inner_score=inner["score"],
                        tails={lv: dict(nu_ml=t["nu_ml"], s_ml=t["s_ml"], ll={str(k): v["ll"] for k, v in t["profile"].items()
                                                                              if k in H.NU_GRID or k == t["nu_ml"]})
                               for lv, t in tails.items()},
                        gauss_ll=tails["pair"]["gauss"]["ll"], rows=rows)
        print(blk, cfg, "inner best", best, flush=True)
        for k, r in rows.items():
            print(f"  {k:34s} inner {inner['score'].get(k, float('nan')):+.4f} | D1 {r['D1']:+.3f} D2 {r['D2']:+.3f} "
                  f"cov_sel {r['cov_sel']:.3f} cov_all {r['cov_all']:.3f} opt {r['optimism']:+.3f}", flush=True)
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(dict(note="DEVELOPMENT exploration, 2.5 uM (exposed); point estimates", results=out), indent=1,
                               default=float), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main(sys.argv[1])
