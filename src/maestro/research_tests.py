"""Explicit entry point for the opt-in research validation suite.

The production test target remains ``pytest`` (``tests/`` in ``pyproject.toml``).  Research
replays depend on prepared data and optional scientific packages, so they are intentionally not
collected by that default command.  This entry point gives CI and release checks one stable command
for the boundary, replay and metadata contracts that can run in the current checkout.
"""
from __future__ import annotations

import sys


DEFAULT_TARGETS = ("research",)


def main() -> int:
    """Run the opt-in research tests and return pytest's process-style exit code."""
    try:
        import pytest
    except ImportError as exc:  # pragma: no cover - exercised by an environment, not a test
        raise SystemExit("Install the test dependency before running maestro-test-research") from exc
    return int(pytest.main([*DEFAULT_TARGETS, *sys.argv[1:]]))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
