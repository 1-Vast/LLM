"""Write `freeze.json`: the digest of every file the registered runs depend on, and the external manifest.

File summary
- Path: research/belief_planning/freeze.py
- Purpose: register protocol, code, frozen dependencies, development data and the external study's
  metadata manifest before the external study is opened. `locked.py` refuses to run unless every
  digest still matches. The external vault opens only for the manifest whose SHA-256 is here.
- Core points:
  - Files under `research/external_validation/` and Codex's uncommitted edits (`common.py`,
    `episodes.py`, `acquisition.py`, `policy.py`) are frozen as they are now: dependencies, not
    endorsements.
  - Refuses to overwrite an existing freeze. A changed rule needs a new protocol version.
- Run: python -m research.belief_planning.freeze
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from research.external_validation import firewall as F

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FREEZE = HERE / "freeze.json"
MANIFEST = HERE / "manifests" / "gse70138_p2ld.json"
CODE = [
    "src/maestro/planning.py", "src/maestro/acquisition.py", "src/maestro/models.py", "src/maestro/outcome.py",
    "src/maestro/handoff.py", "src/maestro/composition.py",
    "research/belief_planning/__init__.py", "research/belief_planning/world.py", "research/belief_planning/arms.py",
    "research/belief_planning/tasks.py", "research/belief_planning/replay.py", "research/belief_planning/locked.py",
    "research/belief_planning/analysis.py", "research/belief_planning/external_phase2.py",
    "research/belief_planning/l1000_level5.py", "research/belief_planning/freeze.py",
    "research/belief_planning/test_belief_planning.py", "tests/test_belief_planning.py",
    "research/belief_planning/protocol.json", "research/belief_planning/PROTOCOL.md",
    "research/external_validation/arms.py", "research/external_validation/firewall.py",
    "research/external_validation/statistics.py", "research/external_validation/__init__.py",
    "research/sequence_audit/policies.py", "research/sequence_audit/lincs_prepare.py",
    "research/sequence_audit/lincs_evaluate.py", "research/sequence_audit/lincs_analyze.py",
    "research/sequence_audit/analyze.py", "research/dynamic_world_model/common.py",
    "research/dynamic_world_model/episodes.py", "research/dynamic_world_model/protocol.json",
    "research/acquisition_link/evaluate.py", "research/acquisition_followup/two_step.py",
    "research/acquisition_followup/lincs_flow.py", "research/sparse_value/model.py",
    "research/sparse_value/policy.py", "research/belief_planning/manifests/gse70138_p2ld.json",
]
DATA = [
    "outputs/dynamic_world_model_20260926/prepared/conditions.csv",
    "outputs/dynamic_world_model_20260926/prepared/shifts.npz",
    "outputs/dynamic_world_model_20260926/prepared/prepare_manifest.json",
    "outputs/sequence_audit_20260926/l1000/prepared/compounds.csv",
    "outputs/sequence_audit_20260926/l1000/prepared/conditions.csv",
    "outputs/sequence_audit_20260926/l1000/prepared/shifts.npz",
    "outputs/sequence_audit_20260926/l1000/prepared/tiers.json",
    "data/raw/sciplex3/repurposing_samples_20200324.txt",
    "data/raw/sciplex3/repurposing_drugs_20200324.txt",
    "data/external/lincs_l1000_phase1/GSE92742_Broad_LINCS_pert_info.txt.gz",
    "data/external/lincs_l1000_phase1/GSE92742_Broad_LINCS_sig_info.txt.gz",
    "data/external/lincs_l1000_phase2/GSE70138_Broad_LINCS_sig_info_2017-03-06.txt.gz",
    "data/external/lincs_l1000_phase2/GSE70138_Broad_LINCS_sig_metrics_2017-03-06.txt.gz",
    "data/external/lincs_l1000_phase2/GSE70138_Broad_LINCS_pert_info_2017-03-06.txt.gz",
    "data/external/lincs_l1000_phase2/GSE70138_Broad_LINCS_gene_info_2017-03-06.txt.gz",
    "data/external/lincs_l1000_phase2/GSE70138_Broad_LINCS_Level5_COMPZ_n118050x12328_2017-03-06.gctx",
]


def main() -> None:
    if FREEZE.exists():
        sys.exit("freeze.json exists; register a new protocol version instead of rewriting it")
    missing = [p for p in CODE + DATA if not (ROOT / p).is_file()]
    if missing:
        sys.exit(f"missing: {missing}")
    digests = {p: F.sha256_file(ROOT / p) for p in CODE + DATA}
    protocol = json.loads((HERE / "protocol.json").read_text(encoding="utf-8"))
    freeze = {
        "frozen_at": datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds"),
        "protocol_version": protocol["version"],
        "status": "registered before the external study's measurements, QC metrics or test labels were read",
        "git": F.git_state(),
        "external_study": {"study": "GSE70138", "task": "P2LD",
                           "manifest": str(MANIFEST.relative_to(ROOT)).replace("\\", "/"),
                           "manifest_sha256": digests[str(MANIFEST.relative_to(ROOT)).replace("\\", "/")],
                           "level5_sha512": "9d078903d3d028f37b0bae584c1afe48f5bab0082e61f6e542de471674c78946cff710132b8e95beb997a39dc2dd6442fdda0fbb1cc9b2399ef21cf636975c9f",
                           "source": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE70nnn/GSE70138/suppl/"},
        "thresholds": protocol["thresholds"],
        "sha256": digests,
    }
    FREEZE.write_bytes(json.dumps(freeze, indent=1).encode("utf-8"))
    print(json.dumps({k: v for k, v in freeze.items() if k != "sha256"}, indent=1))


if __name__ == "__main__":
    main()
