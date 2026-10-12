"""Development step 4: nested certificates on the confirmation-like route table (phase-1 tier).

Outer fold f: a Pooler fitted (``pool.fit_nested``) on the other folds' queries of all three
regimes is applied to fold f. Reports per regime, on active queries: pooled specific and centred
cosine against the generic baseline and single routes; activity AUROC; certificate calibration
and selective risk against applicability distance and route agreement.
"""
import json
import numpy as np
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score
import rkt
from dev_common import CACHE
from pool import SPECIFIC_ROUTES, fit_nested, perp
from dev_pool import aurc

z = dict(np.load(CACHE / "dev2_routes.npz"))
G = z["G_table"][z["fold"], z["line"]].astype(np.float64)
truth = z["truth"].astype(np.float64); act = z["active"]; F = z["F"].astype(np.float64)
preds = {r: z[f"pred_{r}"].astype(np.float64) for r in SPECIFIC_ROUTES}
av = {r: z[f"av_{r}"] for r in SPECIFIC_ROUTES}
folds = z["fold"]; n = len(truth)
tperp = perp(truth, G)
out = {k: np.zeros(n) for k in ("rho", "p", "agree")}; out_s = np.zeros_like(truth); ref = np.empty(n, "<U40")
rho_r_out = {r: np.zeros(n) for r in SPECIFIC_ROUTES}
for f in range(5):
    tr, te = folds != f, folds == f
    gamma = float(z["gammas"][f])
    pm = fit_nested(F[tr], {r: v[tr] for r, v in av.items()}, {r: v[tr] for r, v in preds.items()}, G[tr], truth[tr],
                    act[tr], folds[tr], float(np.mean(z["gammas"][np.arange(5) != f])))
    s, cert = pm.certify({r: v[te] for r, v in preds.items()}, G[te], F[te], {r: v[te] for r, v in av.items()})
    out_s[te] = s; out["rho"][te] = cert.rho; out["p"][te] = cert.p_active; out["agree"][te] = cert.agreement; ref[te] = cert.refusal
    for r in SPECIFIC_ROUTES:
        rho_r_out[r][te] = cert.rho_route[r]
    print("fold", f, "done", flush=True)
gam = z["gammas"][folds]
rho_used = np.where(ref == "", out["rho"], 0.0)
final = rkt.unit_rows(gam[:, None] * G + (rho_used * np.sqrt(1 - gam ** 2))[:, None] * out_s)
pooled_cc = rkt.centred_cosine(final, truth); pooled_spec = rkt.centred_cosine(out_s, tperp)
expected = np.sqrt(gam ** 2 + rho_used ** 2 * (1 - gam ** 2))
res = {"gammas": z["gammas"].round(4).tolist()}
for reg in ("A", "A1", "B"):
    m = (z["regime"] == reg) & act; mr = z["regime"] == reg
    b = {"n_active": int(m.sum()), "pooled_centred": round(float(pooled_cc[m].mean()), 4),
         "expected_centred_mean": round(float(expected[m].mean()), 4),
         "generic_centred": round(float(rkt.centred_cosine(G[m], truth[m]).mean()), 4),
         "pooled_specific": round(float(pooled_spec[m].mean()), 4),
         "refusal_fraction": round(float((ref[m] != "").mean()), 4),
         "activity_auroc": round(float(roc_auc_score(act[mr], out["p"][mr])), 4)}
    for r in SPECIFIC_ROUTES:
        mm = m & av[r]
        if mm.any():
            b[f"{r}_centred"] = round(float(rkt.centred_cosine(preds[r][mm], truth[mm]).mean()), 4)
            b[f"{r}_specific"] = round(float(rkt.centred_cosine(perp(preds[r][mm], G[mm]), tperp[mm]).mean()), 4)
            b[f"{r}_coverage"] = round(float(mm.sum() / m.sum()), 4)
    ok = m & (ref != "NO_TRANSFER_ROUTE")
    b["cert_spearman_specific"] = round(float(spearmanr(out["rho"][ok], pooled_spec[ok]).statistic), 4)
    b["cert_spearman_centred"] = round(float(spearmanr(expected[m], pooled_cc[m]).statistic), 4)
    sims = []
    Fi = 0
    # applicability distance: max top-similarity over available analogue routes (pheno, chem, know)
    idx = {"context": 1, "pheno": 1 + 1 + 3, "chem": 1 + 1 + 3 + 1 + 5, "know": 1 + 1 + 3 + 1 + 5 + 1 + 5}
    top = np.max(np.stack([np.where(av[r], F[:, idx[r]], 0) for r in ("pheno", "chem", "know")], 1), 1)
    loss = 1 - pooled_cc[m]
    b["aurc_certificate"] = round(aurc(expected[m], loss), 4)
    b["aurc_applicability"] = round(aurc(top[m], loss), 4)
    b["aurc_random"] = round(float(loss.mean()), 4)
    b["aurc_oracle"] = round(aurc(-loss, loss), 4)
    res[reg] = b
print(json.dumps(res, indent=1))
(CACHE / "dev_pool2_summary.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
