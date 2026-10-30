"""Exploratory, structure-first identity census for the CDI data gate.

This script writes only research/ artifacts.  It never changes src/ or tools/ and
does not infer a biological target from a drug name.  Name matches are retained
as candidates; only exact InChIKey matches are counted as structure matches.
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd
from rdkit import Chem


ROOT = Path(r"D:/MAESTRO")
EP = ROOT / "research/2026-10-30-cdi-r3"
API = EP / "raw/chembl_molecules_batch.json"
KLAEGER = ROOT / "data/external/klaeger2017_chembl/klaeger2017_CHEMBL3991601_kd.csv"
PRISM_DIR = ROOT / "data/external/prism_19q4/raw"


def norm_name(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return re.sub(r"[^A-Z0-9]", "", str(value).upper())


def smiles_components(value: object) -> list[str]:
    if value is None or pd.isna(value):
        return []
    # PRISM repeats the same SMILES several times in a comma-separated cell.
    return [x.strip() for x in str(value).split(",") if x.strip()]


def structure(smiles: str) -> tuple[str, str] | None:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    return Chem.MolToSmiles(mol, canonical=True), Chem.MolToInchiKey(mol)


def file_meta(path: Path) -> dict:
    stat = path.stat()
    return {"path": str(path), "bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns}


def load_chembl() -> tuple[dict, dict[str, set[str]]]:
    records = json.loads(API.read_text(encoding="utf-8"))["molecules"]
    by_id: dict[str, dict] = {}
    name_index: dict[str, set[str]] = defaultdict(set)
    for rec in records:
        mid = rec["molecule_chembl_id"]
        structures = rec.get("molecule_structures") or {}
        ikey = structures.get("standard_inchi_key")
        smiles = structures.get("canonical_smiles")
        if not ikey or not smiles:
            continue
        entry = {
            "molecule_chembl_id": mid,
            "pref_name": rec.get("pref_name"),
            "canonical_smiles": smiles,
            "standard_inchi_key": ikey,
            "synonyms": sorted({x.get("synonyms") for x in []}),
        }
        syns = []
        for syn in rec.get("molecule_synonyms") or []:
            if syn.get("synonyms"):
                syns.append(syn["synonyms"])
        entry["synonyms"] = sorted(set(syns))
        by_id[mid] = entry
        for label in [rec.get("pref_name"), *syns]:
            key = norm_name(label)
            if key:
                name_index[key].add(mid)
    return by_id, name_index


def collect_prism() -> tuple[dict[str, dict], list[dict]]:
    files = [
        PRISM_DIR / "primary-screen-replicate-collapsed-treatment-info.csv",
        PRISM_DIR / "secondary-screen-replicate-collapsed-treatment-info.csv",
        PRISM_DIR / "secondary-screen-replicate-treatment-info.csv",
    ]
    by_broad: dict[str, dict] = {}
    for path in files:
        usecols = [
            "broad_id",
            "name",
            "smiles",
            "target",
            "moa",
            "screen_id",
            "dose",
            "perturbation_type",
        ]
        header = pd.read_csv(path, nrows=0).columns
        usecols = [c for c in usecols if c in header]
        for chunk in pd.read_csv(path, usecols=usecols, chunksize=200_000, low_memory=False):
            for row in chunk.to_dict("records"):
                bid = row.get("broad_id")
                if not bid or pd.isna(bid):
                    continue
                item = by_broad.setdefault(
                    str(bid),
                    {
                        "broad_id": str(bid),
                        "names": set(),
                        "smiles": set(),
                        "targets": set(),
                        "moas": set(),
                        "screens": set(),
                        "doses": set(),
                        "source_files": set(),
                    },
                )
                for field, key in [("names", "name"), ("targets", "target"), ("moas", "moa")]:
                    val = row.get(key)
                    if val is not None and not pd.isna(val) and str(val).strip():
                        item[field].add(str(val).strip())
                for smi in smiles_components(row.get("smiles")):
                    item["smiles"].add(smi)
                for key, field in [("screen_id", "screens"), ("dose", "doses")]:
                    val = row.get(key)
                    if val is not None and not pd.isna(val):
                        item[field].add(str(val))
                item["source_files"].add(path.name)
    rows = []
    for item in by_broad.values():
        parsed = [structure(s) for s in sorted(item["smiles"])]
        parsed = [x for x in parsed if x is not None]
        keys = sorted({x[1] for x in parsed})
        canonical = sorted({x[0] for x in parsed})
        names = sorted(item["names"])
        rows.append(
            {
                "broad_id": item["broad_id"],
                "name": names[0] if names else "",
                "all_names": ";".join(names),
                "n_raw_smiles": len(item["smiles"]),
                "n_parsed_smiles": len(parsed),
                "n_unique_inchikey": len(keys),
                "inchikey": keys[0] if len(keys) == 1 else "",
                "structure_status": (
                    "unique" if len(keys) == 1 else "conflicting" if len(keys) > 1 else "unparsed"
                ),
                "targets": ";".join(sorted(item["targets"])),
                "moas": ";".join(sorted(item["moas"])),
                "screens": ";".join(sorted(item["screens"])),
                "n_dose_labels": len(item["doses"]),
                "source_files": ";".join(sorted(item["source_files"])),
            }
        )
    return by_broad, rows


def main() -> None:
    chembl, name_index = load_chembl()
    prism, rows = collect_prism()
    exact = 0
    name_candidate = 0
    ambiguous_name = 0
    for row in rows:
        ikey = row["inchikey"]
        direct = [mid for mid, rec in chembl.items() if rec["standard_inchi_key"] == ikey] if ikey else []
        row["exact_chembl_ids"] = ";".join(sorted(direct))
        if direct:
            exact += 1
            row["mapping_status"] = "exact_structure"
        else:
            candidates = set()
            for label in row["all_names"].split(";") if row["all_names"] else []:
                candidates.update(name_index.get(norm_name(label), set()))
            row["name_candidate_chembl_ids"] = ";".join(sorted(candidates))
            if len(candidates) == 1:
                name_candidate += 1
                row["mapping_status"] = "name_only_candidate"
            elif len(candidates) > 1:
                ambiguous_name += 1
                row["mapping_status"] = "ambiguous_name_candidate"
            else:
                row["mapping_status"] = "unmapped"
        row.setdefault("name_candidate_chembl_ids", "")

    kd = pd.read_csv(KLAEGER, low_memory=False)
    kd = kd[kd["molecule_chembl_id"].isin(chembl)]
    kd_counts = (
        kd.groupby("molecule_chembl_id")
        .agg(
            kd_rows=("activity_id", "size"),
            kd_targets=("target_chembl_id", "nunique"),
            kd_exact_rows=("standard_relation", lambda s: int((s == "=").sum())),
            kd_right_censored_rows=("standard_relation", lambda s: int((s == ">").sum())),
        )
        .reset_index()
    )
    by_id = {r["molecule_chembl_id"]: r for r in kd_counts.to_dict("records")}
    for row in rows:
        mids = row.get("exact_chembl_ids", "").split(";") if row.get("exact_chembl_ids") else []
        agg = [by_id[x] for x in mids if x in by_id]
        row["kd_rows"] = sum(x["kd_rows"] for x in agg)
        row["kd_targets"] = sum(x["kd_targets"] for x in agg)
        row["kd_exact_rows"] = sum(x["kd_exact_rows"] for x in agg)
        row["kd_right_censored_rows"] = sum(x["kd_right_censored_rows"] for x in agg)

    out_csv = EP / "prism_structure_identity_candidates.csv"
    pd.DataFrame(rows).sort_values(["mapping_status", "broad_id"]).to_csv(out_csv, index=False)
    summary = {
        "definition": "Exact structure means PRISM canonicalized SMILES InChIKey equals ChEMBL standard_inchi_key. Name matches are candidates only.",
        "chembl_records_with_structure": len(chembl),
        "prism_unique_broad_ids": len(rows),
        "prism_unique_structure_rows": sum(r["structure_status"] == "unique" for r in rows),
        "prism_conflicting_structure_rows": sum(r["structure_status"] == "conflicting" for r in rows),
        "prism_unparsed_structure_rows": sum(r["structure_status"] == "unparsed" for r in rows),
        "exact_structure_matches": exact,
        "name_only_candidates": name_candidate,
        "ambiguous_name_candidates": ambiguous_name,
        "exact_match_rows_with_kd": sum(r["mapping_status"] == "exact_structure" and r["kd_rows"] > 0 for r in rows),
        "input_files": [file_meta(API), file_meta(KLAEGER)] + [file_meta(x) for x in [
            PRISM_DIR / "primary-screen-replicate-collapsed-treatment-info.csv",
            PRISM_DIR / "secondary-screen-replicate-collapsed-treatment-info.csv",
            PRISM_DIR / "secondary-screen-replicate-treatment-info.csv",
        ]],
        "scientific_boundary": "This census establishes identity candidates only; it does not establish same target, cellular engagement, dose/time matching, replicate independence, or causal mediation.",
    }
    (EP / "identity_census.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
