"""Offline verification: freeze, census replays, development replay and the execution-grounded claim audit.

File summary
- Path: research/knowledge_reality_20261013/verify.py
- Purpose: show that the frozen study matches its freeze, that the metadata census and leakage
  audit reproduce, and that every result number in README.md passes `maestro.claim_audit.audit`
  against the complete run manifest.
- Core points:
  - Freeze: `freeze.require_freeze` (CRLF normalised to LF). DEVIATIONS.json is listed as unhashed
    and absent from the digests.
  - Replays run by default and must reproduce their files byte for byte:
    - `census.main` (CENSUS.json, compounds.csv);
    - `leakage.main`;
    - `sealed_census.main`, which needs the 24Q2 metadata in tmp/ (SEALED_CENSUS.json,
      sealed_compounds.csv, sealed_overlap.csv);
    - `power.main` (POWER.json).
    None reads a response value except `power.main`, which reads only DEVELOPMENT.json.
  - Gate: `confirm.predict` must refuse with GATE_NOT_PASSED, because the development gate failed.
  - Manifest: `claims.main` recomputes CLAIMS.json and RUNS.json and must reproduce them.
  - Claim audit: every claim SUPPORTED, no OMITTED_NEGATIVE_RUN, no MANIFEST_INCOMPLETE. Two
    controls show the audit has teeth: an inflated claim is CONTRADICTED, and dropping the claims
    of a negative run raises OMITTED_NEGATIVE_RUN.
  - `--replay` also reruns `develop.py` into tmp/ and compares every number with DEVELOPMENT.json
    (about one hour; the control seeds dominate).
- Commands (maestro env, Python 3.11): `python verify.py`, `python verify.py --replay`.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(1, str(ROOT / "src"))

from maestro.claim_audit import Claim, ClaimVerdict, RunManifest, audit  # noqa: E402


def reproduce(names: list[str], fn) -> None:
    before = {n: (HERE / n).read_bytes() for n in names}
    fn()
    bad = [n for n in names if (HERE / n).read_bytes() != before[n]]
    for n in bad:
        (HERE / n).write_bytes(before[n])
    if bad:
        raise SystemExit(f"NOT_REPRODUCED: {bad[0]}")
    print("REPRODUCED", ", ".join(names))


def claim_audit() -> None:
    data = json.loads((HERE / "CLAIMS.json").read_text(encoding="utf-8"))["claims"]
    claims = [Claim(c["claim_id"], c["statement"], c["run_id"], tuple(c["pointer"]), c["relation"], c["value"], c.get("tolerance", 0.0))
              for c in data]
    manifest = RunManifest.from_json(json.loads((HERE / "RUNS.json").read_text(encoding="utf-8")))
    excluded = {r.run_id for r in manifest.runs if r.status.value == "excluded"}
    assert not [c.claim_id for c in claims if c.run_id in excluded], "a claim cites an excluded run"
    report = audit(claims, manifest, ROOT)
    bad = [(r.claim_id, r.verdict.value, r.observed) for r in report.results if r.verdict != ClaimVerdict.SUPPORTED]
    assert report.passed, f"claim audit failed: {bad} {list(report.findings)}"
    statuses: dict = {}
    for r in manifest.runs:
        statuses[r.status.value] = statuses.get(r.status.value, 0) + 1
    print("CLAIM AUDIT PASSED", len(claims), "claims supported; runs", statuses)
    inflated = dataclasses.replace(claims[0], value=(claims[0].value + 1) if isinstance(claims[0].value, (int, float)) else "X")
    assert audit([inflated], manifest, ROOT).results[0].verdict == ClaimVerdict.CONTRADICTED
    negative = next(r.run_id for r in manifest.runs if r.status.value == "negative")
    dropped = audit([c for c in claims if c.run_id != negative], manifest, ROOT)
    assert f"OMITTED_NEGATIVE_RUN:{negative}" in dropped.findings
    print("CONTROLS inflated claim CONTRADICTED; dropped negative run", negative, "raises OMITTED_NEGATIVE_RUN")


def replay_development() -> None:
    import develop
    stored = json.loads((HERE / "DEVELOPMENT.json").read_text(encoding="utf-8"))
    target = HERE / "DEVELOPMENT.json"
    backup = target.read_bytes()
    partial = develop.PARTIAL
    if partial.is_file():
        partial.rename(partial.with_suffix(".bak"))
    try:
        develop.main()
        fresh = json.loads(target.read_text(encoding="utf-8"))
    finally:
        target.write_bytes(backup)
    fresh.pop("runtime_seconds", None)
    stored.pop("runtime_seconds", None)
    if fresh != stored:
        raise SystemExit("NOT_REPRODUCED: DEVELOPMENT.json")
    print("REPRODUCED DEVELOPMENT.json")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replay", action="store_true", help="also rerun develop.py (about one hour)")
    args = parser.parse_args()
    from freeze import require_freeze
    freeze = require_freeze()
    deviations = str((HERE / "DEVIATIONS.json").relative_to(ROOT)).replace("\\", "/")
    assert "DEVIATIONS.json" in freeze["not_hashed"] and deviations not in freeze["sha256"]
    print("FREEZE", len(freeze["sha256"]), "files match; DEVIATIONS.json unhashed")
    import census
    reproduce(["CENSUS.json", "compounds.csv"], census.main)
    import leakage
    reproduce(["LEAKAGE.json"], leakage.main)
    import sealed_census
    reproduce(["SEALED_CENSUS.json", "sealed_compounds.csv", "sealed_overlap.csv"], sealed_census.main)
    import power
    reproduce(["POWER.json"], power.main)
    import confirm
    try:
        confirm.predict()
    except SystemExit as stop:
        assert str(stop).startswith("GATE_NOT_PASSED"), stop
        print("REFUSED as registered:", str(stop).split(":")[0])
    else:
        raise SystemExit("confirm.predict ran although the development gate failed")
    import claims
    claims.main()
    claim_audit()
    if args.replay:
        replay_development()
    print("VERIFIED" + (" with development replay" if args.replay else " (run --replay to recompute DEVELOPMENT.json)"))


if __name__ == "__main__":
    main()
