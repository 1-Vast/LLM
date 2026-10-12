"""Development step 2: pooled predictor and certificates, nested over the five phase-1 folds.

Outer fold f: meta-models are fitted on the queries of the other folds (their pooled-model inputs
come from an inner out-of-fold pass) and applied to fold f. Reports, on active queries:
* specific cosine (generic direction removed) and centred cosine of the pooled prediction against
  each single route, a fixed route priority and the generic baseline;
* activity AUROC;
* certificate calibration (Spearman of expected vs realised specific cosine) and selective risk
  against two conventional uncertainty scores (applicability distance and route dispersion).
"""
from __future__ import annotations

import json

import numpy as np
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score

import rkt
from dev_common import CACHE, load_phase1, vehicle_thresholds
from pool import SPECIFIC_ROUTES, Pooler, perp, route_features


def own_activity(z_routes, Y, thr):
    """Activity of the query compound in its visible other lines (zeros in regime B)."""
    comp, line, reg = z_routes["comp"], z_routes["line"], z_routes["regime"]
    norms = np.linalg.norm(np.nan_to_num(Y), axis=2) / thr[None]
    measured = np.isfinite(Y[..., 0])
    out = np.zeros((len(comp), 3))
    for i, (c, T, R) in enumerate(zip(comp, line, reg)):
        if R != "A":
            continue
        m = measured[c].copy(); m[T] = False
        if m.any():
            v = norms[c, m]
            out[i] = [(v > 1).sum(), v.max(), v.mean()]
    return out


def aurc(conf, loss):
    order = np.argsort(-conf)
    cum = np.cumsum(loss[order]) / np.arange(1, len(loss) + 1)
    return float(cum.mean())


def main():
    zz = load_phase1()
    Y = zz["cp"].astype(np.float64)
    thr = vehicle_thresholds(zz)
    z = dict(np.load(CACHE / "dev_routes.npz"))
    G = rkt.unit_rows(np.load(CACHE / "dev_generic.npy").astype(np.float64))
    truth = z["truth"].astype(np.float64)
    tperp = perp(truth, G)
    act = z["active"]
    n_lines = Y.shape[1]
    oa = own_activity(z, Y, thr)
    av = {r: z[f"av_{r}"] for r in SPECIFIC_ROUTES}
    sup = {r: z[f"sup_{r}"] for r in SPECIFIC_ROUTES}
    preds = {r: z[f"pred_{r}"].astype(np.float64) for r in SPECIFIC_ROUTES}
    F = route_features(sup, av, None, z["line"], n_lines, oa)
    spec = {r: np.where(av[r], rkt.centred_cosine(perp(preds[r], G), tperp), np.nan) for r in SPECIFIC_ROUTES}
    folds = z["fold"]
    n = len(truth)
    out_s = np.zeros((n, truth.shape[1])); out_rho = np.zeros(n); out_p = np.zeros(n); out_ref = np.empty(n, "<U40")
    out_rho_r = {r: np.zeros(n) for r in SPECIFIC_ROUTES}; out_agree = np.zeros(n); gammas = []
    for f in range(5):
        tr, te = folds != f, folds == f
        gamma = float(np.mean(rkt.centred_cosine(G[tr & act], truth[tr & act])))
        gammas.append(gamma)
        # inner out-of-fold pooled inputs for the pooled meta-model
        P_in = np.full(n, np.nan); agree_in = np.zeros(n); rho_in = {r: np.zeros(n) for r in SPECIFIC_ROUTES}
        for g in set(range(5)) - {f}:
            itr, ite = tr & (folds != g), folds == g
            sub = {r: v[itr] for r, v in av.items()}
            pm = Pooler(gamma).fit(F[itr], sub, {r: v[itr] for r, v in spec.items()}, act[itr],
                                   (np.zeros(itr.sum()), np.zeros(itr.sum()), {r: np.zeros(itr.sum()) for r in SPECIFIC_ROUTES}))
            s, rr, w, ag = pm.combine({r: v[ite] for r, v in preds.items()}, G[ite], F[ite], {r: v[ite] for r, v in av.items()})
            P_in[ite] = rkt.centred_cosine(s, tperp[ite]); agree_in[ite] = ag
            for r in SPECIFIC_ROUTES:
                rho_in[r][ite] = rr[r]
        pm = Pooler(gamma).fit(F[tr], {r: v[tr] for r, v in av.items()}, {r: v[tr] for r, v in spec.items()}, act[tr],
                               (P_in[tr], agree_in[tr], {r: v[tr] for r, v in rho_in.items()}))
        s, cert = pm.certify({r: v[te] for r, v in preds.items()}, G[te], F[te], {r: v[te] for r, v in av.items()})
        out_s[te] = s; out_rho[te] = cert.rho; out_p[te] = cert.p_active; out_ref[te] = cert.refusal; out_agree[te] = cert.agreement
        for r in SPECIFIC_ROUTES:
            out_rho_r[r][te] = cert.rho_route[r]
    gamma = float(np.mean(gammas))
    res = {"gamma_mean": round(gamma, 4)}
    pooled_spec = rkt.centred_cosine(out_s, tperp)
    final = rkt.unit_rows(gamma * G + (np.where(out_ref == "", out_rho, 0.0) * np.sqrt(1 - gamma ** 2))[:, None] * out_s)
    pooled_cc = rkt.centred_cosine(final, truth)
    priority = np.zeros_like(truth); have = np.zeros(n, bool)
    for r in SPECIFIC_ROUTES:
        take = av[r] & ~have
        priority[take] = preds[r][take]; have |= take
    for reg in ("A", "B"):
        m = (z["regime"] == reg) & act
        block = {"n_active": int(m.sum())}
        block["pooled_specific"] = round(float(pooled_spec[m].mean()), 4)
        block["priority_specific"] = round(float(rkt.centred_cosine(perp(priority[m], G[m]), tperp[m]).mean()), 4)
        for r in SPECIFIC_ROUTES:
            mm = m & av[r]
            if mm.any():
                block[f"{r}_specific_on_its_queries"] = round(float(np.nanmean(spec[r][mm])), 4)
                block[f"pooled_specific_on_{r}_queries"] = round(float(pooled_spec[mm].mean()), 4)
        block["pooled_centred"] = round(float(pooled_cc[m].mean()), 4)
        block["generic_centred"] = round(float(rkt.centred_cosine(G[m], truth[m]).mean()), 4)
        block["refused_specific_fraction"] = round(float((out_ref[m] != "").mean()), 4)
        mr = (z["regime"] == reg)
        block["activity_auroc_pooled"] = round(float(roc_auc_score(act[mr], out_p[mr])), 4)
        # certificate calibration on actives with a pooled direction
        ok = m & (out_ref != "NO_TRANSFER_ROUTE")
        block["cert_spearman"] = round(float(spearmanr(out_rho[ok], pooled_spec[ok]).statistic), 4)
        top_sim = np.max(np.stack([np.where(av[r], sup[r][:, 0] if r != "context" else sup[r][:, 1], 0) for r in SPECIFIC_ROUTES], 1), 1)
        disp = out_agree
        loss = 1 - pooled_spec[ok]
        block["aurc_certificate"] = round(aurc(out_rho[ok], loss), 4)
        block["aurc_applicability"] = round(aurc(top_sim[ok], loss), 4)
        block["aurc_route_agreement"] = round(aurc(disp[ok], loss), 4)
        block["aurc_random"] = round(float(loss.mean()), 4)
        block["aurc_oracle"] = round(aurc(-loss, loss), 4)
        res[reg] = block
    print(json.dumps(res, indent=1))
    (CACHE / "dev_pool_summary.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    np.savez_compressed(CACHE / "dev_pool.npz", s=out_s.astype(np.float16), rho=out_rho, p_active=out_p, refusal=out_ref,
                        agree=out_agree, **{f"rho_{r}": v for r, v in out_rho_r.items()})


if __name__ == "__main__":
    main()
