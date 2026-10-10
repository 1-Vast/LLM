"""Match Tahoe-100M drugs to PRISM Repurposing 19Q4 compounds (metadata only; no outcome value read).

Keys, in order: InChIKey connectivity block (first 14 characters) from SMILES, then normalized name.
Writes DRUG_MATCH.json with every Tahoe drug, its PRISM broad_id(s) per screen, and the key used.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd
from rdkit import Chem, RDLogger

RDLogger.DisableLog("rdApp.*")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "data/external/prism_19q4/raw"
META = ROOT / "data/external/tahoe_phenotype_20261010/metadata"


def norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(name).lower())


def ikey14(smiles: str | None) -> str | None:
    if not isinstance(smiles, str) or not smiles:
        return None
    mol = Chem.MolFromSmiles(smiles.split(",")[0].strip())
    if mol is None:
        return None
    try:
        return Chem.MolToInchiKey(mol)[:14]
    except Exception:
        return None


def prism_table() -> pd.DataFrame:
    sec = pd.read_csv(RAW / "secondary-screen-replicate-collapsed-treatment-info.csv")
    pri = pd.read_csv(RAW / "primary-screen-replicate-collapsed-treatment-info.csv")
    sec = sec[sec.screen_id.isin(["HTS002", "MTS010"])][["broad_id", "name", "smiles", "screen_id"]]
    pri = pri[["broad_id", "name", "smiles"]].assign(screen_id="HTS")
    t = pd.concat([sec, pri]).drop_duplicates(["broad_id", "screen_id"])
    t["ik"] = t.smiles.map(ikey14)
    t["nm"] = t.name.map(norm)
    return t


def main() -> dict:
    drugs = pd.read_parquet(META / "tahoe_drugs.parquet")
    prism = prism_table()
    by_ik = prism.dropna(subset=["ik"]).groupby("ik")
    by_nm = prism.groupby("nm")
    out = {}
    for _, row in drugs.iterrows():
        ik, nm = ikey14(row.canonical_smiles), norm(row.drug)
        hit, key = None, None
        if ik is not None and ik in by_ik.groups:
            hit, key = by_ik.get_group(ik), "inchikey14"
        elif nm in by_nm.groups:
            hit, key = by_nm.get_group(nm), "name"
        rec = {"key": key, "secondary": [], "primary": []}
        if hit is not None:
            rec["secondary"] = sorted(set(hit[hit.screen_id.isin(["HTS002", "MTS010"])].broad_id))
            rec["primary"] = sorted(set(hit[hit.screen_id == "HTS"].broad_id))
            rec["prism_names"] = sorted(set(hit.name.astype(str)))
        out[row.drug] = rec
    summary = {
        "tahoe_drugs": len(out),
        "matched_any": sum(bool(v["secondary"] or v["primary"]) for v in out.values()),
        "matched_secondary": sum(bool(v["secondary"]) for v in out.values()),
        "matched_primary": sum(bool(v["primary"]) for v in out.values()),
        "by_key": pd.Series([v["key"] for v in out.values()]).value_counts(dropna=False).to_dict(),
    }
    (HERE / "DRUG_MATCH.json").write_text(json.dumps({"summary": summary, "drugs": out}, indent=1, default=str), encoding="utf-8")
    return summary


if __name__ == "__main__":
    print(json.dumps(main(), indent=1, default=str))
