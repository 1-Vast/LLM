"""Freeze compound groups and chemical inputs without opening phenotype values."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import rdFingerprintGenerator
from rdkit import DataStructs

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "cpjump_source"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    assert not (ROOT / "b_metadata_freeze.json").exists(), "Preserve frozen metadata"
    table = pd.read_csv(SOURCE / "compound_identity_and_annotations.tsv", sep="\t", dtype=str, keep_default_na=False)
    table = table[table.pert_type.eq("trt")].sort_values("broad_sample").reset_index(drop=True)
    group = pd.read_csv(SOURCE / "compound_structure_grouping.tsv", sep="\t", dtype=str, keep_default_na=False).set_index("broad_sample")
    parent = {s: s for s in table.broad_sample}
    def find(s):
        while parent[s] != s:
            s = parent[s]
        return s
    def union(a, b):
        a, b = find(a), find(b)
        parent[max(a, b)] = min(a, b)
    for column in ("same_name_group", "exact_InChIKey_group", "connectivity_block_group"):
        seen = {}
        for s in table.broad_sample:
            value = group.loc[s, column]
            if value:
                if value in seen:
                    union(s, seen[value])
                seen[value] = s
    table["group"] = [find(s) for s in table.broad_sample]
    table["fold"] = [int(hashlib.sha256(("20261030|" + g).encode()).hexdigest(), 16) % 5 for g in table.group]
    assert len(table) == 260
    table.to_csv(ROOT / "b_compound_split.tsv", sep="\t", index=False, lineterminator="\n")
    generator = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=1024, includeChirality=True)
    fingerprints = []
    for smiles in table.smiles:
        mol = Chem.MolFromSmiles(smiles)
        assert mol is not None, "Structure not admitted"
        array = np.zeros(1024, dtype=np.uint8)
        DataStructs.ConvertToNumpyArray(generator.GetFingerprint(mol), array)
        fingerprints.append(array)
    np.savez_compressed(ROOT / "b_chemical_features.npz", compounds=table.broad_sample.to_numpy(dtype=str), fingerprints=np.asarray(fingerprints))
    pins = [Path(__file__), SOURCE / "compound_identity_and_annotations.tsv", SOURCE / "compound_structure_grouping.tsv",
            SOURCE / "selected_well_identity_freeze.tsv", ROOT / "b_compound_split.tsv", ROOT / "b_chemical_features.npz"]
    freeze = {"phase": "before_phenotype_values", "phenotype_values_opened": False,
        "queries": 260, "groups": table.group.nunique(), "names": table.pert_iname.nunique(),
        "fold_counts": {str(k): int(v) for k, v in table.groupby("fold").size().items()},
        "grouping": "Transitive closure of source normalized name, exact InChIKey and connectivity first block; grouping is not intervention equivalence",
        "fold_rule": "integer sha256('20261030|'+lexical minimum source ID in group) modulo5",
        "sha256": {str(p): sha(p) for p in pins}, "http_attempts": 0}
    (ROOT / "b_metadata_freeze.json").write_text(json.dumps(freeze, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: freeze[k] for k in ("queries", "groups", "names", "fold_counts")}))

if __name__ == "__main__":
    main()
