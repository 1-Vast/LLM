"""Shared, logged access to already-opened Jaaks outcomes for the confirmation-campaign study.

File summary
- Path: research/astra/confirmation_campaign_20261004/common.py
- Purpose: the single entry point through which every workstream reads Jaaks 2022 outcomes. The
  release was opened by `feedback_validation_20261003`, so every analysis here is EXPLORATORY.
- Core points:
  - `exposed_ticket(purpose, owner)` refuses unless this study's campaign contract is frozen
    (`protocol/freeze.json`) and every file it lists, plus every file of the earlier builder freeze,
    is unchanged. It appends one line to this study's `protocol/access_log.jsonl`; earlier logs are
    never written.
  - The returned ticket is accepted by the frozen `jaaks.build_panels`.
  - `partition()` returns the design-only HD/E line split frozen with the contract.
- Interfaces: `exposed_ticket`, `partition`, constants `HERE`, `ROOT`, `JAAKS`, `ACCESS_LOG`, `FREEZE`.
- Depends on: tools.datasets.combination_screens.open_vault; the frozen feedback-validation study.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRIOR_FREEZE = ROOT / "research/astra/feedback_validation_20261003/protocol/freeze.json"
FREEZE = HERE / "protocol/freeze.json"
ACCESS_LOG = HERE / "protocol/access_log.jsonl"
PARTITION = HERE / "protocol/partition.json"
JAAKS = ROOT / "data/external/gdsc_combinations/jaaks2022_figshare/original_screen_all_tissues_fitted.csv"
JAAKS_SHA256 = "1188968ce7fdcfb66d03791cf266515b7c7a2794e1fc73c966dba40266ffa278"
OWNERS = ("parent", "design", "resources", "verify")


def exposed_ticket(purpose: str, owner: str, source: Path = JAAKS, *, log_path: Path = ACCESS_LOG,
                   freeze_path: Path = FREEZE, prior_freeze: Path = PRIOR_FREEZE) -> dict:
    """Log one EXPLORATORY reading after both freezes verify; return a builder ticket."""
    from tools.datasets.combination_screens import VaultRefusal, open_vault

    if owner not in OWNERS:
        raise ValueError(f"UNKNOWN_OWNER: {owner}")
    if not freeze_path.is_file():
        raise VaultRefusal("CONTRACT_NOT_FROZEN", f"no campaign contract freeze at {freeze_path}")
    import tempfile
    with tempfile.TemporaryDirectory() as scratch:      # verify the earlier builder freeze, log nothing there
        open_vault(prior_freeze, Path(scratch) / "check.jsonl", purpose="integrity check", source=source, root=ROOT)
    entry = open_vault(freeze_path, log_path, purpose=f"[{owner}] EXPLORATORY (exposed data): {purpose}",
                       source=source, root=ROOT)
    if source == JAAKS and entry["data_sha256"] != JAAKS_SHA256:
        raise ValueError("DATA_HASH_MISMATCH: the Jaaks release differs from the registered file")
    return entry


def partition(path: Path = PARTITION) -> dict:
    """tissue -> {'E': [...], 'HD': [...], 'repeat_lines_E': [...], 'repeat_lines_HD': [...]}"""
    return json.loads(path.read_text(encoding="utf-8"))["split"]
