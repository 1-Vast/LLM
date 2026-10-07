"""Check both compact replays with raw-data reads, GPU packages and network blocked.

This is a portability diagnostic inside the current Windows environment, not a
clean Linux installation test. Reused outcomes add no independent evidence.
"""
from __future__ import annotations

import argparse
import builtins
from contextlib import ExitStack
import importlib.abc
import io
import json
from pathlib import Path
import runpy
import socket
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


class NoLargePackages(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in {"torch", "h5py", "pandas", "scipy", "sklearn"}:
            raise ImportError("Large optional package forbidden in scalar replay: " + fullname)


def guarded_open(original):
    def open_file(file, *args, **kwargs):
        if isinstance(file, (str, bytes, Path)):
            path = Path(file).resolve()
            if path.is_relative_to(ROOT / "data") or path.suffix == ".ckpt":
                raise RuntimeError("Raw/model asset read forbidden in scalar replay")
        return original(file, *args, **kwargs)
    return open_file


def deny_network(*args, **kwargs):
    raise RuntimeError("Network forbidden in scalar replay")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    finder = NoLargePackages()
    sys.meta_path.insert(0, finder)
    try:
        with ExitStack() as stack:
            stack.enter_context(patch("builtins.open", guarded_open(builtins.open)))
            stack.enter_context(patch("io.open", guarded_open(io.open)))
            stack.enter_context(patch.object(socket.socket, "connect", deny_network))
            stack.enter_context(patch.object(socket.socket, "connect_ex", deny_network))
            for module, args_list in (
                ("packet", ["replay", "--source", str(HERE / "compact_packet2"), "--out", str(out / "development")]),
                ("transfer", ["replay", "--packet", str(HERE / "transfer_packet1"), "--out", str(out / "transfer")]),
            ):
                sys.argv = [module, *args_list]
                runpy.run_module("research.astra.decision_opportunity_20261007." + module, run_name="__main__")
    finally:
        sys.meta_path.remove(finder)
    development = json.loads((out / "development/REPLAY.json").read_text())
    expected = json.loads((HERE / "packet_replay2/REPLAY.json").read_text())
    assert development["episodes"] == expected["episodes"]
    transfer = (out / "transfer/EPISODES.jsonl").read_text().splitlines()
    expected_transfer = (HERE / "transfer_run1/EPISODES.jsonl").read_text().splitlines()
    assert [json.loads(line) for line in transfer] == [json.loads(line) for line in expected_transfer]
    receipt = {"status": "PASS", "development_episodes": len(development["episodes"]),
               "transfer_episodes": len(transfer), "exact_decisions_utilities_charges": True,
               "blocked": ["all repository data/ reads", "checkpoint reads", "network connections",
                           "torch", "h5py", "pandas", "scipy", "sklearn"],
               "scope": "Same Windows interpreter; not a clean Linux installation or fresh scientific evidence"}
    (out / "PORTABILITY_RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
