"""Audit small source tables and local availability without reading outcome matrices."""
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
ASSETS = [
    "data/external/prism_19q4", "data/external/depmap_19q4",
    "data/external/lincs_l1000_gse92742", "data/external/lincs_l1000_phase1",
    "data/external/lincs_l1000_phase2", "data/external/tahoe_phenotype_20261010",
    "data/external/mapkg_20261009", "data/external/jump_target",
    "data/external/gdsc2_fitted", "data/external/batchie_zenodo_13871987",
    "data/raw/prism", "data/raw/sciplex3",
    "research/dual_core_scientific_20261011/literature/datasets/cxcl9_2026",
]


def main():
    receipt = {"scope": "File availability and input metadata only; no phenotype values opened."}
    receipt["local_assets"] = []
    for relative in ASSETS:
        target = REPO / relative
        files = sorted(p for p in target.rglob("*") if p.is_file()) if target.is_dir() else []
        receipt["local_assets"].append({
            "path": relative, "exists": target.exists(), "files": len(files),
            "bytes": sum(p.stat().st_size for p in files),
            "examples": [p.relative_to(REPO).as_posix() for p in files[:4]],
        })
    logs = json.loads((ROOT / "retrieval_log.json").read_text(encoding="utf-8"))
    receipt["source_hash_checks"] = [{
        "id": row["id"],
        "match": hashlib.sha256((ROOT / row["path"]).read_bytes()).hexdigest() == row["sha256"],
    } for row in logs if "path" in row]
    plates = list(csv.DictReader(io.StringIO(gzip.decompress(
        (ROOT / "sources/jump_plate_metadata.body").read_bytes()).decode())))
    receipt["jump"] = {"plate_rows": len(plates), "columns": list(plates[0]),
                       "sources": sorted({row["Metadata_Source"] for row in plates})}
    compounds = list(csv.DictReader((ROOT / "sources/bbbc021_compound.body").open(encoding="utf-8")))
    moa = list(csv.DictReader((ROOT / "sources/bbbc021_moa.body").open(encoding="utf-8")))
    receipt["bbbc021"] = {"compound_rows_including_control": len(compounds),
                          "moa_rows": len(moa), "moa_compounds": len({r["compound"] for r in moa}),
                          "moa_classes": len({r["moa"] for r in moa}),
                          "noncontrol_moa_rows": sum(r["compound"] != "DMSO" for r in moa),
                          "noncontrol_moa_compounds": len({r["compound"] for r in moa if r["compound"] != "DMSO"}),
                          "noncontrol_moa_classes": len({r["moa"] for r in moa if r["compound"] != "DMSO"})}
    # Full canonical SMILES equality is deliberately strict: no salt stripping,
    # tautomer pooling, name alias merging or relaxed stereochemistry.
    from rdkit import Chem
    from rdkit import RDLogger
    RDLogger.DisableLog("rdApp.error")

    def canonical(value):
        mol = Chem.MolFromSmiles(value) if value else None
        return Chem.MolToSmiles(mol, isomericSmiles=True) if mol else None

    prism = list(csv.DictReader((REPO / "data/external/prism_19q4/raw/primary-screen-replicate-collapsed-treatment-info.csv").open(encoding="utf-8")))
    index = {}
    for row in prism:
        structure = canonical(row["smiles"])
        if structure:
            index.setdefault(structure, []).append(row)
    matches = []
    valid = 0
    for row in compounds:
        structure = canonical(row["smiles"])
        valid += structure is not None
        if structure in index:
            matches.append({"bbbc_compound": row["compound"],
                            "prism_names": sorted({r["name"] for r in index[structure]}),
                            "prism_broad_ids": sorted({r["broad_id"] for r in index[structure]}),
                            "prism_doses_uM": sorted({r["dose"] for r in index[structure]})})
    receipt["bbbc021_prism_input_join"] = {
        "rule": "RDKit canonical isomeric SMILES equality; no normalization",
        "valid_bbbc_structures": valid, "matched_bbbc_compounds": len(matches),
        "matches": matches,
        "interpretation": "Compound identity overlap only. BBBC 24 h imaging is not PRISM 5 day viability or a same-unit bridge.",
    }
    (ROOT / "ASSET_AUDIT.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps({"source_hashes_ok": all(r["match"] for r in receipt["source_hash_checks"]),
                      "bbbc021": receipt["bbbc021"], "structure_matches": len(matches),
                      "local_assets": [{k: r[k] for k in ("path", "files", "bytes")} for r in receipt["local_assets"]]}, indent=2))


if __name__ == "__main__":
    main()
