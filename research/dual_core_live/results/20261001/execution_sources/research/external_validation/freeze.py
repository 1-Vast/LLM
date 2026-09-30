"""Write `freeze.json`: every digest the locked replay and the gates depend on.

File summary
- Path: research/external_validation/freeze.py
- Purpose: record, before the registered run, the git state and the SHA-256 of the protocol, the
  decision code, the policies and models it imports, the registered prompt, the calibration and
  retrieval inputs, the prepared data and the manifests. `locked_replay` refuses to run, and a
  `Vault` refuses to open, if any of them has changed.
- Core points:
  - Grouped digests (policy, model, retrieval library, prompt, calibration, baseline selection)
    are hashes over the listed files, so each named component can be cited by one value.
  - The descriptive report code (`risk_audit`, `calibration_audit`, `paired_ablation`, `report`)
    is written after the freeze and never decides a status.
- Run: python -m research.external_validation.freeze
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import firewall as F
from . import locked_replay as R

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

PROTOCOL = ["research/external_validation/protocol.json", "research/external_validation/PROTOCOL.md"]
DECISION = ["research/external_validation/statistics.py", "research/external_validation/promotion.py"]
HARNESS = ["research/external_validation/__init__.py", "research/external_validation/firewall.py",
           "research/external_validation/ontology.py",
           "research/external_validation/locked_replay.py", "research/external_validation/manifests.py",
           "research/external_validation/schemas/dataset_manifest.schema.json",
           "research/external_validation/schemas/split_manifest.schema.json",
           "research/external_validation/schemas/episode_manifest.schema.json",
           "research/external_validation/manifests/external_candidates.json",
           "research/external_validation/manifests/hypothesis_ontology.json"]
POLICY = ["research/external_validation/arms.py", "research/sequence_audit/policies.py",
          "research/sparse_value/policy.py", "research/acquisition_link/evaluate.py",
          "research/acquisition_followup/two_step.py", "src/maestro/acquisition.py", "src/maestro/composition.py",
          "src/maestro/outcome.py", "src/maestro/models.py", "src/maestro/handoff.py"]
MODEL = ["research/sparse_value/model.py", "research/dynamic_world_model/episodes.py"]
CALIBRATION = ["research/dynamic_world_model/common.py", "research/dynamic_world_model/protocol.json"]
DATA_CODE = ["research/sequence_audit/lincs_prepare.py", "research/sequence_audit/lincs_evaluate.py",
             "research/sequence_audit/analyze.py", "research/sequence_audit/lincs_analyze.py"]
PROMPT = ["research/dynamic_world_model/agent_arms.py"]


def prepared_files() -> list[str]:
    folders = (R.C.PREPARED, R.C.FROZEN, R.LP.OUT, R.OUT / "manifests")
    return [p.relative_to(ROOT).as_posix() for folder in folders for p in sorted(folder.iterdir()) if p.is_file()]


def group(paths: list[str], digests: dict) -> str:
    return F.sha256_json({p: digests[p] for p in paths})


def main() -> None:
    data = prepared_files()
    files = PROTOCOL + DECISION + HARNESS + POLICY + MODEL + CALIBRATION + DATA_CODE + PROMPT + data
    digests = {p: F.sha256_file(ROOT / p) for p in files}
    spec = json.loads((HERE / "protocol.json").read_text(encoding="utf-8"))
    local = datetime.now(timezone(timedelta(hours=8)))
    freeze = {
        "frozen_at": local.isoformat(timespec="seconds"),
        "status": "registered before the development ladder ran; SciPlex3 and L1000 are development data",
        "git": F.git_state([ROOT / p for p in files if not p.startswith("outputs/")]),
        "components": {
            "policy": group(POLICY, digests), "model": group(MODEL + ["research/external_validation/arms.py"], digests),
            "retrieval_library": group([p for p in data if "manifests" not in p], digests),
            "prompt": group(PROMPT, digests), "calibration": group(CALIBRATION, digests),
            "baseline_selection": F.sha256_json({"rule": spec["strongest_baseline_rule"],
                                                 "code": digests["research/external_validation/promotion.py"]}),
            "decision": group(DECISION + PROTOCOL, digests),
            "datasets": {p.rsplit("/", 1)[-1]: digests[p] for p in data if "/manifests/" in p},
        },
        "endpoints": spec["endpoints"]["primary"], "thresholds": spec["thresholds"],
        "multiplicity": spec["multiplicity"],
        "external_study": {"registered": None, "manifest_sha256": None,
                           "blocker": json.loads((HERE / "manifests/external_candidates.json").read_text(encoding="utf-8"))["blocker"]},
        "sha256": digests,
    }
    (HERE / "freeze.json").write_bytes(json.dumps(freeze, indent=1).encode("utf-8"))
    print(json.dumps({k: v for k, v in freeze.items() if k != "sha256"}, indent=1))


if __name__ == "__main__":
    main()
