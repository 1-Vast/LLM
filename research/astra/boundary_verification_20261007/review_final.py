"""Pin final pre-execution independent source review; never edits worker protocol."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent / "boundary_acquisition_20261007"


def main():
    p = json.loads((STUDY / "DRAFT_PROTOCOL.json").read_text())
    arms = {arm["name"]: arm for arm in p["arms"]}
    assert len(arms) == 12 and arms["M2_KG4096"]["normal_draws"] == 4096
    assert not any(STUDY.glob("*run*/EPISODES.jsonl"))
    source = ["DRAFT_PROTOCOL.json", "register.py", "method.py", "execute.py", "test_boundary.py"]
    receipt = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "Final pre-target-replay protocol/source review accepted for descriptive execution",
        "source_hashes": {name: hashlib.sha256((STUDY / name).read_bytes()).hexdigest() for name in source},
        "freeze_already_written": (STUDY / "FREEZE.json").exists(),
        "target_replays_present": False,
        "verified_corrections": ["M0 same-boundary control", "M2 same-boundary no-stop control", "sharedM0 tau",
                                 "nested outer+own-row feature/error exclusion", "fewer-active design control",
                                 "exactlogabsSTATEfeature", "permutedsource-qualification mask", "full292matchedtrain/target permutation",
                                 "Evaluator context argument", "finite/symmetric/PSD guards", "single4096drawKG comparator"],
        "nonclaims": ["Biologicalcalibration", "Untouchedholdout", "PAC stopping", "Firstness", "Exacttop5KG crossing surrogate"],
    }
    with (HERE / "FINAL_DRAFT_REVIEW.json").open("x", encoding="utf-8") as handle:
        json.dump(receipt, handle, indent=2); handle.write("\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
