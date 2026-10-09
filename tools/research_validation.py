"""Checkout-local entry point for the three maintained research test suites.

The production test target remains ``pytest`` (core testpaths in ``pyproject.toml``). Research
tests depend on optional scientific packages and are intentionally run explicitly.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


DEFAULT_TARGETS = (
    "research/astra/state_readout_repair_20261009/test_readout.py",
    "research/astra/state_feedback_repair_20261009/test_posterior.py",
    "research/decision_value/test_utility.py",
)
ROOT = Path(__file__).resolve().parents[1]
STUDIES = (
    ("research/astra/state_readout_repair_20261009", "outputs/paper_01286/state_readout_repair/RESULTS.json"),
    ("research/astra/state_feedback_repair_20261009", "outputs/paper_01286/state_feedback_repair/RESULTS.json"),
    ("research/decision_value", "outputs/decision_value_validation_20261009/RESULTS.json"),
)


def blocked_assets(root: Path = ROOT) -> list[str]:
    """Return absent or hash-mismatched frozen inputs and missing result outputs."""
    blocked = []
    for study, result in STUDIES:
        freeze_path = root / study / "FREEZE.json"
        if not freeze_path.is_file():
            blocked.append(f"{study}/FREEZE.json")
            continue
        freeze = json.loads(freeze_path.read_bytes())
        for relative, expected in freeze.get("inputs", {}).items():
            path = root / relative
            if not path.is_file():
                blocked.append(relative)
            elif hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                blocked.append(f"{relative} (SHA256_MISMATCH)")
        verifier_freeze = root / study / "VERIFY_FREEZE.json"
        verifier = root / study / "verify.py"
        if verifier_freeze.is_file():
            pin = json.loads(verifier_freeze.read_bytes())
            if not verifier.is_file() or hashlib.sha256(verifier.read_bytes()).hexdigest() != pin.get("verifier_sha256"):
                blocked.append(f"{study}/verify.py (SHA256_MISMATCH)")
            if hashlib.sha256(freeze_path.read_bytes()).hexdigest() != pin.get("trial_freeze_sha256"):
                blocked.append(f"{study}/FREEZE.json (SHA256_MISMATCH)")
        if not (root / result).is_file():
            blocked.append(result)
    return sorted(set(blocked))


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
    args = sys.argv[1:]
    if args == ["--verify"]:
        blocked = blocked_assets()
        if blocked:
            print("BLOCKED/ASSET_MISSING")
            print("\n".join(blocked))
            return 2
        for study, _ in STUDIES:
            result = subprocess.run(
                [sys.executable, str(ROOT / study / "verify.py")], cwd=ROOT, check=False
            )
            if result.returncode:
                return result.returncode
        return 0
    try:
        import pytest
    except ImportError as exc:  # pragma: no cover - exercised by an environment, not a test
        raise SystemExit("Install the test dependency before running this research test command") from exc
    return int(pytest.main([str(ROOT / target) for target in DEFAULT_TARGETS] + args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
