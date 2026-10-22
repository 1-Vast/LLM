"""Source-only, nested physical-site CiPA conditional information diagnostic."""
import os
for _name in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_name] = "1"
import argparse
from collections import defaultdict
import importlib.util
import json
from pathlib import Path
import time

import numpy as np
from sklearn.linear_model import Ridge
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/cipa_control_information"
CODE = Path(__file__).resolve()
PREDECESSOR = ROOT / "research/cipa_calibration_probe_20261022/model_probe.py"
spec = importlib.util.spec_from_file_location("frozen_cipa", PREDECESSOR)
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
DATA = OUT / "SOURCE_ONLY_BUNDLES.json"
KEYS, HEADS, TARGETS = old.KEYS, old.HEADS, old.TARGETS
CONDITIONAL_FITS = []
PREPROCESSING = []
VOCABULARY = [("cell", c) for c in ("AXG", "CDI")] + [("platform", p) for p in ("AXN", "CLY", "ECR", "MCS")]
SLOTS = sorted((d, c) for d in old.CONTROLS for c in ("1", "4"))


def read(path):
    return old.read(path)


def digest(path):
    return old.digest(path)


def write(name, value):
    with (OUT / name).open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False, allow_nan=False)


def metadata():
    # Filter physical site BEFORE projecting identity; no dev numerical use.
    rows = [{k: r[k] for k in KEYS} for r in read(DATA)["bundles"] if r["site"] in "12345"]
    assert all(r["split"] == "source" for r in rows)
    assert len({r["bundle_id"] for r in rows}) == len(rows)
    return sorted(rows, key=lambda r: r["bundle_id"])


def labels_for(ids):
    wanted = set(ids)
    result = {}
    for row in read(DATA)["bundles"]:
        if row["site"] in "12345" and row["bundle_id"] in wanted:
            result[row["bundle_id"]] = [row[k] for k in TARGETS]
    assert set(result) == wanted, "Only source labels may cross this API"
    return result


def make_manifest(meta):
    manifest = old.make_manifest(meta)
    for context, item in manifest["contexts"].items():
        item["metadata_policies"] = {"fixed": item["metadata_policies"]["fixed"]}
        assert context.split("|")[0] in "12345"
    manifest.pop("random_generator")
    return manifest


def conditional_configs():
    return [{"id": f"{family}:a{alpha}", "family": family, "alpha": alpha}
            for family in ("conditional", "maskonly", "metadataonly") for alpha in (1, 32)]


def prepare():
    assert read(old.OUT / "ENDPOINT_SCHEMA_AUDIT.json")["status"] == "PASS"
    for original, key, target in ((old.DATA, "bundles", "SOURCE_ONLY_BUNDLES.json"),
                                  (old.OUT / "SOURCE_DEV_ROWS.json", "rows", "SOURCE_ONLY_ROWS.json")):
        records = [r for r in read(original)[key] if r["site"] in set("12345") and r["split"] == "source"]
        write(target, {key: records, "source_path": original.relative_to(ROOT).as_posix(),
                       "source_sha256": digest(original), "filter_before_endpoint_access": True})
    source_rows = read(OUT / "SOURCE_ONLY_ROWS.json")["rows"]
    source_bundles = read(DATA)["bundles"]
    assert len(source_rows) == 5997 and len(source_bundles) == 1119
    assert all(r["ead"] in (0., 1.) for r in source_rows)
    assert all(np.isfinite(r["ddfpdc_available_fraction"]) and 0 <= r["ddfpdc_available_fraction"] <= 1 for r in source_bundles)
    assert all(np.isfinite(r["ead_mean"]) and 0 <= r["ead_mean"] <= 1 for r in source_bundles)
    meta = metadata()
    manifest = make_manifest(meta)
    write("QUERY_MANIFEST.json", manifest)
    write("PREPARE_AUDIT.json", {
        "status": "PASS", "predictive_fits": 0, "source_sites": list("12345"),
        "dev_numeric_access": 0, "reserve_numeric_access": 0,
        "converted_source_dev_json_previously_exposed": True,
        "contexts_by_site": {s: sum(k.split("|")[0] == s for k in manifest["contexts"]) for s in "12345"},
        "ordinary_configs": old.configs(), "conditional_configs": conditional_configs(),
        "query_slots": [list(slot) for slot in SLOTS],
        "source_bundle_count": len(source_bundles), "source_exported_row_count": len(source_rows),
        "source_numerical_eligibility": "all exported EAD binary; bundle E/M finite in[0,1]; missing H retained",
        "feature_order": {"conditional": [f"{k}={v}" for k, v in VOCABULARY] +
                            [f"{d}|{c}|{h}" for d, c in SLOTS for h in HEADS] + [f"{d}|{c}|Hvalid" for d, c in SLOTS],
                          "maskonly": [f"{k}={v}" for k, v in VOCABULARY] + [f"{d}|{c}|Hvalid" for d, c in SLOTS],
                          "metadataonly": [f"{k}={v}" for k, v in VOCABULARY]},
        "selection": "outer5LOSO; inner4LOSO equal physical-site combined mean; lexical ties",
        "labels_at_prediction_api": "training source + acquired8; no heldout terminal truth",
    })


def identity(rows):
    assert all(set(r) == set(KEYS) for r in rows)
    assert all(r["site"] in "12345" for r in rows)


class Conditional:
    """One direct drug-dose/head model, trained once across training contexts."""
    def __init__(self, config, source, labels, summary, stage):
        identity(source)
        assert set(labels) == {r["bundle_id"] for r in source}
        self.config, self.scale = config, summary.scale
        self.contexts = old.contexts(source)
        self.training_sites = sorted({r["site"] for r in source})
        self.vocabulary = VOCABULARY
        self.slots = SLOTS
        self.outputs = sorted({(r["drug"], r["dose_code"]) for r in source if r["drug"] not in old.CONTROLS})
        context_rows = list(self.contexts.values())
        raw = np.array([self.features(rows, labels) for rows in context_rows])
        finite = np.isfinite(raw)
        count = finite.sum(axis=0)
        self.imputation = np.divide(np.where(finite, raw, 0).sum(axis=0), count,
                                    out=np.zeros(raw.shape[1]), where=count > 0)
        filled = np.where(finite, raw, self.imputation)
        self.mean = filled.mean(axis=0)
        self.std = filled.std(axis=0)
        self.std[self.std == 0] = 1.
        x = (filled - self.mean) / self.std
        site_counts = {s: sum(rows[0]["site"] == s for rows in context_rows) for s in self.training_sites}
        weights = np.array([1 / (len(site_counts) * site_counts[rows[0]["site"]]) for rows in context_rows])
        assert np.isclose(weights.sum(), 1.)
        PREPROCESSING.append({"stage": stage, "config": config["id"], "source_sites": self.training_sites,
            "source_contexts": list(self.contexts), "context_weights": weights.tolist(), "H_scale": self.scale,
            "imputation": self.imputation.tolist(), "mean": self.mean.tolist(), "population_std": self.std.tolist()})
        by_context = [{(r["drug"], r["dose_code"]): labels[r["bundle_id"]] for r in rows} for rows in context_rows]
        self.models = {}
        for output in self.outputs:
            y = np.array([table.get(output, [None] * 3) for table in by_context], dtype=float)
            y[:, 2] /= self.scale
            for head in range(3):
                valid = np.isfinite(y[:, head])
                n = int(valid.sum())
                start, cpu = time.perf_counter(), time.process_time()
                if n == 0:
                    assert head == 2
                    model = float(summary.global_mean[head] / self.scale)
                    solver = "source-global-H-fallback"
                elif n == 1:
                    model = float(y[valid, head][0])
                    solver = "single-valid-intercept"
                else:
                    model = Ridge(alpha=config["alpha"], solver="cholesky", fit_intercept=True)
                    model.fit(x[valid], y[valid, head], sample_weight=weights[valid])
                    solver = "ridge"
                self.models[(output, head)] = model
                CONDITIONAL_FITS.append({"stage": stage, "config": config["id"], "drug_dose": list(output),
                    "head": HEADS[head], "source_sites": self.training_sites, "n_training_contexts": len(x),
                    "n_training_valid": n, "valid_weight_sum": float(weights[valid].sum()), "solver": solver,
                    "cpu_seconds": time.process_time() - cpu, "wall_seconds": time.perf_counter() - start})

    def features(self, rows, labels):
        identity(rows)
        assert len({(r["site"], r["cell"], r["platform"]) for r in rows}) == 1
        query = {(r["drug"], r["dose_code"]): r for r in rows
                 if r["drug"] in old.CONTROLS and r["dose_code"] in ("1", "4")}
        assert set(query) == set(self.slots)
        values = np.array([labels[query[key]["bundle_id"]] for key in self.slots], dtype=float)
        values[:, 2] /= self.scale
        meta = [float(rows[0][k] == value) for k, value in self.vocabulary]
        mask = np.isfinite(values[:, 2]).astype(float).tolist()
        if self.config["family"] == "metadataonly":
            return meta
        if self.config["family"] == "maskonly":
            return meta + mask
        return meta + values.ravel().tolist() + mask

    def predict(self, paid, paid_labels, terminal):
        identity(paid + terminal)
        assert set(paid_labels) == {r["bundle_id"] for r in paid}
        assert len(paid) == 8 and not ({r["bundle_id"] for r in paid} & {r["bundle_id"] for r in terminal})
        assert not ({r["site"] for r in paid + terminal} & set(self.training_sites))
        raw = np.array(self.features(paid, paid_labels))
        x = ((np.where(np.isfinite(raw), raw, self.imputation) - self.mean) / self.std).reshape(1, -1)
        result = np.empty((len(terminal), 3))
        for i, row in enumerate(terminal):
            for head in range(3):
                model = self.models[((row["drug"], row["dose_code"]), head)]
                result[i, head] = model if isinstance(model, float) else float(model.predict(x)[0])
        result[:, 2] *= self.scale
        return old.bounded(result)


def fold_predictions(source, labels, heldout, feedback, manifest, dictionary, stage, configs):
    """No heldout terminal labels enter this function."""
    identity(source + heldout)
    assert not ({r["site"] for r in source} & {r["site"] for r in heldout})
    summary = old.Summary(source, labels, stage)
    nested = old.nested_vectors(source, labels, stage)
    index = {r["bundle_id"]: r for r in heldout}
    models = {c["id"]: Conditional(c, source, labels, summary, stage) for c in configs if c["family"] in ("conditional", "maskonly", "metadataonly")}
    output = {}
    for context, rows in old.contexts(heldout).items():
        cm = manifest["contexts"][context]
        paid = old.rows_by_ids(cm["metadata_policies"]["fixed"], index)
        paid_labels = {r["bundle_id"]: feedback[r["bundle_id"]] for r in paid}
        terminal = old.rows_by_ids(cm["terminal"], index)
        predictions = {}
        for config in configs:
            if config["id"] in models:
                p = models[config["id"]].predict(paid, paid_labels, terminal)
            else:
                p = old.predict(config, source, labels, paid, paid_labels, terminal, summary, dictionary, stage, context, nested)
            predictions[config["id"]] = p.tolist()
        output[context] = {"bundle_ids": cm["terminal"], "predictions": predictions}
    return output, summary, nested


def site_scores(predictions, labels, scale):
    truth, pred = [], defaultdict(list)
    for item in predictions.values():
        truth.extend(labels[bid] for bid in item["bundle_ids"])
        for cid, values in item["predictions"].items():
            pred[cid].extend(values)
    return {cid: old.losses(np.array(values), truth, scale) for cid, values in pred.items()}


def choose_configs(scores):
    configs = old.configs() + conditional_configs()
    mean = {c["id"]: float(np.mean([s[c["id"]]["combined"] for s in scores.values()])) for c in configs}
    def choose(candidates):
        return min(candidates, key=lambda c: (mean[c["id"]], c["id"]))
    by_family = {f: choose([c for c in configs if c["family"] == f]) for f in sorted({c["family"] for c in configs})}
    ordinary = old.configs()
    return {"inner_site_scores": scores, "mean_physical_site_combined": mean, "families": by_family,
            "sourcebest": by_family["lookup"],
            "strongrefit": choose([c for c in ordinary if c["family"] in ("ridge", "augmented", "trees")]),
            "overallupdater": choose([c for c in ordinary if c["family"] != "lookup"])}


def portfolio(candidates, source, labels, paid, paid_labels, terminal, summary, dictionary, context, nested, stage):
    index = {r["bundle_id"]: r for r in paid}
    folds = old.portfolio_folds(list(index))
    scores, predictions = {}, {}
    for config in candidates:
        heldout_predictions, fold_scores = [], []
        for f, validation_ids in enumerate(folds):
            validation = old.rows_by_ids(validation_ids, index)
            training = [r for r in paid if r["bundle_id"] not in validation_ids]
            training_labels = {r["bundle_id"]: paid_labels[r["bundle_id"]] for r in training}
            p = old.predict(config, source, labels, training, training_labels, validation, summary, dictionary,
                            f"{stage}:portfolio_fold_{f}", context, nested)
            fold_scores.append(old.losses(p, [paid_labels[r["bundle_id"]] for r in validation], summary.scale))
            heldout_predictions.append({"bundle_ids": validation_ids, "predictions": p.tolist()})
        scores[config["id"]] = {"folds": fold_scores, "mean": float(np.mean([s["combined"] for s in fold_scores]))}
        predictions[config["id"]] = heldout_predictions
    choice = min(candidates, key=lambda c: (scores[c["id"]]["mean"], c["id"]))
    p = old.predict(choice, source, labels, paid, paid_labels, terminal, summary, dictionary, stage + ":portfolio_final", context, nested)
    return p, {"choice": choice, "candidate_scores": scores, "folds": folds, "all_control_cv_predictions": predictions}


def verify_freeze():
    seal = read(OUT / "FREEZE.json")
    needed = [CODE, CODE.parent / "test_boundaries.py", PREDECESSOR, DATA, OUT / "SOURCE_ONLY_ROWS.json",
              OUT / "PROTOCOL.md", OUT / "QUERY_MANIFEST.json", OUT / "PREPARE_AUDIT.json",
              old.OUT / "ENDPOINT_INPUT_SEAL.json", old.OUT / "ENDPOINT_ARTIFACT_SEAL.json"]
    for path in needed:
        assert path.relative_to(ROOT).as_posix() in seal["files"], f"Not frozen: {path}"
    for name, expected in seal["files"].items():
        assert digest(ROOT / name) == expected, f"Frozen file changed: {name}"
    return digest(OUT / "FREEZE.json")


def fit_predict():
    freeze_hash = verify_freeze()
    assert not (OUT / "FORECASTS.json").exists() and not (OUT / "FORECAST_SEAL.json").exists()
    start, cpu = time.perf_counter(), time.process_time()
    meta = metadata()
    manifest = read(OUT / "QUERY_MANIFEST.json")
    assert make_manifest(meta) == manifest
    dictionary = old.make_dictionary(meta)
    choices, inner_predictions, forecasts, feedback, portfolios = {}, {}, {}, {}, {}
    all_configs = old.configs() + conditional_configs()
    for outer_site in "12345":
        source = [r for r in meta if r["site"] != outer_site]
        labels = labels_for(r["bundle_id"] for r in source)
        inner_scores, inner_predictions[outer_site] = {}, {}
        for inner_site in sorted({r["site"] for r in source}):
            training = [r for r in source if r["site"] != inner_site]
            train_labels = {r["bundle_id"]: labels[r["bundle_id"]] for r in training}
            heldout = [r for r in source if r["site"] == inner_site]
            query_ids = [bid for c, cm in manifest["contexts"].items() if c.split("|")[0] == inner_site for bid in cm["metadata_policies"]["fixed"]]
            paid_labels = {bid: labels[bid] for bid in query_ids}
            output, summary, _ = fold_predictions(training, train_labels, heldout, paid_labels, manifest, dictionary,
                                                  f"outer_{outer_site}:inner_{inner_site}", all_configs)
            inner_predictions[outer_site][inner_site] = {"scale": summary.scale, "contexts": output}
            inner_scores[inner_site] = site_scores(output, labels, summary.scale)
        choice = choose_configs(inner_scores)
        choices[outer_site] = choice
        heldout = [r for r in meta if r["site"] == outer_site]
        query_ids = [bid for c, cm in manifest["contexts"].items() if c.split("|")[0] == outer_site for bid in cm["metadata_policies"]["fixed"]]
        paid_labels = labels_for(query_ids)
        feedback[outer_site] = [{"bundle_id": bid, "targets_EMH": paid_labels[bid]} for bid in query_ids]
        selected_configs = {c["id"]: c for c in choice["families"].values()}
        output, summary, nested = fold_predictions(source, labels, heldout, paid_labels, manifest, dictionary,
                                                   f"outer_{outer_site}:forecast", list(selected_configs.values()))
        candidates = [choice["families"][f] for f in sorted({c["family"] for c in old.configs()})]
        index = {r["bundle_id"]: r for r in heldout}
        for context, item in output.items():
            raw = item["predictions"]
            selected = {f"fixed:{f}": raw[c["id"]] for f, c in choice["families"].items()}
            selected["fixed:strongrefit"] = raw[choice["strongrefit"]["id"]]
            selected["fixed:overallupdater"] = raw[choice["overallupdater"]["id"]]
            selected["fixed:mixture"] = old.bounded(.5 * np.array(raw[choice["sourcebest"]["id"]]) +
                                                      .5 * np.array(raw[choice["strongrefit"]["id"]])).tolist()
            paid = old.rows_by_ids(manifest["contexts"][context]["metadata_policies"]["fixed"], index)
            pl = {r["bundle_id"]: paid_labels[r["bundle_id"]] for r in paid}
            terminal = old.rows_by_ids(item["bundle_ids"], index)
            p, portfolios[context] = portfolio(candidates, source, labels, paid, pl, terminal, summary, dictionary,
                                               context, nested, f"outer_{outer_site}")
            selected["fixed:portfolio"] = p.tolist()
            item["all_candidate_predictions"] = raw
            item["predictions"] = selected
        forecasts[outer_site] = {"scale": summary.scale, "contexts": output}
        print(f"outer {outer_site} complete; ordinary fits={len(old.FITS)}, conditional fits={len(CONDITIONAL_FITS)}", flush=True)
    write("SOURCE_CHOICES.json", choices)
    write("INNER_CV_PREDICTIONS.json", inner_predictions)
    write("QUERY_FEEDBACK.json", feedback)
    write("PORTFOLIO_CHOICES.json", portfolios)
    write("FORECASTS.json", {"head_order": list(HEADS), "outer_sites": forecasts})
    write("FIT_COUNTS.json", {"ordinary_fits": old.FITS, "conditional_fits": CONDITIONAL_FITS,
        "ordinary_head_solver_fit_count": len(old.FITS),
        "conditional_head_solver_fit_count": sum(r["solver"] == "ridge" for r in CONDITIONAL_FITS),
        "conditional_head_construction_count": len(CONDITIONAL_FITS), "summary_constructions": old.SUMMARIES,
        "conditional_dispatch_counts": {solver: sum(r["solver"] == solver for r in CONDITIONAL_FITS)
                                        for solver in ("ridge", "single-valid-intercept", "source-global-H-fallback")},
        "conditional_preprocessing": PREPROCESSING,
        "total_cpu_seconds": time.process_time() - cpu, "total_wall_seconds": time.perf_counter() - start,
        "query_cost_per_physical_site": {s: 8 * sum(c.split("|")[0] == s for c in manifest["contexts"]) for s in "12345"},
        "tree_seed": 104729, "tree_n_jobs": 2, "blas_threads": 1,
        "dev_numeric_access": 0, "reserve_numeric_access": 0})
    files = ("SOURCE_CHOICES.json", "INNER_CV_PREDICTIONS.json", "QUERY_FEEDBACK.json", "PORTFOLIO_CHOICES.json", "FORECASTS.json", "FIT_COUNTS.json")
    write("FORECAST_SEAL.json", {"freeze_sha256": freeze_hash, "files": {n: digest(OUT / n) for n in files},
        "outer_terminal_truth_extracted_for_scoring": False,
        "source_terminal_truth_used_for_nested_training_and_inner_selection": True})


def score():
    verify_freeze()
    seal = read(OUT / "FORECAST_SEAL.json")
    assert seal["freeze_sha256"] == digest(OUT / "FREEZE.json")
    for name, expected in seal["files"].items():
        assert digest(OUT / name) == expected
    forecasts = read(OUT / "FORECASTS.json")
    scores, pooled_predictions, pooled_truth, raw_h_errors = {}, defaultdict(list), [], defaultdict(list)
    for site, item in forecasts["outer_sites"].items():
        ids = [bid for context in item["contexts"].values() for bid in context["bundle_ids"]]
        labels = labels_for(ids)
        scores[site] = site_scores(item["contexts"], labels, item["scale"])
        for context in item["contexts"].values():
            truth = np.array([labels[bid] for bid in context["bundle_ids"]], dtype=float)
            normalized_truth = truth.copy()
            normalized_truth[:, 2] /= item["scale"]
            pooled_truth.extend(normalized_truth.tolist())
            for method, values in context["predictions"].items():
                p = np.array(values)
                valid = np.isfinite(truth[:, 2])
                raw_h_errors[method].extend(np.abs(p[valid, 2] - truth[valid, 2]).tolist())
                p[:, 2] /= item["scale"]
                pooled_predictions[method].extend(p.tolist())
    methods = sorted(scores["1"])
    aggregate = {m: {"combined": float(np.mean([scores[s][m]["combined"] for s in "12345"])),
                    "components": {h: float(np.mean([scores[s][m]["components"][h] for s in "12345"])) for h in HEADS}}
                 for m in methods}
    pooled = {m: old.losses(np.array(p), pooled_truth, 1.) for m, p in pooled_predictions.items()}
    for method, item in pooled.items():
        item["raw_H_MAE"] = float(np.mean(raw_h_errors[method]))
    comparisons = {}
    for candidate in ("fixed:conditional", "fixed:maskonly", "fixed:metadataonly"):
        comparisons[candidate] = {}
        for comparator in methods:
            differences = {s: scores[s][candidate]["combined"] - scores[s][comparator]["combined"] for s in "12345"}
            comparisons[candidate][comparator] = {"site_differences": differences,
                "mean_difference": aggregate[candidate]["combined"] - aggregate[comparator]["combined"],
                "component_differences": {h: aggregate[candidate]["components"][h] - aggregate[comparator]["components"][h] for h in HEADS},
                "pooled_component_differences": {h: pooled[candidate]["components"][h] - pooled[comparator]["components"][h] for h in HEADS},
                "leave_one_site_out_mean_differences": {s: float(np.mean([d for t, d in differences.items() if s != t])) for s in "12345"}}
    ordinary = ["fixed:" + f for f in sorted({c["family"] for c in old.configs()})] + ["fixed:mixture", "fixed:portfolio"]
    best_ordinary = min(ordinary, key=lambda m: (aggregate[m]["combined"], m))
    reference_gates = {}
    for reference in (best_ordinary, "fixed:maskonly", "fixed:metadataonly"):
        c = comparisons["fixed:conditional"][reference]
        reference_gates[reference] = {
            "absolute_gain_at_least_0.005": c["mean_difference"] <= -.005,
            "pooled_components_nonworse_epsilon_1e-12": all(d <= 1e-12 for d in c["pooled_component_differences"].values()),
            "at_least_four_sites_better": sum(d < -1e-12 for d in c["site_differences"].values()) >= 4,
            "every_delete_one_site_mean_better": all(d < -1e-12 for d in c["leave_one_site_out_mean_differences"].values())}
    gate = all(all(checks.values()) for checks in reference_gates.values())
    write("TERMINAL_SCORES.json", {"by_physical_site": scores, "equal_physical_site": aggregate,
        "pooled_equal_bundles": pooled, "comparisons": comparisons,
        "best_prespecified_ordinary_comparator": best_ordinary, "information_gate_by_reference": reference_gates,
        "information_gate": gate, "score_after_forecast_seal": True,
        "interpretation": "exploratory ordinary source-only nested replay; five physical environments; no confirmation or novelty claim"})
    write("SCORE_SEAL.json", {"forecast_seal_sha256": digest(OUT / "FORECAST_SEAL.json"), "scores_sha256": digest(OUT / "TERMINAL_SCORES.json")})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("prepare", "fit_predict", "score"))
    args = parser.parse_args()
    with threadpool_limits(limits=1, user_api="blas"):
        {"prepare": prepare, "fit_predict": fit_predict, "score": score}[args.phase]()
