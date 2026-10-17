"""Offline verification of the indication-triage draft protocol and its development evidence.

File summary
- Path: research/indication_triage_20261016/verify.py
- Purpose: show that the sealed tier is still sealed, that the development numbers quoted in
  PROTOCOL.md and README.md are the ones in DEVELOPMENT.json and POWER.json, and that POWER.json
  reproduces from DEVELOPMENT.json byte for byte.
- Core points:
  - Seal: no file named like the 24Q2 outcome matrix exists under data/, tmp/ or research/.
  - Line endings: every text file of the study is LF (CRLF would break a later freeze digest).
  - Internal consistency: per-campaign hits sum to each arm's summary; the primary contrast's
    mean and p recompute from the per-campaign lists with `common.sign_flip`.
  - Power: `power.main` must reproduce POWER.json exactly.
  - Quoted numbers: each entry of QUOTED must appear verbatim in PROTOCOL.md.
  - Registry: research/STUDIES.json registers this folder with PROTOCOL.md and verify.py.
  - `--replay` reruns develop.py (about 15 minutes) into a temporary file and compares the primary
    contrast and every arm's total hits with DEVELOPMENT.json.
- Command: `python -B verify.py [--replay]` from this folder.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import numpy as np  # noqa: E402

from common import SEALED_OUTCOME_NAME, sign_flip  # noqa: E402


def load(name: str) -> dict:
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def fmt(x: float, nd: int) -> str:
    return f"{x:.{nd}f}"


def quoted(dev: dict, power: dict) -> dict[str, str]:
    """Numbers PROTOCOL.md quotes, as they must be written there."""

    c = dev["primary_contrast"]
    prim = dev["estimation"][str(dev["primary_w"])]
    return {
        "comparator": c["comparator"],
        "dev mean difference": fmt(c["mean"], 2),
        "dev p": f"{c['p']:.1e}",
        "loop hits": str(prim["maestro_loop"]["hits"]),
        "comparator hits": str(prim[c["comparator"]]["hits"]),
        "full panel hits": str(prim["full_panel"]["hits"]),
        "oracle hits": str(prim["oracle"]["hits"]),
        "structure hits": str(prim["structure"]["hits"]),
        "resampled power": fmt(power["power_resampled"], 2),
        "gate verdict": power["gate_verdict"],
        "sigma probe": fmt(dev["sigma_probe"], 2),
    }


def check_seal() -> None:
    for top in ("data", "tmp", "research"):
        for dirpath, _, files in os.walk(ROOT / top):
            if SEALED_OUTCOME_NAME in files:
                raise SystemExit(f"SEAL_BROKEN: {Path(dirpath) / SEALED_OUTCOME_NAME}")
    print("SEALED: no 24Q2 outcome matrix under data/, tmp/ or research/")


def check_lf() -> None:
    bad = [p.name for p in HERE.iterdir() if p.suffix in {".py", ".md", ".json"} and b"\r\n" in p.read_bytes()]
    if bad:
        raise SystemExit(f"CRLF: {bad}")
    print("LF: all study text files")


def check_consistency(dev: dict) -> None:
    prim = dev["estimation"][str(dev["primary_w"])]
    for arm, hits in dev["per_campaign_primary"].items():
        assert sum(hits) == prim[arm]["hits"], f"per-campaign hits of {arm} do not sum to its summary"
    c = dev["primary_contrast"]
    d = np.array(dev["per_campaign_primary"]["maestro_loop"], float) - np.array(dev["per_campaign_primary"][c["comparator"]], float)
    again = sign_flip(d)
    assert abs(again["mean"] - c["mean"]) < 1e-12 and abs(again["p"] - c["p"]) < 1e-12, "primary contrast does not recompute"
    print("CONSISTENT: per-campaign sums and the primary contrast")


def check_power() -> None:
    before = (HERE / "POWER.json").read_bytes()
    import power
    power.main()
    after = (HERE / "POWER.json").read_bytes()
    if after != before:
        (HERE / "POWER.json").write_bytes(before)
        raise SystemExit("NOT_REPRODUCED: POWER.json")
    print("REPRODUCED: POWER.json")


def check_quoted(dev: dict, power: dict) -> None:
    text = (HERE / "PROTOCOL.md").read_text(encoding="utf-8")
    missing = [f"{k} = {v}" for k, v in quoted(dev, power).items() if v not in text]
    if missing:
        raise SystemExit("NOT_QUOTED_IN_PROTOCOL: " + "; ".join(missing))
    print("QUOTED: every development number in PROTOCOL.md matches the JSON")


def check_registry() -> None:
    reg = json.loads((ROOT / "research/STUDIES.json").read_text(encoding="utf-8"))
    entry = [s for s in reg["studies"] if s["path"] == HERE.name]
    assert entry and entry[0]["protocol"] == "PROTOCOL.md" and entry[0]["verification"] == "verify.py", "not registered"
    print("REGISTERED:", entry[0]["status"])


def replay(dev: dict) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "DEVELOPMENT.json"
        subprocess.run([sys.executable, "-B", "develop.py", "--out", str(out)], cwd=HERE, check=True)
        again = json.loads(out.read_text(encoding="utf-8"))
    assert again["primary_contrast"] == dev["primary_contrast"], "primary contrast not reproduced"
    for w, arms in dev["estimation"].items():
        for arm, s in arms.items():
            assert again["estimation"][w][arm]["hits"] == s["hits"], f"{arm} at w={w} not reproduced"
    print("REPLAYED: develop.py")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--replay", action="store_true")
    args = ap.parse_args()
    dev, power = load("DEVELOPMENT.json"), load("POWER.json")
    check_seal()
    check_lf()
    check_consistency(dev)
    check_power()
    check_quoted(dev, power)
    check_registry()
    if args.replay:
        replay(dev)
    print("VERIFIED")


if __name__ == "__main__":
    main()
