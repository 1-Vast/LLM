"""Put the package and the tools directory on the import path for every test module.

File summary
- Path: tests/conftest.py
- Purpose: one place decides the import path, instead of each module repeating a
  `sys.path.insert` line and tools/shared being unreachable.
- Core points:
  - `src/` holds the packages under test (`maestro`, `agent`, `evaluation`,
    `virtual_cell`).
  - the repository root is added so `tools.shared...` imports resolve; `tools/shared`
    carries no manifest, so the tool router still discovers only registered tools.
- Interfaces: pytest plugin hooks only
- Depends on: (standard library only)
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

for path in (ROOT / "src", ROOT):
    entry = str(path)
    if entry not in sys.path:
        sys.path.insert(0, entry)
