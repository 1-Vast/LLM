"""Freeze block P: hash every file the registered run depends on, then open the sealed tier.

Writes FREEZE.json once, holding:
* the sha256 of every .py and .md in the block, of PROTOCOL_CONFIG.json and EXTRACT_RECEIPT.json;
* the sha256 of every cached LLM prior record (so the prompts and replies cannot change after the
  freeze), with their count and total provider spend to date;
* the digests of the three data files (phase-2 landmark inputs, development and sealed PRISM tiers);
* the git HEAD and whether the working tree was clean.

After FREEZE.json exists, ``extract.load_prism('sealed')`` stops refusing, so the confirmation run
can read the new compounds' outcomes. Nothing hashed here may be edited afterwards; corrections go
to DEVIATIONS.json.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = HERE / "FREEZE.json"

# Exploratory outputs that are still being written when the block is frozen. They are declared here
# with their reason so a later hash check does not read a legitimate late write as tampering. Nothing
# in this list may influence the registered design, and each entry says why it cannot.
PENDING = {
    "feasibility/f12_budget_power.json": "disclosed budget sensitivity sweep (10/20/30%); the registered budget is "
                                         "0.10, inherited from every F0-F11 experiment, so this sweep cannot select it",
    "feasibility/f12_budget_power.log": "console log of the same sweep",
    "feasibility/f12_rows.csv": "per-campaign rows of the same sweep",
}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def git(*args) -> str:
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=60).stdout.strip()
    except Exception as e:  # recorded, never silently ignored
        return f"unavailable:{type(e).__name__}"


def main() -> dict:
    if OUT.exists():
        raise SystemExit("FREEZE.json exists; the block is frozen")
    rec = json.loads((HERE / "EXTRACT_RECEIPT.json").read_text(encoding="utf-8"))
    code = {}
    for p in sorted(HERE.rglob("*")):
        if p.is_dir() or p.name == "FREEZE.json":
            continue
        rel = str(p.relative_to(HERE)).replace("\\", "/")
        if rel in PENDING:
            continue
        if p.suffix in (".py", ".md", ".json", ".csv", ".log") and not rel.startswith("agent_outputs/"):
            code[rel] = sha256(p)
    priors = {}
    for arm in ("prior", "prior_masked"):
        d = HERE / "agent_outputs" / arm
        if d.exists():
            files = sorted(d.glob("*.json"))
            h = hashlib.sha256()
            for f in files:
                h.update(f.name.encode())
                h.update(sha256(f).encode())
            priors[arm] = {"n": len(files), "combined_sha256": h.hexdigest()}
    ledger = ROOT / "tmp/selective_discovery_spend.json"
    spend = json.loads(ledger.read_text(encoding="utf-8")) if ledger.exists() else {}
    out = {
        "frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_head": git("rev-parse", "HEAD"),
        "git_status_clean": git("status", "--porcelain") == "",
        "git_status": git("status", "--porcelain")[:4000],
        "n_files": len(code),
        "files": code,
        "llm_priors": priors,
        "data": {
            "phase2_landmark": {"file": rec["landmark"]["file"], "sha256": rec["landmark"]["sha256"]},
            "prism_dev": rec["prism"]["blockn"],
            "prism_sealed": rec["prism"]["new"],
            "source_sha512": rec["source_sha512"],
        },
        "pending_excluded": PENDING,
        "provider_spend_at_freeze_usd": spend.get("total_usd"),
        "provider_calls_at_freeze": spend.get("calls"),
        "note": "Hashes cover the registered code, protocol and the pre-freeze LLM prior records. "
                "The sealed PRISM tier opens only once this file exists.",
    }
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    return {k: v for k, v in out.items() if k != "files"}


if __name__ == "__main__":
    print(json.dumps(main(), indent=1))
