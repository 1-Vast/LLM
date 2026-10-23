"""Prepare the frozen paid-reference oracle; schema and synthetic use are target blind."""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import io
import json
import math
from pathlib import Path
import zipfile

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / "log/20261022/az_paid_reference_gate"
OLD = ROOT / "log/20261022/intervention_program_renewal/az_design"
ARCHIVE = OLD / "matrix_well_stats_GDSC_007_010_plus_Spiper1.zip"
ARCHIVE_SHA = "e8cb50f6ce860fa17586a555130cb3b019f6011ed1976c0f0d3e00fb072d3259"
MEMBER = "combo_well_stats_GDSC_007_05May22.csv"
META = "PROJECT_ID PROJECT_NAME BARCODE DRUGSET_ID CELL_LINE_NAME MASTER_CELL_ID COSMIC_ID CELL_ID TISSUE CANCER_TYPE POSITION lib1 lib1_dose lib1_drug_id lib1_conc lib2 lib2_dose lib2_drug_id lib2_conc treatment cmatrix".split()
PAID = ("lib1_y", "lib2_y", "inhibition")
FULL_ROW = ["dose_A_uM", "dose_B_uM", "mono_A", "mono_B", "combination", "present", "mono_A_observed", "mono_B_observed", "combination_observed"]
NO_MONO_ROW = ["dose_A_uM", "dose_B_uM", "combination", "present", "combination_observed"]


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False), encoding="utf-8")


def key(r):
    return tuple(r[f] for f in ("member", "PROJECT_ID", "BARCODE", "cmatrix"))


def pair(m):
    return tuple(sorted((m["lib1_drug_id"], m["lib2_drug_id"])))


def metadata_bundle(log):
    design = json.loads((log / "DESIGN.json").read_text(encoding="utf-8"))
    assert sha(log / "EPISODES.json") == design["episode_file_sha256"]
    assert sha(log / "SELECTED_DESIGN.json") == design["selected_design_sha256"]
    assert design["member"] == MEMBER
    assert not set(map(tuple, design["query_pairs"])) & set(map(tuple, design["target_pairs"]))
    episodes = json.loads((log / "EPISODES.json").read_text(encoding="utf-8"))
    selected = json.loads((log / "SELECTED_DESIGN.json").read_text(encoding="utf-8"))
    return design, episodes, {key(r): r for r in selected}


def schema_from_metadata(design, records, projection_sha):
    ranges = defaultdict(list)
    cancers = set()
    for r in records:
        if r["member"] != MEMBER:
            continue
        m = r["metadata"][0]
        cancers.add(m["CANCER_TYPE"])
        for a in (1, 2):
            drug = m[f"lib{a}_drug_id"]
            for d in r["dose_pairs"]:
                x = Decimal(d[f"lib{a}_conc"])
                if not x.is_finite() or x <= 0:
                    raise ValueError("Nonpositive/nonfinite metadata concentration")
                ranges[drug].append(math.log10(float(x)))
    target_pairs = sorted(map(tuple, design["target_pairs"]))
    query_pairs = sorted(map(tuple, design["query_pairs"]))
    base = [f"target_pair:{'|'.join(p)}" for p in target_pairs] + [f"cancer_type:{c}" for c in sorted(cancers)]
    full_names = base + ["target_dose_A_uM", "target_dose_B_uM", "paid_u", "paid_v"]
    no_names = base + ["target_dose_A_uM", "target_dose_B_uM"]
    for witness in (0, 1):
        qnames = [f"w{witness}:pair:{'|'.join(p)}" for p in query_pairs]
        full_names += qnames + [f"w{witness}:r{i}:{f}" for i in range(49) for f in FULL_ROW]
        no_names += qnames + [f"w{witness}:r{i}:{f}" for i in range(49) for f in NO_MONO_ROW]
    return {"version": 1, "metadata_projection_sha256": projection_sha,
            "target_pairs": target_pairs, "query_pairs": query_pairs, "cancer_types": sorted(cancers),
            "drug_log10_uM_ranges": {d: [min(v), max(v)] for d, v in sorted(ranges.items())},
            "max_paid_rows": 49, "full_paid_row": FULL_ROW, "without_mono_paid_row": NO_MONO_ROW,
            "full_columns": full_names, "without_mono_columns": no_names,
            "dimensions": {"full": len(full_names), "without_mono": len(no_names), "effect": 2, "dose": 2, "raw_dose": 2},
            "feature_dtype": "float32", "effect_dose_y_dtype": "float64",
            "response_units": "released inhibitory fraction; identity conversion for inhibition/lib1_y/lib2_y; finite values outside [0,1] retained",
            "row_order": "active EPISODES order, then Decimal canonical dose A/B, then integer POSITION",
            "normalization": "per source drug (log10(uM)-metadata_min)/(metadata_max-metadata_min); constant range maps to 0",
            "missing_feature_encoding": "zero plus per-output observed masks; padding has present=0; target y is never zero-filled",
            "missing_effect": "NaN in effect; zero feature placeholder in full; common valid_mask=False",
            "arrays": ["full", "without_mono", "effect", "dose", "raw_dose", "y", "episode", "pair", "role", "valid_mask"]}


def make_schema(log):
    design, _, _ = metadata_bundle(log)
    projection = OLD / "DESIGN_MATRICES.jsonl"
    assert sha(projection) == design["source_projection_sha256"]
    def records():
        with projection.open(encoding="utf-8") as stream:
            for line in stream:
                yield json.loads(line)
    schema = schema_from_metadata(design, records(), design["source_projection_sha256"])
    path = log / "FEATURE_SCHEMA.json"
    if path.exists():
        raise RuntimeError("Existing schema cannot be overwritten")
    write(path, schema)
    print(json.dumps({"schema": str(path), "dimensions": schema["dimensions"], "target_numeric_use": False}))


def routes_for(episodes, targets_only=False):
    routes = {}
    for e in episodes:
        if e["role"] == "reserve" or (targets_only and e["role"] != "test"):
            continue
        target = tuple(e["target"])
        value = ("test_target" if targets_only else "target", e["role"])
        if target in routes and routes[target] != value:
            raise ValueError("Contradictory target roles")
        routes[target] = value
        if not targets_only:
            for w in e["witnesses"]:
                w = tuple(w)
                value = ("paid", e["role"])
                if w in routes and routes[w] != value:
                    raise ValueError("Paid/target or cross-role overlap")
                routes[w] = value
    return routes


def number(token, ledger, scope, field):
    counts = ledger.setdefault(scope, {}).setdefault(field, {"attempted": 0, "finite": 0, "missing_or_nonfinite": 0, "finite_outside_0_1": 0})
    counts["attempted"] += 1
    try:
        value = float(token)
    except (TypeError, ValueError):
        value = float("nan")
    if math.isfinite(value):
        counts["finite"] += 1
        counts["finite_outside_0_1"] += not 0 <= value <= 1
        return value
    counts["missing_or_nonfinite"] += 1
    return None


def scan_csv(stream, routes, selected):
    """Only routed allowed response columns are indexed or converted."""
    reader = csv.reader(stream)
    header = next(reader)
    idx = {f: header.index(f) for f in META + list(PAID)}
    found = defaultdict(list)
    ledger = {}
    for raw in reader:
        if len(raw) != len(header):
            raise ValueError("Source row width mismatch; no token disclosed")
        k = (MEMBER, raw[idx["PROJECT_ID"]], raw[idx["BARCODE"]], raw[idx["cmatrix"]])
        if k not in routes:
            continue
        category, role = routes[k]
        row = {f: raw[idx[f]] for f in META}
        expected = selected[k]["metadata"][0]
        if any(row[f] != expected[f] for f in expected):
            raise ValueError("Selected matrix metadata mismatch")
        fields = PAID if category == "paid" else (("inhibition",) if role != "test" or category == "test_target" else ())
        row["observed"] = {f: number(raw[idx[f]], ledger, f"{category}:{role}", f) for f in fields}
        found[k].append(row)
    for k in routes:
        rows = found[k]
        expected = selected[k]
        if len(rows) != expected["rows"]:
            raise ValueError("Selected matrix row count mismatch")
        if Counter(r["POSITION"] for r in rows) != Counter(expected["positions"]):
            raise ValueError("Selected matrix positions mismatch")
        actual_doses = Counter(tuple(r[f] for f in ("lib1_dose", "lib1_conc", "lib2_dose", "lib2_conc")) for r in rows)
        expected_doses = Counter({tuple(d[f] for f in ("lib1_dose", "lib1_conc", "lib2_dose", "lib2_conc")): d["count"] for d in expected["dose_pairs"]})
        if actual_doses != expected_doses:
            raise ValueError("Selected matrix dose support mismatch")
    return dict(found), ledger


def canonical(r):
    axes = sorted((r[f"lib{a}_drug_id"], Decimal(r[f"lib{a}_conc"]), r["observed"].get(f"lib{a}_y")) for a in (1, 2))
    return axes


def ordered(rows):
    return sorted(rows, key=lambda r: (canonical(r)[0][1], canonical(r)[1][1], int(r["POSITION"])))


def paid_summary(rows, schema):
    sums = defaultdict(list)
    required = set()
    for r in rows:
        for drug, conc, value in canonical(r):
            required.add((drug, conc))
            if value is not None:
                sums[(drug, conc)].append(value)
    mono = {k: math.fsum(v) / len(v) for k, v in sums.items()}
    full = np.zeros((schema["max_paid_rows"], 9), dtype=np.float32)
    without = np.zeros((schema["max_paid_rows"], 5), dtype=np.float32)
    residuals = []
    audit = []
    for i, r in enumerate(ordered(rows)):
        if i >= schema["max_paid_rows"]:
            raise ValueError("Paid matrix exceeds frozen padding")
        a, b = canonical(r)
        y = r["observed"]["inhibition"]
        full[i] = [float(a[1]), float(b[1]), a[2] if a[2] is not None else 0,
                   b[2] if b[2] is not None else 0, y if y is not None else 0,
                   1, a[2] is not None, b[2] is not None, y is not None]
        without[i] = full[i, [0, 1, 4, 5, 8]]
        u, v = mono.get(a[:2]), mono.get(b[:2])
        if y is not None and u is not None and v is not None:
            residuals.append(y - (u + v - u * v))
        audit.append({"position": r["POSITION"], "drug_ids": [a[0], b[0]],
                      "concentrations_uM": [str(a[1]), str(b[1])], "mono": [a[2], b[2]], "inhibition": y})
    return {"mono": mono, "full": full.ravel(), "without_mono": without.ravel(),
            "mean_residual": math.fsum(residuals) / len(residuals) if residuals else None,
            "all_mono_doses_finite": required <= mono.keys(),
            "all_combo_finite": all(r["observed"]["inhibition"] is not None for r in rows), "raw": audit}


def normalized_dose(drug, dose, schema):
    lo, hi = schema["drug_log10_uM_ranges"][drug]
    return (math.log10(float(dose)) - lo) / (hi - lo) if hi != lo else 0.0


def assemble(episodes, found, schema):
    active = [e for e in episodes if e["role"] != "reserve"]
    n = sum(len(found[tuple(e["target"])]) for e in active)
    data = {"full": np.zeros((n, schema["dimensions"]["full"]), np.float32),
            "without_mono": np.zeros((n, schema["dimensions"]["without_mono"]), np.float32),
            "effect": np.full((n, 2), np.nan), "dose": np.zeros((n, 2)), "raw_dose": np.zeros((n, 2)), "y": np.full(n, np.nan),
            "episode": np.empty(n, np.int32), "pair": np.empty(n, np.int16), "role": np.empty(n, dtype="U10"),
            "valid_mask": np.zeros(n, bool)}
    targets = list(map(tuple, schema["target_pairs"]))
    queries = list(map(tuple, schema["query_pairs"]))
    paid_keys = {tuple(w) for e in active for w in e["witnesses"]}
    paid = {k: paid_summary(found[k], schema) for k in sorted(paid_keys)}
    summaries, observations = [], []
    paid_roles = {tuple(w): e["role"] for e in active for w in e["witnesses"]}
    for k, s in paid.items():
        p = list(pair(found[k][0]))
        summaries.append({"key": list(k), "role": paid_roles[k], "pair": p, "mean_residual": s["mean_residual"], "rows": len(found[k])})
        observations.append({"key": list(k), "role": paid_roles[k], "pair": p, "rows": s["raw"]})
    rows_out, meta_out = [], []
    cursor = 0
    for eid, e in enumerate(active):
        p = tuple(e["pair"])
        pi = targets.index(p)
        ws = [tuple(w) for w in e["witnesses"]]
        if ws[0] == ws[1] or any(pair(found[w][0]) == p for w in ws):
            raise ValueError("Invalid paid witness identity")
        target_rows = ordered(found[tuple(e["target"])])
        effects = []
        for r in target_rows:
            a, b = canonical(r)
            effects.append([paid[ws[0]]["mono"].get(a[:2]), paid[ws[1]]["mono"].get(b[:2])])
        reasons = []
        if (any(value is None for uv in effects for value in uv)
                or not all(paid[w]["all_mono_doses_finite"] for w in ws)):
            reasons.append("missing_required_mono")
        if not all(paid[w]["all_combo_finite"] for w in ws):
            reasons.append("nonfinite_paid_combination")
        valid = not reasons
        base = np.zeros(len(targets) + len(schema["cancer_types"]), np.float32)
        base[pi] = 1
        base[len(targets) + schema["cancer_types"].index(e["cancer_type"])] = 1
        paid_full, paid_without = [], []
        q_pairs = []
        for w in ws:
            qp = pair(found[w][0])
            q_pairs.append(list(qp))
            one_hot = np.zeros(len(queries), np.float32)
            one_hot[queries.index(qp)] = 1
            paid_full.extend((one_hot, paid[w]["full"]))
            paid_without.extend((one_hot, paid[w]["without_mono"]))
        paid_full = np.concatenate(paid_full)
        paid_without = np.concatenate(paid_without)
        for r, uv in zip(target_rows, effects):
            a, b = canonical(r)
            doses = [float(a[1]), float(b[1])]
            safe_uv = [v if v is not None else 0.0 for v in uv]
            data["full"][cursor] = np.concatenate((base, doses, safe_uv, paid_full))
            data["without_mono"][cursor] = np.concatenate((base, doses, paid_without))
            data["effect"][cursor] = [v if v is not None else np.nan for v in uv]
            data["dose"][cursor] = [normalized_dose(a[0], a[1], schema), normalized_dose(b[0], b[1], schema)]
            data["raw_dose"][cursor] = doses
            if e["role"] != "test":
                value = r["observed"]["inhibition"]
                data["y"][cursor] = value if value is not None else np.nan
            data["episode"][cursor], data["pair"][cursor] = eid, pi
            data["role"][cursor], data["valid_mask"][cursor] = e["role"], valid
            rows_out.append({"episode_id": eid, "targetkey": list(e["target"]), "position": r["POSITION"], "role": e["role"]})
            cursor += 1
        meta_out.append({"episode_id": eid, "cell": e["cell"], "role": e["role"], "pair": list(p),
                         "query_pairs": q_pairs, "query_keys": [list(w) for w in ws],
                         "query_residual_means": [paid[w]["mean_residual"] for w in ws],
                         "query_residual_valid": [paid[w]["mean_residual"] is not None for w in ws],
                         "valid": valid, "abstain_reason": ";".join(reasons),
                         "logical_bundles": 2, "logical_paid_rows": sum(len(found[w]) for w in ws)})
    return data, rows_out, meta_out, summaries, observations


def verify_predictions(log):
    seal = json.loads((log / "PREDICTIONS_SEAL.json").read_text(encoding="utf-8"))
    verified = {}
    for name, field in (("TEST_PREDICTIONS.npz", "predictions_sha256"),
                        ("TEST_ACTIONS.json", "actions_sha256"),
                        ("SELECTION.json", "selection_sha256")):
        actual = sha(log / name)
        if actual != seal[field]:
            raise ValueError("Predictions/actions/selection seal mismatch")
        verified[field] = actual
    return verified


def extract_test_targets(rows_map, found):
    lookup = {}
    for k, rows in found.items():
        for r in rows:
            lookup[(k, r["POSITION"])] = r["observed"]["inhibition"]
    y = np.full(len(rows_map), np.nan)
    for i, row in enumerate(rows_map):
        if row["role"] == "test":
            value = lookup[(tuple(row["targetkey"]), row["position"])]
            y[i] = value if value is not None else np.nan
    return y


def run(log, stage):
    started = log / ("INPUTS_STARTED.json" if stage == "inputs" else "TEST_TARGETS_STARTED.json")
    outputs = ["DATA.npz", "ROWS.json", "EPISODE_META.json", "PAID_SUMMARIES.json", "PAID_OBSERVATIONS.json", "INPUTS_RECEIPT.json", "ACCESS_INPUTS.json"] if stage == "inputs" else ["TEST_TARGETS.npz", "TEST_TARGETS_RECEIPT.json", "ACCESS_TEST_TARGETS.json"]
    if started.exists() or any((log / name).exists() for name in outputs):
        raise RuntimeError("Existing stage output/STARTED marker; no overwrite")
    protocol = log / "MEASURED_PROTOCOL.md"
    design, episodes, selected = metadata_bundle(log)
    binding = {"utc": datetime.now(timezone.utc).isoformat(), "stage": stage, "code_sha256": sha(Path(__file__)),
               "protocol_sha256": sha(protocol), "design_sha256": sha(log / "DESIGN.json"),
               "schema_sha256": sha(log / "FEATURE_SCHEMA.json"), "archive_expected_sha256": ARCHIVE_SHA}
    if stage == "test-targets":
        binding.update(verify_predictions(log))
        prior = json.loads((log / "INPUTS_RECEIPT.json").read_text(encoding="utf-8"))
        for name in ("DATA.npz", "ROWS.json", "EPISODE_META.json"):
            if sha(log / name) != prior["outputs_sha256"][name]:
                raise ValueError("Input-to-target mapping binding mismatch")
        for field in ("code_sha256", "protocol_sha256", "design_sha256", "schema_sha256"):
            if binding[field] != prior[field]:
                raise ValueError("Frozen stage binding changed")
    write(started, binding)
    try:
        if sha(ARCHIVE) != ARCHIVE_SHA:
            raise ValueError("Pinned source archive hash mismatch")
        routes = routes_for(episodes, targets_only=stage == "test-targets")
        with zipfile.ZipFile(ARCHIVE) as source, source.open(MEMBER) as raw, io.TextIOWrapper(raw, encoding="utf-8-sig", newline="") as stream:
            found, ledger = scan_csv(stream, routes, selected)
        access = {"stage": stage, "response_member": MEMBER, "allowed_metadata_fields": META,
                  "allowed_response_fields": {"paid": list(PAID), "target_train_validation": ["inhibition"], "target_test": []} if stage == "inputs" else {"selected_test_target": ["inhibition"]},
                  "conversion_counts": ledger, "target_attached_mono_or_fitted_fields_indexed": False,
                  "reserve_numeric_conversion": False, "source_response_bytes_contacted": True}
        if stage == "inputs":
            schema = json.loads((log / "FEATURE_SCHEMA.json").read_text(encoding="utf-8"))
            if schema["metadata_projection_sha256"] != design["source_projection_sha256"]:
                raise ValueError("Feature-schema metadata binding mismatch")
            data, rows, meta, summaries, observations = assemble(episodes, found, schema)
            np.savez_compressed(log / "DATA.npz", **data)
            for name, value in (("ROWS.json", rows), ("EPISODE_META.json", meta), ("PAID_SUMMARIES.json", summaries), ("PAID_OBSERVATIONS.json", observations), ("ACCESS_INPUTS.json", access)):
                write(log / name, value)
            binding["array_shapes"] = {k: list(v.shape) for k, v in data.items()}
            binding["coverage"] = {role: {"episodes": sum(e["role"] == role for e in meta), "valid_episodes": sum(e["role"] == role and e["valid"] for e in meta)} for role in ("train", "validation", "test")}
        else:
            rows = json.loads((log / "ROWS.json").read_text(encoding="utf-8"))
            y = extract_test_targets(rows, found)
            with np.load(log / "DATA.npz", allow_pickle=False) as data:
                if y.shape != data["y"].shape:
                    raise ValueError("Test target shape mismatch")
            np.savez_compressed(log / "TEST_TARGETS.npz", y=y)
            write(log / "ACCESS_TEST_TARGETS.json", access)
        binding["outputs_sha256"] = {name: sha(log / name) for name in outputs if name.endswith((".npz", ".json")) and "RECEIPT" not in name}
        write(log / ("INPUTS_RECEIPT.json" if stage == "inputs" else "TEST_TARGETS_RECEIPT.json"), binding)
        print(json.dumps({"stage": stage, "status": "complete", "output_names": outputs}))
    except Exception as error:
        write(log / f"{stage.upper()}_FAILURE.json", {"stage": stage, "exception_type": type(error).__name__, "response_values_disclosed": False})
        raise SystemExit("Preparation failed; retained STARTED and sanitized failure receipt") from None


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("schema", "inputs", "test-targets"))
    parser.add_argument("--log-dir", type=Path, default=LOG)
    args = parser.parse_args()
    if args.stage == "schema":
        make_schema(args.log_dir)
    else:
        run(args.log_dir, args.stage)
