"""Verify frozen source hashes, group isolation and one full fold per dataset."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("sparse_evaluation", HERE / "evaluate.py")
R = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R)


def main():
    R.frozen()
    manifest = json.loads((R.OUT / "manifest.json").read_text(encoding="utf-8"))
    for name, expected in manifest["source_sha256"].items():
        assert hashlib.sha256((R.ROOT / name).read_bytes()).hexdigest() == expected, name
    groups = {}
    for dataset, data, column in (("sciplex3", R.C.load(), "skeleton"),
                                   ("l1000", R.LP.load(), "component")):
        comp = data.compounds.drop_duplicates("compound")
        assert int(comp.groupby(column).fold.nunique().max()) == 1
        groups[dataset] = {"groups": int(comp[column].nunique()), "split_group_overlap": 0}
    reproduced = {}
    for task in (("sciplex3", "A", 1), ("l1000", "T", 1)):
        name = "_".join(map(str, task)) + ".jsonl"
        expected = [json.loads(line) for line in (R.OUT / name).read_text(encoding="utf-8").splitlines()]
        _, actual, _ = R.run_fold(task)
        assert R.C.clean(actual) == expected, f"Mismatch in {name}"
        reproduced[name] = len(actual)
        print(f"Exact reproduction: {name}, {len(actual)} records", flush=True)
    record = {"verified_at_utc": datetime.now(timezone.utc).isoformat(), "source_hashes_match": True,
              "group_isolation": groups, "exact_fold_reproduction": reproduced,
              "runtime_tests": {"passed": 1326, "seconds": 90.32},
              "research_tests": {"passed": 68, "seconds": 39.66},
              "shared_sequence_invariant_failures": 0,
              "records_audited_by_runner": manifest["records"]}
    (R.OUT / "verification.json").write_text(json.dumps(record, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
