"""Independent C4 v2 reconstruction. No imports from the main implementation.

The only scientific source is the frozen CSV. Main-run artifacts are opened
only after independent training, actions, endpoints and bootstrap are complete.
Invocation is a single scientific run; an exclusive result file prevents retry.
"""
import os

for _key in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS",
             "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[_key] = "1"

import csv
import ctypes
import hashlib
import json
import math
from pathlib import Path
import sys
import time
import traceback

START_CPU = time.process_time()
START_WALL = time.monotonic()
import numpy as np

ROOT = Path(__file__).resolve().parent
SOURCE = Path("D:/MAESTRO/tmp/extq1/GDSC2_fitted_dose_response.csv")
EXPECTED_SHA = "0883b3ef6e440603094c43c74044e1d333fce61e92e3efa374ea3a54f0b50302"
STRATEGIES = ("static_global13", "static_tissue13", "probe_blind", "random13",
              "rank8", "rank1", "ridge", "knn5")
CONTROLS = STRATEGIES[:3]


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def peak_memory():
    if os.name == "nt":
        class Counters(ctypes.Structure):
            _fields_ = [("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong)] + [
                (name, ctypes.c_size_t) for name in (
                    "PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage",
                    "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage",
                    "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage")]
        counts = Counters()
        counts.cb = ctypes.sizeof(counts)
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetCurrentProcess.restype = ctypes.c_void_p
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        psapi.GetProcessMemoryInfo.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong]
        if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(counts), counts.cb):
            raise OSError(ctypes.get_last_error(), "GetProcessMemoryInfo")
        return max(counts.PeakWorkingSetSize, counts.PeakPagefileUsage)
    import resource
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == "darwin" else 1024)


def budget():
    assert time.process_time() - START_CPU <= 600, "Independent CPU budget exceeded"
    assert peak_memory() <= 2 * 1024**3, "Independent 2 GiB memory budget exceeded"


def descending(values, count, exclude=()):
    allowed = np.ones(len(values), dtype=bool)
    allowed[list(exclude)] = False
    order = np.argsort(-np.asarray(values), kind="stable")
    return order[allowed[order]][:count].tolist()


def endpoints(x, loglow, loghigh):
    finite = np.isfinite(x)
    hit = finite & (x > loglow + 1e-8) & (x < loghigh - 1e-8) & (x <= 0)
    return finite, hit


def probability(mean, variance, lo, hi):
    sigma = np.sqrt(variance)
    cdf = np.vectorize(lambda t: 0.5 * math.erfc(-t / math.sqrt(2)), otypes=[float])
    return cdf((hi - mean) / sigma) - cdf((lo - mean) / sigma)


def fit_latent(s, finite, rank):
    b = s.mean(axis=1)
    centered = s - b[:, None]
    u, singular, vt = np.linalg.svd(centered, full_matrices=False)
    theta = np.column_stack((b, u[:, :rank] * singular[:rank]))
    design = np.column_stack((np.ones(s.shape[1]), vt[:rank].T))
    mean = theta.mean(axis=0)
    covariance = np.cov(theta, rowvar=False, ddof=1) + np.eye(rank + 1) * 1e-6
    residual = s - theta @ design.T
    noise = np.maximum((residual**2 * finite).sum(axis=0) / finite.sum(axis=0), 0.0025)
    return dict(A=design, m=mean, P=covariance, r=noise,
                reconstruction=theta @ design.T, singular=singular[:rank])


def direct_posterior(model, indices, observed=None):
    """Condition in observation space from the prior; no recursive updates."""
    a, m, p, r = (model[k] for k in ("A", "m", "P", "r"))
    if not len(indices):
        return m.copy(), p.copy()
    observed_design = a[indices]
    cross = p @ observed_design.T
    gram = observed_design @ cross + np.diag(r[indices])
    covariance = p - cross @ np.linalg.solve(gram, cross.T)
    mean = m if observed is None else m + cross @ np.linalg.solve(gram, observed - observed_design @ m)
    return mean, covariance


def panel(model):
    selected = []
    a, r = model["A"], model["r"]
    for _ in range(8):
        _, p = direct_posterior(model, selected)
        cross = a @ p @ a.T
        gains = (cross * cross).sum(axis=0) / (r + np.diag(cross))
        selected.append(descending(gains, 1, selected)[0])
    return selected


def read_selected_rows(meta):
    """Metadata-only choice, retaining functional strings without converting them."""
    lookup = {(c["drug_id"], c["min_conc_raw"], c["max_conc_raw"]): j
              for j, c in enumerate(meta["conditions"])}
    cell_lookup = {c["id"]: i for i, c in enumerate(meta["cells"])}
    selected = {}
    with SOURCE.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        for row_index, row in enumerate(reader):
            sidm = row["SANGER_MODEL_ID"]
            assert sidm in cell_lookup, "Unfrozen cell identity"
            cell = meta["cells"][cell_lookup[sidm]]
            assert row["CELL_LINE_NAME"] == cell["name"] and row["TCGA_DESC"] == cell["tissue"], "Cell identity drift"
            raw_id = row["NLME_RESULT_ID"]
            result_id = int(raw_id)
            assert str(result_id) == raw_id.strip(), "Noncanonical integer NLME_RESULT_ID"
            key = (row["DRUG_ID"], row["MIN_CONC"], row["MAX_CONC"])
            if key not in lookup:
                continue
            j = lookup[key]
            pair = (cell_lookup[sidm], j)
            candidate = (result_id, row_index, row["LN_IC50"])
            if pair not in selected or candidate[:2] < selected[pair][:2]:
                selected[pair] = candidate
            if row_index % 10000 == 0:
                budget()
    return selected


def matrix(selected, cell_rows, conditions):
    x = np.full((len(cell_rows), len(conditions)), np.nan)
    rows = np.full(x.shape, -1, dtype=np.int64)
    results = np.full(x.shape, -1, dtype=np.int64)
    for i, cell_index in enumerate(cell_rows):
        for j, condition_index in enumerate(conditions):
            item = selected.get((cell_index, condition_index))
            if item is None:
                continue
            results[i, j], rows[i, j], raw = item
            try:
                x[i, j] = float(raw)
            except ValueError:
                assert raw.strip().lower() in ("", "na", "nan", "null", "none"), "Unrecognised response token"
    return x, rows, results


def paired_bounds(left, right, known, hit):
    only_left = np.setdiff1d(left, right)
    only_right = np.setdiff1d(right, left)
    base = int(hit[only_left].sum()) - int(hit[only_right].sum())
    return base - int((~known[only_right]).sum()), base + int((~known[only_left]).sum())


def independent_recompute(report):
    meta = load_json(ROOT / "metadata_freeze.json")
    audit = load_json(ROOT / "metadata_audit.json")
    assert SOURCE.resolve() == Path(meta["source"]).resolve()
    assert SOURCE.stat().st_size == meta["source_bytes"] == 20355833
    assert digest(SOURCE) == meta["source_sha256"] == audit["source_sha256"] == EXPECTED_SHA
    assert digest(ROOT / "metadata_freeze.json") == audit["freeze_sha256"]
    assert not audit["inconsistent_cell_metadata"] and not audit["normalised_name_collisions"]
    assert not audit["drug_ids_with_multiple_names"] and not audit["unique_cell_mode_changes"]
    assert not any(audit["reverse_identity_collisions"].values())
    assert not audit["unparseable_result_ids_source_rows"] and not audit["invalid_concentration_metadata_source_rows"]
    cells, conditions = meta["cells"], meta["conditions"]
    train_rows = [i for i, c in enumerate(cells) if c["role"] == "train"]
    test_rows = [i for i, c in enumerate(cells) if c["role"] == "test"]
    assert (len(train_rows), len(test_rows), len(cells)) == (566, 243, 809)
    selected = read_selected_rows(meta)
    train_all, train_source_all, train_result_all = matrix(selected, train_rows, range(len(conditions)))
    counts = np.isfinite(train_all).sum(axis=0)
    train_all[~np.isfinite(train_all)] = np.nan
    with np.errstate(invalid="ignore", divide="ignore"):
        mu_all, sd_all = np.nanmean(train_all, axis=0), np.nanstd(train_all, axis=0, ddof=0)
    eligible = [j for j in range(len(conditions)) if counts[j] / 566 >= 0.9 and sd_all[j] >= 0.1]
    assert len(eligible) >= 64, "Fewer than 64 finite-coverage/SD qualified conditions"
    ordered = sorted(eligible, key=lambda j: hashlib.sha256(("C4-drug|" + conditions[j]["id"]).encode()).hexdigest())
    menu = ordered[:64]
    ids = [conditions[j]["id"] for j in menu]
    x = train_all[:, menu]
    mu, sd = mu_all[menu], sd_all[menu]
    loglow = np.log([float(conditions[j]["min_conc_raw"]) for j in menu])
    loghigh = np.log([float(conditions[j]["max_conc_raw"]) for j in menu])
    known, hit = endpoints(x, loglow, loghigh)
    s = np.where(known, (mu - x) / sd, 0)
    rate = hit.sum(axis=0) / known.sum(axis=0)
    models = {rank: fit_latent(s, known, rank) for rank in (8, 1)}
    probes = panel(models[8])
    lo, hi = (mu - np.minimum(0, loghigh)) / sd, (mu - loglow) / sd
    tissue_rates = {}
    train_tissues = np.array([cells[i]["tissue"] for i in train_rows])
    for tissue in {c["tissue"] for c in cells}:
        mask = train_tissues == tissue
        tissue_rates[tissue] = (hit[mask].sum(axis=0) + 5 * rate) / (known[mask].sum(axis=0) + 5)
    design = np.column_stack((np.ones(566), s[:, probes]))
    penalty = np.diag([0.] + [1.] * 8)
    coefficients = np.zeros((9, 64))
    ridge_noise = np.zeros(64)
    for j in range(64):
        valid = known[:, j]
        d, target = design[valid], s[valid, j]
        coefficients[:, j] = np.linalg.solve(d.T @ d + penalty, d.T @ target)
        ridge_noise[j] = max(float(np.mean((target - d @ coefficients[:, j])**2)), 0.0025)
    report["training"] = {"eligible_count": len(eligible), "menu": ids, "probes": [ids[j] for j in probes],
                          "train_count": 566, "test_count": 243}
    frozen = dict(menu=ids, probes=probes, source_sha256=EXPECTED_SHA,
                  protocol_sha256=digest(ROOT / "protocol_c4_v2.md"), implementation_sha256=digest(Path(__file__)),
                  training_complete_before_test_numeric_conversion=True)
    saved_model = dict(mu=mu, sd=sd, train_x=x, s=s, finite=known, event=hit,
                       low=loglow, high=loghigh, global_rate=rate, probes=np.array(probes),
                       ridge_weights=coefficients, ridge_noise=ridge_noise)
    for rank, model in models.items():
        saved_model.update({key + str(rank): model[key] for key in ("A", "m", "P", "r")})
    np.savez_compressed(ROOT / "independent_training_model.npz", **saved_model)
    frozen["training_model_sha256"] = digest(ROOT / "independent_training_model.npz")
    (ROOT / "independent_training_freeze.json").write_text(json.dumps(frozen, indent=2), encoding="utf-8")
    budget()
    actions = {name: np.zeros((243, 13), dtype=np.int64) for name in STRATEGIES}
    predictions = {rank: np.zeros((243, 64)) for rank in (8, 1)}
    posterior_means = {rank: np.zeros((243, 64)) for rank in (8, 1)}
    posterior_covariances = {rank: np.zeros((243, 64, 64)) for rank in (8, 1)}
    for i, cell_row in enumerate(test_rows):
        # Only the common, already-fixed eight probes become numbers here.
        probe_x, _, _ = matrix(selected, [cell_row], [menu[j] for j in probes])
        probe_known = np.isfinite(probe_x[0])
        probe_s = np.where(probe_known, (mu[probes] - probe_x[0]) / sd[probes], 0)
        cell_s = np.zeros(64)
        cell_s[probes] = probe_s
        tissue_rate = tissue_rates[cells[cell_row]["tissue"]]
        actions["static_global13"][i] = descending(rate, 13)
        actions["static_tissue13"][i] = descending(tissue_rate, 13)
        actions["probe_blind"][i] = probes + descending(tissue_rate, 5, probes)
        sidm = cells[cell_row]["id"]
        actions["random13"][i] = sorted(range(64), key=lambda j: hashlib.sha256(("C4-random|" + sidm + "|" + ids[j]).encode()).hexdigest())[:13]
        observed = [j for p, j in enumerate(probes) if probe_known[p]]
        for rank in (8, 1):
            model = models[rank]
            m, p = direct_posterior(model, observed, cell_s[observed])
            pred_mean, pred_cov = model["A"] @ m, model["A"] @ p @ model["A"].T
            probabilities = probability(pred_mean, model["r"] + np.diag(pred_cov), lo, hi)
            predictions[rank][i] = probabilities
            posterior_means[rank][i], posterior_covariances[rank][i] = pred_mean, pred_cov
            actions["rank" + str(rank)][i] = probes + descending(probabilities, 5, probes)
        ridge_mean = np.r_[1, probe_s] @ coefficients
        actions["ridge"][i] = probes + descending(probability(ridge_mean, ridge_noise, lo, hi), 5, probes)
        neighbor_rate = rate.copy()
        if observed:
            distances = np.mean((s[:, observed] - cell_s[observed])**2, axis=1)
            nearest = np.argsort(distances, kind="stable")[:5]
            weights = 1 / (distances[nearest] + 0.1)
            denominator = (known[nearest] * weights[:, None]).sum(axis=0)
            numerator = (hit[nearest] * weights[:, None]).sum(axis=0)
            np.divide(numerator, denominator, out=neighbor_rate, where=denominator > 0)
        actions["knn5"][i] = probes + descending(neighbor_rate, 5, probes)
        budget()
    action_stack = np.stack([actions[name] for name in STRATEGIES], axis=1)
    (ROOT / "independent_actions_freeze.json").write_text(json.dumps({
        "actions_sha256": hashlib.sha256(action_stack.tobytes(order="C")).hexdigest(),
        "strategy_order": list(STRATEGIES), "all_actions_fixed_before_full_truth_conversion": True,
        "actions": action_stack.tolist()}, indent=2), encoding="utf-8")
    test_x, test_sources, test_results = matrix(selected, test_rows, menu)
    test_known, test_hit = endpoints(test_x, loglow, loghigh)
    bootstrap = np.random.default_rng(20261029).integers(0, 243, size=(2000, 243))
    paired = {}
    for control in CONTROLS:
        bounds = np.array([paired_bounds(actions["rank8"][i], actions[control][i], test_known[i], test_hit[i]) for i in range(243)])
        ci = np.quantile(bounds[bootstrap, 0].mean(axis=1), [0.025, 0.975], method="linear")
        paired[control] = dict(bounds=bounds, mean_lower=float(bounds[:, 0].mean()),
                               mean_upper=float(bounds[:, 1].mean()), ci=ci,
                               gate=bool(bounds[:, 0].mean() >= 0.5 and ci[0] > 0))
    metrics = {}
    for name, choices in actions.items():
        assert all(len(set(row)) == 13 for row in choices), name + " duplicated actions"
        picked_known = np.take_along_axis(test_known, choices, axis=1)
        picked_hit = np.take_along_axis(test_hit, choices, axis=1)
        lower, missing = picked_hit.sum(axis=1), (~picked_known).sum(axis=1)
        metrics[name] = dict(lower=lower, upper=lower + missing, unknown=missing,
                             mean_lower=float(lower.mean()), mean_upper=float((lower + missing).mean()))
    report["independent_main"] = {name: {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in data.items() if k != "bounds"} for name, data in paired.items()}
    report["independent_joint_gate"] = all(item["gate"] for item in paired.values())
    np.savez_compressed(ROOT / "independent_replay_arrays.npz", actions=action_stack,
                        strategy_order=np.array(STRATEGIES), bootstrap_indices=bootstrap,
                        paired_control_order=np.array(CONTROLS),
                        paired_bounds=np.stack([paired[name]["bounds"] for name in CONTROLS], axis=1),
                        candidate_lower=np.stack([metrics[name]["lower"] for name in STRATEGIES], axis=1),
                        candidate_upper=np.stack([metrics[name]["upper"] for name in STRATEGIES], axis=1),
                        test_finite=test_known, test_event=test_hit,
                        train_source_rows=train_source_all[:, menu], train_result_ids=train_result_all[:, menu],
                        test_source_rows=test_sources, test_result_ids=test_results)
    report["independent_artifact_sha256"] = {name: digest(ROOT / name) for name in (
        "independent_training_freeze.json", "independent_training_model.npz",
        "independent_actions_freeze.json", "independent_replay_arrays.npz")}
    return dict(menu=ids, menu_indices=menu, probes=probes, eligible=[conditions[j]["id"] for j in ordered],
                train_ids=[cells[i]["id"] for i in train_rows], test_ids=[cells[i]["id"] for i in test_rows],
                mu=mu, sd=sd, low=loglow, high=loghigh, known=known, hit=hit, s=s, rate=rate, models=models,
                train_x=x, train_sources=train_source_all[:, menu], train_results=train_result_all[:, menu],
                test_x=test_x, test_sources=test_sources, test_results=test_results,
                test_known=test_known, test_hit=test_hit, actions=actions, predictions=predictions,
                posterior_means=posterior_means, posterior_covariances=posterior_covariances,
                ridge_coefficients=coefficients, ridge_noise=ridge_noise, bootstrap=bootstrap,
                paired=paired, metrics=metrics)


def compare_artifacts(recomputed, report):
    """Open main artifacts only after independent reconstruction is finished."""
    q = recomputed

    def check(name, expected, actual, tolerance=1e-8):
        left, right = np.asarray(expected), np.asarray(actual)
        entry = {"name": name, "expected_shape": list(left.shape), "actual_shape": list(right.shape)}
        if left.shape != right.shape:
            entry.update(matches=False, reason="shape mismatch")
        elif left.dtype.kind in "OUS" or right.dtype.kind in "OUS":
            entry.update(matches=bool(np.array_equal(left, right)), tolerance=0)
        else:
            finite_left, finite_right = np.isfinite(left), np.isfinite(right)
            same_missing = bool(np.array_equal(finite_left, finite_right))
            mask = finite_left & finite_right
            difference = np.abs(left[mask].astype(float) - right[mask].astype(float))
            maximum = float(difference.max()) if difference.size else 0.
            exact = tolerance == 0
            matches = bool(np.array_equal(left, right, equal_nan=True)) if exact else bool(same_missing and np.allclose(left, right, rtol=0, atol=tolerance, equal_nan=True))
            entry.update(matches=matches, max_absolute_difference=maximum,
                         matching_finite_masks=same_missing, tolerance=tolerance)
        report["comparisons"].append(entry)
        if not entry["matches"]:
            report["errors"].append(name + " differs")

    artifact_names = ("training_freeze.json", "training_model.npz", "replay_arrays.npz",
                      "experiment_summary.json", "query_trace.jsonl", "actions_freeze.json", "feedback_access.jsonl")
    report["main_artifact_sha256"] = {name: digest(ROOT / name) for name in artifact_names}
    freeze = load_json(ROOT / "training_freeze.json")
    check("menu identities", q["menu"], [item["id"] for item in freeze["menu"]], 0)
    check("menu metadata indices", q["menu_indices"], freeze["menu_indices"], 0)
    meta = load_json(ROOT / "metadata_freeze.json")
    check("all eligible metadata indices", [j for j, c in enumerate(meta["conditions"]) if c["id"] in q["eligible"]], freeze["all_eligible_indices"], 0)
    check("frozen panel", q["probes"], freeze["probes8"], 0)
    check("train order", q["train_ids"], freeze["train_ids"], 0)
    check("test order", q["test_ids"], freeze["test_ids"], 0)
    with np.load(ROOT / "training_model.npz", allow_pickle=False) as model:
        mappings = {"train_y": "train_x", "s": "s", "finite": "known", "event": "hit",
                    "mu": "mu", "sd": "sd", "low": "low", "high": "high", "global_rate": "rate",
                    "ridge_weights": "ridge_coefficients", "ridge_noise": "ridge_noise", "probes": "probes"}
        for artifact_key, own_key in mappings.items():
            check("training." + artifact_key, q[own_key], model[artifact_key], 0 if artifact_key in ("finite", "event", "probes") else 1e-8)
        for rank in (1, 8):
            own = q["models"][rank]
            a, m, p = (model[prefix + str(rank)] for prefix in ("a", "m", "p"))
            check(f"rank{rank}.prior_predictive_mean", own["A"] @ own["m"], a @ m)
            check(f"rank{rank}.prior_predictive_covariance", own["A"] @ own["P"] @ own["A"].T, a @ p @ a.T)
            check(f"rank{rank}.loading_subspace", own["A"][:, 1:] @ own["A"][:, 1:].T, a[:, 1:] @ a[:, 1:].T)
            check(f"rank{rank}.residual_noise", own["r"], model["noise" + str(rank)])
            # Comparing observed-space means/covariances avoids SVD sign choices.
            main_model = dict(A=a, m=m, P=p, r=model["noise" + str(rank)])
            main_mean = np.zeros((243, 64))
            main_cov = np.zeros((243, 64, 64))
            for i in range(243):
                observed = [j for j in q["probes"] if q["test_known"][i, j]]
                y = (q["mu"][observed] - q["test_x"][i, observed]) / q["sd"][observed]
                pm, pc = direct_posterior(main_model, observed, y)
                main_mean[i], main_cov[i] = a @ pm, a @ pc @ a.T
            check(f"rank{rank}.all_cells_direct_posterior_predictive_mean", q["posterior_means"][rank], main_mean)
            check(f"rank{rank}.all_cells_direct_posterior_predictive_covariance", q["posterior_covariances"][rank], main_cov)
            budget()
    main_order = ("rank8", "static_global13", "static_tissue13", "probe_blind", "random13", "rank1", "ridge", "knn5")
    expected_actions = np.stack([q["actions"][name] for name in main_order], axis=1)
    with np.load(ROOT / "replay_arrays.npz", allow_pickle=False) as replay:
        check("all 25272 actions", expected_actions, replay["actions"], 0)
        prior = q["models"][8]["A"] @ q["models"][8]["m"]
        expected_predictions = np.stack((np.tile(prior, (243, 1)), q["posterior_means"][8]), axis=1)
        check("rank8 prior/postprobe predictive means", expected_predictions, replay["predictions"])
        prior_model = q["models"][8]
        prior_variance = prior_model["r"] + np.einsum("ij,jk,ik->i", prior_model["A"], prior_model["P"], prior_model["A"])
        lower = (q["mu"] - np.minimum(0, q["high"])) / q["sd"]
        upper = (q["mu"] - q["low"]) / q["sd"]
        prior_probability = probability(prior, prior_variance, lower, upper)
        expected_probabilities = np.stack((np.tile(prior_probability, (243, 1)), q["predictions"][8]), axis=1)
        check("rank8 prior/postprobe candidate probabilities", expected_probabilities, replay["probability_predictions"])
        check("rank8 prior/postprobe stable probability orders", np.argsort(-expected_probabilities, axis=2, kind="stable"), replay["probability_orders"], 0)
        check("shared bootstrap index array", q["bootstrap"], replay["bootstrap_indices"], 0)
        main_action_hash = hashlib.sha256(np.ascontiguousarray(replay["actions"]).tobytes()).hexdigest()
    summary = load_json(ROOT / "experiment_summary.json")
    for name in STRATEGIES:
        own, main_metric = q["metrics"][name], summary["metrics"][name]
        check(name + ".candidate_count_lower", own["mean_lower"], main_metric["candidate_count_lower"])
        check(name + ".candidate_count_upper", own["mean_upper"], main_metric["candidate_count_upper"])
        check(name + ".mean_unknown_attempts", own["unknown"].mean(), main_metric["mean_unknown_attempts"])
        check(name + ".attempts_per_cell", 13, main_metric["attempts_per_cell"], 0)
    for name in CONTROLS:
        own, main_comparison = q["paired"][name], summary["comparisons"][name]
        for artifact_key, own_key in (("mean_difference_lower", "mean_lower"), ("mean_difference_upper", "mean_upper"),
                                       ("difference_lower_bootstrap_ci95", "ci"), ("passes_point_and_ci", "gate")):
            check(name + "." + artifact_key, own[own_key], main_comparison[artifact_key])
    check("joint main gate", report["independent_joint_gate"], summary["hypothesis_joint_supported"], 0)
    action_freeze = load_json(ROOT / "actions_freeze.json")
    check("frozen action hash", main_action_hash, action_freeze["actions_sha256"], 0)
    check("actions frozen before full truth", True, action_freeze["all_actions_fixed_before_full_truth_conversion"], 0)
    check("frozen strategy order", main_order, action_freeze["strategy_order"], 0)
    verify_logs(q, report, check)
    report["independent_row_selection"] = {key + "_sha256": hashlib.sha256(q[key].tobytes()).hexdigest()
                                           for key in ("train_sources", "train_results", "test_sources", "test_results")}
    report["scope_limitations"] = [
        "Source-row selection is independently reconstructed; main artifacts have no row-index/result-ID arrays for direct identity comparison. Numeric train values and all resulting actions are compared.",
        "Main rank1 posterior is compared by applying an independent direct solver to its stored model; rank1 recursive intermediate/final states are not serialized for cross-implementation state comparison.",
        "Auxiliary boundary/outside-window category tallies and physical assay costs are not numerically certified by this core verifier.",
        "Access logs and freeze declarations can check recorded ordering and values, but cannot prove an unlogged memory access did not happen."]


def verify_logs(q, report, check):
    """Validate recorded actions and permitted oracle accesses against raw-source truth."""
    traces = [json.loads(line) for line in (ROOT / "query_trace.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    check("query trace cell count", 243, len(traces), 0)
    for i, row in enumerate(traces):
        check(f"trace.{i}.cell", q["test_ids"][i], row["cell"], 0)
        check(f"trace.{i}.finite_probe_updates", q["test_known"][i, q["probes"]].sum(), row["finite_probe_updates"], 0)
        check(f"trace.{i}.policies", np.stack([q["actions"][name][i] for name in STRATEGIES]),
              np.stack([row["policies"][name] for name in STRATEGIES]), 0)
    accesses = [json.loads(line) for line in (ROOT / "feedback_access.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    seen = {}
    issues = []
    for entry in accesses:
        i, j, phase = entry["cell_index"], entry["condition_index"], entry["phase"]
        if not (0 <= i < 243 and 0 <= j < 64):
            issues.append("out of range access")
            continue
        group = seen.setdefault((i, phase), [])
        group.append(j)
        if phase == "shared_probe":
            allowed = q["probes"]
        elif phase in ("rank8_selected_followup", "rank1_selected_followup"):
            rank_name = phase.split("_")[0]
            allowed = q["actions"][rank_name][i, 8:].tolist()
            if seen.get((i, "shared_probe")) != q["probes"]:
                issues.append(f"followup before complete probes: cell {i}")
        else:
            issues.append("unknown feedback phase " + phase)
            continue
        if j not in allowed:
            issues.append(f"unselected condition access: {i},{j},{phase}")
        expected = float(q["test_x"][i, j]) if q["test_known"][i, j] else None
        if expected is None:
            if entry["value"] is not None:
                issues.append(f"missing feedback mismatch: {i},{j}")
        elif entry["value"] is None or abs(expected - entry["value"]) > 1e-12:
            issues.append(f"feedback value mismatch: {i},{j}")
    for i in range(243):
        for phase, expected in (("shared_probe", q["probes"]),
                                ("rank8_selected_followup", q["actions"]["rank8"][i, 8:].tolist()),
                                ("rank1_selected_followup", q["actions"]["rank1"][i, 8:].tolist())):
            if seen.get((i, phase)) != expected:
                issues.append(f"access sequence/count mismatch: {i},{phase}")
    report["feedback_log_audit"] = dict(access_count=len(accesses), issues=issues, checked_values_against_independent_source=True)
    report["errors"].extend(issues)


def main():
    output = ROOT / "independent_verification.json"
    # Exclusive creation remains after failure, deliberately prohibiting retries.
    with output.open("x", encoding="utf-8") as handle:
        json.dump({"status": "RUNNING", "implementation_sha256": digest(Path(__file__))}, handle)
    report = dict(status="RUNNING", implementation_sha256=digest(Path(__file__)),
                  scientific_runs=1, errors=[], comparisons=[],
                  scope=["independent source row selection", "training eligibility and SHA menu", "rank8/rank1 SVD and direct posterior", "fixed A-opt8 panel", "all eight 13-action policies", "event/missing paired bounds", "shared bootstrap and joint primary gate"],
                  not_covered=["upstream CSV export and NLME fit independence", "donor/batch independence", "prospective measured efficacy", "dose-level curve quality", "mechanism or agent-specific benefit"])
    try:
        independent = independent_recompute(report)
        compare_artifacts(independent, report)
        budget()
        report["status"] = "VERIFIED" if not report["errors"] else "MISMATCH"
    except Exception as exc:
        report["status"] = "INVALID"
        report["errors"].append(type(exc).__name__ + ": " + str(exc))
        report["traceback"] = traceback.format_exc()
    finally:
        report["cpu_seconds"] = time.process_time() - START_CPU
        report["wall_seconds"] = time.monotonic() - START_WALL
        report["peak_memory_bytes"] = peak_memory()
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("status", "cpu_seconds", "peak_memory_bytes", "errors")}, ensure_ascii=False))
    return 0 if report["status"] == "VERIFIED" else 1


if __name__ == "__main__":
    sys.exit(main())
