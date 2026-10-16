"""Discover core tests by default and keep asset-dependent suites explicit."""
from __future__ import annotations

import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent

for path in (ROOT / "src", ROOT):
    entry = str(path)
    if entry not in sys.path:
        sys.path.insert(0, entry)

SCOPES = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["tool"]["maestro"]["test_scopes"]
# Explicit file arguments still collect these suites; default discovery does not.
collect_ignore = [path for paths in SCOPES.values() for path in paths]


def pytest_sessionstart(session):
    """Refuse stale or overlapping declarations for non-core suites."""
    import pytest

    declared = [path for paths in SCOPES.values() for path in paths]
    invalid = {path for path in declared if not (ROOT / path).is_file() or declared.count(path) != 1}
    if invalid:
        raise pytest.UsageError("Invalid test scope registration: " + ", ".join(sorted(invalid)))


def pytest_collection_modifyitems(config, items):
    import pytest

    for item in items:
        relative = item.path.relative_to(ROOT).as_posix()
        scope = next((key for key, paths in SCOPES.items() if relative in paths),
                     "core" if relative.startswith("tests/") else "research")
        item.add_marker(getattr(pytest.mark, scope))
