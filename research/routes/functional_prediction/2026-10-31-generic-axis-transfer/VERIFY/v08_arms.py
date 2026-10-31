"""Check 2: re-implement arms from PROTOCOL section 5 and compare per-compound predictions with the saved ones.

Required: B0 and C1 on confirmation 1 (NCI-60, 10 folds). Extra (cheap): B1, B2 and an attempt at L on NCI-60;
B0, B1, B2, C1 and an attempt at L on confirmation 2 (PRISM 24Q2, development-pool references).
Inputs: verifier-derived profiles/folds (derived_*.npz), signatures from l1000_*.npz, fingerprints and the
development pool from the frozen npz files. Writes check2_arms.json and pred_verifier_*.npz.
"""
import json
import sys
import time

import numpy as np

VER = "D:/MAESTRO/research/routes/functional_prediction/2026-10-31-generic-axis-transfer/VERIFY/"
sys.path.insert(0, VER)
import vlib  # noqa: E402

STUDY = VER[: -len("VERIFY/")]
PROC = "D:/MAESTRO/data/processed/generic_axis_transfer_20261031/"
D_, K_, SEED = 5, 20, 20261031


def compare(mine, saved):
    nan_eq = bool(np.array_equal(np.isfinite(mine), np.isfinite(saved)))
    both = np.isfinite(mine) & np.isfinite(saved)
    d = float(np.max(np.abs(mine[both] - saved[both]))) if both.any() else float("nan")
    per_row = np.where(both, np.abs(mine - saved), 0).max(axis=1)
    return {"nan_pattern_equal": nan_eq, "max_abs_diff": d, "n_rows_over_1e-6": int((per_row > 1e-6).sum()),
            "n_cells_nan_mismatch": int((np.isfinite(mine) != np.isfinite(saved)).sum())}


def predict_set(qsig, qfp, Rsig, Rfp, Y, centre_query=True, perms=None):
    """Predictions of every arm for queries against one reference set."""
    n = len(qsig)
    out = {a: np.full((n, Y.shape[1]), np.nan) for a in ("B0", "B1", "B2", "C1")}
    ar = vlib.AxisRemoval(Rsig, D_, centre_query=centre_query)
    Rt = ar.transform(Rsig)
    Qt = ar.transform(qsig)
    simC1 = []
    order_info = {"B0_kth_gap_min": np.inf, "C1_kth_gap_min": np.inf}
    for i in range(n):
        s_raw = vlib.mean_cosine(qsig[i], Rsig)
        out["B0"][i] = vlib.weighted_prediction(s_raw, Y, 5)[0]
        out["B1"][i] = vlib.weighted_prediction(s_raw, Y, K_)[0]
        s_c1 = vlib.mean_cosine(Qt[i], Rt)
        simC1.append(s_c1)
        out["C1"][i] = vlib.weighted_prediction(s_c1, Y, K_)[0]
        out["B2"][i] = vlib.weighted_prediction(vlib.tanimoto(qfp[i], Rfp), Y, K_)[0]
        # margin between the k-th and (k+1)-th similarity (how fragile the neighbour set is)
        for name, s, k in (("B0_kth_gap_min", s_raw, 5), ("C1_kth_gap_min", s_c1, K_)):
            ss = np.sort(s[np.isfinite(s)])[::-1]
            if len(ss) > k:
                order_info[name] = min(order_info[name], float(ss[k - 1] - ss[k]))
    L = {}
    if perms is not None:
        for name, perm in perms.items():
            Yp = Y[perm]
            L[name] = np.vstack([vlib.weighted_prediction(simC1[i], Yp, K_)[0] for i in range(n)])
    return out, L, order_info


def main():
    t0 = time.time()
    res = {}
    # ------------------------------------------------------------------ confirmation 1: NCI-60
    Dn = np.load(VER + "derived_nci.npz")
    keys = [str(k) for k in Dn["key"]]
    obs, fold = Dn["observed"], Dn["fold"]
    L1 = np.load(PROC + "l1000_nci.npz", allow_pickle=True)
    lkey = [str(k) for k in L1["key"]]
    sig = L1["x"][[lkey.index(k) for k in keys]].astype(np.float64)
    fp = np.load(PROC + "nci60.npz")["fingerprint"]
    S = np.load(STUDY + "RUN/predictions_nci60.npz")
    assert [str(k) for k in S["key"]] == keys
    pred = {a: np.full_like(obs, np.nan) for a in ("B0", "B1", "B2", "C1")}
    pred_nc = {a: np.full_like(obs, np.nan) for a in ("C1",)}
    Lvar_names = ["global_rng_permutation_per_fold", "fresh_rng_per_fold", "rng_seed_plus_fold", "randomstate_global",
                  "randomstate_fresh_per_fold"]
    predL = {v: np.full_like(obs, np.nan) for v in Lvar_names}
    g_rng = np.random.default_rng(SEED)
    g_rs = np.random.RandomState(SEED)
    gaps = {"B0_kth_gap_min": np.inf, "C1_kth_gap_min": np.inf}
    for f in range(10):
        q = np.flatnonzero(fold == f)
        r = np.flatnonzero(fold != f)
        nr = len(r)
        perms = {"global_rng_permutation_per_fold": g_rng.permutation(nr),
                 "fresh_rng_per_fold": np.random.default_rng(SEED).permutation(nr),
                 "rng_seed_plus_fold": np.random.default_rng(SEED + f).permutation(nr),
                 "randomstate_global": g_rs.permutation(nr),
                 "randomstate_fresh_per_fold": np.random.RandomState(SEED).permutation(nr)}
        out, L, gi = predict_set(sig[q], fp[q], sig[r], fp[r], obs[r], perms=perms)
        for a in pred:
            pred[a][q] = out[a]
        for v in Lvar_names:
            predL[v][q] = L[v]
        for k in gaps:
            gaps[k] = min(gaps[k], gi[k])
        out_nc, _, _ = predict_set(sig[q], fp[q], sig[r], fp[r], obs[r], centre_query=False)
        pred_nc["C1"][q] = out_nc["C1"]
    nci = {a: compare(pred[a], S[f"pred_{a}"]) for a in pred}
    nci["C1_alt_query_not_centred"] = compare(pred_nc["C1"], S["pred_C1"])
    nci["L_variants"] = {v: compare(predL[v], S["pred_L"]) for v in Lvar_names}
    nci["min_gap_kth_vs_next_similarity"] = gaps
    res["nci60"] = nci
    np.savez(VER + "pred_verifier_nci60.npz", key=np.array(keys), **{f"pred_{a}": pred[a] for a in pred})
    print("NCI-60 done", round(time.time() - t0, 1), "s", flush=True)

    # ------------------------------------------------------------------ confirmation 2: PRISM 24Q2 (extra)
    Dp = np.load(VER + "derived_prism.npz")
    pkeys = [str(k) for k in Dp["key"]]
    lines = [str(s) for s in Dp["line"]]
    L2 = np.load(PROC + "l1000_24q2.npz", allow_pickle=True)
    l2key = [str(k) for k in L2["key"]]
    qsig = L2["x"][[l2key.index(k) for k in pkeys]].astype(np.float64)
    qfp = np.load(PROC + "prism24q2.npz")["fingerprint"]
    dev = np.load(PROC + "dev_pool.npz")
    dlines = [str(s) for s in dev["line"]]
    Y = dev["profile"][:, [dlines.index(s) for s in lines]]
    Rsig = dev["signature"].astype(np.float64)
    Rfp = dev["fingerprint"]
    S2 = np.load(STUDY + "RUN/predictions_prism24q2.npz")
    nr = len(Y)
    perms = {"default_rng": np.random.default_rng(SEED).permutation(nr),
             "randomstate": np.random.RandomState(SEED).permutation(nr)}
    out, L, gi = predict_set(qsig, qfp, Rsig, Rfp, Y, perms=perms)
    pr = {a: compare(out[a], S2[f"pred_{a}"]) for a in out}
    pr["L_variants"] = {v: compare(L[v], S2["pred_L"]) for v in L}
    pr["min_gap_kth_vs_next_similarity"] = gi
    res["prism24q2"] = pr
    np.savez(VER + "pred_verifier_prism24q2.npz", key=np.array(pkeys), **{f"pred_{a}": out[a] for a in out})
    print("PRISM done", round(time.time() - t0, 1), "s", flush=True)
    json.dump(res, open(VER + "check2_arms.json", "w", encoding="utf-8", newline="\n"), indent=1, default=float)
    print(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main()
