"""Chemical-identity manifest from identity-only rows; no outcome access."""
import collections
import hashlib
import json
import re
from pathlib import Path

from rdkit import Chem, RDLogger
from rdkit.Chem import inchi

from audit_identity import ROOT, OLD, LOG

RDLogger.DisableLog("rdApp.*")


def main():
    rows = json.loads((LOG / "IDENTITY_ROWS.json").read_text())
    source_manifest = json.loads((OLD / "SOURCE_MANIFEST.json").read_text())
    hashes = {x["Key"]: x["sha256"] for x in source_manifest}
    grouped = collections.defaultdict(list)
    for row in rows:
        if row["library"] == "oasis" and str(row["compound_name"]).upper() != "DMSO":
            grouped[row["compound_id"]].append(row)
    result = []
    for compound_id, group in sorted(grouped.items()):
        source_smiles = sorted({str(x["compound_smiles"]) for x in group if x.get("compound_smiles")})
        canonical = set()
        computed_keys = set()
        computed_inchi = set()
        invalid = []
        for smiles in source_smiles:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                invalid.append(smiles)
                continue
            canonical.add(Chem.MolToSmiles(mol, canonical=True, isomericSmiles=True))
            chemical_inchi = inchi.MolToInchi(mol)
            computed_inchi.add(chemical_inchi)
            computed_keys.add(inchi.InchiToInchiKey(chemical_inchi))
        source_inchi = sorted({str(x["compound_inchi"]) for x in group if x.get("compound_inchi")})
        source_keys = sorted({x for x in source_inchi if re.fullmatch(r"[A-Z]{14}-[A-Z]{10}-[A-Z]", x)})
        unresolved_conflict = len(canonical) > 1 or len(computed_keys) > 1 or bool(invalid)
        status = "KNOWN_SOURCE_STRUCTURE" if len(canonical) == 1 and not unresolved_conflict else (
            "QUARANTINE_STRUCTURE_CONFLICT" if unresolved_conflict else "QUARANTINE_STRUCTURE_MISSING")
        result.append({"compound_id": compound_id, "source_compound_names": sorted({x["compound_name"] for x in group}),
                       "source_smiles": source_smiles, "canonical_source_smiles": sorted(canonical),
                       "source_inchi_or_inchikey": source_inchi, "source_inchikey": source_keys,
                       "computed_standard_inchi": sorted(computed_inchi), "computed_inchikey": sorted(computed_keys),
                       "oasis_ids": sorted({str(x["OASIS_ID"]) for x in group if x.get("OASIS_ID")}),
                       "source_saltdata": sorted({str(x["compound_saltdata"]) for x in group if x.get("compound_saltdata")}),
                       "source_formula": sorted({str(x["compound_formula"]) for x in group if x.get("compound_formula")}),
                       "source_files": [{"key": key, "sha256": hashes[key]} for key in sorted({x["source_file"] for x in group})],
                       "invalid_source_smiles": invalid, "identity_status": status,
                       "multiple_oasis_ids_same_structure": len({str(x["OASIS_ID"]) for x in group if x.get("OASIS_ID")}) > 1 and len(canonical) == 1,
                       "identity_normalization": "RDKit canonical isomeric SMILES only; salt removal/tautomer grouping not applied"})
    output = {"scope": "All 1085 source labels; missing/conflicting identities retained in quarantine without outcome selection",
              "source_identity_rows_sha256": hashlib.sha256((LOG / "IDENTITY_ROWS.json").read_bytes()).hexdigest(),
              "rdkit_version": __import__("rdkit").__version__, "compounds": result}
    (LOG / "STRUCTURE_MANIFEST.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    summary = {"compound_count": len(result), "status_counts": dict(collections.Counter(x["identity_status"] for x in result)),
               "multiple_oasis_ids_same_structure": sum(x["multiple_oasis_ids_same_structure"] for x in result),
               "source_structures_with_multiple_fragments": sum(any("." in s for s in x["canonical_source_smiles"]) for x in result)}
    (LOG / "STRUCTURE_SUMMARY.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
