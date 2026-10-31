"""Freeze scaffold groups using only source identity and concentration metadata."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import rdkit
from rdkit import Chem, DataStructs
from rdkit.Chem import rdFingerprintGenerator
from rdkit.Chem.MolStandardize import rdMolStandardize
from rdkit.Chem.Scaffolds import MurckoScaffold

ROOT = Path(__file__).resolve().parent
SALT = "MAESTRO_CGI_20261030_v1"


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main():
    paths = [ROOT / "cgi_source" / x for x in
             ["screen_identity.tsv", "compound_identity.tsv"]]
    screens, compounds = [pd.read_csv(p, sep="\t", dtype=str).fillna("") for p in paths]
    assert compounds["Internal Compound ID"].is_unique
    assert screens["Screen Name"].is_unique
    generator = rdFingerprintGenerator.GetMorganGenerator(
        radius=2, fpSize=1024, includeChirality=True)
    structures = {}
    fingerprints = {}
    for row in compounds.to_dict("records"):
        ident = row["Internal Compound ID"]
        mol = Chem.MolFromSmiles(row["SMILES string"]) if row["SMILES string"] else None
        if mol is None:
            continue
        parent = rdMolStandardize.FragmentParent(rdMolStandardize.Cleanup(mol))
        Chem.SanitizeMol(parent)
        key = Chem.MolToSmiles(parent, isomericSmiles=False)
        scaffold = MurckoScaffold.MurckoScaffoldSmiles(mol=parent,
                                                     includeChirality=False)
        # Keep all acyclic compounds in one scaffold group; no empty-scaffold escape.
        group = scaffold or "ACYCLIC"
        group_hash = digest(SALT + "|" + group)
        partition = "held_out" if int(group_hash[:16], 16) % 10 < 3 else "development"
        structures[ident] = {"parent_smiles": key, "scaffold": group,
                             "group_hash": group_hash, "partition": partition,
                             "development_fold": int(group_hash[16:32], 16) % 3}
        array = np.zeros(1024, dtype=np.uint8)
        DataStructs.ConvertToNumpyArray(generator.GetFingerprint(parent), array)
        fingerprints[ident] = array
    rows = []
    exclusions = []
    scales = {"M": 1., "mM": 1e-3, "uM": 1e-6, "μM": 1e-6,
              "µM": 1e-6, "nM": 1e-9, "pM": 1e-12}
    for row in screens.to_dict("records"):
        reason = None
        ident = row["Internal Compound ID"]
        if row["Second Compound ID"]:
            reason = "co_treatment"
        elif row["Round"] not in {f"Round-{i:02d}" for i in range(9)}:
            reason = "outside_primary_rounds_0_to_8"
        elif ident not in structures:
            reason = "missing_or_unparsed_source_structure"
        try:
            dose = float(row["Final concentration"]) * scales[row["Concentration units"]]
            if not np.isfinite(dose) or dose <= 0:
                reason = reason or "nonpositive_or_nonfinite_dose"
        except (ValueError, KeyError):
            dose = None
            reason = reason or "unsupported_molar_dose"
        if reason:
            exclusions.append({"screen": row["Screen Name"], "reason": reason})
            continue
        rows.append({"screen": row["Screen Name"], "compound": ident,
                     "compound_name": row["Compound Name"], "round": row["Round"],
                     "dose_M": dose, **structures[ident]})
    frame = pd.DataFrame(rows).sort_values(["compound", "round", "screen"])
    # One deterministic representative screen per compound for the initial diagnostic.
    # Other doses/screens stay grouped and unread, not independent extra examples.
    representative = frame.drop_duplicates("compound", keep="first").copy()
    frame["representative"] = frame["screen"].isin(representative["screen"])
    frame.to_csv(ROOT / "identity_split.tsv", sep="\t", index=False, lineterminator="\n")
    ids = representative["compound"].tolist()
    np.savez_compressed(ROOT / "chemical_features.npz", compounds=np.array(ids),
                        fingerprints=np.vstack([fingerprints[x] for x in ids]))
    summary = {
        "scope": "metadata-only; no CGI scores or hit labels read",
        "salt": SALT, "rdkit_version": rdkit.__version__,
        "input_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "split_sha256": hashlib.sha256((ROOT / "identity_split.tsv").read_bytes()).hexdigest(),
        "feature_sha256": hashlib.sha256((ROOT / "chemical_features.npz").read_bytes()).hexdigest(),
        "eligible_screen_count": len(frame), "representative_compound_count": len(representative),
        "scaffold_group_count": representative["scaffold"].nunique(),
        "partition_counts": representative["partition"].value_counts().to_dict(),
        "partition_groups": representative.groupby("partition")["scaffold"].nunique().to_dict(),
        "development_fold_counts": representative[representative.partition == "development"]
                                   ["development_fold"].value_counts().to_dict(),
        "exclusions": exclusions,
        "features": "Morgan radius2/1024bit/chirality, source SMILES standardized fragment parent; dose separately metadata-only",
        "not_features": ["class", "subclass", "post_treatment_population_doublings",
                         "hit_counts", "CGI-derived annotations", "target-response panels"],
        "claim_limit": "scaffold-separated fixed processed-label diagnostic, not independent preparations or mechanisms"
    }
    (ROOT / "identity_freeze.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k not in
                      ["exclusions", "input_sha256", "not_features"]}, indent=2))
    print("excluded_screen_count", len(exclusions))


if __name__ == "__main__":
    main()
