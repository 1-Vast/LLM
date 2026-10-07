"""Reproduce the frozen boundary run without raw assets, GPU packages or network.

This checks the current Windows interpreter, not a clean installation or an OS
security boundary. Repeated outcomes add no independent scientific evidence.
"""
from __future__ import annotations

import argparse
from contextlib import ExitStack
import builtins
import importlib.abc
import io
import json
from pathlib import Path
import runpy
import socket
import sys
from unittest.mock import patch

from research.astra.decision_opportunity_20261007.verify_affordable_replay import (
    deny_network, guarded_open,
)

HERE = Path(__file__).resolve().parent


class NoLargePackages(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in {"torch", "h5py", "pandas", "sklearn"}:
            raise ImportError("Optional package forbidden in scalar replay: " + fullname)


def json_lines(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    if out.exists():
        raise ValueError("Use a fresh output directory")
    finder = NoLargePackages()
    sys.meta_path.insert(0, finder)
    try:
        with ExitStack() as stack:
            stack.enter_context(patch("builtins.open", guarded_open(builtins.open)))
            stack.enter_context(patch("io.open", guarded_open(io.open)))
            stack.enter_context(patch.object(socket.socket, "connect", deny_network))
            stack.enter_context(patch.object(socket.socket, "connect_ex", deny_network))
            sys.argv = ["execute", "replay", "--packet", str(HERE / "packet2"), "--out", str(out)]
            runpy.run_module("research.astra.boundary_acquisition_20261007.execute", run_name="__main__")
    finally:
        sys.meta_path.remove(finder)
    expected = HERE / "run1"
    actual_rows, expected_rows = json_lines(out / "EPISODES.jsonl"), json_lines(expected / "EPISODES.jsonl")
    for rows in (actual_rows, expected_rows):
        for row in rows:
            row.pop("elapsed_seconds")
    assert actual_rows == expected_rows, "Episode decisions, outcomes or charges changed"
    for name in ("purchases.jsonl", "policy.jsonl"):
        assert json_lines(out / name) == json_lines(expected / name), name
    assert json.loads((out / "REPLACEMENT_AUDIT.json").read_text()) == json.loads(
        (expected / "REPLACEMENT_AUDIT.json").read_text())
    assert (out / "PREFIX_FRONTIER.csv").read_bytes() == (expected / "PREFIX_FRONTIER.csv").read_bytes()
    actual_summary = json.loads((out / "SUMMARY.json").read_text())
    expected_summary = json.loads((expected / "SUMMARY.json").read_text())
    actual_summary.pop("elapsed_seconds")
    expected_summary.pop("elapsed_seconds")
    assert actual_summary == expected_summary, "Summary differs"
    receipt = dict(status="PASS", episodes=len(actual_rows), profiles=actual_summary["profiles"],
        exact_decisions_utilities_charges_and_traces=True,
        blocked=["repository data/ reads", "checkpoint reads", "network connections", "torch", "h5py", "pandas", "sklearn"],
        allowed=["numpy", "scipy.special.ndtr", "production CaseStore", "frozen source files", "1.118 MB scalar packet"],
        excluded_from_equality=["wall-clock timing"],
        scope="Same Windows interpreter; neither clean Linux verification nor fresh biological evidence")
    (out / "PORTABILITY_RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt), flush=True)


if __name__ == "__main__":
    main()
