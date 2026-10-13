"""Offline verification: freeze, choice and result replays, and the execution-grounded claim audit.

File summary
- Path: research/selective_hit_triage_20261013/verify.py
- Purpose: show that the frozen study still matches its freeze, that the locked choices and every
  recorded result reproduce from code and data, and that every number README.md reports passes
  `maestro.claim_audit.audit` against the complete run manifest.
- Core points:
  - Freeze: `outcomes.require_freeze` (CRLF normalised to LF). DEVIATIONS.json is listed as unhashed
    and absent from the digests.
  - Choices: `test_choose.main` recomputes TEST_CHOICES.json and must reproduce it and CHOICES_LOCK.
  - Manifest: `claims.main` recomputes CLAIMS.json and RUNS.json (artifact digests) and must reproduce
    them.
  - Claim audit: every claim SUPPORTED, and no report-level finding (OMITTED_NEGATIVE_RUN,
    MANIFEST_INCOMPLETE). No claim may cite the excluded as-run results.
  - Two controls show the audit has teeth:
    - an inflated copy of one claim must be CONTRADICTED;
    - dropping the claims that cite a negative run must raise OMITTED_NEGATIVE_RUN.
  - `--replay` also reruns `evaluate`, `evaluate_registered` and `posthoc`. Each is write-once and
    must print REPRODUCED. This takes about 20 minutes, because CTRP is re-read from the archive.
- Commands (maestro env, Python 3.11):
  - `python verify.py`
  - `python verify.py --replay`
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


def load_claims() -> list[Claim]:
    data = json.loads((HERE / "CLAIMS.json").read_text(encoding="utf-8"))["claims"]
    return [Claim(c["claim_id"], c["statement"], c["run_id"], tuple(c["pointer"]), c["relation"], c["value"], c.get("tolerance", 0.0))
            for c in data]


def claim_audit() -> None:
    claims = load_claims()
    manifest = RunManifest.from_json(json.loads((HERE / "RUNS.json").read_text(encoding="utf-8")))
    excluded = {r.run_id for r in manifest.runs if r.status.value == "excluded"}
    assert not [c.claim_id for c in claims if c.run_id in excluded], "a claim cites an excluded run"
    report = audit(claims, manifest, ROOT)
    bad = [(r.claim_id, r.verdict.value, r.observed) for r in report.results if r.verdict != ClaimVerdict.SUPPORTED]
    assert report.passed, f"claim audit failed: {bad} {list(report.findings)}"
    statuses = {}
    for r in manifest.runs:
        statuses[r.status.value] = statuses.get(r.status.value, 0) + 1
    print("CLAIM AUDIT PASSED", len(claims), "claims supported;", "runs", statuses)

    inflated = dataclasses.replace(claims[1], value=claims[1].value + 1)
    assert audit([inflated], manifest, ROOT).results[0].verdict == ClaimVerdict.CONTRADICTED
    negative = next(r.run_id for r in manifest.runs if r.status.value == "negative")
    dropped = audit([c for c in claims if c.run_id != negative], manifest, ROOT)
    assert f"OMITTED_NEGATIVE_RUN:{negative}" in dropped.findings
    print("CONTROLS inflated claim CONTRADICTED; dropped negative run", negative, "raises OMITTED_NEGATIVE_RUN")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replay", action="store_true", help="also replay the one-shot evaluations (about 20 minutes)")
    args = parser.parse_args()

    from outcomes import require_freeze
    freeze = require_freeze()
    deviations = str((HERE / "DEVIATIONS.json").relative_to(ROOT)).replace("\\", "/")
    assert "DEVIATIONS.json" in freeze["not_hashed"] and deviations not in freeze["sha256"]
    print("FREEZE", len(freeze["sha256"]), "files match; DEVIATIONS.json unhashed")

    import test_choose
    test_choose.main()
    import claims
    claims.main()
    claim_audit()

    if args.replay:
        import evaluate
        import evaluate_registered
        import posthoc
        evaluate.main()
        evaluate_registered.main()
        posthoc.main()
    print("VERIFIED" + (" with replays" if args.replay else " (run --replay to recompute the results)"))


if __name__ == "__main__":
    main()
