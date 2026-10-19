"""EXPLORATORY (post hoc, after EVALUATION.json): why does the posterior help context selection (D1) but not progression (D2)?

Not part of the frozen protocol; cannot change any verdict. Reads the already-opened evaluation block and its references.
Writes DIAGNOSTIC_D2.json (write-once).

1. Geometry transfer vs model class: the same posterior with its geometry fitted on the evaluation block itself
   (two-fold cross-fit over evaluation clusters, using the other half's reads B and T), graded on the held-out half.
   If this also fails on D2, the reference-to-new-class transfer of geometry is not the bottleneck.
2. Noise shape: excess kurtosis of the replicate difference (B - T)/sqrt(2) of the references, and the share of D2-selected
   raw pairs whose screening-read error |s_A - s_T| exceeds 3 noise SD (heavy tails dominate the extreme pairs D2 picks).
3. Per-compound vs per-pair error: share of the D2-selected raw pairs' error explained by a compound-level offset
   (mean over the compound's lines of s_A - s_T), which a per-compound line covariance cannot remove.
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rsd_core as C  # noqa: E402
import rsd_run as R  # noqa: E402

out_path = HERE / "DIAGNOSTIC_D2.json"
if out_path.exists():
    raise SystemExit("DIAGNOSTIC_D2.json exists (write-once)")
ev_rec = json.loads((HERE / "EVALUATION.json").read_text(encoding="utf-8"))
cfg = ev_rec["cfg"]
S = R.setup("evaluation")
q, ref = S["q"], S["ref"]
A = S["A"][q]
vc0 = R.build_vc(S, cfg)
ev = C.Evaluator(S["T"][q], S["P"][q], vc0.g, S["t"].cluster.to_numpy()[q])
raw = C.raw_score(A, vc0.g)
res = dict(note="EXPLORATORY post hoc diagnosis on the opened evaluation block; not a test of any hypothesis", cfg=cfg)


def utilities(score):
    return dict(D1=float(np.nanmean(ev.d1(C.d1_choose(score))["util"])), D2=float(np.nanmean(ev.d2_pairs(C.d2_choose(score))[2])))


def contrast(score):
    a, b = utilities(score), utilities(raw)
    return {d: a[d] - b[d] for d in ("D1", "D2")}


# 1. geometry fitted on the evaluation block itself (two-fold cross-fit over clusters); D2 graded within each half
cl = S["t"].cluster.to_numpy()[q]
u = np.unique(cl)
rng = np.random.default_rng(20261019)
half = set(rng.permutation(u)[: len(u) // 2])
fold = np.array([c in half for c in cl])
geo = {}
for qq in (2, 10, 40):
    m_ref = np.full_like(raw, np.nan)
    m_own = np.full_like(raw, np.nan)
    vc_r = R.build_vc(S, dict(cfg, q=qq), use_prior=False)
    for f in (True, False):
        test, train = np.where(fold == f)[0], np.where(fold != f)[0]
        vc_own = R.build_vc(dict(S, ref=q[train]), dict(cfg, q=qq), use_prior=False)
        tier = C.tier_of(A[test])
        m_own[test] = vc_own.posterior(np.zeros((len(test), A.shape[1])), A[test], np.ones(len(test)), tier)[0]
        m_ref[test] = vc_r.posterior(np.zeros((len(test), A.shape[1])), A[test], np.ones(len(test)), tier)[0]
    row = {}
    for name, m in (("reference_geometry", m_ref), ("own_block_geometry", m_own)):
        d = {}
        for f in (True, False):
            idx = np.where(fold == f)[0]
            sc_m, sc_r, sT = m[idx], raw[idx], ev._sT[idx]
            d1 = np.nanmean(np.take_along_axis(sT, C.d1_choose(sc_m), 1)) - np.nanmean(np.take_along_axis(sT, C.d1_choose(sc_r), 1))
            d2 = C._u2(sc_m, sT) - C._u2(sc_r, sT)
            d[str(f)] = dict(D1=float(-d1), D2=float(d2))
        row[name] = dict(D1=float(np.mean([d[k]["D1"] for k in d])), D2=float(np.mean([d[k]["D2"] for k in d])), by_half=d)
    geo[f"q={qq}"] = row
res["geometry_transfer_vs_model_class"] = geo

# 2. noise shape
sB, sT_ref = C.selective(S["B"][ref], vc0.g), C.selective(S["T"][ref], vc0.g)
D = ((sB - sT_ref) / np.sqrt(2)).ravel()
D = D[np.isfinite(D)]
z = (D - D.mean()) / D.std()
res["noise_shape_reference"] = dict(n=int(D.size), excess_kurtosis=float(np.mean(z ** 4) - 3), share_abs_z_gt3=float(np.mean(np.abs(z) > 3)),
                                    gaussian_share_abs_z_gt3=0.0027)
sA = C.selective(A, vc0.g)
err = sA - ev._sT
ch = C.d2_choose(raw)
L = raw.shape[1]
li = np.tile(np.arange(L), (ch.shape[0], 1))
e_sel = err[ch, li].ravel()
e_sel = e_sel[np.isfinite(e_sel)]
e_all = err[np.isfinite(err)]
res["d2_selected_raw_pairs"] = dict(n=int(e_sel.size), mean_error=float(e_sel.mean()), sd_error=float(e_sel.std()),
                                    all_pairs_sd_error=float(e_all.std()), share_error_gt_3sd=float(np.mean(np.abs(e_sel) > 3 * e_all.std())),
                                    all_pairs_share_error_gt_3sd=float(np.mean(np.abs(e_all) > 3 * e_all.std())))
# 3. compound-level offset share of the selected pairs' error
off = np.nanmean(err, axis=1)                                 # compound offset of the selective read error
o_sel = off[ch].ravel()
ok = np.isfinite(err[ch, li].ravel()) & np.isfinite(o_sel)
es, os_ = err[ch, li].ravel()[ok], o_sel[ok]
res["d2_error_decomposition"] = dict(mean_error_selected=float(es.mean()), mean_compound_offset_selected=float(os_.mean()),
                                     share_of_mean_error_from_compound_offset=float(os_.mean() / es.mean()))
# per-compound activity of D2 choices: how concentrated are D2 picks on few compounds?
cnt = np.bincount(ch.ravel(), minlength=len(q))
res["d2_pick_concentration"] = dict(top10_compounds_share_of_picks=float(np.sort(cnt)[::-1][:10].sum() / cnt.sum()),
                                    compounds_ever_picked=int((cnt > 0).sum()), n_compounds=int(len(q)))
out_path.write_text(json.dumps(res, indent=1), encoding="utf-8", newline="\n")
print(json.dumps(res, indent=1))
