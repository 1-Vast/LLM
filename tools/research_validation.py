"""Checkout-local entry point for the three maintained research test suites.

The production test target remains ``pytest`` (core testpaths in ``pyproject.toml``). Research
tests depend on optional scientific packages and are intentionally run explicitly.
"""
from __future__ import annotations

import sys
from pathlib import Path


DEFAULT_TARGETS = (
    "research/astra/state_readout_repair_20261009/test_readout.py",
    "research/astra/state_feedback_repair_20261009/test_posterior.py",
    "research/decision_value/test_utility.py",
)
ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    """Run the opt-in research tests and return pytest's process-style exit code."""
    if (
        Path.cwd().resolve() != ROOT
        or not (ROOT / "pyproject.toml").is_file()
        or not (ROOT / "research").is_dir()
    ):
        raise SystemExit(
            "The research test runner is checkout-local. Run `python -m tools.research_validation` "
            f"from the MAESTRO repository root: {ROOT}"
        )
    try:
        import pytest
    except ImportError as exc:  # pragma: no cover - exercised by an environment, not a test
        raise SystemExit("Install the test dependency before running this research test command") from exc
    args = sys.argv[1:]
    return int(pytest.main([str(ROOT / target) for target in DEFAULT_TARGETS] + args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
