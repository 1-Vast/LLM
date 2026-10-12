"""Explicit checkout-local research tests and read-only frozen-input preflight.

No active scientific protocol is released. Preflight authenticates supplied bytes;
it never executes study code or establishes a scientific claim.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TARGETS = ()
STUDIES = ()


def blocked_assets(root: Path = ROOT, studies=None) -> list[str]:
    """Return absent or hash-mismatched inputs, verifier pins and outputs."""
    blocked = []
    for study, result in STUDIES if studies is None else studies:
        freeze_path = root / study / "FREEZE.json"
        if not freeze_path.is_file():
            blocked.append(f"{study}/FREEZE.json")
            continue
        freeze = json.loads(freeze_path.read_bytes())
        for relative, expected in freeze.get("inputs", {}).items():
            path = root / relative
            if not path.is_file():
                blocked.append(relative)
            else:
                with path.open("rb") as stream:
                    digest = hashlib.file_digest(stream, "sha256").hexdigest()
                if digest != expected:
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
    if Path.cwd().resolve() != ROOT or not (ROOT / "pyproject.toml").is_file():
        raise SystemExit("The research runner is checkout-local; run from the MAESTRO repository root")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--study", type=Path, help="Explicit study directory containing FREEZE.json")
    parser.add_argument("--result", type=Path, help="Explicit required result artifact")
    parser.add_argument("--tests", nargs="+", help="Explicit registered research test paths")
    parser.add_argument("--collect-only", action="store_true")
    args = parser.parse_args()
    if args.verify:
        if args.tests or args.collect_only:
            parser.error("--verify cannot be combined with research test execution")
        if (args.study is None) != (args.result is None):
            parser.error("--study and --result must be supplied together")
        studies = [(str(args.study), str(args.result))] if args.study is not None else STUDIES
        if not studies:
            print("BLOCKED/ASSET_MISSING")
            print("No active frozen research protocol is released; supply --study PATH --result PATH.")
            return 2
        blocked = blocked_assets(ROOT, studies)
        if blocked:
            print("BLOCKED/ASSET_MISSING")
            print("\n".join(blocked))
            return 2
        print("ENGINEERING_ONLY: supplied frozen inputs and result presence match; no scientific verifier executed")
        return 0
    if args.study or args.result:
        parser.error("--study and --result require --verify")
    targets = args.tests or DEFAULT_TARGETS
    if not targets:
        print("BLOCKED/ASSET_MISSING: no active research suite selected; use --tests PATH")
        return 2
    policy = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    registered = set(policy["tool"]["maestro"]["test_scopes"]["research"])
    if not set(targets) <= registered:
        parser.error("--tests requires registered research test paths")
    import pytest
    return int(pytest.main([str(ROOT / target) for target in targets] + (["--collect-only"] if args.collect_only else [])))


if __name__ == "__main__":
    raise SystemExit(main())
