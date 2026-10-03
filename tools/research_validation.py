"""Checkout-local entry point for the opt-in research test suite.

The production test target remains ``pytest`` (core testpaths in ``pyproject.toml``). Research
replays depend on prepared data and optional scientific packages, so they are intentionally not
collected by that default command. This developer command runs the tests and contracts under the
current checkout's ASTRA entries; historical suites use explicit pytest paths.
"""
from __future__ import annotations

import sys
from pathlib import Path


DEFAULT_TARGETS = ("research/astra",)
ARCHIVE_GLOBS = ("*/results/*", "*/baseline_*/*", "*/snapshots/*", "*/execution_sources/*")
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
    include_archives = "--include-archives" in args
    args = [arg for arg in args if arg != "--include-archives"]
    exclusions = [] if include_archives else [
        f"--ignore={ROOT / 'research/experiments'}", f"--ignore={ROOT / 'research/data'}",
        *(f"--ignore-glob={pattern}" for pattern in ARCHIVE_GLOBS),
    ]
    targets = ("research",) if include_archives else DEFAULT_TARGETS
    return int(pytest.main([str(ROOT / target) for target in targets] + exclusions + args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
