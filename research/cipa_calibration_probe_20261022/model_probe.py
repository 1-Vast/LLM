"""Frozen ordinary CiPA probe: metadata prepare, restricted fit/forecast, separate score."""
import os
for _name in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_name] = "1"
import argparse
from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path
import time

import numpy as np
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.linear_model import Ridge
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/cipa_calibration_probe"
CODE = Path(__file__).resolve()
DATA = OUT / "SOURCE_DEV_BUNDLES.json"
KEYS = ("bundle_id", "site", "cell", "platform", "drug", "dose_code", "split")
HEADS = ("E", "M", "H")
TARGETS = ("ead_mean", "ddfpdc_available_fraction", "ddfpdc_mean")
CONTROLS = {"Dofetilide", "Nifedipine", "Mexiletine", "Ranolazine"}
SEEDS = (11, 23, 47, 89, 179)
FITS = []
SUMMARIES = []


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write(name, value):
    with (OUT / name).open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False, allow_nan=False)


def metadata():
    # Conversion already sees source/dev scalars. Only identity dictionaries cross
    # into preparation/proposal; this is computational isolation, not raw blindness.
    rows = [{k: r[k] for k in KEYS} for r in read(DATA)["bundles"]]
    assert all(r["site"] in set("1234567") for r in rows)
    assert len({r["bundle_id"] for r in rows}) == len(rows)
    return sorted(rows, key=lambda r: r["bundle_id"])


def labels_for(ids):
    # Filter by authorized IDs BEFORE extracting any target/count/mask fields.
    wanted = set(ids)
    result = {}
    for row in read(DATA)["bundles"]:
        if row["bundle_id"] in wanted:
            result[row["bundle_id"]] = [row[k] for k in TARGETS]
    assert set(result) == wanted
    return result


def contexts(rows):
    groups = defaultdict(list)
    for row in rows:
        groups["|".join(row[k] for k in ("site", "cell", "platform"))].append(row)
    return dict(sorted(groups.items()))


def portfolio_folds(ids):
    ordered = sorted(ids, key=lambda bid: (sha256(bid.encode()).hexdigest(), bid))
    return [ordered[f::4] for f in range(4)]


def make_manifest(meta):
    result = {}
    all_drugs = {r["drug"] for r in meta}
    assert len(all_drugs) == 28 and CONTROLS <= all_drugs
    for context, rows in contexts(meta).items():
        pool = sorted(r["bundle_id"] for r in rows if r["drug"] in CONTROLS)
        terminal = sorted(r["bundle_id"] for r in rows if r["drug"] not in CONTROLS)
        expected = {(d, str(c)) for d in CONTROLS for c in range(1, 5)}
        assert {(r["drug"], r["dose_code"]) for r in rows if r["drug"] in CONTROLS} == expected
        missing = (all_drugs - CONTROLS) | set()
        expected_terminal = {(d, str(c)) for d in missing for c in range(1, 5)}
        actual_terminal = {(r["drug"], r["dose_code"]) for r in rows if r["drug"] not in CONTROLS}
        if context == "3|CDI|MCS":
            assert expected_terminal - actual_terminal == {("Ibutilide", "1")}
        else:
            assert actual_terminal == expected_terminal
        assert len(pool) == 16 and len(terminal) == (95 if context == "3|CDI|MCS" else 96)
        fixed = sorted(r["bundle_id"] for r in rows if r["drug"] in CONTROLS and r["dose_code"] in ("1", "4"))
        policies = {"fixed": fixed}
        for seed in SEEDS:
            chosen = np.random.default_rng(seed).choice(len(pool), 8, replace=False)
            policies[f"random_{seed}"] = [pool[int(i)] for i in chosen]
        result[context] = {"pool": pool, "terminal": terminal, "metadata_policies": policies,
                           "portfolio_folds": portfolio_folds(fixed)}
    return {"contexts": result, "control_drugs": sorted(CONTROLS), "budget_per_context": 8,
            "random_generator": "numpy.default_rng PCG64; indices into sorted pool; preserve drawn order"}


def configs():
    result = []
    for mode in ("all", "cell", "cell_platform"):
        result.append({"id": f"lookup:{mode}", "family": "lookup", "mode": mode})
    for family in ("offset", "affine", "multivariate"):
        for kappa in (1, 8, 32):
            result.append({"id": f"{family}:k{kappa}", "family": family, "kappa": kappa})
    for family in ("ridge", "augmented"):
        for alpha in (.1, 10, 100):
            for weight in (1, 8):
                result.append({"id": f"{family}:a{alpha}:w{weight}", "family": family, "alpha": alpha, "weight": weight})
    for leaf in (1, 4):
        for weight in (1, 8):
            result.append({"id": f"trees:l{leaf}:w{weight}", "family": "trees", "leaf": leaf, "weight": weight})
    return sorted(result, key=lambda c: c["id"])


def prepare():
    assert read(OUT / "ENDPOINT_SCHEMA_AUDIT.json")["status"] == "PASS"
    meta = metadata()
    manifest = make_manifest(meta)
    write("QUERY_MANIFEST.json", manifest)
    write("PREPARE_AUDIT.json", {
        "status": "PASS", "predictive_fits": 0, "metadata_only_proposals": True,
        "numerical_conversion_already_exposed": True, "later_numeric_access": 0,
        "source_sites": list("12345"), "dev_sites": ["6", "7"],
        "contexts_by_site": {s: sum(k.split("|")[0] == s for k in manifest["contexts"]) for s in "1234567"},
        "configs": configs(), "features": ["drug*dose onehot", "cell onehot", "platform onehot", "physical site onehot"],
        "default_source_vector": "same-cell lookup (fallback all then source-global); H/source-only scale",
        "uncertainty": "per drug/dose/head variance among training-source contexts, ddof=0; fewer than two finite values -> zero; H divided by source scale",
        "nested_features": "augmented source rows leave entire own physical source site out, including inner scale; target vectors use training sources only",
        "selection": "mean of physical-site combined losses, physical-site components pooled equally over context bundles; exact ties lexical configuration id",
        "overall_updater": "best nonlookup configuration; strongrefit best ridge/augmented/trees; mixture fixed 50/50 sourcebest+strongrefit",
        "portfolio": "one source-tuned candidate per six updating families plus best lookup; balanced hash order round-robin folds; average available heads then average four folds",
        "ridge_intercept": "direct/augmented sklearn unpenalized intercept; residual identity departures penalize all coefficients",
        "fit_counts": "each actual head solver fit logged with stage/physical target site/context/config/seed/cpu/wall; lookup summary constructions logged separately",
        "freeze_required": ["PROTOCOL.md", "ENDPOINT_CONTRACT.md", "SOURCE_DEV_BUNDLES.json", "QUERY_MANIFEST.json", "PREPARE_AUDIT.json", "ENDPOINT_SCHEMA_AUDIT.json", "model_probe.py", "endpoint_contract.py"],
    })


class Summary:
    def __init__(self, rows, labels, stage):
        assert rows and set(r["site"] for r in rows) <= set("12345")
        self.rows = rows
        self.y = np.array([labels[r["bundle_id"]] for r in rows], dtype=float)
        valid = self.y[np.isfinite(self.y[:, 2]), 2]
        assert len(valid)
        scale = float(np.subtract(*np.percentile(valid, [75, 25])))
        if not scale > 0:
            scale = float(np.std(valid))
        self.scale = scale if np.isfinite(scale) and scale > 0 else 1.0
        self.global_mean = np.nanmean(self.y, axis=0)
        assert np.isfinite(self.global_mean).all()
        self.tables = {}
        for mode, keys in (("all", ("drug", "dose_code")), ("cell", ("drug", "dose_code", "cell")), ("cell_platform", ("drug", "dose_code", "cell", "platform"))):
            grouped = defaultdict(list)
            for i, row in enumerate(rows):
                grouped[tuple(row[k] for k in keys)].append(i)
            self.tables[mode] = (keys, {key: self._mean(self.y[idx]) for key, idx in grouped.items()})
        SUMMARIES.append({"stage": stage, "source_sites": sorted({r["site"] for r in rows}), "bundles": len(rows), "scale": self.scale})

    @staticmethod
    def _mean(y):
        return np.array([float(np.mean(col[np.isfinite(col)])) if np.isfinite(col).any() else np.nan for col in y.T])

    def lookup(self, rows, mode="cell", normalized=True):
        levels = {"all": ("all",), "cell": ("all", "cell"), "cell_platform": ("all", "cell", "cell_platform")}[mode]
        result = np.tile(self.global_mean, (len(rows), 1))
        for level in levels:
            keys, table = self.tables[level]
            for i, row in enumerate(rows):
                value = table.get(tuple(row[k] for k in keys))
                if value is not None:
                    mask = np.isfinite(value)
                    result[i, mask] = value[mask]
        if normalized:
            result[:, 2] /= self.scale
        return result

    def uncertainty(self, row):
        idx = [i for i, r in enumerate(self.rows) if (r["drug"], r["dose_code"]) == (row["drug"], row["dose_code"])]
        y = self.y[idx].copy()
        y[:, 2] /= self.scale
        return sum(float(np.var(col[np.isfinite(col)])) if np.isfinite(col).sum() >= 2 else 0. for col in y.T)


def make_dictionary(meta):
    keys = sorted({key for row in meta for key in feature_keys(row)})
    return {key: i for i, key in enumerate(keys)}


def feature_keys(row):
    assert set(row) == set(KEYS)
    return [("drug_dose", row["drug"], row["dose_code"]), ("cell", row["cell"]), ("platform", row["platform"]), ("site", row["site"])]


def onehot(rows, dictionary):
    matrix = np.zeros((len(rows), len(dictionary)))
    for i, row in enumerate(rows):
        for key in feature_keys(row):
            matrix[i, dictionary[key]] = 1.
    return matrix


def bounded(prediction):
    assert np.isfinite(prediction).all(), "Nonfinite prediction cannot be selectively dropped"
    prediction[:, :2] = np.clip(prediction[:, :2], 0., 1.)
    return prediction


def predict(config, source, source_labels, paid, paid_labels, test_meta, summary, dictionary, stage, context, nested=None):
    # No terminal truth parameter exists. Row arguments are exact identity schemas.
    assert all(set(r) == set(KEYS) for r in source + paid + test_meta)
    assert set(source_labels) == {r["bundle_id"] for r in source}
    assert set(paid_labels) == {r["bundle_id"] for r in paid}
    assert not ({r["bundle_id"] for r in paid} & {r["bundle_id"] for r in test_meta})
    family = config["family"]
    if family == "lookup":
        return bounded(summary.lookup(test_meta, config["mode"], normalized=False))
    base = summary.lookup(test_meta)
    target = np.array([paid_labels[r["bundle_id"]] for r in paid], dtype=float).reshape(-1, 3)
    target[:, 2] /= summary.scale
    if family in ("offset", "affine", "multivariate"):
        control = summary.lookup(paid)
        output = base.copy()
        for head in range(3):
            valid = np.isfinite(target[:, head])
            if not valid.any():
                continue
            if family == "offset":
                x, z = np.ones((len(paid), 1)), np.ones((len(test_meta), 1))
            elif family == "affine":
                x = np.column_stack([np.ones(len(paid)), control[:, head]])
                z = np.column_stack([np.ones(len(test_meta)), base[:, head]])
            else:
                x = np.column_stack([np.ones(len(paid)), control])
                z = np.column_stack([np.ones(len(test_meta)), base])
            start, cpu = time.perf_counter(), time.process_time()
            coefficient = np.linalg.solve(x[valid].T @ x[valid] + config["kappa"] * np.eye(x.shape[1]), x[valid].T @ (target[valid, head] - control[valid, head]))
            record_fit(stage, context, config, head, int(valid.sum()), start, cpu)
            output[:, head] += z @ coefficient
    else:
        training = source + paid
        y = np.array([source_labels[r["bundle_id"]] for r in source] + [paid_labels[r["bundle_id"]] for r in paid], dtype=float)
        y[:, 2] /= summary.scale
        x, z = onehot(training, dictionary), onehot(test_meta, dictionary)
        if family == "augmented":
            assert nested is not None and nested.shape == (len(source), 3)
            x = np.column_stack([x, np.vstack([nested, summary.lookup(paid)])])
            z = np.column_stack([z, base])
        weights = np.array([1.] * len(source) + [float(config["weight"])] * len(paid))
        output = np.empty_like(base)
        for head in range(3):
            valid = np.isfinite(y[:, head])
            start, cpu = time.perf_counter(), time.process_time()
            if family == "trees":
                model = ExtraTreesRegressor(n_estimators=128, min_samples_leaf=config["leaf"], random_state=104729, n_jobs=2)
            else:
                model = Ridge(alpha=config["alpha"], solver="cholesky")
            model.fit(x[valid], y[valid, head], sample_weight=weights[valid])
            record_fit(stage, context, config, head, int(valid.sum()), start, cpu)
            output[:, head] = model.predict(z)
    output[:, 2] *= summary.scale
    return bounded(output)


def record_fit(stage, context, config, head, n, start, cpu):
    FITS.append({"stage": stage, "context": context, "physical_site": context.split("|")[0], "config": config["id"], "head": HEADS[head], "n_training_valid": n,
                 "seed": 104729 if config["family"] == "trees" else None, "cpu_seconds": time.process_time() - cpu, "wall_seconds": time.perf_counter() - start})


def nested_vectors(source, labels, stage):
    result = np.empty((len(source), 3))
    for site in sorted({r["site"] for r in source}):
        training = [r for r in source if r["site"] != site]
        sublabels = {r["bundle_id"]: labels[r["bundle_id"]] for r in training}
        summary = Summary(training, sublabels, stage + ":nested_exclude_" + site)
        ids = [i for i, r in enumerate(source) if r["site"] == site]
        result[ids] = summary.lookup([source[i] for i in ids])
    return result


def losses(prediction, truth, scale):
    truth = np.array(truth, dtype=float)
    assert prediction.shape == truth.shape and np.isfinite(prediction).all()
    component, coverage = {}, {}
    for head, name in enumerate(HEADS):
        valid = np.isfinite(truth[:, head])
        coverage[name] = {"valid": int(valid.sum()), "total": len(valid)}
        if not valid.any():
            component[name] = None
        elif head < 2:
            p, y = prediction[valid, head], truth[valid, head]
            component[name] = float(np.mean(p*p - 2*p*y + y))
        else:
            component[name] = float(np.mean(np.abs(prediction[valid, head] - truth[valid, head])) / scale)
    available = [v for v in component.values() if v is not None]
    return {"components": component, "combined": float(np.mean(available)), "raw_H_MAE": None if component["H"] is None else component["H"] * scale, "coverage": coverage}


def rows_by_ids(ids, index):
    return [index[bid] for bid in ids]


def source_cv(meta, manifest, dictionary):
    source_all = [r for r in meta if r["split"] == "source"]
    all_labels = labels_for(r["bundle_id"] for r in source_all)
    index = {r["bundle_id"]: r for r in meta}
    scores = defaultdict(dict)
    for site in "12345":
        source = [r for r in source_all if r["site"] != site]
        labels = {r["bundle_id"]: all_labels[r["bundle_id"]] for r in source}
        summary = Summary(source, labels, "source_cv_hold_" + site)
        nested = nested_vectors(source, labels, "source_cv_hold_" + site)
        site_predictions, site_truth = defaultdict(list), []
        for context, cm in manifest["contexts"].items():
            if context.split("|")[0] != site:
                continue
            paid = rows_by_ids(cm["metadata_policies"]["fixed"], index)
            paid_labels = {r["bundle_id"]: all_labels[r["bundle_id"]] for r in paid}
            terminal = rows_by_ids(cm["terminal"], index)
            site_truth.extend(all_labels[r["bundle_id"]] for r in terminal)
            for config in configs():
                p = predict(config, source, labels, paid, paid_labels, terminal, summary, dictionary, "source_cv", context, nested)
                site_predictions[config["id"]].extend(p.tolist())
        for cid, prediction in site_predictions.items():
            scores[cid][site] = losses(np.array(prediction), site_truth, summary.scale)
        print(f"source CV site {site} complete; actual head fits={len(FITS)}", flush=True)
    mean = {cid: float(np.mean([s["combined"] for s in bysite.values()])) for cid, bysite in scores.items()}
    def choose(candidates):
        return min(candidates, key=lambda c: (mean[c["id"]], c["id"]))
    byfamily = {family: choose([c for c in configs() if c["family"] == family]) for family in sorted({c["family"] for c in configs()})}
    refit = choose([c for c in configs() if c["family"] in ("ridge", "augmented", "trees")])
    updater = choose([c for c in configs() if c["family"] != "lookup"])
    return {"scores": dict(scores), "mean_physical_site_combined": mean, "families": byfamily,
            "sourcebest": byfamily["lookup"], "strongrefit": refit, "overallupdater": updater,
            "primary": {"policy": "fixed", "config": updater}, "selection_uses_dev_labels": False}


def proposals(rows, cm, summary, index):
    result = dict(cm["metadata_policies"])
    pool = rows_by_ids(cm["pool"], index)
    result["source_uncertainty"] = [r["bundle_id"] for r in sorted(pool, key=lambda r: (-summary.uncertainty(r), r["bundle_id"]))[:8]]
    vectors = np.column_stack([np.ones(len(pool)), summary.lookup(pool)])
    a = 8 * np.eye(4)
    selected = []
    for _ in range(8):
        inverse = np.linalg.inv(a)
        possible = [i for i in range(len(pool)) if i not in selected]
        choice = min(possible, key=lambda i: (-float(vectors[i] @ inverse @ vectors[i]), pool[i]["bundle_id"]))
        selected.append(choice)
        a += np.outer(vectors[choice], vectors[choice])
    result["linear_design"] = [pool[i]["bundle_id"] for i in selected]
    assert all(len(ids) == len(set(ids)) == 8 and set(ids) <= set(cm["pool"]) for ids in result.values())
    return result


def portfolio(candidates, source, labels, paid, paid_labels, terminal, summary, dictionary, context, nested):
    index = {r["bundle_id"]: r for r in paid}
    folds = portfolio_folds(list(index))
    scores = {}
    for config in candidates:
        fold_scores = []
        for f, validation_ids in enumerate(folds):
            validation = rows_by_ids(validation_ids, index)
            training = [r for r in paid if r["bundle_id"] not in validation_ids]
            training_labels = {r["bundle_id"]: paid_labels[r["bundle_id"]] for r in training}
            p = predict(config, source, labels, training, training_labels, validation, summary, dictionary, f"portfolio_fold_{f}", context, nested)
            fold_scores.append(losses(p, [paid_labels[r["bundle_id"]] for r in validation], summary.scale))
        scores[config["id"]] = {"folds": fold_scores, "mean": float(np.mean([s["combined"] for s in fold_scores]))}
    choice = min(candidates, key=lambda c: (scores[c["id"]]["mean"], c["id"]))
    prediction = predict(choice, source, labels, paid, paid_labels, terminal, summary, dictionary, "portfolio_final", context, nested)
    return prediction, {"choice": choice, "candidate_scores": scores, "folds": folds}


def verify_freeze():
    seal = read(OUT / "FREEZE.json")
    assert isinstance(seal["files"], dict)
    needed = [CODE, CODE.parent / "endpoint_contract.py"] + [OUT / n for n in ("PROTOCOL.md", "ENDPOINT_CONTRACT.md", "SOURCE_DEV_BUNDLES.json", "QUERY_MANIFEST.json", "PREPARE_AUDIT.json", "ENDPOINT_SCHEMA_AUDIT.json")]
    for path in needed:
        assert path.relative_to(ROOT).as_posix() in seal["files"], f"Not frozen: {path}"
    for name, expected in seal["files"].items():
        assert digest(ROOT / name) == expected, f"Frozen file changed: {name}"
    assert read(OUT / "ENDPOINT_SCHEMA_AUDIT.json")["status"] == "PASS"
    return digest(OUT / "FREEZE.json")


def fit_predict():
    freeze_hash = verify_freeze()
    assert not (OUT / "FORECASTS.json").exists() and not (OUT / "FORECAST_SEAL.json").exists()
    start, cpu = time.perf_counter(), time.process_time()
    meta = metadata()
    index = {r["bundle_id"]: r for r in meta}
    manifest = read(OUT / "QUERY_MANIFEST.json")
    assert make_manifest(meta) == manifest
    dictionary = make_dictionary(meta)
    choices = source_cv(meta, manifest, dictionary)
    source = [r for r in meta if r["split"] == "source"]
    labels = labels_for(r["bundle_id"] for r in source)
    summary = Summary(source, labels, "development_all_source")
    nested = nested_vectors(source, labels, "development_all_source")
    forecasts, feedback, portfolio_choices, query_lists = {}, {}, {}, {}
    candidates = list(choices["families"].values())
    for context, rows in contexts([r for r in meta if r["split"] == "dev"]).items():
        cm = manifest["contexts"][context]
        terminal = rows_by_ids(cm["terminal"], index)
        policies = proposals(rows, cm, summary, index)
        query_lists[context] = policies
        output = {}
        for policy, ids in policies.items():
            paid = rows_by_ids(ids, index)
            paid_labels = labels_for(ids)
            feedback[context + ":" + policy] = [{"bundle_id": bid, "targets_EMH": paid_labels[bid]} for bid in ids]
            if policy == "fixed":
                unique = {c["id"]: c for c in candidates + [choices["strongrefit"], choices["overallupdater"]]}
                predictions = {cid: predict(c, source, labels, paid, paid_labels, terminal, summary, dictionary, "dev_fixed", context, nested) for cid, c in unique.items()}
                for family, config in choices["families"].items():
                    output["fixed:" + family] = predictions[config["id"]].tolist()
                output["fixed:strongrefit"] = predictions[choices["strongrefit"]["id"]].tolist()
                output["fixed:overallupdater"] = predictions[choices["overallupdater"]["id"]].tolist()
                output["fixed:mixture"] = bounded(.5 * predictions[choices["sourcebest"]["id"]] + .5 * predictions[choices["strongrefit"]["id"]]).tolist()
                p, search = portfolio(candidates, source, labels, paid, paid_labels, terminal, summary, dictionary, context, nested)
                output["fixed:portfolio"] = p.tolist()
                portfolio_choices[context] = search
            else:
                output[policy + ":overallupdater"] = predict(choices["overallupdater"], source, labels, paid, paid_labels, terminal, summary, dictionary, "dev_" + policy, context, nested).tolist()
        forecasts[context] = {"bundle_ids": cm["terminal"], "predictions": output}
        print(f"development {context} forecasts done; head fits={len(FITS)}", flush=True)
    write("SOURCE_CHOICES.json", choices)
    write("QUERY_LISTS.json", query_lists)
    write("QUERY_FEEDBACK.json", feedback)
    write("PORTFOLIO_CHOICES.json", portfolio_choices)
    write("FORECASTS.json", {"scale": summary.scale, "head_order": list(HEADS), "contexts": forecasts})
    write("FIT_COUNTS.json", {"fits": FITS, "head_solver_fit_count": len(FITS), "summary_constructions": SUMMARIES,
        "total_cpu_seconds": time.process_time() - cpu, "total_wall_seconds": time.perf_counter() - start,
        "counts_by_stage": {stage: sum(r["stage"] == stage for r in FITS) for stage in sorted({r["stage"] for r in FITS})},
        "source_cv_query_cost_per_physical_site": {site: 8 * sum(k.split("|")[0] == site for k in manifest["contexts"]) for site in "12345"},
        "development_policy_cost_per_physical_site": {site: 8 * sum(k.split("|")[0] == site for k in manifest["contexts"]) for site in "67"},
        "seed": 104729, "tree_n_jobs": 2, "blas_threads": 1})
    files = ("SOURCE_CHOICES.json", "QUERY_LISTS.json", "QUERY_FEEDBACK.json", "PORTFOLIO_CHOICES.json", "FORECASTS.json", "FIT_COUNTS.json")
    write("FORECAST_SEAL.json", {"freeze_sha256": freeze_hash, "files": {n: digest(OUT / n) for n in files}, "terminal_truth_extracted": False})


def score():
    verify_freeze()
    seal = read(OUT / "FORECAST_SEAL.json")
    assert seal["freeze_sha256"] == digest(OUT / "FREEZE.json")
    for name, expected in seal["files"].items():
        assert digest(OUT / name) == expected
    forecasts = read(OUT / "FORECASTS.json")
    scale = forecasts["scale"]
    methods = None
    bysite, pooled_pred, pooled_truth = {}, defaultdict(list), []
    for context, item in forecasts["contexts"].items():
        truth = labels_for(item["bundle_ids"])
        y = [truth[bid] for bid in item["bundle_ids"]]
        pooled_truth.extend(y)
        assert methods is None or methods == set(item["predictions"])
        methods = set(item["predictions"])
        bysite[context] = {}
        for name, values in item["predictions"].items():
            bysite[context][name] = losses(np.array(values), y, scale)
            pooled_pred[name].extend(values)
    pooled = {name: losses(np.array(p), pooled_truth, scale) for name, p in pooled_pred.items()}
    baseline = "fixed:lookup"
    comparison = {}
    for name in sorted(methods):
        differences = {context: bysite[context][name]["combined"] - bysite[context][baseline]["combined"] for context in bysite}
        mean_difference = float(np.mean(list(differences.values())))
        comp_difference = {head: pooled[name]["components"][head] - pooled[baseline]["components"][head] for head in HEADS}
        comparison[name] = {"paired_site_combined_difference": differences, "mean_site_combined_difference": mean_difference,
            "pooled_component_difference": comp_difference, "opportunity_gate": mean_difference < 0 and all(v <= 0 for v in comp_difference.values())}
    write("TERMINAL_SCORES.json", {"by_context_physical_site": bysite, "pooled_equal_bundles": pooled, "comparisons_to_frozen_sourcebest": comparison,
        "primary_method": "fixed:overallupdater", "terminal_only_after_forecast_seal": True, "later_numeric_access": 0,
        "interpretation": "ordinary exploratory two-site development screen; seeds are not biological replicates"})
    write("SCORE_SEAL.json", {"forecast_seal_sha256": digest(OUT / "FORECAST_SEAL.json"), "scores_sha256": digest(OUT / "TERMINAL_SCORES.json")})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("prepare", "fit_predict", "score"))
    args = parser.parse_args()
    with threadpool_limits(limits=1, user_api="blas"):
        {"prepare": prepare, "fit_predict": fit_predict, "score": score}[args.phase]()
