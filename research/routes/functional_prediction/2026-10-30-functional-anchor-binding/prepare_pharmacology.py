"""Project independent 2020 pharmacology metadata; never open CGI outcomes."""
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from rdkit import Chem, rdBase
from rdkit.Chem.MolStandardize import rdMolStandardize

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[3]
PARENT = ROOT.parent / "2026-10-30-conditional-intervention-admission"
DRUGS = PROJECT / "data/external/lincs_l1000_gse92742/repurposing_drugs_20200324.txt"
SAMPLES = DRUGS.with_name("repurposing_samples_20200324.txt")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_table(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader((line for line in stream if not line.startswith("!")), delimiter="\t"))


def parent_key(smiles):
    with rdBase.BlockLogs():
        molecule = Chem.MolFromSmiles(smiles)
        if molecule is None:
            return None
        molecule = rdMolStandardize.FragmentParent(molecule)
        Chem.SanitizeMol(molecule)
        return Chem.MolToSmiles(molecule, isomericSmiles=True)


def main():
    destination = ROOT / "pharmacology_freeze.json"
    assert not destination.exists(), "metadata freeze already exists"
    rows = read_table(PARENT / "identity_split.tsv")
    queries = sorted((r for r in rows if r["partition"] == "development" and r["representative"] == "True"), key=lambda r: r["compound"])
    assert len(queries) == 231 and len({r["compound"] for r in queries}) == 231
    drugs = read_table(DRUGS)
    samples = read_table(SAMPLES)
    annotations = defaultdict(set)
    for row in drugs:
        targets = tuple(sorted(set(filter(None, row["target"].split("|")))))
        mechanisms = tuple(sorted(set(filter(None, row["moa"].split("|")))))
        annotations[row["pert_iname"]].add((targets, mechanisms))
    names_by_structure = defaultdict(set)
    rejected = defaultdict(int)
    for row in samples:
        if row["qc_incompatible"] != "0":
            rejected["qc_incompatible_or_unknown"] += 1
            continue
        key = parent_key(row["smiles"])
        if key is None:
            rejected["unparseable_smiles"] += 1
            continue
        names_by_structure[key].add(row["pert_iname"])
    projected = []
    for row in queries:
        names = sorted(names_by_structure.get(parent_key(row["parent_smiles"]), []))
        signatures = {signature for name in names for signature in annotations.get(name, set())}
        # Conflicting alias annotations are missing, rather than silently unioned.
        status = "unmatched_structure" if not names else "missing_annotation"
        targets, mechanisms = (), ()
        if len(signatures) > 1:
            status = "ambiguous_annotation"
        elif len(signatures) == 1:
            targets, mechanisms = next(iter(signatures))
            status = "annotated" if targets or mechanisms else "empty_annotation"
        projected.append({"compound": row["compound"], "development_fold": row["development_fold"],
                          "parent_smiles": row["parent_smiles"], "match_status": status,
                          "source_pert_inames": "|".join(names), "targets": "|".join(targets),
                          "moa": "|".join(mechanisms)})
    tokens = sorted({prefix + token for row in projected for prefix, field in [("target:", "targets"), ("moa:", "moa")] for token in row[field].split("|") if token})
    token_index = {token: i for i, token in enumerate(tokens)}
    features = np.zeros((len(projected), len(tokens) + 1), dtype=np.float64)
    for i, row in enumerate(projected):
        for prefix, field in [("target:", "targets"), ("moa:", "moa")]:
            for token in filter(None, row[field].split("|")):
                features[i, token_index[prefix + token]] = 1
        features[i, -1] = row["match_status"] == "annotated"
    roster = ROOT / "pharmacology_identity.tsv"
    with roster.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(projected[0]), delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(projected)
    array = ROOT / "pharmacology_features.npz"
    np.savez_compressed(array, compounds=np.array([r["compound"] for r in projected]),
                        features=features, feature_names=np.array(tokens + ["annotation_available"]))
    counts = {status: sum(r["match_status"] == status for r in projected) for status in sorted({r["match_status"] for r in projected})}
    record = {"scope": "Metadata-only projection after prior development exposure; no new or protected CGI calls read",
              "source_date": "2020-03-24", "source_declared_restriction": "Drug Repurposing Hub: non-commercial research use",
              "identity_rule": "RDKit isomeric canonical FragmentParent equality; no name/CID/fuzzy query join or tautomer matching",
              "limits": "Parent-structure/annotation correspondence is not certification of assay stock or actual target engagement; source stereochemistry may be unspecified",
              "ambiguity_rule": "All exact-parent aliases must agree on the complete target/MOA signature; conflicting or absent signatures are missing",
              "sample_qc_rule": "Only source qc_incompatible exactly0; purity is not filtered",
              "compounds": len(projected), "counts": counts, "feature_shape": list(features.shape),
              "annotated_by_fold": {str(f): sum(r["match_status"] == "annotated" and r["development_fold"] == str(f) for r in projected) for f in range(3)},
              "excluded_source_sample_rows": dict(rejected),
              "sha256": {str(p): sha(p) for p in [DRUGS, SAMPLES, PARENT / "identity_split.tsv", Path(__file__), roster, array]},
              "outcome_access": False, "http_attempts": 0, "held_out_queries_projected": 0}
    destination.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: record[k] for k in ["compounds", "counts", "feature_shape", "annotated_by_fold", "outcome_access"]}, indent=2))


if __name__ == "__main__":
    main()
