"""DEVELOPMENT diagnostic on 2.5 uM REFERENCE compounds only (exposed): where do the heavy tails of the replicate noise
come from? Writes dev/noise_anatomy.json (write-once).

1. Standardised replicate differences z_ij = (s_B - s_T)/sqrt(2)/sqrt(beta_k n0_j) (frozen line and tier scales).
2. Per compound: mean of z^2 over its lines (its relative noise variance). Dispersion of these values against the
   chi-square sampling spread expected under homogeneous Gaussian noise.
3. Kurtosis of z after dividing each compound's row by its own RMS (removes compound-level scale): what remains is
   pair-level tail.
4. Per-read noise variances from the three reads: Var(A-B) = vA + vB etc. solved per compound; correlation of the
   per-read variances across a compound's reads (is noisiness compound-intrinsic or read-specific?).
5. Compound-level Student-t (one lambda per read, shared across lines) vs pair-level Student-t: ML fit of both to z.
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

path = HERE / "dev" / "noise_anatomy_v2.json"   # v1 (noise_anatomy.json): NaN summaries, see DEVELOPMENT_LOG
if path.exists():
    raise SystemExit(f"{path.name} exists (write-once)")
S = HD.setup("evaluation", HD.DEV_DOSE)
vc = H.build_factor_vc(S, 2, False)
ref = S["ref"]
n0 = vc.noise_diag()
tier = C.tier_of(S["A"][ref])
sd = np.sqrt(vc.beta[tier][:, None] * n0[None, :])
sA, sB, sT = (C.selective(X[ref], vc.g) for X in (S["A"], S["B"], S["T"]))
Z = (sB - sT) / np.sqrt(2) / sd
full = (np.isfinite(Z).sum(1) >= 100) & (np.isfinite(sA).sum(1) >= 100)
res0 = dict(n_reference=int(len(ref)), n_dropped_fewer_than_100_lines=int((~full).sum()))
Z, sA, sB, sT, sd, tier = Z[full], sA[full], sB[full], sT[full], sd[full], tier[full]
ok = np.isfinite(Z)
n_i = ok.sum(1)
ms = np.nansum(Z ** 2, 1) / n_i
res = dict(res0, n_compounds=int(len(n_i)), lines_per_compound_median=float(np.median(n_i)))
zz = Z[ok]
zs = (zz - zz.mean()) / zz.std()
res["pair_z"] = dict(excess_kurtosis=float(np.mean(zs ** 4) - 3), share_abs_gt3=float(np.mean(np.abs(zs) > 3)))
# 2. compound-level variance dispersion: under homogeneous Gaussian noise, var(ms) ~ 2/n
res["compound_mean_z2"] = dict(sd=float(np.std(ms)), expected_sd_homogeneous=float(np.sqrt(np.mean(2.0 / n_i))),
                               quantiles={str(p): float(np.quantile(ms, p)) for p in (0.05, 0.25, 0.5, 0.75, 0.95, 0.99)},
                               by_tier={str(k): float(np.mean(ms[tier == k])) for k in range(3)})
# 3. pair-level tail after removing compound scale
Zr = Z / np.sqrt(ms)[:, None]
zr = Zr[ok]
zr = (zr - zr.mean()) / zr.std()
res["after_compound_scale"] = dict(excess_kurtosis=float(np.mean(zr ** 4) - 3), share_abs_gt3=float(np.mean(np.abs(zr) > 3)))
# 4. per-read variances
def mv(X, Y):
    D = (X - Y) / sd
    return np.nanmean(D ** 2, 1)
ab, at, bt = mv(sA, sB), mv(sA, sT), mv(sB, sT)
vA, vB, vT = (ab + at - bt) / 2, (ab + bt - at) / 2, (at + bt - ab) / 2
V = np.stack([vA, vB, vT], 1)
lv = np.log(np.clip(V, 1e-3, None))
cors = [float(np.corrcoef(lv[:, i], lv[:, j])[0, 1]) for i, j in ((0, 1), (0, 2), (1, 2))]
res["per_read_variance"] = dict(log_var_correlation_between_reads=cors, mean=V.mean(0).tolist(),
                                share_negative=float(np.mean(V < 0)), cv=float(np.std(V) / np.mean(V)))
# 5. compound-level vs pair-level Student-t, ML on z
def compound_ll(nu, s):
    c, w = H.diff_mixture(nu)
    ss = np.nansum(Z ** 2, 1)
    lp = (np.log(w)[None, :] - 0.5 * ss[:, None] / (s * s * c[None, :])
          - 0.5 * n_i[:, None] * np.log(2 * np.pi * s * s * c[None, :]))
    m = lp.max(1, keepdims=True)
    return float((m[:, 0] + np.log(np.exp(lp - m).sum(1))).sum() / n_i.sum())
from scipy.optimize import minimize_scalar  # noqa: E402
comp = {}
for nu in (2.0, 3.0, 5.0, 10.0, 20.0, 50.0, 100.0, 300.0):
    r = minimize_scalar(lambda ls: -compound_ll(nu, np.exp(ls)), bounds=(np.log(0.2), np.log(3)), method="bounded")
    comp[str(nu)] = dict(s=float(np.exp(r.x)), ll=float(-r.fun))
pair = H.fit_tail(Z.ravel())
res["fit"] = dict(compound_level_t=comp, pair_level_t=dict(nu_ml=pair["nu_ml"], ll=pair["profile"][pair["nu_ml"]]["ll"]),
                  gaussian_ll=pair["gauss"]["ll"])
path.parent.mkdir(exist_ok=True)
path.write_text(json.dumps(dict(note="DEVELOPMENT diagnostic, 2.5 uM evaluation-block references (exposed)", results=res),
                           indent=1), encoding="utf-8", newline="\n")
print(json.dumps(res, indent=1))
