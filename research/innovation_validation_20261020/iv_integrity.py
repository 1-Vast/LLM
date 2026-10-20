"""Before/after receipts for the two closed predecessor packages and their consumed inputs (no sealed outcome payload is read).

C/G/F outcome files are only stat-ed. The authorised S file and the exported environment are hashed.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGES = ("functional_rule_revision_20261020", "self_improving_virtual_cell_20261020")
PRIOR_WORK = ROOT / "tmp" / "functional_rule_revision_20261020"
SVC_WORK = ROOT / "tmp" / "self_improving_virtual_cell_20261020"
PROMPTS = ("NEXT_RESEARCH_PROMPT.md", "NEXT_SELF_IMPROVING_RESEARCH_PROMPT.md", "NEXT_INNOVATION_VALIDATION_PROMPT.md")


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def receipt() -> dict:
    out = {"packages": {}}
    for pkg in PACKAGES:
        base = ROOT / "research" / pkg
        out["packages"][pkg] = {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(base.rglob("*")) if p.is_file() and "__pycache__" not in p.parts}
    out["prompts"] = {n: sha(ROOT / "log" / "20261020" / n) for n in PROMPTS if (ROOT / "log" / "20261020" / n).exists()}
    sealed = {}
    for role in "SCGF":
        f = PRIOR_WORK / "sealed" / f"outcomes_{role}.npy"
        stat = f.stat()
        entry = {"bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns}
        if role == "S":
            entry["sha256"] = sha(f)
        sealed[role] = entry
    out["prior_sealed_outcome_files"] = sealed
    vs = PRIOR_WORK / "vault_state.json"
    out["prior_vault_state"] = {"sha256": sha(vs), "mtime_ns": vs.stat().st_mtime_ns}
    out["prior_groups_cache"] = {"sha256": sha(PRIOR_WORK / "groups.npz")}
    out["svc_env_export"] = {"sha256": sha(SVC_WORK / "env_export.npz")}
    return out


if __name__ == "__main__":
    print(json.dumps(receipt(), indent=1, sort_keys=True))
