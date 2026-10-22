"""Verify chemistry reservation without loading a functional/count/feature file."""
import collections
import hashlib
import json
from pathlib import Path

from rdkit import Chem, DataStructs
from rdkit.Chem import rdFingerprintGenerator

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261021/oasis_evaluation_contract"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    checks = []
    def check(name, condition):
        checks.append({"name": name, "passed": bool(condition)})
        if not condition:
            raise AssertionError(name)
    saved = json.loads((OUT / "RESERVATION_v2.json").read_text())
    source = ROOT / saved["source_path"]
    check("source pinned", sha(source) == saved["source_sha256"])
    check("protocol pinned", sha(OUT / "PROTOCOL.md") == saved["protocol_sha256"])
    check("code pinned", sha(Path(__file__).with_name("reserve_chemistry.py")) == saved["code_sha256"])
    original = json.loads((OUT / "RESERVATION.json").read_text())
    check("initial failed code retained", sha(Path(__file__).with_name("reserve_chemistry_initial_failed.py")) == original["code_sha256"])
    records = json.loads(source.read_text())["compounds"]
    rows = saved["mapping"]
    check("all original labels retained", {r["compound_id"] for r in records} == {r["compound_id"] for r in rows} and len(records) == len(rows))
    check("known structure counts reconciled", sum(r["role"] != "quarantine" for r in rows) == sum(r["identity_status"] == "KNOWN_SOURCE_STRUCTURE" for r in records))
    check("quarantined structures retained", all(r["role"] == "quarantine" for r in rows if r["source_identity_status"] != "KNOWN_SOURCE_STRUCTURE"))
    by_parent, by_scaffold, by_group = collections.defaultdict(set), collections.defaultdict(set), collections.defaultdict(set)
    known = [r for r in rows if r["role"] != "quarantine"]
    for row in known:
        by_parent[row["parent_smiles"]].add(row["role"])
        if row["scaffold"]:
            by_scaffold[row["scaffold"]].add(row["role"])
        by_group[row["group_id"]].add(row["role"])
    check("parent disjoint", all(len(v) == 1 for v in by_parent.values()))
    check("nonempty scaffold disjoint", all(len(v) == 1 for v in by_scaffold.values()))
    check("group disjoint", all(len(v) == 1 for v in by_group.values()))
    check("all three roles populated", {r["role"] for r in known} == {"dev", "selection", "reserve"})
    generator = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    fps = [generator.GetFingerprint(Chem.MolFromSmiles(r["parent_smiles"])) for r in known]
    cross_max = 0.0
    for i in range(1, len(fps)):
        values = DataStructs.BulkTanimotoSimilarity(fps[i], fps[:i])
        for j, value in enumerate(values):
            if known[i]["role"] != known[j]["role"]:
                cross_max = max(cross_max, value)
    check("all close analogues disjoint", cross_max < saved["similarity_threshold"])
    check("reported maximum reproduced", cross_max == saved["summary"]["cross_role_max_tanimoto"])
    check("role counts reconciled", dict(collections.Counter(r["role"] for r in rows)) == saved["summary"]["role_label_counts"])
    receipt = {"status": "PASS", "checks": checks, "checks_passed": len(checks),
               "reservation_sha256": sha(OUT / "RESERVATION_v2.json"),
               "raw_outcome_files_read": 0, "count_or_morphology_files_read": 0,
               "scientific_status": "Split integrity only; world/agent/inheritance/RSI NOT_TESTED"}
    (OUT / "VERIFICATION.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps({"status": "PASS", "checks_passed": len(checks)}))


if __name__ == "__main__":
    main()
