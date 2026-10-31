"""Extra check: the 'at least one measured L1000 option' inclusion criterion, re-derived from the GSE92742
metadata (pert_info, sig_info) without the large gctx. Counts level-5 signatures per key x option for
trt_cp pert_ids whose inchi_key_prefix equals the key, at 10 uM, in the 18 core line x 6/24 h options,
and compares them with n_sig in l1000_nci.npz and l1000_24q2.npz. Writes check_extra_l1000_meta.json.
"""
import gzip
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
    out = {"pert_info_columns": list(pi.columns), "sig_info_columns": list(si.columns)}
    out["dose_units"] = Counter(si["pert_dose_unit"]).most_common(6)
    out["time_units"] = Counter(si["pert_time_unit"]).most_common(4)
    cp = pi[pi["pert_type"] == "trt_cp"]
    by_prefix = defaultdict(set)
    for pid, pre in zip(cp["pert_id"], cp["inchi_key_prefix"]):
        if isinstance(pre, str) and pre not in ("-666", ""):
            by_prefix[pre].add(pid)
    s = si[si["pert_type"] == "trt_cp"].copy()
    s["dose"] = pd.to_numeric(s["pert_dose"], errors="coerce")
    s["time"] = pd.to_numeric(s["pert_time"], errors="coerce")
    opt_labels = [str(o) for o in np.load(PROC + "nci60.npz")["option"]]
    cells = sorted({o.split("|")[0] for o in opt_labels})
    out["option_labels"] = opt_labels
    sel = s[s["cell_id"].isin(cells) & s["time"].isin([6, 24])]
    rules = {
        "dose==10_um": sel[(sel["dose"] == 10) & sel["pert_dose_unit"].isin(["µM", "um", "uM", "\u00b5M"])],
        "dose_round2==10": sel[(sel["dose"].round(2) == 10)],
        "idose_10um_text": sel[sel["pert_idose"].astype(str).str.replace(" ", "").str.lower().isin(["10µm", "10um", "10.0um", "10.0µm"])],
    }
    out["idose_examples"] = Counter(sel["pert_idose"]).most_common(8)
    for set_name, fname in (("nci60", "l1000_nci.npz"), ("prism24q2", "l1000_24q2.npz")):
        L = np.load(PROC + fname, allow_pickle=True)
        keys = [str(k) for k in L["key"]]
        ik = [str(k) for k in L["ik14"]]
        nsig = L["n_sig"].astype(int)
        lopt = [str(o) for o in L["option"]]
        assert lopt == opt_labels
        res = {}
        for rname, df in rules.items():
            cnt = Counter(zip(df["pert_id"], df["cell_id"], df["time"].astype(int)))
            mine = np.zeros_like(nsig)
            for i, k in enumerate(ik):
                for pid in by_prefix.get(k, ()):
                    for j, o in enumerate(opt_labels):
                        c, t = o.split("|")
                        mine[i, j] += cnt.get((pid, c, int(t.split()[0])), 0)
            res[rname] = {"n_sig_equal": bool(np.array_equal(mine, nsig)),
                          "n_cells_differ": int((mine != nsig).sum()),
                          "keys_measured_verifier": int((mine > 0).any(axis=1).sum()),
                          "keys_measured_npz": int((nsig > 0).any(axis=1).sum()),
                          "measured_flag_differs": int(((mine > 0).any(axis=1) != (nsig > 0).any(axis=1)).sum())}
        res["n_keys"] = len(keys)
        out[set_name] = res
        # 24Q2: sealed compounds absent from l1000_24q2.npz -- do they have any matching LINCS signature?
        if set_name == "prism24q2":
            import csv
            from rdkit import Chem, RDLogger
            RDLogger.DisableLog("rdApp.*")
            sealed = list(csv.DictReader(open(ROOT + "log/research_records/knowledge_reality_20261013/sealed_compounds.csv",
                                              encoding="utf-8", newline="")))
            miss = [r for r in sealed if r["core"].strip() not in set(keys)]
            df = rules["dose==10_um"]
            cnt = Counter(zip(df["pert_id"], df["cell_id"], df["time"].astype(int)))
            info = []
            for r in miss:
                m = Chem.MolFromSmiles(r["smiles"])
                k14 = Chem.MolToInchiKey(m)[:14] if m is not None else None
                pids = sorted(by_prefix.get(k14, ()))
                n = sum(cnt.get((p, c.split("|")[0], int(c.split("|")[1].split()[0])), 0) for p in pids for c in opt_labels)
                info.append({"core": r["core"], "ik14": k14, "conn": r["conn"], "lincs_pert_ids": pids, "n_core_10uM_sigs": n})
            out["sealed_missing_from_l1000_24q2"] = info
    json.dump(out, open(VER + "check_extra_l1000_meta.json", "w", encoding="utf-8", newline="\n"), indent=1, default=str)
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
