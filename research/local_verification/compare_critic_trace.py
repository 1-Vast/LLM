"""Compare two traces of the same inputs, with the typed critic off and on, and rule on the boundary.

File summary
- Path: research/local_verification/compare_critic_trace.py
- Purpose: the typed decision model is advisory. That claim is only worth as much as a run that
  checks it, so this compares a trace taken with `--decision-critic off` against one taken with it
  on and reports whether the difference stayed inside the advisory block.
- Core points:
  - The deterministic check block must be byte-identical between the two runs; anything else means
    a model prediction moved a premise, which is the failure the boundary exists to prevent.
  - Every judgment must read `evidence_kind: model_prediction`.
  - A changed selection is reported, not assumed wrong: it is legal only as a tie-break from a
    graded scope, and the verdict says so rather than deciding it.
- Interfaces: `main()`
- Depends on: (standard library only)
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def first_turn(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    record = payload.get("record", payload)
    turns = record.get("turns") or [record]
    return turns[0]


def selection(turn: dict[str, Any]) -> list[str]:
    return [action.get("identifier") for action in turn.get("selected_actions") or []]


def main() -> int:
    parser = argparse.ArgumentParser(description="Rule on whether the typed critic stayed advisory.")
    parser.add_argument("--without", type=Path, required=True, help="Trace taken with --decision-critic off.")
    parser.add_argument("--with", dest="with_critic", type=Path, required=True, help="Trace taken with it on.")
    arguments = parser.parse_args()

    off, on = first_turn(arguments.without), first_turn(arguments.with_critic)
    review = on.get("decision_review") or {}
    judgments = review.get("judgments") or []
    failures: list[str] = []

    if off.get("check") != on.get("check"):
        differing = sorted(
            key for key in set(off.get("check", {})) | set(on.get("check", {}))
            if off.get("check", {}).get(key) != on.get("check", {}).get(key)
        )
        failures.append(f"the deterministic check changed: {differing}")
    illegal = sorted({
        str(item.get("evidence_kind")) for item in judgments if item.get("evidence_kind") != "model_prediction"
    })
    if illegal:
        failures.append(f"a judgment claimed an origin other than model_prediction: {illegal}")

    print(f"critic reached provider   {bool(review.get('model_version'))}")
    print(f"model_version             {review.get('model_version')!r}")
    print(f"judgments                 {len(judgments)}")
    print(f"refusals                  {review.get('refusals') or 'none'}")
    print(f"suppressed_by_revocation  {review.get('suppressed_by_revocation')}")
    print(f"findings                  {review.get('findings') or 'none'}")
    print()
    for item in judgments:
        print(
            f"  {item.get('question_id'):<28} scope={item.get('scope')} kind={item.get('kind')} "
            f"value={item.get('value')!r} p={item.get('probability')} "
            f"evidence_kind={item.get('evidence_kind')}"
        )
    print()
    print(f"check block identical     {off.get('check') == on.get('check')}")
    print(f"selection without critic  {selection(off)}")
    print(f"selection with critic     {selection(on)}")
    if selection(off) != selection(on):
        print()
        print("The selection moved. That is legal only as a tie-break from a scope the judgment")
        print("ledger has graded. Report this rather than accepting it: it is the finding this")
        print("comparison exists to surface.")

    print()
    if failures:
        print("VERDICT  boundary violated")
        for item in failures:
            print(f"  - {item}")
        return 1
    if not review.get("model_version"):
        print("VERDICT  inconclusive: the critic never reached the provider, so nothing was tested.")
        print("         run probe_typesafe.py to find out why before reading anything into this.")
        return 2
    print("VERDICT  the critic stayed advisory on this case")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
