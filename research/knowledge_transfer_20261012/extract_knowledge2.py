"""Confirmation knowledge and design metadata for the phase-2 tiers (no response values are read).

* Compound identities: PubChem CIDs for reference compounds come from phase 1 (same compound key);
  for query compounds, by InChIKey through the phase-1 perturbagen table, then by name or by
  InChIKey of the MAP-KG drug table (``DRUG_merged_drugs_with_residuals.csv``).
* Campaign grid: which (query compound, line) cells have a 10 uM / 24 h signature, counted from
  ``sig_info`` metadata only; the sealed response file is not opened.
Writes ``cache/phase2_knowledge.json``.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from extract_phase1 import compound_key

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SRC = ROOT / "data/external/lincs_l1000_phase2"
P1 = ROOT / "data/external/lincs_l1000_gse92742"
MAPKG_DRUGS = ROOT / "data/external/mapkg_20261009/DRUG_merged_drugs_with_residuals.csv"
LINES = ["A375", "HA1E", "HELA", "HT29", "MCF7", "PC3", "YAPC"]


def main():
    t0 = time.time()
    ref = np.load(SRC / "derived/blockq_phase2_reference.npz", allow_pickle=True)
    pert2 = pd.read_csv(SRC / "meta/GSE70138_Broad_LINCS_pert_info_2017-03-06.txt.gz", sep="\t", low_memory=False)
    pert2 = pert2.drop_duplicates("pert_id").set_index("pert_id")
    pert1 = pd.read_csv(P1 / "GSE92742_Broad_LINCS_pert_info.txt.gz", sep="\t", low_memory=False)
    cid1 = pd.to_numeric(pert1.pubchem_cid, errors="coerce")
    by_inchi = {k: int(c) for k, c in zip(pert1.inchi_key.astype(str), cid1) if np.isfinite(c) and k not in ("-666", "nan")}
    by_pid1 = {p: int(c) for p, c in zip(pert1.pert_id, cid1) if np.isfinite(c)}

    drugs = pd.read_csv(MAPKG_DRUGS, usecols=["PubChem ID", "Drug Name", "smiles"])
    by_name = {str(n).strip().lower(): int(c) for n, c in zip(drugs["Drug Name"], drugs["PubChem ID"]) if isinstance(n, str)}

    def entry(tier):
        keys = [str(k) for k in ref[f"{tier}_compound"]]
        pids = [str(p).split("|") for p in ref[f"{tier}_pert_ids"]]
        names = [str(n) for n in ref[f"{tier}_iname"]]
        smiles = [str(s) for s in ref[f"{tier}_smiles"]]
        inchis = [next((str(pert2.loc[p].inchi_key) for p in ps if p in pert2.index and isinstance(pert2.loc[p].inchi_key, str)), "")
                  for ps in pids]
        return keys, pids, names, smiles, inchis

    out = {}
    need_rdkit = []
    for tier in ("ref", "query"):
        keys, pids, names, smiles, inchis = entry(tier)
        rows = []
        for k, ps, n, s, ik in zip(keys, pids, names, smiles, inchis):
            cids, how = [], ""
            c = next((by_pid1[p] for p in ps if p in by_pid1), None)
            if c is not None:
                cids, how = [c], "phase1_pert_id"
            elif ik in by_inchi:
                cids, how = [by_inchi[ik]], "phase1_inchikey"
            elif n.strip().lower() in by_name:
                cids, how = [by_name[n.strip().lower()]], "mapkg_name"
            else:
                need_rdkit.append((tier, len(rows), ik))
            rows.append({"key": k, "name": n, "smiles": s, "inchikey": ik, "cids": cids, "cid_source": how})
        out[tier] = rows

    if need_rdkit:  # last resort: InChIKey of MAP-KG SMILES, computed only when needed
        from rdkit import Chem, RDLogger
        RDLogger.DisableLog("rdApp.*")
        wanted = {ik for _, _, ik in need_rdkit if ik}
        found = {}
        for c, smi in zip(drugs["PubChem ID"], drugs["smiles"]):
            if not isinstance(smi, str):
                continue
            m = Chem.MolFromSmiles(smi)
            if m is None:
                continue
            ik = Chem.MolToInchiKey(m)
            if ik in wanted and ik not in found:
                found[ik] = int(c)
        for tier, i, ik in need_rdkit:
            if ik in found:
                out[tier][i]["cids"] = [found[ik]]
                out[tier][i]["cid_source"] = "mapkg_smiles_inchikey"

    sig = pd.read_csv(SRC / "meta/GSE70138_Broad_LINCS_sig_info_2017-03-06.txt.gz", sep="\t", low_memory=False)
    cp = sig[(sig.pert_type == "trt_cp") & sig.cell_id.isin(LINES) & sig.pert_idose.astype(str).str.startswith("10.0 um")
             & (sig.pert_itime == "24 h")].copy()
    cp["key"] = [compound_key(n, p) for n, p in zip(cp.pert_iname, cp.pert_id)]
    counts = cp.groupby(["key", "cell_id"]).size()
    for row in out["query"]:
        row["n_sig"] = [int(counts.get((row["key"], l), 0)) for l in LINES]
    rec = {"created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "lines": LINES,
           "note": "Identities and signature counts from metadata; no response value was read.",
           "cid_sources": {t: pd.Series([r["cid_source"] or "none" for r in out[t]]).value_counts().to_dict() for t in out},
           "seconds": round(time.time() - t0, 1), **out}
    (HERE / "cache" / "phase2_knowledge.json").write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: rec[k] for k in ("cid_sources", "seconds")}, indent=1))
    g = np.array([r["n_sig"] for r in out["query"]]) > 0
    print("query lines per compound", np.bincount(g.sum(1), minlength=8).tolist())


if __name__ == "__main__":
    main()
