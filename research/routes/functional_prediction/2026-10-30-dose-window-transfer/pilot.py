"""Fixed two-anchor curve transfer; source-only tuning and background holdouts."""
import os

for option in ["OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"]:
    os.environ[option] = "4"

from itertools import combinations, product
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np
import pandas as pd
import scipy
from scipy.optimize import least_squares
from scipy.special import expit, softmax
import sklearn
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[3]
PARENT = ROOT.parent / "2026-10-30-virtual-cell-four-directions"
OUTPUT = PROJECT / "data/processed/virtual_cell_dose_transfer_20261030/c2_hts001"
ANCHORS = [1, 8]
QUERIES = list(range(2, 8))
METHODS = ["source_mean", "linear", "additive_shape", "candidate", "pooled_shape",
           "full_anchored_ridge", "joint_covariance", "smooth_gp", "hill_map",
           "profile_neighbor", "profile_tree", "wrong_shape"]
CONFIGS = {
    "source_mean": [None], "linear": [None], "additive_shape": [None],
    "candidate": [0, .01, .1, 1, 10], "pooled_shape": [0, .01, .1, 1, 10],
    "full_anchored_ridge": [.01, .1, 1, 10, 100],
    "joint_covariance": [.001, .01, .1, 1, 10],
    "smooth_gp": list(product([.5, 1, 2], [.001, .01, .1, 1])),
    "hill_map": [.01, .1, 1, 10], "profile_neighbor": [.1, 1, 10],
    "profile_tree": list(product([2, 3], [5, 10])),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_data():
    frame = pd.read_csv(PARENT / "census_c_wells.csv", float_precision="round_trip")
    frame = frame[frame.drug1 != "control"]
    cells, drugs = sorted(frame["cell.line"].unique()), sorted(frame.drug1.unique())
    y = np.empty((len(cells), len(drugs), 10, 2))
    doses = np.empty((len(drugs), 10))
    for ci, cell in enumerate(cells):
        for di, drug in enumerate(drugs):
            part = frame[(frame["cell.line"] == cell) & (frame.drug1 == drug)]
            grid = sorted(part["drug1.conc"].unique())
            assert len(grid) == 10
            if ci:
                assert np.array_equal(doses[di], grid)
            doses[di] = grid
            for xi, dose in enumerate(grid):
                group = part[part["drug1.conc"] == dose].sort_values("well")
                assert len(group) == 2 and group.upid.nunique() == 1
                y[ci, di, xi] = group.relative_growth.to_numpy()
    assert y.shape == (6, 14, 10, 2) and np.isfinite(y).all()
    return cells, drugs, doses, y


def choice_loss(prediction, truth, pair_roster):
    # Drug indices are in lexical order, giving deterministic decision ties.
    losses = []
    for first, second, points in pair_roster:
        values = []
        for ia, ib in points:
            chosen = truth[first, ia] if prediction[first, ia] <= prediction[second, ib] else truth[second, ib]
            values.append(chosen - min(truth[first, ia], truth[second, ib]))
        losses.append(np.mean(values))
    return float(np.mean(losses))


def hill(theta, x):
    return -np.exp(theta[0]) * expit(np.log(10) * np.exp(theta[1]) * (x - theta[2]))


class SourceFit:
    def __init__(self, indices, responses, x, u, roster, optimizer_log):
        self.indices = tuple(indices)
        self.y = responses[list(indices)]
        self.x, self.u, self.roster = x, u, roster
        self.z = self.y[:, :, ANCHORS].reshape(len(indices), -1)
        self.mean = self.y.mean(axis=0)
        self.a = self.y[:, :, ANCHORS[0]]
        self.d = self.y[:, :, ANCHORS[1]] - self.a
        self.r = self.y - self.a[:, :, None] - self.d[:, :, None] * u
        self.global_variance = max(.01, float(np.mean((self.y - self.mean) ** 2)))
        self.zmean = self.z.mean(axis=0)
        self.zcenter = self.z - self.zmean
        self.center = self.y - self.mean
        self.zscale = np.maximum(.1, self.z.std(axis=0))
        self.optimizer_log = optimizer_log
        self.tree_models = {}
        self.hill_prior = None

    def features(self, anchors, source_mean):
        features = []
        a = anchors[:, 0]
        d = anchors[:, 1] - a
        for di in range(14):
            for qi in QUERIES:
                features.append(np.r_[np.eye(14)[di], self.x[di, qi], self.u[di, qi],
                                      a[di], d[di], source_mean[di, qi], anchors.ravel()])
        return np.asarray(features)

    def q(self, penalty, pooled=False):
        numerator = np.sum(self.d[:, :, None] * self.r, axis=0)
        denominator = np.sum(self.d ** 2, axis=0)[:, None] + penalty * len(self.y) * .25 ** 2
        if pooled:
            numerator = numerator.sum(axis=0, keepdims=True)
            denominator = denominator.sum(axis=0, keepdims=True)
        q = np.divide(numerator, denominator, out=np.zeros_like(numerator), where=denominator >= 1e-12)
        return np.broadcast_to(q, (14, 10)).copy()

    def build_hill_prior(self):
        if self.hill_prior is not None:
            return
        fits = np.empty((len(self.y), 14, 3))
        for ci, source in enumerate(self.y):
            for di in range(14):
                lo = np.array([np.log(.001), np.log(.1), self.x[di].min()-2])
                hi = np.array([np.log(10), np.log(5), self.x[di].max()+2])
                initial = np.clip([np.log(max(.1, -source[di].min())), 0, np.median(self.x[di])], lo+1e-8, hi-1e-8)
                result = least_squares(lambda theta: hill(theta, self.x[di])-source[di], initial,
                                       bounds=(lo, hi), max_nfev=200)
                self.optimizer_log.append({"phase": "source", "fit_cells": self.indices,
                                           "source_index": self.indices[ci], "drug_index": di,
                                           "success": bool(result.success), "status": int(result.status),
                                           "nfev": result.nfev})
                fits[ci, di] = result.x if result.success else initial
        self.hill_prior = (fits.mean(axis=0), np.maximum(.25, fits.var(axis=0)))

    def predict(self, method, config, anchors, target_id):
        # Only the target's permitted two anchors enter this interface.
        a = anchors[:, 0]
        d = anchors[:, 1] - a
        linear = a[:, None] + d[:, None] * self.u
        if method == "source_mean":
            return self.mean.copy()
        if method == "linear":
            return linear
        if method == "additive_shape":
            return linear + self.r.mean(axis=0)
        if method in ["candidate", "pooled_shape", "wrong_shape"]:
            q = self.q(config, pooled=method == "pooled_shape")
            if method == "wrong_shape":
                q = np.roll(q, 1, axis=0)
            return linear + d[:, None] * q
        if method == "full_anchored_ridge":
            result = linear.copy()
            for di in range(14):
                features = np.column_stack([self.a[:, di], self.d[:, di]])
                center, scale = features.mean(axis=0), np.maximum(.1, features.std(axis=0))
                f = (features-center)/scale
                target = (np.array([a[di], d[di]])-center)/scale
                rmean = self.r[:, di].mean(axis=0)
                coef = np.linalg.solve(f.T@f + config*np.eye(2), f.T@(self.r[:, di]-rmean))
                result[di] += rmean + target@coef
            return result
        if method == "joint_covariance":
            regularizer = config*self.global_variance*(len(self.y)-1)
            dual = np.linalg.solve(self.zcenter@self.zcenter.T + regularizer*np.eye(len(self.y)),
                                   self.zcenter@(anchors.ravel()-self.zmean))
            return self.mean + np.einsum("c,cdx->dx", dual, self.center)
        if method == "smooth_gp":
            length, noise = config
            result = self.mean.copy()
            for di in range(14):
                kernel = np.exp(-.5*((self.x[di, :, None]-self.x[di, ANCHORS])/length)**2)
                amplitude = max(.01, float(self.y[:, di].var(axis=0).mean()))
                matrix = amplitude*kernel[ANCHORS] + amplitude*noise*np.eye(2)
                residual = anchors[di]-self.mean[di, ANCHORS]
                result[di] += amplitude*kernel@np.linalg.solve(matrix, residual)
            return result
        if method == "profile_neighbor":
            distances = np.mean(((self.z-anchors.ravel())/self.zscale)**2, axis=1)
            weights = softmax(-distances/config)
            return linear + np.einsum("c,cdx->dx", weights, self.r)
        if method == "profile_tree":
            if config not in self.tree_models:
                xx, yy = [], []
                for ci in range(len(self.y)):
                    source_mean = (self.y.sum(axis=0)-self.y[ci])/(len(self.y)-1)
                    xx.extend(self.features(self.y[ci][:, ANCHORS], source_mean))
                    yy.extend(self.y[ci][:, QUERIES].ravel())
                depth, minimum = config
                model = HistGradientBoostingRegressor(max_iter=50, learning_rate=.1, max_depth=depth,
                    min_samples_leaf=minimum, l2_regularization=1, random_state=1031, early_stopping=False)
                model.fit(np.asarray(xx), np.asarray(yy))
                self.tree_models[config] = model
            result = linear.copy()
            result[:, QUERIES] = self.tree_models[config].predict(self.features(anchors, self.mean)).reshape(14, 6)
            return result
        if method == "hill_map":
            self.build_hill_prior()
            mean, variance = self.hill_prior
            result = linear.copy()
            for di in range(14):
                lo = np.array([np.log(.001), np.log(.1), self.x[di].min()-2])
                hi = np.array([np.log(10), np.log(5), self.x[di].max()+2])
                initial = np.clip(mean[di], lo+1e-8, hi-1e-8)
                def residual(theta):
                    observed = (hill(theta, self.x[di, ANCHORS])-anchors[di])/np.sqrt(self.global_variance)
                    prior = np.sqrt(config)*(theta-mean[di])/np.sqrt(variance[di])
                    return np.r_[observed, prior]
                fit = least_squares(residual, initial, bounds=(lo, hi), max_nfev=200)
                self.optimizer_log.append({"phase": "target", "fit_cells": self.indices,
                    "target_id": target_id, "drug_index": di, "penalty": config,
                    "success": bool(fit.success), "status": int(fit.status), "nfev": fit.nfev})
                result[di] = hill(fit.x if fit.success else initial, self.x[di])
            return result
        raise ValueError(method)


def main():
    started, cpu_started = time.monotonic(), time.process_time()
    if OUTPUT.exists():
        raise SystemExit("Existing output directory: preserve execution, do not overwrite")
    OUTPUT.mkdir(parents=True)
    cells, drugs, doses, wells = load_data()
    y = wells.mean(axis=-1)
    x = np.log10(doses)
    u = (x-x[:, [ANCHORS[0]]])/(x[:, [ANCHORS[1]]]-x[:, [ANCHORS[0]]])
    assert np.allclose(u, u[0])
    roster = []
    for first, second in combinations(range(14), 2):
        lookup = {doses[second, qi]: qi for qi in QUERIES}
        points = [(qi, lookup[doses[first, qi]]) for qi in QUERIES if doses[first, qi] in lookup]
        if points:
            roster.append((first, second, points))
    receipt = {"status": "running", "python_executable": sys.executable,
        "source_endpoint_sha256": sha(PARENT/"census_c_wells.csv"),
        "raw_source_sha256": "e6ff575664705d6021d98e1dad41751c87d86a425a3794f7e2a7e3b12468d617",
        "script_sha256": sha(Path(__file__)), "protocol_sha256": sha(ROOT/"protocol.md"),
        "amendment_sha256": sha(ROOT/"protocol_v1_1.md"), "cells": cells, "drugs": drugs,
        "dose_M": doses.tolist(), "anchor_indices": ANCHORS, "query_indices": QUERIES,
        "methods": METHODS, "configurations": CONFIGS, "threads": 4,
        "versions": {"python": sys.version, "numpy": np.__version__, "pandas": pd.__version__,
                     "scipy": scipy.__version__, "sklearn": sklearn.__version__},
        "pair_roster": [{"first": drugs[a], "second": drugs[b], "indices": p} for a,b,p in roster],
        "memory_measurement": None, "completed_outer_cells": []}
    (OUTPUT/"run.json").write_text(json.dumps(receipt, indent=2)+"\n", encoding="utf-8")
    optimizer_log, selections, rows = [], [], []
    cache = {}
    def check_clock():
        if time.monotonic()-started > 900:
            raise TimeoutError("15-minute cooperative matrix wall limit")
    def get_fit(indices):
        key = tuple(indices)
        if key not in cache:
            cache[key] = SourceFit(key, y, x, u, roster, optimizer_log)
        return cache[key]
    failure = None
    try:
        for outer, cell in enumerate(cells):
            check_clock()
            source_indices = [ci for ci in range(6) if ci != outer]
            chosen = {}
            for method, configs in CONFIGS.items():
                losses = []
                for config in configs:
                    validation_losses = []
                    for vi in source_indices:
                        fit_indices = [ci for ci in source_indices if ci != vi]
                        prediction = get_fit(fit_indices).predict(method, config, y[vi][:, ANCHORS], cells[vi])
                        assert np.isfinite(prediction).all()
                        validation_losses.append(choice_loss(prediction, y[vi], roster))
                        check_clock()
                    losses.append(float(np.mean(validation_losses)))
                selected = int(np.argmin(losses))
                chosen[method] = configs[selected]
                selections.append({"outer_cell": cell, "method": method, "selected": configs[selected],
                                   "configurations": configs, "inner_losses": losses})
            chosen["wrong_shape"] = chosen["candidate"]
            final_fit = get_fit(source_indices)
            for method in METHODS:
                prediction = final_fit.predict(method, chosen[method], y[outer][:, ANCHORS], cell)
                assert prediction.shape == (14, 10) and np.isfinite(prediction).all()
                for di, drug in enumerate(drugs):
                    for qi in range(10):
                        rows.append({"method": method, "cell": cell, "drug": drug, "dose_index": qi,
                            "dose_M": doses[di, qi], "y0": wells[outer, di, qi, 0], "y1": wells[outer, di, qi, 1],
                            "prediction": prediction[di, qi], "is_anchor": qi in ANCHORS, "is_query": qi in QUERIES})
                check_clock()
            receipt["completed_outer_cells"].append(cell)
            (OUTPUT/"run.json").write_text(json.dumps(receipt, indent=2)+"\n", encoding="utf-8")
            print(json.dumps({"outer_complete": cell, "elapsed_seconds": time.monotonic()-started}), flush=True)
        check_clock()
    except Exception as exc:
        failure = exc
    pd.DataFrame(rows).to_csv(OUTPUT/"predictions.csv", index=False, float_format="%.17g")
    (OUTPUT/"selection.json").write_text(json.dumps(selections, indent=2)+"\n", encoding="utf-8")
    (OUTPUT/"optimizer.json").write_text(json.dumps(optimizer_log, indent=2)+"\n", encoding="utf-8")
    if failure is None and time.monotonic()-started > 900:
        failure = TimeoutError("15-minute matrix wall limit reached before completion receipt")
    receipt.update(status="complete" if failure is None else "inconclusive", wall_seconds=time.monotonic()-started,
        cpu_seconds=time.process_time()-cpu_started, prediction_rows=len(rows),
        predictions_sha256=sha(OUTPUT/"predictions.csv"), selection_sha256=sha(OUTPUT/"selection.json"),
        optimizer_failure_count=sum(not item["success"] for item in optimizer_log),
        failure=None if failure is None else {"type":type(failure).__name__,"message":str(failure)})
    (OUTPUT/"run.json").write_text(json.dumps(receipt, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({k:receipt[k] for k in ["status", "wall_seconds", "prediction_rows", "optimizer_failure_count"]}))
    if failure is not None:
        decision = {"status":"INCONCLUSIVE_NO_HTS031_RELEASE","gate_pass":False,
                    "reason":"Incomplete fixed matrix; resource/implementation failure is not a scientific negative",
                    "failure":receipt["failure"]}
        (OUTPUT/"decision.json").write_text(json.dumps(decision,indent=2)+"\n",encoding="utf-8")
        raise failure


if __name__ == "__main__":
    with threadpool_limits(limits=4):
        main()
