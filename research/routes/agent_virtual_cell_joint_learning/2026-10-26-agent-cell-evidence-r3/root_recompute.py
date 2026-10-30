"""Coordinator's Decimal recheck; not an independent-agent review."""
import csv
from decimal import Decimal
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
result = json.loads((HERE / "CONTRAST_RESULTS.json").read_text(encoding="utf-8"))
raw = ROOT / "research/eight_directions_20261026/evidence_audit/raw/PAIR_SCREEN.csv"
expected = {"147": ("BJ", "N22", "O22"), "148": ("BJ", "N22", "O22"),
            "157": ("A673", "O1", "O2"), "158": ("A673", "O1", "O2")}
probes = {tuple(sorted((("Axitinib", Decimal(".1")), (drug, Decimal(".1"))))): name
          for name, drug in [("a", "Dexrazoxane"), ("b", "Lestaurtinib")]}
paid, source, plate_counts = {}, [], {}
with raw.open(encoding="utf-8-sig", newline="") as stream:
    for row in csv.DictReader(stream):
        stage, plate = row["Iteration"], row["Plate"]
        old = stage.isdigit() and 1 <= int(stage) <= 10
        bought = stage == "11" and plate in expected
        if not (old or bought):
            continue
        if bought:
            assert row["Cell line"] == expected[plate][0]
            plate_counts[plate] = plate_counts.get(plate, 0) + 1
        if row["Drug 1"] not in {"Axitinib", "Dexrazoxane", "Lestaurtinib"}:
            continue
        if row["Drug 2"] not in {"Axitinib", "Dexrazoxane", "Lestaurtinib"}:
            continue
        key = tuple(sorted((row[f"Drug {i}"], Decimal(row[f"Conc {i} (uM)"])) for i in (1, 2)))
        label = probes.get(key)
        if label is None:
            continue
        if old:
            source.append((row["Cell line"], stage, plate, label))
            continue
        assert row["Well"] == expected[plate][1 if label == "a" else 2]
        assert row["Failed QC"].lower() == "false"
        assert (plate, label) not in paid
        paid[plate, label] = row
assert not source and not result["source_probe_rows"]
assert plate_counts == {p: 383 for p in expected} and len(paid) == 8
differences = {}
for plate in expected:
    d = Decimal(paid[plate, "a"]["Viability"]) - Decimal(paid[plate, "b"]["Viability"])
    differences[plate] = str(d)
    reported = next(x["d"] for x in result["differences"] if x["plate"] == plate)
    assert abs(d - Decimal(str(reported))) < Decimal("1e-15")
for item in result["paid_probe_rows"]:
    row = paid[item["plate"], item["probe"]]
    assert (item["file"], item["well"], item["cell"]) == (row["file"], row["Well"], row["Cell line"])
for item in result["sensitivity"]:
    eps = Decimal(str(item["epsilon"]))
    crossing = all(Decimal(differences[p]) > eps for p in ("157", "158")) and all(
        Decimal(differences[p]) < -eps for p in ("147", "148"))
    assert crossing == item["repeat_consistent_crossing"]
for relative, digest in result["files"].items():
    assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest
out = dict(status="coordinator_recompute_passed", independent_agent_review_complete=False,
           source_exact_probe_rows=len(source), physical_plate_records=plate_counts,
           decimal_differences=differences, checked_result_sha256=hashlib.sha256(
               (HERE / "CONTRAST_RESULTS.json").read_bytes()).hexdigest(),
           limits="Checks fixed probes and artifact consistency; no biological noise inference or policy gain.")
(HERE / "root_recompute_results.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
print(json.dumps(out, indent=2))
