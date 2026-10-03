"""Put the source packages and checkout root on the import path for test modules.

File summary
- Path: conftest.py
- Purpose: one place decides the import path, instead of each module repeating a
  `sys.path.insert` line.
- Core points:
  - `src/` holds the packages under test (`maestro`, `agent`, `evaluation`,
    `virtual_cell`).
  - the repository root is added so tests can import `tests.fixtures` and checkout-local tools.
- Interfaces: pytest plugin hooks only
- Depends on: (standard library only)
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

for path in (ROOT / "src", ROOT):
    entry = str(path)
    if entry not in sys.path:
        sys.path.insert(0, entry)


def pytest_collection_modifyitems(config, items):
    """Label explicit scopes; never skip or hide missing research assets."""
    import pytest
    core = set(config.getini("testpaths"))
    regression = {"research/case_memory_integration/test_external_evaluation.py",
                  "research/astra/test_reproducibility_audit.py"}
    for item in items:
        relative = item.path.relative_to(ROOT).as_posix()
        scope = "core" if relative in core else "regression" if relative in regression else "research"
        item.add_marker(getattr(pytest.mark, scope))
