"""Secondary cross-check against the maintained module (loaded by file path; not used for the main checks):
maintained selective_r vs the verifier's per-compound r, and maintained transfer_profile (k=5, k=20 raw) vs the
saved B0/B1 predictions. Writes check_extra_maintained.json.
"""
import importlib.util
import json
import sys

import numpy as np

ROOT = "D:/MAESTRO/"
VER = ROOT + "research/routes/functional_prediction/2026-10-31-generic-axis-transfer/VERIFY/"
STUDY = VER[: -len("VERIFY/")]
PROC = ROOT + "data/processed/generic_axis_transfer_20261031/"
sys.path.insert(0, VER)
import vlib  # noqa: E402

spec = importlib.util.spec_from_file_location("tt_maintained", ROOT + "src/virtual_cell/transcriptional_transfer.py")
tt = importlib.util.module_from_spec(spec)
sys.modules["tt_maintained"] = tt
spec.loader.exec_module(tt)


def main():
    out = {}
    for s, ml, dname in (("nci60", 40, "derived_nci.npz"), ("prism24q2", 50, "derived_prism.npz")):
        P = np.load(STUDY + f"RUN/predictions_{s}.npz")
        D = np.load(VER + dname)
        obs = D["observed"]
        gen = D["generic"] if D["generic"].ndim == 2 else np.broadcast_to(D["generic"], obs.shape)
        res = {}
        for a in vlib.ARMS:
            m = np.array([tt.selective_r(P[f"pred_{a}"][i], obs[i], gen[i], min_lines=ml) for i in range(len(obs))])
            v = np.array([vlib.sel_r(P[f"pred_{a}"][i], obs[i], gen[i], ml) for i in range(len(obs))])
            res[f"selective_r_{a}_max_abs_diff_maintained_vs_verifier"] = float(np.nanmax(np.abs(m - v)))
            res[f"selective_r_{a}_nan_equal"] = bool(np.array_equal(np.isnan(m), np.isnan(v)))
        out[s] = res
    # maintained transfer_profile on NCI-60 folds and on the 24Q2 queries
    Dn = np.load(VER + "derived_nci.npz")
    keys = [str(k) for k in Dn["key"]]
    L1 = np.load(PROC + "l1000_nci.npz", allow_pickle=True)
    lk = [str(k) for k in L1["key"]]
    sig = L1["x"][[lk.index(k) for k in keys]]
    obs, fold = Dn["observed"], Dn["fold"]
    S = np.load(STUDY + "RUN/predictions_nci60.npz")
    mB0 = np.full_like(obs, np.nan)
    mB1 = np.full_like(obs, np.nan)
    for f in range(10):
        q, r = np.flatnonzero(fold == f), np.flatnonzero(fold != f)
        for i in q:
            mB0[i] = tt.transfer_profile(sig[i], sig[r], obs[r], k=5).values
            mB1[i] = tt.transfer_profile(sig[i], sig[r], obs[r], k=20).values
    for a, m in (("B0", mB0), ("B1", mB1)):
        both = np.isfinite(m) & np.isfinite(S[f"pred_{a}"])
        out["nci60"][f"transfer_profile_{a}_max_abs_diff_vs_saved"] = float(np.max(np.abs(m[both] - S[f"pred_{a}"][both])))
        out["nci60"][f"transfer_profile_{a}_nan_equal"] = bool(np.array_equal(np.isfinite(m), np.isfinite(S[f"pred_{a}"])))
    Dp = np.load(VER + "derived_prism.npz")
    pk = [str(k) for k in Dp["key"]]
    lines = [str(x) for x in Dp["line"]]
    L2 = np.load(PROC + "l1000_24q2.npz", allow_pickle=True)
    l2 = [str(k) for k in L2["key"]]
    qsig = L2["x"][[l2.index(k) for k in pk]]
    dev = np.load(PROC + "dev_pool.npz")
    dl = [str(x) for x in dev["line"]]
    Y = dev["profile"][:, [dl.index(x) for x in lines]]
    S2 = np.load(STUDY + "RUN/predictions_prism24q2.npz")
    for a, k in (("B0", 5), ("B1", 20)):
        m = np.vstack([tt.transfer_profile(qsig[i], dev["signature"], Y, k=k).values for i in range(len(pk))])
        both = np.isfinite(m) & np.isfinite(S2[f"pred_{a}"])
        out["prism24q2"][f"transfer_profile_{a}_max_abs_diff_vs_saved"] = float(np.max(np.abs(m[both] - S2[f"pred_{a}"][both])))
        out["prism24q2"][f"transfer_profile_{a}_nan_equal"] = bool(np.array_equal(np.isfinite(m), np.isfinite(S2[f"pred_{a}"])))
    json.dump(out, open(VER + "check_extra_maintained.json", "w", encoding="utf-8", newline="\n"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
