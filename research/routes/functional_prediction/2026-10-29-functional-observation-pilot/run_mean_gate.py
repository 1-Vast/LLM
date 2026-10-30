"""Frozen H_MEAN.v1.1: control-only raw-mean holdout check."""
import time

started = time.monotonic()

from collections import Counter
import csv
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import psutil
import scipy
from scipy.optimize import least_squares

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / "2026-10-29-functional-joint-discovery/sources/root/hts001_raw.body"
CELLS = ["BR1", "DS3", "DS7", "DS8", "DS9", "MGH", "PC9"]
ROLES = [list("BDFHJLN"), list("CEGIKMO")]
accessed = 0


def guard():
    assert time.monotonic() - started <= 180, "wall resource limit"
    assert time.process_time() <= 120, "CPU resource limit"
    assert psutil.Process().memory_info().peak_wset <= 512 * 1024**2, "memory limit"


def fit_models(train_mean, x0, x1):
    scale = float(np.sqrt(np.mean(train_mean**2)))
    assert np.isfinite(scale) and scale > 0, "invalid training scale"
    target = train_mean / scale
    fits = []
    for basis in [x0, x1]:
        initial = (np.array([np.log(np.mean(target)), 0.0]) if not fits
                   else np.r_[fits[0].x, 0.0])
        fit = least_squares(lambda theta: np.exp(basis @ theta) - target, initial,
                            jac=lambda theta: np.exp(basis @ theta)[:, None] * basis,
                            method="trf", ftol=1e-10, xtol=1e-10, gtol=1e-10,
                            max_nfev=200)
        assert fit.success and np.isfinite(fit.x).all(), "optimizer failed"
        assert np.isfinite(np.exp(basis @ fit.x)).all(), "nonfinite fitted mean"
        fits.append(fit)
    sse = [float(np.sum(f.fun**2)) for f in fits]
    assert np.isfinite(sse).all(), "nonfinite training SSE"
    assert sse[1] <= sse[0] + 1e-10 * (1 + sse[0]), "nestedness violation"
    predictions = [scale * np.exp(x @ fit.x) for x, fit in zip([x0, x1], fits)]
    assert all(np.isfinite(pred).all() for pred in predictions), "nonfinite raw prediction"
    raw_parameters = [np.r_[fit.x[0] + np.log(scale), fit.x[1:]].tolist() for fit in fits]
    assert all(np.isfinite(p).all() for p in raw_parameters), "nonfinite raw parameter"
    optimizer = [{"status": int(f.status), "message": str(f.message),
                  "success": bool(f.success), "nfev": int(f.nfev)} for f in fits]
    return scale, predictions, raw_parameters, sse, optimizer


def score(train_mean, valid_mean, x0, x1):
    scale, predictions, parameters, sse, optimizer = fit_models(train_mean, x0, x1)
    losses = [float(np.mean(((valid_mean - pred) / scale)**2)) for pred in predictions]
    raw_sse = [float(value * scale**2) for value in sse]
    raw_losses = [float(value * scale**2) for value in losses]
    delta = float(losses[0] - losses[1])
    assert np.isfinite(losses + raw_losses + raw_sse + [delta]).all(), "nonfinite loss or D"
    return delta, {"train_scale": scale, "parameters": parameters,
                   "train_normalized_SSE": sse, "train_raw_SSE": raw_sse,
                   "validation_normalized_MSE": losses, "validation_raw_MSE": raw_losses,
                   "predictions": [p.tolist() for p in predictions], "optimizer": optimizer}


receipt_path = ROOT / "execution_receipt.json"
if receipt_path.exists():
    raise SystemExit("Execution receipt exists; no automatic replay")
protocol_receipt = json.loads((ROOT / "protocol_receipt_v1_1.json").read_text(encoding="utf-8"))
for name, expected in protocol_receipt["files"].items():
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
draws = np.load(ROOT / "bootstrap_draws.npy", allow_pickle=False)
assert draws.shape == (500, 7, 2, 7) and draws.dtype == np.dtype("int64")
assert draws.min() >= 0 and draws.max() < 7
raw = SOURCE.read_bytes()
assert len(raw) == 3039472
assert hashlib.sha256(raw).hexdigest() == "e6ff575664705d6021d98e1dad41751c87d86a425a3794f7e2a7e3b12468d617"
del raw
receipt = {"state": "started_before_count_parsing", "protocol": "H_MEAN.v1.1",
           "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           "python": sys.executable, "source_sha256": "e6ff575664705d6021d98e1dad41751c87d86a425a3794f7e2a7e3b12468d617",
           "optimizer": {"identity": "scipy.optimize.least_squares", "method": "trf",
                         "scipy_version": scipy.__version__, "numpy_version": np.__version__},
           "outer_timeout_seconds": 180}
receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")

try:
    meta = json.loads((ROOT / "metadata_qualification.json").read_text(encoding="utf-8"))
    values = {}
    with SOURCE.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream)
        header = next(reader)
        index = {name: header.index(name) for name in ["drug1", "drug1.conc", "drug1.units", "time",
                                                      "cell.line", "upid", "well", "cell.count"]}
        for row in reader:
            if row[index["drug1"]] != "control":
                continue
            if Decimal(row[index["time"]]) >= 72:
                continue
            assert Decimal(row[index["drug1.conc"]]) == 0 and row[index["drug1.units"]] == "M"
            cell, plate, well = [row[index[k]] for k in ["cell.line", "upid", "well"]]
            assert cell in CELLS and plate in meta["cells"][cell]["plates"]
            assert well in meta["cells"][cell]["wells"]
            assert row[index["time"]] in meta["cells"][cell]["time_grids"][0], "unexpected time coordinate"
            key = (cell, well, row[index["time"]])
            assert key not in values, "duplicate eligible coordinate"
            accessed += 1
            value = float(row[index["cell.count"]])
            assert np.isfinite(value) and value >= 0, "invalid control count"
            values[key] = value
    guard()
    plates, point = [], {}
    for cell in CELLS:
        guard()
        times = [t for t in meta["cells"][cell]["time_grids"][0] if Decimal(t) < 72]
        time_array = np.array([float(t) for t in times])
        u = (time_array - time_array[0]) / (time_array[-1] - time_array[0])
        x0, x1 = np.column_stack([np.ones(len(u)), u]), np.column_stack([np.ones(len(u)), u, u*u])
        arrays = [np.array([[[values[(cell, r + c, t)] for t in times] for c in ["02", "23"]]
                            for r in rows]) for rows in ROLES]
        means = [a.mean(axis=(0, 1)) for a in arrays]
        delta, detail = score(*means, x0, x1)
        point[cell] = {"D": delta, "times_hours": time_array.tolist(), "train_mean": means[0].tolist(),
                       "validation_mean": means[1].tolist(), **detail}
        plates.append((arrays, x0, x1))
    expected_accesses = 28 * sum(len(point[c]["times_hours"]) for c in CELLS)
    assert accessed == len(values) == expected_accesses
    bootstrap = np.empty((500, 7))
    terminations = [Counter(), Counter()]
    max_nfev = [0, 0]
    for b, draw in enumerate(draws):
        for c, (arrays, x0, x1) in enumerate(plates):
            means = [arrays[role][draw[c, role]].mean(axis=(0, 1)) for role in [0, 1]]
            bootstrap[b, c], detail = score(*means, x0, x1)
            for model, fit in enumerate(detail["optimizer"]):
                terminations[model][(fit["status"], fit["message"])] += 1
                max_nfev[model] = max(max_nfev[model], fit["nfev"])
        guard()
    delta = float(np.mean([point[c]["D"] for c in CELLS]))
    bootstrap_delta = bootstrap.mean(axis=1)
    q05, q95 = np.quantile(bootstrap_delta, [0.05, 0.95], method="linear")
    assert np.isfinite(bootstrap).all() and np.isfinite([delta, q05, q95]).all()
    guard()
    status = ("CONDITIONAL_HELDOUT_CURVATURE_GAIN" if delta > 0 and q05 > 0 else
              "EXPONENTIAL_PREFERRED_IN_THIS_COMPARISON" if delta < 0 and q95 < 0 else "INCONCLUSIVE")
    result = {"protocol": "H_MEAN.v1.1", "status": status, "point": point, "Delta": delta,
              "bootstrap_D_by_plate": bootstrap.tolist(), "bootstrap_Delta": bootstrap_delta.tolist(),
              "stability_q05_q95": [float(q05), float(q95)],
              "bootstrap_positive_fraction": float(np.mean(bootstrap_delta > 0)),
              "count_values_accessed": accessed, "drug_count_values_accessed": 0,
              "bootstrap_optimizer": [{"model": model, "max_nfev": max_nfev[model],
                                       "terminations": [{"status": k[0], "message": k[1], "fits": n}
                                                        for k, n in counts.items()]}
                                      for model, counts in enumerate(terminations)],
              "optimizer": receipt["optimizer"],
              "resource": {"cpu_seconds": time.process_time(),
                           "wall_seconds": time.monotonic() - started,
                           "peak_working_set_bytes": psutil.Process().memory_info().peak_wset,
                           "enforcement": "cooperative checks; outer 180s wall timeout; no OS CPU/memory hard limits",
                           "accounting": "CPU includes imports; internal wall begins before non-time imports; outer wall covers launch through output"},
              "protocol_receipt_sha256": hashlib.sha256((ROOT / "protocol_receipt_v1_1.json").read_bytes()).hexdigest(),
              "draws_sha256": hashlib.sha256((ROOT / "bootstrap_draws.npy").read_bytes()).hexdigest(),
              "inference_scope": "conditional fixed-plate row-block stability; not biological CI or rate validation"}
    guard()
    (ROOT / "primary_result.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    guard()
    receipt.update(state="complete", status=status, count_values_accessed=accessed,
                   seconds=time.monotonic() - started)
    print(json.dumps({k: result[k] for k in ["status", "Delta", "stability_q05_q95", "bootstrap_positive_fraction", "resource"]}))
except Exception as error:
    receipt.update(state="inconclusive_exception", count_values_accessed=accessed,
                   exception_type=type(error).__name__, detail=str(error), seconds=time.monotonic() - started,
                   resource={"cpu_seconds": time.process_time(),
                             "peak_working_set_bytes": psutil.Process().memory_info().peak_wset})
    raise
finally:
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
