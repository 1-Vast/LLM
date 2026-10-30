"""One frozen, retrospective coordinate-prediction run; see PROTOCOL_v2.md."""
import os

for thread_option in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[thread_option] = "1"

import ctypes
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


EPISODE = Path(__file__).resolve().parent
SOURCES = EPISODE.parent / "2026-10-28-agent-a-matched-signal-function" / "sources"
METADATA = EPISODE.parent / "2026-10-28-agent-a-mechanism-branches" / "static_substitution_metadata.json"
GROUPS = [
    ("AK", "ZS", "AKTpS473", 7, 10, True),
    ("901", "PLX", "MAPKpT202", 3, 9, False),
    ("Tm", "RO", "S6pS240", 44, 10, True),
    ("P6", "SR", "GSK3abpS21", 14, 10, False),
]
RIDGE_GRID = [10.0 ** k for k in range(-4, 5)]
RBF_GRID = [(ell, reg) for ell in (0.3, 1.0, 3.0) for reg in (0.01, 0.1, 1.0)]
METHODS = ("scalar_ridge", "full_ridge", "full_rbf", "partner_mean", "source_copy")
ROLE_ACCESSES = []
TARGET_EVALUATIONS = []


class InvalidInput(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise InvalidInput(message)


def parse_numbers(values):
    try:
        numbers = np.asarray(values, dtype=float)
    except ValueError as error:
        raise InvalidInput("non-numeric required cell") from error
    require(np.isfinite(numbers).all(), "missing/nonfinite required cell")
    return numbers


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    path = EPISODE / name
    with path.open("x", encoding="utf-8", newline="\n") as out:
        json.dump(value, out, ensure_ascii=False, indent=2, allow_nan=False)
        out.write("\n")
    return sha(path)


def peak_working_set():
    class Counters(ctypes.Structure):
        _fields_ = [("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong)] + [
            (name, ctypes.c_size_t) for name in (
                "PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage",
                "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage",
                "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage")]
    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    current = ctypes.windll.kernel32.GetCurrentProcess
    current.restype = ctypes.c_void_p
    query = ctypes.windll.psapi.GetProcessMemoryInfo
    query.argtypes = [ctypes.c_void_p, ctypes.POINTER(Counters), ctypes.c_ulong]
    if not query(current(), ctypes.byref(counters), counters.cb):
        raise OSError("GetProcessMemoryInfo failed")
    return counters.PeakWorkingSetSize


def metadata_contract(exp, nodes):
    mapping = json.loads((EPISODE / "mapping.json").read_text(encoding="utf-8"))
    mapped = {row["source_index"]: row for row in mapping["condition_mapping"]}
    require(len(mapped) == 88 and 45 not in mapped, "S1C mapping changed")
    labels = {label: i + 1 for i, label in enumerate(exp)}
    for row in mapped.values():
        idx = row["source_index"]
        require(row["author_index_line_1based"] == idx and exp[idx - 1] == row["author_label"],
                "conditional positional mapping mismatch")
    frozen = json.loads(METADATA.read_text(encoding="utf-8"))["groups"]
    contracts = []
    for number, (group, definition) in enumerate(zip(frozen, GROUPS), 1):
        source, target, node, col, n, exact = definition
        require(nodes[col - 1][0] == node, "checkpoint column mismatch")
        records = []
        for context in group["contexts"]:
            require(len(context["left_conditions"]) == len(context["right_conditions"]) == 1,
                    "ambiguous source pair")
            ac = context["left_conditions"][0]["source_index"]
            bc = context["right_conditions"][0]["source_index"]
            left = {(t["code"], t["dose_token"]) for t in mapped[ac]["author_tokens"]}
            right = {(t["code"], t["dose_token"]) for t in mapped[bc]["author_tokens"]}
            common = left & right
            require(len(common) == 1 and len(left) == len(right) == 2, "partner token mismatch")
            partner = next(iter(common))
            require({t[0] for t in left - common} == {source}, "source direction mismatch")
            require({t[0] for t in right - common} == {target}, "target direction mismatch")
            mono = labels.get("|".join(partner))
            require(mono in mapped and len(mapped[mono]["author_tokens"]) == 1, "missing monotherapy")
            records.append({"partner": context["partner"], "C": mono, "AC": ac, "BC": bc,
                            "C_label": exp[mono - 1], "AC_label": exp[ac - 1], "BC_label": exp[bc - 1]})
        require(len(records) == n, "frozen partner count changed")
        sr, tr = {r["AC"] for r in records}, {r["BC"] for r in records}
        require(not sr & tr, "source-target overlap within task")
        contracts.append({"group": number, "source_code": source, "target_code": target,
                          "checkpoint": node, "checkpoint_column_1based": col,
                          "exact_name": exact, "records": records})
    require(len(frozen) == len(contracts) == 4, "group count changed")
    return contracts


def role_package(tokens, contract):
    records = contract["records"]
    protein_rows = sorted({r[role] for r in records for role in ("C", "AC", "BC")})
    source_y_rows = sorted({r[role] for r in records for role in ("C", "AC")})
    target_y_rows = {r["BC"] for r in records}
    require(not set(source_y_rows) & target_y_rows, "functional label role violation")
    audit = {"group": contract["group"], "protein_rows": protein_rows,
             "protein_columns_1based": list(range(1, 83)), "source_function_rows": source_y_rows,
             "withheld_function_rows_for_this_task": sorted(target_y_rows), "function_column_1based": 87}
    ROLE_ACCESSES.append(audit)
    # Only these conversions deliver numeric values to this task's fitter.
    proteins = {i: parse_numbers(tokens[i - 1][:82]) for i in protein_rows}
    source_y = {i: float(parse_numbers([tokens[i - 1][86]])[0]) for i in source_y_rows}
    xc = np.stack([proteins[r["C"]] for r in records])
    xac = np.stack([proteins[r["AC"]] for r in records])
    xbc = np.stack([proteins[r["BC"]] for r in records])
    yc = np.asarray([source_y[r["C"]] for r in records])
    yac = np.asarray([source_y[r["AC"]] for r in records])
    return xac - xc, yac - yc, xbc - xc, yc, yac, audit


def predict(x, d, target, method, parameter):
    mu = x.mean(axis=0)
    sd = x.std(axis=0, ddof=0)
    constant = sd == 0
    scale = np.where(constant, 1.0, sd)
    z, zt = (x - mu) / scale, (target - mu) / scale
    z[:, constant] = 0.0
    zt[:, constant] = 0.0
    centered = d - d.mean()
    if method in ("scalar_ridge", "full_ridge"):
        u, singular, vt = np.linalg.svd(z, full_matrices=False)
        beta = vt.T @ ((singular / (singular ** 2 + parameter)) * (u.T @ centered))
        answer = d.mean() + zt @ beta
    else:
        ell, regularizer = parameter
        def kernel(a, b):
            distance = ((a[:, None, :] - b[None, :, :]) ** 2).sum(axis=2)
            return np.exp(-distance / (2.0 * x.shape[1] * ell ** 2))
        weight = np.linalg.solve(kernel(z, z) + regularizer * np.eye(len(d)), centered)
        answer = d.mean() + kernel(zt, z) @ weight
    diagnostics = {"constant_columns_zero_based_in_model": np.flatnonzero(constant).tolist(),
                   "target_nonconstant_offsets_on_constant_columns":
                       int(np.count_nonzero(target[:, constant] != mu[constant]))}
    return answer, diagnostics


def fit_task(package, contract):
    x, d, target, yc, yac, audit = package
    predictions = {"partner_mean": (yc + d.mean()).tolist(), "source_copy": yac.tolist()}
    fits = {}
    count = 0
    for method in METHODS[:3]:
        feature = [contract["checkpoint_column_1based"] - 1] if method == "scalar_ridge" else list(range(82))
        xx, tt = x[:, feature], target[:, feature]
        grid = RBF_GRID if method == "full_rbf" else RIDGE_GRID
        scores = []
        for parameter in grid:
            errors = []
            for held_out in range(len(d)):
                keep = np.arange(len(d)) != held_out
                estimated, _ = predict(xx[keep], d[keep], xx[held_out:held_out + 1], method, parameter)
                errors.append(float((estimated[0] - d[held_out]) ** 2))
                count += 1
            scores.append(float(np.mean(errors)))
        selected = int(np.argmin(scores))
        estimated, diagnostic = predict(xx, d, tt, method, grid[selected])
        count += 1
        predictions[method] = (yc + estimated).tolist()
        fits[method] = {"grid_in_order": grid, "source_loo_mse": scores, "selected_index": selected,
                        "selected_parameter": grid[selected], "final_transform": diagnostic}
    return {**contract, "predictions": predictions, "fits": fits,
            "source_increment_constant": bool(np.ptp(d) == 0), "fit_count": count}, audit


def evaluate(tokens, tasks):
    outcomes = []
    for task in tasks:
        TARGET_EVALUATIONS.append({"group": task["group"], "rows": [r["BC"] for r in task["records"]]})
        actual = parse_numbers([tokens[r["BC"] - 1][86] for r in task["records"]])
        losses, detail = {}, []
        for method, values in task["predictions"].items():
            residual = np.asarray(values) - actual
            losses[method] = {"mse": float(np.mean(residual ** 2)), "mae": float(np.mean(abs(residual)))}
        s = losses["scalar_ridge"]["mse"]
        a = min(losses[m]["mse"] for m in ("partner_mean", "source_copy"))
        f = min(losses[m]["mse"] for m in ("full_ridge", "full_rbf"))
        status = ("scalar_strict_best" if all(s < losses[m]["mse"] for m in METHODS[1:]) else
                  "dominated_by_simple_and_full" if s >= a and s >= f else "mixed_or_tied")
        for i, record in enumerate(task["records"]):
            detail.append({**record, "actual_target_coordinate": float(actual[i]),
                           "predictions": {m: task["predictions"][m][i] for m in METHODS},
                           "residuals": {m: float(task["predictions"][m][i] - actual[i]) for m in METHODS}})
        outcomes.append({"group": task["group"], "n": len(actual), "exact_name": task["exact_name"],
                         "source_code": task["source_code"], "target_code": task["target_code"],
                         "losses": losses, "panel_status": status,
                         "source_increment_constant": task["source_increment_constant"],
                         "target_coordinate_constant": bool(np.ptp(actual) == 0), "details": detail})
    statuses = [g["panel_status"] for g in outcomes]
    degenerate = any(g["source_increment_constant"] or g["target_coordinate_constant"] for g in outcomes)
    disposition = ("retain_configuration_for_independent_test" if
                   all(s == "scalar_strict_best" for s in statuses) and not degenerate else
                   "stop_this_configuration_on_this_panel" if
                   all(s == "dominated_by_simple_and_full" for s in statuses) else "mixed_or_inconclusive")
    summaries = {}
    for name, subset in (("equal_group_macro", outcomes), ("exact_name_group_macro", [g for g in outcomes if g["exact_name"]])):
        summaries[name] = {m: {metric: float(np.mean([g["losses"][m][metric] for g in subset]))
                              for metric in ("mse", "mae")} for m in METHODS}
    return {"disposition": disposition, "groups": outcomes, **summaries,
            "biological_confidence_interval": None, "p_value": None,
            "independent_drug_decision_gain": None, "unseen_drug_or_cell_transfer": None,
            "scope": "Conditional on positional indexing and fixed historical preprocessing; task-local label isolation only."}


def main():
    started = time.perf_counter()
    require(not any((EPISODE / name).exists() for name in
                    ("predictions_role_isolated.json", "results.json", "run_error.json")), "run already exists")
    freeze = json.loads((EPISODE / "input_freeze.json").read_text(encoding="utf-8"))
    for item in freeze["files"]:
        require(sha(Path(item["path"])) == item["sha256"], "frozen input/script changed: " + item["path"])
    exp = [line.split()[0] for line in (SOURCES / "q1_pertbio_exp_index.txt").read_text().splitlines()]
    nodes = [line.split() for line in (SOURCES / "q1_pertbio_node_index.txt").read_text().splitlines()]
    require(len(exp) == len(set(exp)) == 89 and len(nodes) == len({n[0] for n in nodes}) == 99,
            "index shape/uniqueness failure")
    require([i for i, n in enumerate(nodes) if n[-1] == "1"] == list(range(82)) and
            nodes[86][0] == "cellviab" and nodes[86][-1] == "2", "node type/endpoint failure")
    contracts = metadata_contract(exp, nodes)
    # Keep all cells as strings; never turn the complete response matrix into numeric data.
    tokens = [line.split() for line in (SOURCES / "q1_pertbio_data.txt").read_text().splitlines()]
    require(len(tokens) == 89 and all(len(row) == 99 for row in tokens), "response matrix shape failure")
    tasks, audit = [], []
    for contract in contracts:
        task, accessed = fit_task(role_package(tokens, contract), contract)
        tasks.append(task)
        audit.append(accessed)
        require(time.perf_counter() - started <= 60, "formal run exceeded 60 seconds")
    prediction_sha = save("predictions_role_isolated.json", {
        "protocol_sha256": sha(EPISODE / "PROTOCOL_v2.md"), "script_sha256": sha(Path(__file__)),
        "isolation": "Per-task algorithm label isolation; global physical labels overlap.", "tasks": tasks})
    save("input_role_audit.json", {"tasks": audit, "all_numeric_role_rows_count":
         len({i for a in audit for i in a["protein_rows"]}),
         "cross_task_source_target_rows": sorted({i for a in audit for i in a["source_function_rows"]} &
                                                {i for a in audit for i in a["withheld_function_rows_for_this_task"]})})
    result = evaluate(tokens, tasks)
    result["predictions_sha256_saved_before_evaluation"] = prediction_sha
    result["runtime"] = {"wall_seconds": time.perf_counter() - started,
                         "peak_working_set_bytes": peak_working_set(), "python": sys.version,
                         "numpy": np.__version__, "total_small_fits": sum(t["fit_count"] for t in tasks),
                         "external_requests": 0, "completed_utc": datetime.now(timezone.utc).isoformat()}
    require(result["runtime"]["wall_seconds"] <= 60 and
            result["runtime"]["peak_working_set_bytes"] <= 512 * 1024 ** 2, "resource ceiling exceeded")
    save("results.json", result)
    print(json.dumps({"disposition": result["disposition"], "macro": result["equal_group_macro"],
                      "runtime": result["runtime"]}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        if not (EPISODE / "run_error.json").exists():
            save("run_error.json", {"status": "invalid_input" if isinstance(error, InvalidInput) else "invalid_implementation",
                                    "error_type": type(error).__name__, "message": str(error),
                                    "predictions_already_saved": (EPISODE / "predictions_role_isolated.json").exists(),
                                    "entered_role_accesses": ROLE_ACCESSES,
                                    "entered_target_evaluations": TARGET_EVALUATIONS})
        raise
