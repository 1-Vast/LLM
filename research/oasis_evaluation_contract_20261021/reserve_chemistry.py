"""Outcome-blind chemical reservation. Never opens functional/feature sources."""
from __future__ import annotations

import collections
import hashlib
import json
from pathlib import Path
import time

from rdkit import Chem, DataStructs, RDLogger, __version__ as rdkit_version
from rdkit.Chem import rdFingerprintGenerator
from rdkit.Chem.MolStandardize import rdMolStandardize
from rdkit.Chem.Scaffolds import MurckoScaffold

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261021/oasis_evaluation_contract"
SOURCE = ROOT / "log/20261021/oasis_identity_qualification/STRUCTURE_MANIFEST.json"
SALT = "oasis_reservation_20261021_v1"
THRESHOLD = 0.70
RDLogger.DisableLog("rdApp.warning")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def group_records(records):
    """Pure chemical calculation: no phenotype, count, QC or response argument."""
    ids = [r["compound_id"] for r in records]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate compound IDs in structure manifest")
    output, known, molecules = [], [], []
    for r in sorted(records, key=lambda x: x["compound_id"]):
        row = {"compound_id": r["compound_id"], "source_identity_status": r["identity_status"]}
        row.update(role="quarantine", reason=r["identity_status"], parent_smiles=None, scaffold=None, group_id=None)
        smiles = r.get("canonical_source_smiles", [])
        if r["identity_status"] == "KNOWN_SOURCE_STRUCTURE" and len(smiles) == 1:
            try:
                original = Chem.MolFromSmiles(smiles[0])
                if original is None:
                    raise ValueError("unparseable source structure")
                mol = rdMolStandardize.Cleanup(original)
                mol = rdMolStandardize.FragmentParent(mol)
                mol = rdMolStandardize.Uncharger().uncharge(mol)
                Chem.SanitizeMol(mol)
                Chem.RemoveStereochemistry(mol)
                parent = Chem.MolToSmiles(mol, canonical=True, isomericSmiles=False)
                scaffold = MurckoScaffold.MurckoScaffoldSmiles(mol=mol, includeChirality=False)
                if not parent:
                    raise ValueError("empty parent")
                row.update(parent_smiles=parent, scaffold=scaffold,
                           source_fragment_count=len(Chem.GetMolFrags(original)), reason=None)
                known.append(row)
                molecules.append(mol)
            except (ValueError, RuntimeError) as exc:
                row["reason"] = "STANDARDISATION_FAILED:" + type(exc).__name__
        output.append(row)
    if not known:
        raise ValueError("No known chemical structures; no split can be qualified")
    parent = list(range(len(known)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j):
        a, b = find(i), find(j)
        if a != b:
            parent[max(a, b)] = min(a, b)

    buckets = {}
    for i, row in enumerate(known):
        keys = [("parent", row["parent_smiles"])]
        if row["scaffold"]:
            keys.append(("scaffold", row["scaffold"]))
        for key in keys:
            if key in buckets:
                union(i, buckets[key])
            else:
                buckets[key] = i
    generator = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    fps = [generator.GetFingerprint(m) for m in molecules]
    similarity_edges = 0
    for i in range(1, len(fps)):
        for j, value in enumerate(DataStructs.BulkTanimotoSimilarity(fps[i], fps[:i])):
            if value >= THRESHOLD:
                union(i, j)
                similarity_edges += 1
    groups = collections.defaultdict(list)
    for i in range(len(known)):
        groups[find(i)].append(i)
    for members in groups.values():
        text = "\n".join(sorted({known[i]["parent_smiles"] for i in members}))
        token = hashlib.sha256(text.encode()).hexdigest()
        value = int.from_bytes(hashlib.sha256((SALT + "|" + token).encode()).digest()[:8], "big") / 2**64
        role = "dev" if value < 0.60 else ("selection" if value < 0.80 else "reserve")
        for i in members:
            known[i].update(group_id=token, role=role)
    cross_max = 0.0
    for i in range(1, len(fps)):
        values = DataStructs.BulkTanimotoSimilarity(fps[i], fps[:i])
        for j, value in enumerate(values):
            if known[i]["role"] != known[j]["role"]:
                cross_max = max(cross_max, value)
    if cross_max >= THRESHOLD:
        raise AssertionError("Cross-role close analogue escaped grouping")
    summary = {"labels": len(output), "known_standardised": len(known),
               "role_label_counts": dict(collections.Counter(r["role"] for r in output)),
               "role_group_counts": dict(collections.Counter(known[v[0]]["role"] for v in groups.values())),
               "largest_group_labels": max(map(len, groups.values())),
               "chemical_groups": len(groups), "similarity_edges": similarity_edges,
               "cross_role_max_tanimoto": cross_max,
               "quarantine_reasons": dict(collections.Counter(r["reason"] for r in output if r["role"] == "quarantine"))}
    return output, summary


def write_once(path, value):
    encoded = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists():
        if path.read_text(encoding="utf-8") != encoded:
            raise RuntimeError("Existing reservation differs; refuse to overwrite")
        return False
    path.write_text(encoded, encoding="utf-8")
    return True


def main():
    start, cpu = time.perf_counter(), time.process_time()
    before = sha(SOURCE)
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    mapping, summary = group_records(source["compounds"])
    if before != sha(SOURCE):
        raise RuntimeError("Source manifest changed during grouping")
    result = {"scope": "Chemical reservation only; no outcomes or morphological/count features opened",
              "source_path": str(SOURCE.relative_to(ROOT)), "source_sha256": before,
              "protocol_sha256": sha(OUT / "PROTOCOL.md"), "code_sha256": sha(Path(__file__)),
              "rdkit": rdkit_version, "salt": SALT, "similarity_threshold": THRESHOLD,
              "summary": summary, "mapping": mapping}
    OUT.mkdir(parents=True, exist_ok=True)
    created = write_once(OUT / "RESERVATION_v2.json", result)
    (OUT / "SPLIT_STATUS_v2.json").write_text(json.dumps({"reservation_created": created, "summary": summary,
        "wall_seconds": time.perf_counter() - start, "process_cpu_seconds": time.process_time() - cpu,
        "functional_values_opened": False, "biological_qualification": "NOT_ESTABLISHED"}, indent=2), encoding="utf-8")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
