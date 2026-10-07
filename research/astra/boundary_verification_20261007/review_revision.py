"""Record the corrected protocol's acceptance before registration and target replay."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent / "boundary_acquisition_20261007"


def main():
    path = STUDY / "DRAFT_PROTOCOL.json"
    protocol = json.loads(path.read_text())
    names = {arm["name"] for arm in protocol["arms"]}
    assert "M0_boundary_common" in names and "M2_boundary_common_no_stop" in names
    assert "M0 reference" in protocol["acquisition"]["stop"]
    assert "Genuine nested" in protocol["training"]["fit"]
    assert "fewer active" in protocol["training"]["control"]
    assert not (STUDY / "FREEZE.json").exists()
    assert not any(STUDY.glob("*run*/EPISODES.jsonl"))
    result = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "revised_draft_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "status": "Accepted for bounded exposed-development execution, conditional on implementation matching contract",
        "arms": len(protocol["arms"]), "contexts": len(protocol["contexts"]),
        "review_items_resolved": ["same-boundary world control", "same-world no-stop control", "sharedM0 threshold",
                                  "genuine nested outer/context exclusion", "design control fewer-active-feature disclosure"],
        "scientific_limits": ["Uncalibrated Gaussian crossing and stop surrogate", "STATE training residuals in-sample",
                              "All five contexts previously exposed", "No drug-specific or HOP62-directed override"],
        "target_replay_before_review": False,
    }
    with (HERE / "REVISED_DRAFT_REVIEW.json").open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2); handle.write("\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
