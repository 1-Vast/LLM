"""Before/after receipts for the closed prior package and its consumed inputs (no G/F payload is read)."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRIOR = ROOT / "research" / "functional_rule_revision_20261020"
WORK = ROOT / "tmp" / "functional_rule_revision_20261020"
PROMPT_OLD = ROOT / "log" / "20261020" / "NEXT_RESEARCH_PROMPT.md"
PROMPT_NEW = ROOT / "log" / "20261020" / "NEXT_SELF_IMPROVING_RESEARCH_PROMPT.md"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def receipt() -> dict:
    files = {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(PRIOR.rglob("*")) if p.is_file() and "__pycache__" not in p.parts}
    out = {"prior_package_sha256": files, "consumed_prompts": {p.name: sha(p) for p in (PROMPT_OLD, PROMPT_NEW) if p.exists()}}
    out["prior_sealed_outcome_files"] = {}
    for role in "SCGF":
        f = WORK / "sealed" / f"outcomes_{role}.npy"
        stat = f.stat()
        entry = {"bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns}
        if role == "S":      # S is fully authorised development data; C/G/F are only stat-ed (never hashed or loaded here)
            entry["sha256"] = sha(f)
        out["prior_sealed_outcome_files"][role] = entry
    vs = WORK / "vault_state.json"
    out["prior_vault_state"] = {"sha256": sha(vs), "mtime_ns": vs.stat().st_mtime_ns}
    g = WORK / "groups.npz"
    out["prior_groups_cache"] = {"sha256": sha(g), "bytes": g.stat().st_size}
    return out


if __name__ == "__main__":
    print(json.dumps(receipt(), indent=1, sort_keys=True))
