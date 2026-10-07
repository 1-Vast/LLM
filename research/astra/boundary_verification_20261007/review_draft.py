"""Record the independent protocol review before any target replay."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
STUDY = ROOT / "research/astra/boundary_acquisition_20261007"


def main():
    path = STUDY / "DRAFT_PROTOCOL.json"
    protocol = json.loads(path.read_text(encoding="utf-8"))
    assert not (STUDY / "FREEZE.json").exists(), "Draft review must precede registration"
    review = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "draft_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "target_replay_exists": any(STUDY.glob("*run*/EPISODES.jsonl")),
        "status": "Pre-registration review: four concrete corrections sent to worker and parent",
        "accepted": [
            "All five contexts explicitly previously exposed; no fresh outcome holdout claim.",
            "Full146 candidate menu, source-matched paired wells and native39-coordinate endpoint retained.",
            "Common13-credit ceiling, exactly5B, at most8distinctA, no candidate-specific exception.",
            "Fixed ridge, PSD diagonal variance rescaling and heuristic train-derived stop fraction.",
            "TrainingSTATE residuals explicitly in-sample, no calibrated risk or PAC claim.",
        ],
        "corrections": [
            {"id": "world_control", "issue": "M0KG versus M2boundary confounds predictor and acquisition.",
             "request": "AddM0boundarycommon using same boundary score and stopping convention."},
            {"id": "stop_control", "issue": "All boundary arms stop; cannot assign a utility change to stopping versus acquisition.",
             "request": "AddM2boundarycommon_nostop with same up-to8 acquisition cap."},
            {"id": "outer_fold", "issue": "Leaving one context out of ridge rows can still leak its outcomes through other rows' precomputed panelLOO labels/features.",
             "request": "Rebuild all other rows' panel/STATEmeans/features/floor/normalization excluding the outer context too, or explicitly name diagnostic partialOOF instead of heldoutcontext calibration."},
            {"id": "method_claim", "issue": "Max-pair expected crossing surrogate and fixed stop fraction are not exacttop5KG or calibrated biological confidence.",
             "request": "Preserve Gaussian-model/heuristic naming and numerical finite/PSD/tie safeguards; no HOP62/drug-specific tuning."},
        ],
        "methods": "PMLR2013 top-m gap; NeurIPS2014 incumbent/optimistic symmetric difference; correlatedKG2009 primary metadata/abstract",
    }
    with (HERE / "DRAFT_REVIEW.json").open("x", encoding="utf-8") as handle:
        json.dump(review, handle, indent=2); handle.write("\n")
    print(json.dumps({"created_utc": review["created_utc"], "draft_sha256": review["draft_sha256"], "target_replay_exists": review["target_replay_exists"]}))


if __name__ == "__main__":
    main()
