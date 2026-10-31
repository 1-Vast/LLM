"""Extra check: the confirmation-2 reference pool (dev_pool.npz) equals the block N 19Q4 primary profiles and the
block M landmark signatures it is described as (PROTOCOL sections 3-4). Writes check_extra_devpool.json.
"""
import json

import numpy as np

ROOT = "D:/MAESTRO/"
VER = ROOT + "research/routes/functional_prediction/2026-10-31-generic-axis-transfer/VERIFY/"
PROC = ROOT + "data/processed/generic_axis_transfer_20261031/"


def main():
    dev = np.load(PROC + "dev_pool.npz")
    drugs = [str(d) for d in dev["drug"]]
    out = {"n_dev": len(drugs), "n_unique_drugs": len(set(drugs)), "n_unique_ik14": len(set(str(i) for i in dev["ik14"]))}
    N = {}
    for tier in ("open", "sealed"):
        z = np.load(ROOT + f"data/external/prism_19q4/derived/block_n_prism_{tier}.npz")
        assert [str(s) for s in z["line"]] == [str(s) for s in dev["line"]]
        for d, row in zip(z["drug"], z["primary"]):
            N[str(d)] = row.astype(np.float64)
    M = {}
    for tier in ("open", "sealed"):
        z = np.load(ROOT + f"data/external/lincs_l1000_gse92742/derived/block_m_landmark_{tier}.npz", allow_pickle=True)
        assert [str(s) for s in z["option"]] == [str(s) for s in dev["option"]]
        for d, x in zip(z["drug"], z["x"]):
            M.setdefault(str(d), x)
    out["n_block_n_drugs"] = len(N)
    out["n_block_m_drugs"] = len(M)
    out["dev_not_in_block_n"] = [d for d in drugs if d not in N][:10]
    out["dev_not_in_block_m"] = [d for d in drugs if d not in M][:10]
    out["block_n_not_in_dev"] = len(set(N) - set(drugs))
    have_n = [i for i, d in enumerate(drugs) if d in N]
    P = np.vstack([N[drugs[i]] for i in have_n])
    D = dev["profile"][have_n]
    out["profile_nan_equal"] = bool(np.array_equal(np.isfinite(P), np.isfinite(D)))
    out["profile_max_abs_diff"] = float(np.nanmax(np.abs(P - D)))
    have_m = [i for i, d in enumerate(drugs) if d in M]
    X = np.stack([M[drugs[i]] for i in have_m]).astype(np.float64)
    S = dev["signature"][have_m].astype(np.float64)
    out["signature_nan_equal"] = bool(np.array_equal(np.isfinite(X), np.isfinite(S)))
    out["signature_max_abs_diff"] = float(np.nanmax(np.abs(X - S)))
    out["dev_drugs_with_no_measured_option"] = int((~np.isfinite(dev["signature"][..., 0]).any(axis=1)).sum())
    json.dump(out, open(VER + "check_extra_devpool.json", "w", encoding="utf-8", newline="\n"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
