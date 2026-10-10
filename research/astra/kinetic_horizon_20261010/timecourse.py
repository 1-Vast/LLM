"""Pool D (MIX-Seq trametinib 0.1 uM time course, 24 lines, 3/6/12/24/48 h, DMSO hash at every
time): when to observe, the temporal fingerprint of STATE's 24 h forecast, and the kinetic readout
as a rate.  Runs only after FREEZE.json (the Tram_* hashes are sealed).

Per line L and time t, on the v1 projection of the 1,905 axis genes present in MIX-Seq:
* O_L(t)  = mean treated - mean DMSO of the same time hash;
* A_L(t)  = log2 share of L among treated cells of the hash minus log2 share among DMSO cells
            (pseudocount 0.5), then centred over lines;
* g_L(t)  = G1 log-odds shift; k_L(t) = log2 minimal cycle slowdown (horizon_data.kinetic).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import horizon_data as H  # noqa: E402
import mixseq_panel as MP  # noqa: E402
import mixseq_state as MS  # noqa: E402

TIMES = (3, 6, 12, 24, 48)
MIN_CELLS = 10
SEED = 20261010
B = 2000


def corr(a, b):
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 6 or np.std(a[ok]) == 0 or np.std(b[ok]) == 0:
        return np.nan
    return float(np.corrcoef(a[ok], b[ok])[0, 1])


def boot_lines(fn, n, seed=SEED, b=B):
    rng = np.random.default_rng(seed)
    vals = [fn(rng.integers(0, n, n)) for _ in range(b)]
    return [float(np.nanpercentile(vals, 2.5)), float(np.nanpercentile(vals, 97.5))]


def panel(lines: list, variant: str = "v1") -> dict:
    sp = MP.split()
    cal = MS.calibration(sp)
    c = MP.load_units(["D_control"])
    t = MP.load_units(["D_treated"])
    present = c["present"]
    nl, nt = len(lines), len(TIMES)
    O = np.full((nl, nt, int(present.sum())), np.nan, np.float32)
    n_t, n_c = np.zeros((nl, nt), int), np.zeros((nl, nt), int)
    ph_t, ph_c = np.zeros((nl, nt, 3), int), np.zeros((nl, nt, 3), int)
    tot_t = {h: int((t["hash_tag"] == f"Tram_{h}hr").sum()) for h in TIMES}
    tot_c = {h: int((c["hash_tag"] == f"DMSO_{h}hr").sum()) for h in TIMES}
    for i, d in enumerate(lines):
        for k, h in enumerate(TIMES):
            tm = (t["depmap"] == d) & (t["hash_tag"] == f"Tram_{h}hr")
            cm = (c["depmap"] == d) & (c["hash_tag"] == f"DMSO_{h}hr")
            n_t[i, k], n_c[i, k] = int(tm.sum()), int(cm.sum())
            ph_t[i, k] = np.bincount(t["phase"][tm], minlength=3)
            ph_c[i, k] = np.bincount(c["phase"][cm], minlength=3)
            if n_t[i, k] >= MIN_CELLS and n_c[i, k] >= MIN_CELLS:
                O[i, k] = MS.project(t["frac"][tm], cal, variant)[:, present].mean(0) - MS.project(c["frac"][cm], cal, variant)[:, present].mean(0)
    A = np.array([[np.log2((n_t[i, k] + 0.5) / tot_t[h]) - np.log2((n_c[i, k] + 0.5) / tot_c[h]) for k, h in enumerate(TIMES)] for i in range(nl)])
    A = A - A.mean(0, keepdims=True)
    g = np.log((ph_t[..., 0] + 0.5) / (ph_t[..., 1:].sum(-1) + 0.5)) - np.log((ph_c[..., 0] + 0.5) / (ph_c[..., 1:].sum(-1) + 0.5))
    kin = np.array([[H.kinetic(dict(zip(("G1", "S", "G2M"), ph_t[i, k])), dict(zip(("G1", "S", "G2M"), ph_c[i, k])))
                     for k in range(nt)] for i in range(nl)])
    return {"O": O, "A": A, "g": g, "k": kin, "n_t": n_t, "n_c": n_c, "present": present}


def analyse(lines: list, late: np.ndarray, state_paired: np.ndarray, tahoe_generic: np.ndarray, ccle_pred: np.ndarray) -> dict:
    """late: PRISM trametinib per line; state_paired: lines x 2000 STATE 24 h forecast (0.05 uM);
    tahoe_generic: 2000 Tahoe observed mean 24 h trametinib response; ccle_pred: frozen basal prior."""
    p = panel(lines)
    O, A, g, kin, present = p["O"], p["A"], p["g"], p["k"], p["present"]
    n = len(lines)
    mag = -np.linalg.norm(O, axis=-1)
    out = {"lines": lines, "cells_treated": p["n_t"].tolist(), "cells_dmso": p["n_c"].tolist()}
    # T1: when to observe
    t1 = {}
    for k, h in enumerate(TIMES):
        rec = {}
        for name, X in (("response_magnitude", mag[:, k]), ("abundance", A[:, k]), ("g1_shift", g[:, k]), ("kinetic", kin[:, k])):
            rec[name] = {"r": corr(X, late), "ci95": boot_lines(lambda b, X=X: corr(X[b], late[b]), n)}
        t1[f"{h}h"] = rec
    z = lambda x: (x - np.nanmean(x)) / np.nanstd(x)  # noqa: E731
    t1["ccle_prior"] = {"r": corr(ccle_pred, late), "ci95": boot_lines(lambda b: corr(ccle_pred[b], late[b]), n)}
    for k, h in enumerate(TIMES):
        m = mag[:, k]
        t1[f"{h}h"]["prior_plus_magnitude"] = {
            "r": corr(z(ccle_pred) + z(m), late),
            "increment_over_prior": corr(z(ccle_pred) + z(m), late) - corr(ccle_pred, late),
            "increment_ci95": boot_lines(lambda b, m=m: corr(z(ccle_pred[b]) + z(m[b]), late[b]) - corr(ccle_pred[b], late[b]), n)}
    rs = np.array([t1[f"{h}h"]["response_magnitude"]["r"] for h in TIMES])
    hit = np.flatnonzero(rs >= np.nanmax(rs) - 0.05) if np.isfinite(rs).any() else []
    t1["earliest_within_mub_of_best"] = int(TIMES[int(hit[0])]) if len(hit) else None
    out["T1_when_to_observe"] = t1
    # T2: temporal fingerprint (generic and line-specific)
    S = state_paired[:, present]
    sbar = np.nanmean(S, 0)
    tg = tahoe_generic[present]
    t2 = {}
    for k, h in enumerate(TIMES):
        ok = np.isfinite(O[:, k]).all(1)
        obar = O[ok, k].mean(0)
        spec = [corr(S[i] - S[ok].mean(0), O[i, k] - obar) for i in np.flatnonzero(ok)]
        t2[f"{h}h"] = {"generic_r_state": corr(sbar, obar), "generic_scale_state": float(obar @ sbar / (sbar @ sbar)),
                       "generic_r_tahoe24h": corr(tg, obar), "generic_scale_tahoe24h": float(obar @ tg / (tg @ tg)),
                       "line_specific_r_state": float(np.nanmean(spec)), "observed_norm": float(np.linalg.norm(obar)),
                       "n_lines": int(ok.sum())}
    out["T2_temporal_fingerprint"] = t2
    # T3: kinetic readout as a rate: k(t) vs A(t') - A(t), consecutive times, pooled after per-interval standardisation
    xs, ys, gs, cs = [], [], [], []
    per = {}
    for k in range(len(TIMES) - 1):
        dA = A[:, k + 1] - A[:, k]
        per[f"{TIMES[k]}->{TIMES[k + 1]}h"] = {"kinetic": corr(kin[:, k], dA), "g1_shift": corr(g[:, k], dA), "abundance_so_far": corr(A[:, k], dA)}
        xs.append(z(kin[:, k])); gs.append(z(g[:, k])); cs.append(z(A[:, k])); ys.append(z(dA))
    X, G, Cc, Y = (np.concatenate(v) for v in (xs, gs, cs, ys))
    out["T3_kinetic_rate"] = {"per_interval": per, "pooled_kinetic_r": corr(X, Y), "pooled_g1_r": corr(G, Y), "pooled_abundance_so_far_r": corr(Cc, Y),
                              "pooled_kinetic_ci95": boot_lines(lambda b: corr(np.concatenate([xs[k][b] for k in range(4)]), np.concatenate([ys[k][b] for k in range(4)])), n)}
    return out
