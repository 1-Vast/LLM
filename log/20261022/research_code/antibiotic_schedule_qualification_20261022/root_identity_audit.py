"""Offline identity-only projection of the pinned example growth table."""
import base64
import csv
import hashlib
import io
import json
import math
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/antibiotic_schedule_qualification/schema_audit"
FIELDS = ["Time", "Dose_A", "Dose_B", "Growth", "Dosing_Type"]
TYPES = {"A+B", "A-B", "B-A"}


def project(payload):
    table = csv.DictReader(io.StringIO(payload.decode("utf-8-sig")))
    if table.fieldnames != FIELDS:
        raise ValueError("Unregistered schema; do not guess identity columns")
    counts, keys, times, trajectories, coverage = Counter(), Counter(), set(), set(), {}
    for row in table:
        kind = row["Dosing_Type"]
        if kind not in TYPES:
            raise ValueError("Unregistered identity label; do not export")
        t, a, b = (float(row[x]) for x in FIELDS[:3])
        if not all(math.isfinite(x) for x in (t, a, b)):
            raise ValueError("Nonfinite identity key")
        identity = (a, b, kind)
        counts[kind] += 1
        keys[(t, *identity)] += 1
        times.add(t)
        trajectories.add(identity)
        coverage.setdefault(identity, set()).add(t)
    return {"headers": FIELDS, "rows": sum(counts.values()), "rows_by_type": dict(counts),
            "unique_time_keys": len(times), "unique_dose_pair_type_keys": len(trajectories),
            "trajectories_by_type": dict(Counter(x[2] for x in trajectories)),
            "unique_time_dose_type_keys": len(keys),
            "duplicate_identity_rows": sum(n - 1 for n in keys.values()),
            "time_count_per_trajectory_histogram": dict(Counter(len(v) for v in coverage.values())),
            "growth_read_by_projection": False, "growth_values_exported": False}


def checks():
    prefix = b"Time,Dose_A,Dose_B,Growth,Dosing_Type\n"
    a = project(prefix + b"0,1,2,9.123456,A+B\n0,1,2,8.123456,A+B\n")
    assert a["rows"] == 2 and a["duplicate_identity_rows"] == 1
    b = project(prefix + b"0,1,2,UNREAD_TEXT,A+B\n0,1,2,999999,A+B\n")
    assert a == b
    for invalid in (b"Time,Growth\n0,1\n", prefix + b"NaN,1,2,0,A+B\n", prefix + b"0,1,2,0,unknown\n"):
        try:
            project(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid identity/schema accepted")
    return {"distinct_projection_checks_passed": 5}


def main():
    target = OUT / "IDENTITY.json"
    if target.exists():
        raise FileExistsError(target)
    source = OUT / "sealed_sources/growth_data.csv.http.json"
    payload = base64.b64decode(json.loads(source.read_bytes())["content"])
    actual = hashlib.sha1(b"blob " + str(len(payload)).encode() + b"\0" + payload).hexdigest()
    if actual != "4197e4588383cd2a2441704f758f2533a3abe6bf":
        raise ValueError("Source integrity changed")
    result = {"identity": project(payload), "checks": checks(),
              "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
              "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    target.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
