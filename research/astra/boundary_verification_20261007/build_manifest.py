"""Record the final independent-verification artifacts once."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    artifacts = []
    for path in sorted(HERE.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or path.name == "RUN_MANIFEST.json":
            continue
        artifacts.append({"path": str(path.relative_to(HERE)).replace("\\", "/"),
                          "bytes": path.stat().st_size,
                          "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    manifest = {"schema": "independent_boundary_verification_v1",
                "created_utc": datetime.now(timezone.utc).isoformat(),
                "status": "Complete; write-quiescent independent verification",
                "canonical_study": "../boundary_acquisition_20261007/packet2 and run1",
                "artifacts": artifacts,
                "receipt": "VERDICT.json", "assessment": "VERIFIED.json",
                "source_reconciliation": "PROVENANCE_RECONCILIATION.json",
                "new_biological_outcome_downloads": 0,
                "new_API_calls": 0, "fresh_STATE_forwards": 0,
                "production_edits": 0, "commits": 0, "pushes": 0}
    destination = HERE / "RUN_MANIFEST.json"
    with destination.open("x", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, allow_nan=False); handle.write("\n")
    check = json.loads(destination.read_text(encoding="utf-8"))
    mismatch = [row["path"] for row in check["artifacts"]
                if hashlib.sha256((HERE / row["path"]).read_bytes()).hexdigest() != row["sha256"]]
    assert not mismatch
    print(json.dumps({"artifacts": len(artifacts), "hash_mismatches": len(mismatch),
                      "manifest_sha256": hashlib.sha256(destination.read_bytes()).hexdigest()}))


if __name__ == "__main__":
    main()
