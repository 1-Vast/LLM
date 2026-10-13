"""Explicit checkout-local research tests and read-only frozen-input preflight.

No active scientific protocol is released. Preflight authenticates supplied bytes;
it never executes study code or establishes a scientific claim.

Three status levels stay separate:
- software tests (`python -m pytest`) show that code and contracts execute;
- research verification (each study's own verifier: replays, provenance, claim audit)
  authenticates a study's results;
- the scientific verdict is the study's predeclared hypothesis outcome.
This preflight is an engineering check below research verification: it confirms that
the frozen bytes a study declares are present and unchanged, and that the named result
exists. It reads no result value.

Supported FREEZE.json schemas (exactly one digest mapping, non-empty):
- `inputs`: checkout-relative path -> sha256 of the raw bytes;
- `sha256`: checkout-relative path -> sha256, CRLF normalised to LF (the rule the
  frozen studies declare) or raw bytes;
- `files`: path -> sha256, same digest rule as `sha256`. The block Q freeze tool wrote
  study-relative code keys and checkout-relative external keys into one mapping, so
  each key resolves against the study directory first and the checkout root second.
  Either way the resolved file must match the digest; a key that resolves to no file
  is reported missing.
Any other schema is refused (FREEZE_SCHEMA_UNSUPPORTED), never skipped.
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
SCHEMAS = ("inputs", "sha256", "files")


def _digests(path: Path, normalised: bool) -> set[str]:
    data = path.read_bytes()
    found = {hashlib.sha256(data).hexdigest()}
    if normalised:
        found.add(hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest())
    return found


def frozen_entries(freeze: dict, study: str) -> tuple[str, list[tuple[str, tuple[str, ...], str]]]:
    """Return (schema, [(name, candidate checkout-relative paths, expected sha256)]) or raise ValueError."""
    present = [key for key in SCHEMAS if key in freeze]
    if len(present) != 1:
        keys = ",".join(sorted(freeze)) or "none"
        raise ValueError(f"FREEZE_SCHEMA_UNSUPPORTED: need exactly one of {'/'.join(SCHEMAS)}; keys {keys}")
    schema = present[0]
    mapping = freeze[schema]
    if not isinstance(mapping, dict) or not mapping:
        raise ValueError(f"FREEZE_SCHEMA_EMPTY: '{schema}' lists no frozen file")
    entries = []
    for relative, expected in mapping.items():
        if not isinstance(relative, str) or not isinstance(expected, str) or not expected:
            raise ValueError(f"FREEZE_SCHEMA_UNSUPPORTED: '{relative}' has no digest string")
        candidates = (f"{study}/{relative}", relative) if schema == "files" else (relative,)
        entries.append((candidates[0], candidates, expected))
    return schema, entries


def authenticate(root: Path = ROOT, studies=None) -> tuple[list[str], dict[str, tuple[str, int]]]:
    """Return (blocked items, {study: (schema, frozen files authenticated)})."""
    blocked, checked = [], {}
    root = Path(root).resolve()
    for study, result in STUDIES if studies is None else studies:
        freeze_path = root / study / "FREEZE.json"
        if not freeze_path.is_file():
            blocked.append(f"{study}/FREEZE.json")
            continue
        freeze = json.loads(freeze_path.read_bytes())
        try:
            schema, entries = frozen_entries(freeze, str(study).replace("\\", "/").rstrip("/"))
        except ValueError as refusal:
            blocked.append(f"{study}/FREEZE.json ({refusal})")
            entries, schema = [], None
        ok = 0
        for relative, candidates, expected in entries:
            paths = [(root / c).resolve() for c in candidates]
            path = next((q for q in paths if q.is_relative_to(root) and q.is_file()), paths[0])
            if not all(q.is_relative_to(root) for q in paths):
                blocked.append(f"{relative} (PATH_OUTSIDE_CHECKOUT)")
            elif not path.is_file():
                blocked.append(relative)
            elif expected not in _digests(path, normalised=schema != "inputs"):
                blocked.append(f"{relative} (SHA256_MISMATCH)")
            else:
                ok += 1
        if schema is not None:
            checked[str(study)] = (schema, ok)
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
    return sorted(set(blocked)), checked


def blocked_assets(root: Path = ROOT, studies=None) -> list[str]:
    """Return absent, unsupported or hash-mismatched inputs, verifier pins and outputs."""
    return authenticate(root, studies)[0]


def main() -> int:
    if Path.cwd().resolve() != ROOT or not (ROOT / "pyproject.toml").is_file():
        raise SystemExit("The research runner is checkout-local; run from the MAESTRO repository root")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
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
        studies = [(args.study.as_posix(), args.result.as_posix())] if args.study is not None else STUDIES
        if not studies:
            print("BLOCKED/ASSET_MISSING")
            print("No active frozen research protocol is released; supply --study PATH --result PATH.")
            return 2
        blocked, checked = authenticate(ROOT, studies)
        if blocked:
            schema_refused = any("FREEZE_SCHEMA_" in item for item in blocked)
            print("BLOCKED/FREEZE_SCHEMA_UNSUPPORTED" if schema_refused else "BLOCKED/ASSET_MISSING")
            print("\n".join(blocked))
            return 2
        for study, (schema, count) in checked.items():
            print(f"ENGINEERING_ONLY: {count} frozen files authenticated in {study} (schema '{schema}'); result present")
        print("Not executed: research verification (the study's verifier, replays, claim audit) and the scientific verdict.")
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
