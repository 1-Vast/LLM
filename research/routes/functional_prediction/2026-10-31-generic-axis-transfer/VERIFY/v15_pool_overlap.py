"""Extra check: no 24Q2 query is a development-pool compound by connectivity block, by name or by Broad ID.
Writes check_extra_pool_overlap.json.
"""
import csv
import json
import re

import numpy as np
from rdkit import Chem, RDLogger

RDLogger.DisableLog("rdApp.*")
ROOT = "D:/MAESTRO/"
PROC = ROOT + "data/processed/generic_axis_transfer_20261031/"
VER = ROOT + "research/routes/functional_prediction/2026-10-31-generic-axis-transfer/VERIFY/"


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def main():
    dev = np.load(PROC + "dev_pool.npz")
    names = [str(d) for d in dev["drug"]]
    dev_ik = {str(i) for i in dev["ik14"] if len(str(i)) == 14}
    no_ik = [n for n, i in zip(names, dev["ik14"]) if len(str(i)) != 14]
    P = np.load(PROC + "prism24q2.npz")
    q = [str(k) for k in P["key"]]
    L = np.load(PROC + "l1000_24q2.npz", allow_pickle=True)
    qik = {str(k): str(i) for k, i in zip(L["key"], L["ik14"]) if str(k) in set(q)}
    sealed = {r["core"]: r for r in csv.DictReader(open(ROOT + "log/research_records/knowledge_reality_20261013/sealed_compounds.csv",
                                                         encoding="utf-8", newline=""))}
    info = list(csv.DictReader(open(ROOT + "data/external/prism_19q4/raw/primary-screen-replicate-collapsed-treatment-info.csv",
                                    encoding="utf-8", newline="")))
    dev_cores, no_ik_struct = set(), {}
    nameset = set(names)
    for r in info:
        if r["name"] in nameset:
            for b in re.split(r"[,;\s]+", r["broad_id"]):
                m = re.match(r"(BRD-[A-Z]\d{8})", b)
                if m:
                    dev_cores.add(m.group(1))
        if r["name"] in set(no_ik) and r["smiles"]:
            for smi in r["smiles"].split(","):
                mol = Chem.MolFromSmiles(smi.strip())
                if mol is not None:
                    no_ik_struct.setdefault(r["name"], set()).add(Chem.MolToInchiKey(mol)[:14])
    devn = {norm(n) for n in names}
    out = {"n_queries": len(q), "n_dev": len(names), "dev_without_ik14": no_ik,
           "query_ik14_in_dev": sorted(c for c in q if qik[c] in dev_ik),
           "query_name_in_dev": sorted(c for c in q if norm(sealed[c]["name"]) in devn),
           "n_dev_broad_cores": len(dev_cores),
           "query_core_in_dev": sorted(set(q) & dev_cores),
           "dev_without_ik14_with_structure_in_19q4_info": {k: sorted(v) for k, v in no_ik_struct.items()}}
    out["pass"] = not (out["query_ik14_in_dev"] or out["query_name_in_dev"] or out["query_core_in_dev"])
    json.dump(out, open(VER + "check_extra_pool_overlap.json", "w", encoding="utf-8", newline="\n"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
