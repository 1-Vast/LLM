"""Shared, exposed-data access for the reproducible-allocation study.

File summary
- Path: research/astra/reproducible_allocation_20261003/common.py
- Purpose: one entry point through which every workstream reads Jaaks 2022 outcomes. The release
  was opened by the feedback-validation study (its vault log lists six openings), so everything in
  this study that reads it is EXPLORATORY and is labelled so in its outputs.
- Core points:
  - `exposed_ticket(purpose, owner)` verifies the earlier freeze is intact (`open_vault` refuses on
    any changed frozen file) and appends the reading to this study's own `protocol/access_log.jsonl`.
    The earlier study's vault log is never written.
  - The returned ticket is accepted by the frozen `jaaks.build_panels`.
- Interfaces: `exposed_ticket`, constants `HERE`, `ROOT`, `JAAKS`, `JAAKS_SHA256`, `ACCESS_LOG`.
- Depends on: tools.datasets.combination_screens.open_vault; the frozen feedback-validation study.
"""
from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRIOR = ROOT / "research/astra/feedback_validation_20261003"
PRIOR_FREEZE = PRIOR / "protocol/freeze.json"
ACCESS_LOG = HERE / "protocol/access_log.jsonl"
JAAKS = ROOT / "data/external/gdsc_combinations/jaaks2022_figshare/original_screen_all_tissues_fitted.csv"
JAAKS_SHA256 = "1188968ce7fdcfb66d03791cf266515b7c7a2794e1fc73c966dba40266ffa278"
OWNERS = ("parent", "repeats", "allocation", "review")


def exposed_ticket(purpose: str, owner: str, source: Path = JAAKS, *, log_path: Path = ACCESS_LOG,
                   freeze_path: Path = PRIOR_FREEZE) -> dict:
    """Log one EXPLORATORY reading of an already-opened release and return a builder ticket."""
    from tools.datasets.combination_screens import open_vault

    if owner not in OWNERS:
        raise ValueError(f"UNKNOWN_OWNER: {owner}")
    entry = open_vault(freeze_path, log_path, purpose=f"[{owner}] EXPLORATORY (exposed data): {purpose}",
                       source=source, root=ROOT)
    if source == JAAKS and entry["data_sha256"] != JAAKS_SHA256:
        raise ValueError("DATA_HASH_MISMATCH: the Jaaks release differs from the registered file")
    return entry
