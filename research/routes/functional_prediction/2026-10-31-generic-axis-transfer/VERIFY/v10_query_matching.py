"""Extra check: how are 24Q2 queries matched to L1000? Compare ik14-prefix matching with Broad-ID (pert_id core)
matching, using GSE92742 metadata only. No 24Q2 outcome value is read. Writes check_extra_query_matching.json.
"""
import csv
import json
from collections import Counter, defaultdict

import numpy as np
import pandas as pd

ROOT = "D:/MAESTRO/"
PROC = ROOT + "data/processed/generic_axis_transfer_20261031/"
VER = ROOT + "research/routes/functional_prediction/2026-10-31-generic-axis-transfer/VERIFY/"
LINCS = ROOT + "data/external/lincs_l1000_gse92742/"


def main():
    pi = pd.read_csv(LINCS + "GSE92742_Broad_LINCS_pert_info.txt.gz", sep="\t", dtype=str, compression="gzip")
    si = pd.read_csv(LINCS + "GSE92742_Broad_LINCS_sig_info.txt.gz", sep="\t", dtype=str, compression="gzip")
    cp = pi[pi["pert_type"] == "trt_cp"]
    by_prefix = defaultdict(set)
    for pid, pre in zip(cp["pert_id"], cp["inchi_key_prefix"]):
        by_prefix[str(pre)].add(pid)
    opts = [str(o) for o in np.load(PROC + "nci60.npz")["option"]]
    cells = {o.split("|")[0] for o in opts}
    s = si[(si["pert_type"] == "trt_cp") & si["cell_id"].isin(cells) & (si["pert_idose"] == "10 \u00b5M")]
    s = s[pd.to_numeric(s["pert_time"], errors="coerce").isin([6, 24])]
    cnt = Counter(zip(s["pert_id"], s["cell_id"], s["pert_time"].astype(float).astype(int)))

    def nsig(pids):
        v = np.zeros(len(opts), int)
        for j, o in enumerate(opts):
            c, t = o.split("|")
            v[j] = sum(cnt.get((p, c, int(t.split()[0])), 0) for p in pids)
        return v

    sealed = list(csv.DictReader(open(ROOT + "log/research_records/knowledge_reality_20261013/sealed_compounds.csv",
                                      encoding="utf-8", newline="")))
    L = np.load(PROC + "l1000_24q2.npz", allow_pickle=True)
    lk = {str(k): i for i, k in enumerate(L["key"])}
    ik_count = Counter(r["conn"] for r in sealed)
    rows = []
    for r in sealed:
        core, ik = r["core"].strip(), r["conn"].strip()
        by_core = nsig([core])
        by_ik = nsig(sorted(by_prefix.get(ik, ())))
        rows.append({"core": core, "ik14": ik, "shared_ik14_in_sealed": ik_count[ik], "measured_by_core": bool(by_core.any()),
                     "measured_by_ik14": bool(by_ik.any()), "in_l1000_24q2": core in lk,
                     "npz_measured": bool(L["n_sig"][lk[core]].any()) if core in lk else None,
                     "npz_equals_ik14_counts": bool(np.array_equal(L["n_sig"][lk[core]], by_ik)) if core in lk else None,
                     "npz_equals_core_counts": bool(np.array_equal(L["n_sig"][lk[core]], by_core)) if core in lk else None})
    df = pd.DataFrame(rows)
    out = {
        "n_sealed": len(df),
        "n_measured_by_ik14": int(df["measured_by_ik14"].sum()),
        "n_measured_by_core": int(df["measured_by_core"].sum()),
        "n_measured_in_npz": int(df["npz_measured"].fillna(False).sum()),
        "measured_by_ik14_not_in_npz_set": df[df["measured_by_ik14"] & ~df["npz_measured"].fillna(False).astype(bool)]
        .to_dict("records"),
        "measured_by_core_not_by_ik14": df[df["measured_by_core"] & ~df["measured_by_ik14"]]["core"].tolist(),
        "npz_measured_but_not_by_core": df[df["npz_measured"].fillna(False).astype(bool) & ~df["measured_by_core"]]["core"].tolist(),
        "npz_counts_equal_ik14_counts_all": bool(df["npz_equals_ik14_counts"].dropna().all()),
        "npz_counts_equal_core_counts_for_measured": bool(df[df["npz_measured"].fillna(False).astype(bool)]["npz_equals_core_counts"].all()),
        "sealed_ik14_shared_groups": {k: [r["core"] for r in sealed if r["conn"] == k] for k, v in ik_count.items() if v > 1},
    }
    json.dump(out, open(VER + "check_extra_query_matching.json", "w", encoding="utf-8", newline="\n"), indent=1, default=str)
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
