"""Read-only verification of an imported repeat study; never refreeze outcomes.

Checks saved scores and measurements, not model training or unseen biology.
Default output is stdout. --output requires a new file.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path
import sqlite3
from statistics import fmean
import zipfile

ROOT = Path(__file__).resolve().parents[3]
STUDY = ROOT / "research/astra/repeat_signal_20261005"
ARCHIVE = ROOT / "research/MAESTRO_repeat_signal_20261005.zip"
ARMS = ["simple", "hotspot", "hotspot_shuffled", "dependency",
        "dependency_shuffled", "target_dependency", "target_shuffled",
        "rna_binary", "prior_control"]


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def rows(path):
    with (gzip.open if path.suffix == ".gz" else open)(path, "rt", newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def checkout_path(name):
    path = (ROOT / name).resolve()
    require(path.is_relative_to(ROOT), "Path outside checkout: " + name)
    return path


def pearson(a, b):
    ma, mb = fmean(a), fmean(b)
    va, vb = sum((x-ma)**2 for x in a), sum((x-mb)**2 for x in b)
    require(va > 0 and vb > 0, "Undefined correlation")
    return sum((x-ma)*(y-mb) for x, y in zip(a, b)) / math.sqrt(va*vb)


def line_average(groups):
    lines = defaultdict(list)
    for (_, sidm, _), value in groups.items():
        lines[sidm].append(value)
    return fmean(fmean(values) for values in lines.values())


def verify():
    manifest = load(STUDY / "RUN_MANIFEST.json")
    exact = 0
    with zipfile.ZipFile(ARCHIVE) as bundle:
        names = [item.filename for item in bundle.infolist() if not item.is_dir()]
        require(len(names) == len(set(names)), "Duplicate archive names")
        for name in names:
            path = checkout_path(name)
            require(path.is_relative_to(STUDY), "Unexpected archive root")
            require(path.read_bytes() == bundle.read(name), "Archive byte mismatch: " + name)
            exact += 1
    for name, expected in manifest["files"].items():
        path = checkout_path(name)
        require(path.stat().st_size == expected["bytes"] and digest(path) == expected["sha256"],
                "Imported manifest mismatch: " + name)
    require(digest(ARCHIVE) == load(Path(__file__).parent / "import_receipt.json")["archive_sha256"],
            "Archive hash differs from import receipt")
    freezes = {}
    for freeze in sorted(STUDY.glob("freeze*.json")):
        counts = defaultdict(int)
        variations = []
        for name, expected in load(freeze)["files"].items():
            path = checkout_path(name)
            status = "missing"
            actual = None
            if path.exists():
                raw = path.read_bytes()
                actual = hashlib.sha256(raw).hexdigest()
                status = "exact" if actual == expected else "mismatch"
                if status == "mismatch" and path.suffix in (".py", ".md", ".json", ".csv"):
                    if hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest() == expected:
                        status = "LF_equivalent_raw_bytes_differ"
            counts[status] += 1
            if status != "exact":
                variations.append({"path": name, "status": status,
                                   "recorded_sha256": expected, "checkout_sha256": actual})
        freezes[freeze.name] = {"counts": dict(counts), "differences": variations}
    large_sources = {}
    for name, item in manifest["large_source_inputs"].items():
        path = checkout_path(item["path"])
        status = "missing_not_packaged"
        if path.exists():
            status = "exact" if digest(path) == item["sha256"] else "mismatch"
        large_sources[name] = {"path": item["path"], "status": status,
                               "recorded_sha256": item["sha256"]}

    catalog = load(STUDY / "evidence_catalog_manifest.json")
    databases = {}
    for filename, hash_key in [("feature_catalog.sqlite", "feature_db_sha256"),
                                ("experimental_evidence.sqlite", "experimental_db_sha256")]:
        path = STUDY / filename
        before = digest(path)
        require(before == catalog[hash_key], "Database catalog hash mismatch")
        with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) as db:
            db.execute("PRAGMA query_only=ON")
            require(db.execute("PRAGMA integrity_check").fetchone()[0] == "ok", "Database integrity failed")
            tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
            counts = {name: db.execute('SELECT count(*) FROM "'+name.replace('"', '""')+'"').fetchone()[0]
                      for name in tables}
            if filename.startswith("experimental"):
                for name, expected in catalog["counts"].items():
                    require(counts[name] == expected, "Database count mismatch: " + name)
                for table in ["measurement", "candidate_prediction", "benchmark_pair", "raw_repeat_endpoint"]:
                    count = db.execute("SELECT count(*) FROM " + table + " t LEFT JOIN assay_condition c USING(condition_id) WHERE c.condition_id IS NULL").fetchone()[0]
                    require(count == 0, "Orphan conditions: " + table)
                for col in ["R1_measurement", "R2_measurement", "R3_measurement"]:
                    count = db.execute("SELECT count(*) FROM benchmark_pair b LEFT JOIN measurement m ON b."+col+"=m.measurement_id WHERE b."+col+" IS NOT NULL AND (m.measurement_id IS NULL OR m.condition_id!=b.condition_id)").fetchone()[0]
                    require(count == 0, "Invalid benchmark measurement link")
            else:
                for name, key in [("drug", "drugs"), ("drug_target_annotation", "target_annotations"),
                                  ("cell_context", "cell_pathway_scores"), ("target_dependency", "dependency_values")]:
                    require(counts[name] == catalog["feature_counts"][key], "Feature count mismatch")
            databases[filename] = {"integrity": "ok", "counts": counts,
                                   "sha256": before, "unchanged": digest(path) == before}

    estimates = {}
    for folder, first, second, section in [("results", "y1", "y2", "main"),
                                           ("raw_results", "raw_y1", "raw_y2", "results")]:
        grouped = defaultdict(list)
        saved = rows(STUDY / folder / "paired_actions.csv.gz")
        for row in saved:
            grouped[tuple(row[k] for k in ("Tissue", "SIDM", "role"))].append(row)
        corr, residual = {}, {}
        for key, group in grouped.items():
            a, b = [[float(row[col]) for row in group] for col in (first, second)]
            pa, pb = [[float(row[col]) for row in group] for col in ("prior_A", "prior_B")]
            corr[key] = pearson(a, b)
            residual[key] = (pearson([x-p for x,p in zip(a,pa)], [x-p for x,p in zip(b,pb)])
                             + pearson([x-p for x,p in zip(a,pb)], [x-p for x,p in zip(b,pa)]))/2
        summary = load(STUDY / folder / "summary.json")
        expected = summary[section] if folder == "results" else summary[section]["raw_y"]["summary"]
        point = {"pearson": line_average(corr), "residual_split": line_average(residual)}
        for key, value in point.items():
            require(abs(value - expected[key]["mean"]) < 1e-12, "Saved correlation mismatch")
        estimates[folder] = {"rows": len(saved), "lines": len({r["SIDM"] for r in saved}), **point}

    # Rebuild event aggregation from the saved plate endpoints, not raw intensities.
    event_keys = ("Tissue", "SIDM", "ANCHOR_ID", "LIBRARY_ID", "event")
    concentrations = defaultdict(list)
    plate_rows = rows(STUDY / "raw_results/plate_endpoints.csv.gz")
    for row in plate_rows:
        key = tuple(row[k] for k in event_keys) + (row["ANCHOR_CONC"],)
        concentrations[key].append(float(row["raw_y"]))
    events = defaultdict(list)
    for key, values in concentrations.items():
        events[key[:-1]].append(fmean(values))
    checks = 0
    for row in rows(STUDY / "raw_results/paired_actions.csv.gz"):
        for number in (1, 2, 3):
            value = row["raw_y"+str(number)]
            if not value:
                continue
            key = tuple(row[k] for k in event_keys[:-1]) + (row["event"+str(number)],)
            require(key in events and abs(max(events[key])-float(value)) < 1e-12,
                    "Saved raw event aggregation mismatch")
            checks += 1
    estimates["raw_results"]["saved_plate_rows"] = len(plate_rows)
    estimates["raw_results"]["event_values_reconstructed"] = checks

    policies = {}
    for folder, arms, cost_suffix in [("rna_results", ["simple", "rna", "shuffled"], "measurements"),
                                      ("recovered_biology_results", ARMS, "cost")]:
        data = rows(STUDY / folder / "predictions.csv.gz")
        grouped = defaultdict(list)
        for row in data:
            grouped[tuple(row[k] for k in ("Tissue", "SIDM", "role"))].append(row)
        per = {tuple(row[k] for k in ("Tissue", "SIDM", "role")): row
               for row in rows(STUDY / folder / "per_role.csv")}
        summary = load(STUDY / folder / "summary.json")
        train = {sidm for tissue in summary["folds"].values() for sidm in tissue}
        evaluation = {r["SIDM"] for r in data}
        require(len(train) == 111 and len(evaluation) == 14 and not train & evaluation,
                "Training/evaluation identities overlap")
        values, confirmed = defaultdict(dict), {}
        headroom, first_round_hits, verification_capacities = [], [], []
        oracle_gain = 0
        for key, group in grouped.items():
            cap = math.ceil(.2*len(group))
            screens = math.floor(.7*cap)
            for arm in arms:
                require(all(math.isfinite(float(r[arm+"_score"])) for r in group), "Nonfinite score")
                order = sorted(group, key=lambda r: (-float(r[arm+"_score"]), r["pair"]))
                positive = lambda r, column: r[column] in ("True", "1", "1.0")
                verification = [r for r in order[:screens] if positive(r, "hit1")][:cap-screens]
                hits = {r["pair"] for r in verification if positive(r, "hit2")}
                actual = {"P2_confirmed": len(hits), "P2_"+cost_suffix: screens+len(verification),
                          "R2_positive": sum(positive(r, "hit2") for r in order[:cap])}
                require(screens+len(verification) <= cap, "Budget exceeded")
                for metric, value in actual.items():
                    column = metric+"_"+arm
                    require(value == float(per[key][column]), "Per-role accounting mismatch")
                    values[column][key] = value
                confirmed[key, arm] = hits
                if arm == "prior_control":
                    screen_hits = [r for r in order[:screens] if positive(r, "hit1")]
                    capacity = cap-screens
                    oracle = min(capacity, sum(positive(r, "hit2") for r in screen_hits))
                    oracle_gain += oracle-len(hits)
                    first_round_hits.append(len(screen_hits))
                    verification_capacities.append(capacity)
                    if len(screen_hits) > capacity:
                        headroom.append({"SIDM": key[1], "role": key[2],
                                         "first_round_hits": len(screen_hits),
                                         "verification_capacity": capacity,
                                         "observed_confirmed": len(hits),
                                         "fixed_screen_oracle_confirmed": oracle})
        means = {column: line_average(group) for column, group in values.items()}
        for column, value in means.items():
            require(abs(value-summary["summary"][column]["mean"]) < 1e-12, "Policy summary mismatch")
        result = {"groups": len(grouped), "policy_runs": len(grouped)*len(arms),
                  "training_lines": len(train), "evaluation_lines": len(evaluation), "means": means}
        if "prior_control" in arms:
            result["true_arm_confirmed_set_differences_from_static"] = {
                arm: sum(confirmed[key, arm] != confirmed[key, "prior_control"] for key in grouped)
                for arm in ("hotspot", "dependency", "target_dependency", "rna_binary")}
            check = {"campaigns": len(grouped), "verification_order_relevant_campaigns": len(headroom),
                     "fixed_screen_oracle_total_confirmations_gain": oracle_gain,
                     "mean_first_round_hits": fmean(first_round_hits),
                     "mean_verification_capacity": fmean(verification_capacities),
                     "saturated_cases": headroom}
            recorded = load(Path(__file__).parent / "decision_headroom.json")
            for key, value in check.items():
                require(value == recorded[key], "Fixed-screen headroom mismatch: " + key)
            result["fixed_screen_headroom"] = check
        policies[folder] = result
    return {"scope": "Imported bytes, database links and saved-score accounting; no refit, unseen labels, physical costs or biological certification",
            "archive_sha256": digest(ARCHIVE), "archive_files_exact": exact,
            "manifest_files_exact": len(manifest["files"]), "freezes": freezes,
            "large_source_inputs": large_sources, "databases": databases,
            "point_estimates": estimates, "policies": policies}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.output and args.output.exists():
        raise FileExistsError("Refusing to overwrite existing receipt")
    result = json.dumps(verify(), indent=2, allow_nan=False) + "\n"
    if args.output:
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(result)
    else:
        print(result, end="")


if __name__ == "__main__":
    main()
