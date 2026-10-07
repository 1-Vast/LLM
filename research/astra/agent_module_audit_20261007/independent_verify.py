"""Rebuild metadata counts and preservation checks without importing the diagnostic."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=HERE / "independent_verification.json")
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    saved = json.loads((HERE / "condition_source_results.json").read_text(encoding="utf-8"))
    rebuilt = {}
    for context, source in saved["inputs"].items():
        path = ROOT / source["path"]
        assert sha256(path) == source["sha256"], context
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["revision"] == source["revision"], context
        rows = []
        for label, plate, count in data["condition_plate_counts"]:
            components = ast.literal_eval(label)
            assert len(components) == 1 and len(components[0]) == 3
            drug, dose, unit = components[0]
            if drug != "DMSO_TF":
                rows.append((label, str(plate), drug, dose, unit))
        assert len(set((r[0], r[1]) for r in rows)) == len(rows)
        drugs = {r[2] for r in rows}
        labels = {r[0] for r in rows}
        expected = {
            "source_groups": len(rows), "drugs": len(drugs), "labels": len(labels),
            "multiple_doses_drugs": sum(len({(r[3], r[4]) for r in rows if r[2] == d}) > 1 for d in drugs),
            "multi_source_labels": sum(sum(r[0] == label for r in rows) > 1 for label in labels),
            "comma_containing_drug_source_groups": sum("," in r[2] for r in rows),
            "first_source_per_drug_exact_matches": len(drugs),
            "first_source_per_label_exact_matches": len(labels),
            "complete_scope_exact_matches": len(rows),
        }
        assert all(saved["results"][context][k] == v for k, v in expected.items()), context
        assert saved["results"][context]["drug_only_masked_requests"] == {
            "clarify_requested_dose_and_unit": len(rows)}
        rebuilt[context] = expected
    initial = json.loads((HERE / "INITIAL_HASHES.json").read_text(encoding="utf-8"))
    modified = [path for path, digest in initial.items() if sha256(ROOT / path) != digest]
    allowed = {"src/agent/context.py", "src/agent/discovery.py", "src/agent/orchestrator.py", "src/agent/prediction.py"}
    assert set(modified) <= allowed, modified
    receipt = {"status": "PASS", "metadata_counts_rebuilt": rebuilt,
               "initial_files_checked": len(initial), "modified_initial_files": modified,
               "historical_protocol_and_manifest_hashes_unchanged": True,
               "verification_limits": "Metadata counts and sampled contract scope; no STATE inference or LLM decision-value verification"}
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(receipt, stream, indent=2)
        stream.write("\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
