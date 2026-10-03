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
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent

for path in (ROOT / "src", ROOT):
    entry = str(path)
    if entry not in sys.path:
        sys.path.insert(0, entry)


def _test_scopes():
    policy = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["tool"]
    return {"core": set(policy["pytest"]["ini_options"]["testpaths"]),
            **{key: set(value) for key, value in policy["maestro"]["test_scopes"].items()}}


def pytest_sessionstart(session):
    """A new maintained test cannot silently fall outside the default core."""
    import pytest
    scopes = _test_scopes()
    registered = set().union(*scopes.values())
    files = {path.relative_to(ROOT).as_posix() for path in (ROOT / "tests").rglob("test_*.py")}
    files.update(path.relative_to(ROOT).as_posix() for path in (ROOT / "research/astra").glob("test_*.py"))
    unknown = files - registered
    overlaps = [path for path in registered if sum(path in values for values in scopes.values()) != 1]
    if unknown or overlaps:
        raise pytest.UsageError("Explicit test scope registration required: " + ", ".join(sorted(unknown | set(overlaps))))


def pytest_collection_modifyitems(config, items):
    """Label explicit scopes; never skip or hide missing research assets."""
    import pytest
    scopes = _test_scopes()
    for item in items:
        relative = item.path.relative_to(ROOT).as_posix()
        scope = next((key for key, paths in scopes.items() if relative in paths), "research")
        item.add_marker(getattr(pytest.mark, scope))
