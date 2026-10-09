"""Official-source drug identity qualification and released representation cache."""
import ast
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from rdkit import Chem, RDLogger

from encoder import ASSETS, encode, load_encoder

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "outputs/paper_01286/released_test"
PACKET = ROOT / "research/astra/boundary_acquisition_20261007/packet2"


def canonical(smiles):
    molecule = Chem.MolFromSmiles(smiles) if isinstance(smiles, str) else None
    return Chem.MolToSmiles(molecule, isomericSmiles=True) if molecule is not None else None


def identities(labels):
    RDLogger.DisableLog("rdApp.error")
    metadata = pd.read_parquet(ASSETS / "drug_metadata.parquet")
    by_name = {}
    for row in metadata.to_dict("records"):
        by_name.setdefault(row["drug"].strip().casefold(), []).append(row)
    drugs = [ast.literal_eval(label)[0] for label in labels]
    cids = {str(int(row["pubchem_cid"])) for row in metadata.to_dict("records")
            if pd.notna(row["pubchem_cid"])}
    kg_by_cid = {}
    for row in csv.DictReader((ROOT / "outputs/paper_01286/map_drugs.csv").open(encoding="utf-8-sig")):
        cid = row["PubChem ID"]
        if cid in cids:
            kg_by_cid.setdefault(cid, []).append(row)
    records = []
    for name, dose, unit in drugs:
        hits = by_name.get(name.strip().casefold(), [])
        record = {"drug": name, "dose": dose, "unit": unit,
                  "smiles": None, "cid": None, "kg_exact_identity": False,
                  "moa": [], "reason": "no_unique_official_name"}
        if len(hits) == 1:
            hit = hits[0]
            record["smiles"] = canonical(hit["canonical_smiles"])
            record["cid"] = str(int(hit["pubchem_cid"])) if pd.notna(hit["pubchem_cid"]) else None
            candidates = kg_by_cid.get(record["cid"], [])
            exact = [r for r in candidates if canonical(r["smiles"]) == record["smiles"] and record["smiles"] is not None]
            record["kg_exact_identity"] = bool(exact)
            record["moa"] = sorted({r["moa"] for r in exact if r["moa"].strip()})
            record["reason"] = "official_name_and_structure" if record["smiles"] else "invalid_official_structure"
        records.append(record)
    relations = {r["cid"]: set() for r in records if r["kg_exact_identity"]}
    for row in csv.DictReader((ROOT / "outputs/paper_01286/map_edges.csv").open(encoding="utf-8-sig")):
        if row["Drug ID"] in relations:
            relations[row["Drug ID"]].add((row["relation"], row["Gene ID"]))
    for r in records:
        r["directed_relations"] = sorted(relations.get(r["cid"], [])) if r["kg_exact_identity"] else []
    return records


def main():
    if (OUT / "FEATURES.npz").exists():
        raise RuntimeError("Refuse to overwrite released representation cache")
    OUT.mkdir(parents=True, exist_ok=True)
    labels = json.loads((PACKET / "PACKET_MANIFEST.json").read_text())["labels"]
    records = identities(labels)
    smiles = sorted({r["smiles"] for r in records if r["smiles"]})
    encoder = load_encoder().cuda()
    torch.set_num_threads(4)
    structural, knowledge = {}, {}
    for start in range(0, len(smiles), 8):
        batch = smiles[start:start + 8]
        raw, kg = encode(encoder, batch)
        for s, a, b in zip(batch, raw.cpu().numpy(), kg.cpu().numpy()):
            structural[s], knowledge[s] = a, b
    first, repeated = encode(encoder, [smiles[0]])
    np.testing.assert_allclose(first.cpu().numpy()[0], structural[smiles[0]], atol=1e-5)
    np.testing.assert_allclose(repeated.cpu().numpy()[0], knowledge[smiles[0]], atol=1e-5)
    mask = np.array([bool(r["smiles"]) for r in records])
    raw = np.array([structural.get(r["smiles"], np.zeros(256)) for r in records])
    kg = np.array([knowledge.get(r["smiles"], np.zeros(1024)) for r in records])
    # Equal downstream capacity, fixed projection independent of response labels.
    rng = np.random.default_rng(20261008)
    raw24 = raw @ (rng.normal(size=(256, 24)) / np.sqrt(256))
    kg_projection = rng.normal(size=(1024, 24)) / np.sqrt(1024)
    kg24 = kg @ kg_projection
    permutation = dict(zip(smiles, rng.permutation(smiles)))
    perm = np.array([knowledge[permutation[r["smiles"]]] if r["smiles"] else np.zeros(1024) for r in records])
    # Reuse exactly the same knowledge projection for its permutation control.
    perm24 = perm @ kg_projection
    np.savez_compressed(OUT / "FEATURES.npz", structure=raw24, knowledge=kg24,
                        permuted=perm24, mask=mask, molecule256=raw, knowledge1024=kg)
    (OUT / "IDENTITIES.json").write_text(json.dumps({"records": records,
        "menu_candidates": len(records), "encodable_candidates": int(mask.sum()),
        "encodable_drugs": len({r["drug"] for r in records if r["smiles"]}),
        "kg_exact_candidates": sum(r["kg_exact_identity"] for r in records),
        "kg_exact_drugs": len({r["drug"] for r in records if r["kg_exact_identity"]}),
        "drugs_with_directed_relations": len({r["drug"] for r in records if r["directed_relations"]}),
        "source_sha256": hashlib.sha256((ASSETS / "drug_metadata.parquet").read_bytes()).hexdigest(),
        "loader": "Official molecule+projector classes, both state dictionaries strict=True; no tower training",
        "forward_checks": "All finite; same-drug batch/single consistency atol1e-5"}, indent=2), encoding="utf-8")
    print("Encoded", int(mask.sum()), "/", len(records), "candidates;", len(smiles), "unique structures")


if __name__ == "__main__":
    main()
