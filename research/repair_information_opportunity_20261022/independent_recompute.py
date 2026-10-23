"""Independent exact cached-score envelope; no primary implementation imports.

Uses only csv/json/hashlib/Fraction and saved table identities. Execute only after
the parent signals that the primary computation has finished.
"""
from __future__ import annotations

import csv
from fractions import Fraction as F
import hashlib
import io
import json
from pathlib import Path
import subprocess
import time


ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / "log/20261022/repair_information_opportunity"
IDENTITIES = LOG / "CACHED_TABLE_IDENTITIES.json"
OUT = LOG / "INDEPENDENT_RECOMPUTE.json"
REPAIRS = (
    "M1:none:0:0", "M1:func:10:0.0001",
    "M1:mol:10:0.0001", "M1:both:10:0.0001",
)
BASELINES = ("B1:none", "Cmol", "B1:kernel2")
MARGIN = F(9, 100)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def mean(values):
    values = list(values)
    assert values
    return sum(values, F(0)) / len(values)


def number(value):
    return {"exact": str(value), "decimal": float(value)}


def calculate(identity):
    raw = (ROOT / identity["path"]).read_bytes()
    assert digest(raw) == identity["sha256"]
    assert len(raw) == identity["bytes"]
    rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    assert len(rows) == identity["rows"]
    assert list(rows[0]) == identity["header"]
    cells = {}
    for row in rows:
        cell, arm = row["cell"], row["arm"]
        packet = (row["lineage"], int(row["n_support"]),
                  int(row["n"]), F(row["prev"]))
        assert packet[1] == 3 and packet[2] >= 6
        if cell not in cells:
            cells[cell] = {"packet": packet, "scores": {}}
        assert cells[cell]["packet"] == packet
        scores = cells[cell]["scores"]
        assert arm not in scores
        p = F(row["prec5"])
        hits = min(range(6), key=lambda h: abs(p - F(h, 5)))
        assert abs(p - F(hits, 5)) <= F(1, 10**10)
        scores[arm] = F(hits, 5)
    assert sorted((cell, info["packet"][0]) for cell, info in cells.items()) == [
        tuple(pair) for pair in identity["cell_lineages"]
    ]
    for info in cells.values():
        assert sorted(info["scores"]) == identity["arms"]
    groups = {}
    for cell, info in sorted(cells.items()):
        groups.setdefault(info["packet"][0], []).append(cell)

    def aggregate(per_cell):
        return mean(mean(per_cell[cell] for cell in stocks)
                    for stocks in groups.values())

    baseline_means = {
        arm: aggregate({c: info["scores"][arm] for c, info in cells.items()})
        for arm in BASELINES
    }
    menus = {
        "R_only": REPAIRS,
        "R_plus_B1": REPAIRS + ("B1:none",),
        "R_plus_B1_Cmol": REPAIRS + ("B1:none", "Cmol"),
        "all_saved": tuple(identity["arms"]),
    }
    result = {}
    previous = None
    for name, arms in menus.items():
        per_cell = {c: max(info["scores"][a] for a in arms)
                    for c, info in cells.items()}
        envelope = aggregate(per_cell)
        if previous is not None:
            assert envelope >= previous
        previous = envelope
        fixed = {a: aggregate({c: info["scores"][a] for c, info in cells.items()})
                 for a in arms}
        assert envelope >= max(fixed.values())
        same_action_per_lineage = mean(
            max(mean(cells[c]["scores"][a] for c in stocks) for a in arms)
            for stocks in groups.values()
        )
        assert envelope >= same_action_per_lineage
        result[name] = {
            "arms": list(arms),
            "oracle_precision5": number(envelope),
            "oracle_hits5": number(5 * envelope),
            "single_action_per_lineage_precision5": number(same_action_per_lineage),
            "gain_over_baselines": {
                a: {"precision5": number(envelope - score),
                    "hits5": number(5 * (envelope - score)),
                    "strictly_below_margin": envelope - score < MARGIN}
                for a, score in baseline_means.items()
            },
            "oracle_switching_gain": number(envelope - max(fixed.values())),
            "best_fixed_arms": sorted(a for a in arms if fixed[a] == max(fixed.values())),
            "per_cell": {
                c: {"lineage": info["packet"][0],
                    "oracle_precision5": str(per_cell[c]),
                    "tied_maximizers": sorted(a for a in arms if info["scores"][a] == per_cell[c]),
                    "gain_over_baselines": {
                        a: str(per_cell[c] - info["scores"][a]) for a in BASELINES}}
                for c, info in sorted(cells.items())
            },
        }
    return {"source": identity["path"], "sha256": digest(raw),
            "cells": len(cells), "lineages": len(groups),
            "saved_arms": len(identity["arms"]),
            "baseline_precision5": {a: number(v) for a, v in baseline_means.items()},
            "menus": result}


def main():
    if OUT.exists():
        raise FileExistsError("Refuse to overwrite independent evidence")
    wall, cpu = time.perf_counter(), time.process_time()
    identities_raw = IDENTITIES.read_bytes()
    answer = {
        "kind": "Independent exact recomputation; exposed finite-sample scores only",
        "code_sha256": digest(Path(__file__).read_bytes()),
        "identities_sha256": digest(identities_raw),
        "protocol_sha256": digest((LOG / "UPPER_BOUND_PROTOCOL.md").read_bytes()),
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "margin_precision5": str(MARGIN),
        "margin_hits5": str(5 * MARGIN),
        "tables": [calculate(identity) for identity in json.loads(identities_raw)],
    }
    answer["wall_seconds"] = time.perf_counter() - wall
    answer["cpu_seconds"] = time.process_time() - cpu
    with OUT.open("x", encoding="utf-8") as stream:
        json.dump(answer, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(str(OUT))
    print(digest(OUT.read_bytes()))


if __name__ == "__main__":
    main()
