"""Post-score independent Decimal audit, starting from exported individual rows.

Never imports model_probe, reads aggregate bundle targets, or fits a predictor.
Run only after root has confirmed completion of the separate terminal scorer.
"""
import argparse
from collections import Counter, defaultdict
from decimal import Decimal, getcontext
from hashlib import sha256
import json
from pathlib import Path


getcontext().prec = 50
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/cipa_control_information"
HEADS = ("E", "M", "H")
CONTROLS = {"Dofetilide", "Nifedipine", "Mexiletine", "Ranolazine"}
EXPECTED_FREEZE = "3c04d5d7bb1cc88784f5ba41710253cdde00a1943f42a4f0b7a6d2cff70ff558"
ZERO, ONE = Decimal(0), Decimal(1)
TOL = Decimal("1e-9")
DIFFS = []
CONSTANT_COLUMN_ROUNDOFF = []


def read(name):
    return json.loads((OUT / name).read_text(encoding="utf-8-sig"), parse_float=Decimal)


def digest(path):
    with path.open("rb") as handle:
        return sha256(handle.read()).hexdigest()


def dec(value):
    return value if isinstance(value, Decimal) else Decimal(str(value))


def close(actual, expected, label):
    if actual is None or expected is None:
        assert actual is expected, (label, actual, expected)
        return
    error = abs(dec(actual) - dec(expected))
    DIFFS.append(error)
    assert error <= TOL * max(ONE, abs(dec(expected))), (label, str(error))


def mean(values):
    values = list(values)
    return sum(values, ZERO) / len(values) if values else None


def key(row):
    return "|".join(row[k] for k in ("site", "cell", "platform", "drug", "dose_code"))


def context(bid):
    return "|".join(bid.split("|")[:3])


def quantile(values, fraction):
    ordered = sorted(values)
    index = Decimal(len(ordered) - 1) * fraction
    low = int(index)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (index - low)


def source_scale(targets, sites):
    values = [y[2] for bid, y in targets.items() if bid.split("|")[0] in sites and y[2] is not None]
    assert values
    scale = quantile(values, Decimal(".75")) - quantile(values, Decimal(".25"))
    if scale <= 0:
        center = mean(values)
        scale = mean((x - center) ** 2 for x in values).sqrt()
    return scale if scale > 0 else ONE


def endpoint_rows():
    grouped = defaultdict(list)
    for row in read("SOURCE_ONLY_ROWS.json")["rows"]:
        assert row["site"] in "12345"
        assert row["split"] == "source"
        for field in ("ead", "ddfpdc"):
            assert row[field + "_status"] in ("valid", "missing")
        assert row["ead_status"] == "valid"
        grouped[key(row)].append(row)
    targets = {}
    for bid, rows in grouped.items():
        e = [Decimal(r["ead_raw"]["text"]) for r in rows if r["ead_status"] == "valid"]
        h = [Decimal(r["ddfpdc_raw"]["text"]) for r in rows if r["ddfpdc_status"] == "valid"]
        assert all(y in (ZERO, ONE) for y in e)
        assert all(y.is_finite() for y in e + h)
        targets[bid] = [mean(e), Decimal(len(h)) / len(rows), mean(h)]
    return grouped, targets


def row_scores(ids, predictions, grouped, scale):
    """Brier is computed per individual row, then averaged per bundle."""
    assert len(ids) == len(predictions)
    pieces = {head: [] for head in HEADS}
    raw_h = []
    for bid, prediction in zip(ids, predictions):
        p = [dec(x) for x in prediction]
        assert len(p) == 3 and all(x.is_finite() for x in p)
        assert all(ZERO <= x <= ONE for x in p[:2])
        rows = grouped[bid]
        e = [Decimal(r["ead_raw"]["text"]) for r in rows if r["ead_status"] == "valid"]
        if e:
            pieces["E"].append(mean((p[0] - y) ** 2 for y in e))
        pieces["M"].append(mean((p[1] - (ONE if r["ddfpdc_status"] == "valid" else ZERO)) ** 2 for r in rows))
        h = [Decimal(r["ddfpdc_raw"]["text"]) for r in rows if r["ddfpdc_status"] == "valid"]
        if h:
            error = abs(p[2] - mean(h))
            raw_h.append(error)
            pieces["H"].append(error / (scale[bid] if isinstance(scale, dict) else scale))
    components = {head: mean(values) for head, values in pieces.items()}
    return {"components": components,
            "combined": mean(x for x in components.values() if x is not None),
            "raw_H_MAE": mean(raw_h),
            "coverage": {head: {"valid": len(values), "total": len(ids)} for head, values in pieces.items()}}


def compare_score(actual, expected, label):
    for head in HEADS:
        close(actual["components"][head], expected["components"][head], label + ":" + head)
    close(actual["combined"], expected["combined"], label + ":combined")
    close(actual["raw_H_MAE"], expected["raw_H_MAE"], label + ":rawH")
    assert actual["coverage"] == expected["coverage"], label + ":coverage"


SITES = set("12345")
VOCABULARY = [("cell", c) for c in ("AXG", "CDI")] + [("platform", p) for p in ("AXN", "CLY", "ECR", "MCS")]
SLOTS = sorted((d, c) for d in CONTROLS for c in ("1", "4"))
ORDINARY_FAMILIES = {"lookup", "offset", "affine", "multivariate", "ridge", "augmented", "trees"}
CONDITIONAL_FAMILIES = {"conditional", "maskonly", "metadataonly"}


def configs():
    result = [{"id": "lookup:" + mode, "family": "lookup", "mode": mode}
              for mode in ("all", "cell", "cell_platform")]
    for family in ("offset", "affine", "multivariate"):
        result.extend({"id": f"{family}:k{k}", "family": family, "kappa": k} for k in (1, 8, 32))
    for family in ("ridge", "augmented"):
        result.extend({"id": f"{family}:a{a}:w{w}", "family": family, "alpha": dec(a), "weight": w}
                      for a in ("0.1", "10", "100") for w in (1, 8))
    result.extend({"id": f"trees:l{leaf}:w{w}", "family": "trees", "leaf": leaf, "weight": w}
                  for leaf in (1, 4) for w in (1, 8))
    return sorted(result, key=lambda c: c["id"]) + [
        {"id": f"{family}:a{a}", "family": family, "alpha": a}
        for family in ("conditional", "maskonly", "metadataonly") for a in (1, 32)]


def verify_seals():
    assert digest(OUT / "FREEZE.json") == EXPECTED_FREEZE
    freeze = read("FREEZE.json")
    assert len(freeze["files"]) == 29
    for name, expected in freeze["files"].items():
        assert digest(ROOT / name) == expected, name
    prior = ROOT / "log/20261022/cipa_calibration_probe"
    for name, expected in json.loads((prior / "ENDPOINT_ARTIFACT_SEAL.json").read_text()).items():
        assert digest(prior / name) == expected, name
    for record in json.loads((prior / "ENDPOINT_INPUT_SEAL.json").read_text()).values():
        assert digest(ROOT / record["path"]) == record["sha256"], record["path"]
    for name in ("SOURCE_ONLY_ROWS.json",):
        # Source container provenance is checked without decoding predecessor dev endpoints.
        record = read(name)
        assert digest(ROOT / record["source_path"]) == record["source_sha256"]
        assert record["filter_before_endpoint_access"] is True
    forecast = read("FORECAST_SEAL.json")
    assert forecast["freeze_sha256"] == EXPECTED_FREEZE
    assert forecast["outer_terminal_truth_extracted_for_scoring"] is False
    assert forecast["source_terminal_truth_used_for_nested_training_and_inner_selection"] is True
    for name, expected in forecast["files"].items():
        assert digest(OUT / name) == expected, name
    score = read("SCORE_SEAL.json")
    assert score["forecast_seal_sha256"] == digest(OUT / "FORECAST_SEAL.json")
    assert score["scores_sha256"] == digest(OUT / "TERMINAL_SCORES.json")
    return len(freeze["files"])


def balanced(ids):
    ordered = sorted(ids, key=lambda bid: (sha256(bid.encode()).hexdigest(), bid))
    return [ordered[f::4] for f in range(4)]


def audit_manifest(manifest, grouped, targets):
    assert len(grouped) == len(targets) == 1119
    assert sum(map(len, grouped.values())) == 5997
    contexts = {context(bid) for bid in grouped}
    assert len(contexts) == 10 and set(manifest["contexts"]) == contexts
    assert Counter(c.split("|")[0] for c in contexts) == Counter({s: 2 for s in SITES})
    all_drugs = {bid.split("|")[3] for bid in grouped}
    assert len(all_drugs) == 28 and manifest["control_drugs"] == sorted(CONTROLS)
    assert manifest["budget_per_context"] == 8
    for ctx, cm in manifest["contexts"].items():
        bids = sorted(bid for bid in grouped if context(bid) == ctx)
        pool = [bid for bid in bids if bid.split("|")[3] in CONTROLS]
        terminal = [bid for bid in bids if bid.split("|")[3] not in CONTROLS]
        paid = [ctx + "|" + d + "|" + code for d, code in SLOTS]
        assert cm["pool"] == pool and cm["terminal"] == terminal
        assert cm["metadata_policies"] == {"fixed": paid}
        assert cm["portfolio_folds"] == balanced(paid)
        assert len(pool) == 16 and len(terminal) == (95 if ctx == "3|CDI|MCS" else 96)
        assert set(paid) <= set(pool) and not set(terminal) & set(pool)
        assert len({bid.split("|")[3] for bid in terminal}) == 24
        expected = {ctx + "|" + d + "|" + str(c) for d in all_drugs for c in range(1, 5)}
        if ctx == "3|CDI|MCS":
            expected.remove("3|CDI|MCS|Ibutilide|1")
        assert set(bids) == expected
    assert "3|CDI|MCS|Ibutilide|1" not in grouped


def rescore_contexts(contexts, grouped, scale, expected_site=None):
    ids, predictions = [], defaultdict(list)
    for ctx, item in contexts.items():
        if expected_site is not None:
            assert ctx.split("|")[0] == expected_site
        assert item["bundle_ids"] == MANIFEST["contexts"][ctx]["terminal"]
        ids.extend(item["bundle_ids"])
        for cid, p in item["predictions"].items():
            predictions[cid].extend(p)
    return {cid: row_scores(ids, p, grouped, scale) for cid, p in predictions.items()}


def audit_constant_predictions(contexts, targets, sites, candidate_field="predictions"):
    """Check intercept/fallback dispatch outputs directly, without a predictive solve."""
    source = {bid: y for bid, y in targets.items() if bid.split("|")[0] in sites}
    global_mean = [mean(y[h] for y in source.values() if y[h] is not None) for h in range(3)]
    for item in contexts.values():
        for cid, predictions in item[candidate_field].items():
            if cid.split(":")[0] not in CONDITIONAL_FAMILIES:
                continue
            for bid, p in zip(item["bundle_ids"], predictions):
                drug_dose = bid.split("|")[3:]
                for h in range(3):
                    valid = [y[h] for source_bid, y in source.items() if source_bid.split("|")[3:] == drug_dose and y[h] is not None]
                    if len(valid) <= 1:
                        expected = valid[0] if valid else global_mean[h]
                        if h < 2:
                            expected = min(ONE, max(ZERO, expected))
                        close(p[h], expected, "constant or global fallback forecast")


def audit_inner(choices, inner, grouped, targets, all_configs):
    assert set(choices) == set(inner) == SITES
    for outer, cv in inner.items():
        choice = choices[outer]
        assert set(cv) == SITES - {outer}
        actual_scores = {}
        for heldout, entry in cv.items():
            scale = source_scale(targets, SITES - {outer, heldout})
            close(entry["scale"], scale, "inner IQR")
            assert set(entry["contexts"]) == {c for c in MANIFEST["contexts"] if c.split("|")[0] == heldout}
            for item in entry["contexts"].values():
                assert set(item["predictions"]) == {c["id"] for c in all_configs}
            actual_scores[heldout] = rescore_contexts(entry["contexts"], grouped, scale, heldout)
            audit_constant_predictions(entry["contexts"], targets, SITES - {outer, heldout})
            for cid, expected in actual_scores[heldout].items():
                compare_score(choice["inner_site_scores"][heldout][cid], expected, "inner:" + outer + ":" + heldout + ":" + cid)
        means = {c["id"]: mean(actual_scores[s][c["id"]]["combined"] for s in actual_scores) for c in all_configs}
        assert set(choice["mean_physical_site_combined"]) == set(means)
        for cid, expected in means.items():
            close(choice["mean_physical_site_combined"][cid], expected, "inner selection mean")
        def best(candidates):
            return min(candidates, key=lambda c: (means[c["id"]], c["id"]))
        assert set(choice["families"]) == ORDINARY_FAMILIES | CONDITIONAL_FAMILIES
        for family, config in choice["families"].items():
            assert config == best(c for c in all_configs if c["family"] == family)
        assert choice["sourcebest"] == choice["families"]["lookup"]
        assert choice["strongrefit"] == best(c for c in all_configs if c["family"] in {"ridge", "augmented", "trees"})
        assert choice["overallupdater"] == best(c for c in all_configs if c["family"] in ORDINARY_FAMILIES - {"lookup"})


def audit_portfolios(programs, choices, grouped, targets):
    assert set(programs) == set(MANIFEST["contexts"])
    for ctx, item in programs.items():
        site = ctx.split("|")[0]
        paid = MANIFEST["contexts"][ctx]["metadata_policies"]["fixed"]
        folds = balanced(paid)
        assert item["folds"] == folds and all(len(f) == 2 for f in folds)
        candidates = {c["id"]: c for f, c in choices[site]["families"].items() if f in ORDINARY_FAMILIES}
        assert set(item["candidate_scores"]) == set(item["all_control_cv_predictions"]) == set(candidates)
        means = {}
        for cid, entry in item["candidate_scores"].items():
            saved = item["all_control_cv_predictions"][cid]
            assert len(saved) == len(entry["folds"]) == 4
            independent = []
            for f, (ids, prediction, score) in enumerate(zip(folds, saved, entry["folds"])):
                assert prediction["bundle_ids"] == ids
                reconstructed = row_scores(ids, prediction["predictions"], grouped, source_scale(targets, SITES - {site}))
                compare_score(score, reconstructed, "portfolio:" + ctx + ":" + cid + ":" + str(f))
                independent.append(reconstructed["combined"])
            means[cid] = mean(independent)
            close(entry["mean"], means[cid], "portfolio mean")
        assert item["choice"] == candidates[min(means, key=lambda cid: (means[cid], cid))]


def audit_preprocessing(record, config, sites, targets):
    contexts = sorted({context(bid) for bid in targets if bid.split("|")[0] in sites})
    assert record["source_contexts"] == contexts
    assert record["source_sites"] == sorted(sites)
    scale = source_scale(targets, sites)
    close(record["H_scale"], scale, "feature H IQR")
    weights = [ONE / len(contexts)] * len(contexts)
    assert len(record["context_weights"]) == len(weights)
    for actual, expected in zip(record["context_weights"], weights):
        close(actual, expected, "context weight")
    raw = []
    for ctx in contexts:
        _, cell, platform = ctx.split("|")
        metadata = {"cell": cell, "platform": platform}
        values = [targets[ctx + "|" + d + "|" + code] for d, code in SLOTS]
        masks = [ONE if y[2] is not None else ZERO for y in values]
        meta = [ONE if metadata[k] == value else ZERO for k, value in VOCABULARY]
        if config["family"] == "metadataonly":
            row = meta
        elif config["family"] == "maskonly":
            row = meta + masks
        else:
            row = meta + [v if h < 2 or v is None else v / scale for y in values for h, v in enumerate(y)] + masks
        raw.append(row)
    imputations = [mean(v for v in col if v is not None) for col in zip(*raw)]
    imputations = [ZERO if v is None else v for v in imputations]
    filled = [[imputations[i] if v is None else v for i, v in enumerate(row)] for row in raw]
    means = [mean(col) for col in zip(*filled)]
    # Detect constant columns before finite-precision Decimal averaging; repeating
    # decimal division can otherwise create a spurious variance near 1e-100.
    stds = [ZERO if min(col) == max(col) else mean((v - center) ** 2 for v in col).sqrt()
            for center, col in zip(means, zip(*filled))]
    stds = [v if v > 0 else ONE for v in stds]
    for name, expected in (("imputation", imputations), ("mean", means), ("population_std", stds)):
        assert len(record[name]) == len(expected)
        for index, (a, b) in enumerate(zip(record[name], expected)):
            if name == "population_std" and b == ONE and ZERO < a < Decimal("1e-12"):
                col = [row[index] for row in filled]
                assert min(col) == max(col), "Tiny-std exception only for an exactly constant Decimal column"
                v = float(record["imputation"][index])
                floating_mean = sum([v] * len(contexts)) / len(contexts)
                floating_std = ((v - floating_mean) ** 2) ** .5
                assert abs(a - dec(floating_std)) <= Decimal("1e-25")
                close(record["mean"][index], floating_mean, "constant-column float mean")
                transformed = (v - float(record["mean"][index])) / float(a)
                checked_heads, all_exact_zero = 0, True
                conditions = {tuple(bid.split("|")[3:]) for bid in targets if bid.split("|")[0] in sites and bid.split("|")[3] not in CONTROLS}
                for drug, dose in conditions:
                    for h in range(3):
                        valid = [ctx for ctx in contexts if targets.get(ctx + "|" + drug + "|" + dose, [None]*3)[h] is not None]
                        if len(valid) >= 2:
                            weight = 1. / len(contexts)
                            center = sum(weight * transformed for _ in valid) / sum(weight for _ in valid)
                            all_exact_zero &= all(transformed - center == 0. for _ in valid)
                            checked_heads += 1
                assert all_exact_zero, "A nonzero centered training column would invalidate the zero-coefficient implication"
                heldout = {}
                if 6 <= index < 30 and (index - 6) % 3 == 2:
                    drug, dose = SLOTS[(index - 6) // 3]
                    for ctx in sorted({context(bid) for bid in targets if bid.split("|")[0] not in sites}):
                        value = targets[ctx + "|" + drug + "|" + dose][2]
                        input_value = v if value is None else float(value) / float(scale)
                        heldout[ctx] = (input_value - float(record["mean"][index])) / float(a)
                CONSTANT_COLUMN_ROUNDOFF.append({"stage": record["stage"], "config": record["config"], "column": index,
                    "mathematical_population_std": ZERO, "declared_zero_std_fallback": ONE, "saved_float_std": a,
                    "saved_imputation": record["imputation"][index], "saved_mean": record["mean"][index],
                    "training_standardized_constant": transformed, "ridge_heads_with_exact_zero_centered_column": checked_heads,
                    "heldout_standardized_inputs": heldout,
                    "coefficient_implication": "All observed-head subsets center this column to exact floating zero. Its centered design cross-products and design-transpose times any finite dual coefficients are exactly zero; ridge coefficient is zero in the stated solver path. Coefficients were not serialized, and no refit was performed."})
                continue
            close(a, b, "preprocessing " + name + ":" + record["stage"] + ":" + config["id"] + ":" + str(index))


def audit_ledger(ledger, choices, programs, targets, all_configs):
    ordinary, conditional, preprocessing, summaries = Counter(), Counter(), Counter(), Counter()
    def summary(stage, sites):
        summaries[(stage, tuple(sorted(sites)), sum(bid.split("|")[0] in sites for bid in targets))] += 1
    def add_ordinary(stage, ctx, config, paid, sites):
        family = config["family"]
        if family == "lookup":
            return
        for h, head in enumerate(HEADS):
            n = sum(targets[bid][h] is not None for bid in paid)
            if family in {"ridge", "augmented", "trees"}:
                n += sum(y[h] is not None for bid, y in targets.items() if bid.split("|")[0] in sites)
            if n:
                ordinary[(stage, ctx, config["id"], head, n)] += 1
    def fold(stage, sites, heldout, candidates):
        summary(stage, sites)
        for site in sorted(sites):
            summary(stage + ":nested_exclude_" + site, sites - {site})
        for config in candidates:
            if config["family"] in CONDITIONAL_FAMILIES:
                preprocessing[(stage, config["id"], tuple(sorted(sites)))] += 1
                outputs = sorted({tuple(bid.split("|")[3:]) for bid in targets if bid.split("|")[0] in sites and bid.split("|")[3] not in CONTROLS})
                contexts = sorted({context(bid) for bid in targets if bid.split("|")[0] in sites})
                for drug, dose in outputs:
                    for h, head in enumerate(HEADS):
                        n = sum(targets.get(ctx + "|" + drug + "|" + dose, [None]*3)[h] is not None for ctx in contexts)
                        solver = "ridge" if n >= 2 else "single-valid-intercept" if n else "source-global-H-fallback"
                        conditional[(stage, config["id"], drug, dose, head, tuple(sorted(sites)), len(contexts), n, solver)] += 1
            else:
                for ctx, cm in MANIFEST["contexts"].items():
                    if ctx.split("|")[0] == heldout:
                        add_ordinary(stage, ctx, config, cm["metadata_policies"]["fixed"], sites)
    for outer in sorted(SITES):
        for inner in sorted(SITES - {outer}):
            fold(f"outer_{outer}:inner_{inner}", SITES - {outer, inner}, inner, all_configs)
        fold(f"outer_{outer}:forecast", SITES - {outer}, outer, list(choices[outer]["families"].values()))
        for ctx, cm in MANIFEST["contexts"].items():
            if ctx.split("|")[0] != outer:
                continue
            paid = cm["metadata_policies"]["fixed"]
            for family in sorted(ORDINARY_FAMILIES):
                config = choices[outer]["families"][family]
                for f, validation in enumerate(balanced(paid)):
                    add_ordinary(f"outer_{outer}:portfolio_fold_{f}", ctx, config, [bid for bid in paid if bid not in validation], SITES - {outer})
            add_ordinary(f"outer_{outer}:portfolio_final", ctx, programs[ctx]["choice"], paid, SITES - {outer})
    actual = Counter((r["stage"], r["context"], r["config"], r["head"], r["n_training_valid"]) for r in ledger["ordinary_fits"])
    assert actual == ordinary, {"ordinary_missing": list((ordinary-actual).items())[:5], "ordinary_extra": list((actual-ordinary).items())[:5]}
    actual = Counter((r["stage"], r["config"], *r["drug_dose"], r["head"], tuple(r["source_sites"]), r["n_training_contexts"], r["n_training_valid"], r["solver"]) for r in ledger["conditional_fits"])
    assert actual == conditional, {"conditional_missing": list((conditional-actual).items())[:5], "conditional_extra": list((actual-conditional).items())[:5]}
    actual = Counter((r["stage"], tuple(r["source_sites"]), r["bundles"]) for r in ledger["summary_constructions"])
    assert actual == summaries
    for r in ledger["summary_constructions"]:
        close(r["scale"], source_scale(targets, set(r["source_sites"])), "summary IQR")
    config_by_id = {c["id"]: c for c in all_configs}
    actual = Counter((r["stage"], r["config"], tuple(r["source_sites"])) for r in ledger["conditional_preprocessing"])
    assert actual == preprocessing
    for r in ledger["conditional_preprocessing"]:
        audit_preprocessing(r, config_by_id[r["config"]], set(r["source_sites"]), targets)
    for r in ledger["ordinary_fits"]:
        assert r["physical_site"] == r["context"].split("|")[0]
        assert r["seed"] == (104729 if r["config"].startswith("trees:") else None)
    for r in ledger["conditional_fits"]:
        close(r["valid_weight_sum"], dec(r["n_training_valid"]) / r["n_training_contexts"], "unrenormalized valid weights")
    for r in ledger["ordinary_fits"] + ledger["conditional_fits"]:
        assert r["cpu_seconds"] >= 0 and r["wall_seconds"] >= 0
    dispatches = Counter(r["solver"] for r in ledger["conditional_fits"])
    assert ledger["ordinary_head_solver_fit_count"] == sum(ordinary.values())
    assert ledger["conditional_head_construction_count"] == sum(conditional.values())
    assert ledger["conditional_head_solver_fit_count"] == dispatches["ridge"]
    assert ledger["conditional_dispatch_counts"] == {s: dispatches[s] for s in ("ridge", "single-valid-intercept", "source-global-H-fallback")}
    assert ledger["query_cost_per_physical_site"] == {s: 16 for s in SITES}
    assert ledger["dev_numeric_access"] == ledger["reserve_numeric_access"] == 0
    assert (ledger["tree_seed"], ledger["tree_n_jobs"], ledger["blas_threads"]) == (104729, 2, 1)
    return {"ordinary_head_solver_fits": sum(ordinary.values()), "conditional_dispatches": dict(dispatches),
            "conditional_head_constructions": sum(conditional.values()), "conditional_preprocessing_records": sum(preprocessing.values()),
            "summary_constructions": sum(summaries.values()),
            "tree_head_fits": sum(r["config"].startswith("trees:") for r in ledger["ordinary_fits"]),
            "trees_per_tree_head_fit": 128,
            "ordinary_fits_by_stage": dict(Counter(r["stage"] for r in ledger["ordinary_fits"])),
            "conditional_dispatches_by_stage": {stage: dict(Counter(r["solver"] for r in ledger["conditional_fits"] if r["stage"] == stage))
                                                for stage in sorted({r["stage"] for r in ledger["conditional_fits"]})}}


def run():
    global MANIFEST
    freeze_count = verify_seals()
    grouped, targets = endpoint_rows()
    MANIFEST = read("QUERY_MANIFEST.json")
    audit_manifest(MANIFEST, grouped, targets)
    all_configs = configs()
    prepared = read("PREPARE_AUDIT.json")
    assert prepared["ordinary_configs"] == [c for c in all_configs if c["family"] in ORDINARY_FAMILIES]
    assert prepared["conditional_configs"] == [c for c in all_configs if c["family"] in CONDITIONAL_FAMILIES]
    assert prepared["predictive_fits"] == prepared["dev_numeric_access"] == prepared["reserve_numeric_access"] == 0
    assert prepared["query_slots"] == [list(slot) for slot in SLOTS]
    meta_order = [f"{k}={v}" for k, v in VOCABULARY]
    mask_order = [f"{d}|{c}|Hvalid" for d, c in SLOTS]
    assert prepared["feature_order"] == {"metadataonly": meta_order, "maskonly": meta_order + mask_order,
        "conditional": meta_order + [f"{d}|{c}|{h}" for d, c in SLOTS for h in HEADS] + mask_order}
    choices = read("SOURCE_CHOICES.json")
    audit_inner(choices, read("INNER_CV_PREDICTIONS.json"), grouped, targets, all_configs)
    programs = read("PORTFOLIO_CHOICES.json")
    audit_portfolios(programs, choices, grouped, targets)
    feedback = read("QUERY_FEEDBACK.json")
    forecasts = read("FORECASTS.json")
    assert forecasts["head_order"] == list(HEADS) and set(forecasts["outer_sites"]) == SITES
    assert set(feedback) == SITES
    scores = read("TERMINAL_SCORES.json")
    bysite, pooled_predictions, pooled_ids, pooled_scales = {}, defaultdict(list), [], {}
    expected_methods = {"fixed:" + f for f in ORDINARY_FAMILIES | CONDITIONAL_FAMILIES} | {
        "fixed:strongrefit", "fixed:overallupdater", "fixed:mixture", "fixed:portfolio"}
    for site, entry in forecasts["outer_sites"].items():
        scale = source_scale(targets, SITES - {site})
        close(entry["scale"], scale, "outer IQR")
        contexts = {ctx for ctx in MANIFEST["contexts"] if ctx.split("|")[0] == site}
        assert set(entry["contexts"]) == contexts
        query_ids = [bid for ctx, cm in MANIFEST["contexts"].items() if ctx in contexts for bid in cm["metadata_policies"]["fixed"]]
        assert [r["bundle_id"] for r in feedback[site]] == query_ids
        for r in feedback[site]:
            for a, b in zip(r["targets_EMH"], targets[r["bundle_id"]]):
                close(a, b, "paid raw-row labels")
        selected = choices[site]["families"]
        for ctx, item in entry["contexts"].items():
            assert set(item["predictions"]) == expected_methods
            assert set(item["all_candidate_predictions"]) == {c["id"] for c in selected.values()}
            for family, config in selected.items():
                assert item["predictions"]["fixed:" + family] == item["all_candidate_predictions"][config["id"]]
            for alias in ("strongrefit", "overallupdater"):
                assert item["predictions"]["fixed:" + alias] == item["all_candidate_predictions"][choices[site][alias]["id"]]
            for mixture, lookup, strong in zip(item["predictions"]["fixed:mixture"], item["predictions"]["fixed:lookup"], item["predictions"]["fixed:strongrefit"]):
                for a, b, c in zip(mixture, lookup, strong):
                    close(a, (b + c) / 2, "fixed half mixture")
            for candidate in item["all_candidate_predictions"].values():
                assert len(candidate) == len(item["bundle_ids"])
                assert all(len(p) == 3 and all(dec(v).is_finite() for v in p) and all(ZERO <= v <= ONE for v in p[:2]) for p in candidate)
            pooled_ids.extend(item["bundle_ids"])
            pooled_scales.update({bid: scale for bid in item["bundle_ids"]})
            for method, prediction in item["predictions"].items():
                pooled_predictions[method].extend(prediction)
        bysite[site] = rescore_contexts(entry["contexts"], grouped, scale, site)
        audit_constant_predictions(entry["contexts"], targets, SITES - {site}, "all_candidate_predictions")
        for method, expected in bysite[site].items():
            compare_score(scores["by_physical_site"][site][method], expected, "outer:" + site + ":" + method)
    assert len(pooled_ids) == len(set(pooled_ids)) == 959
    pooled = {m: row_scores(pooled_ids, p, grouped, pooled_scales) for m, p in pooled_predictions.items()}
    aggregate = {m: {"combined": mean(bysite[s][m]["combined"] for s in sorted(SITES)),
                     "components": {h: mean(bysite[s][m]["components"][h] for s in sorted(SITES)) for h in HEADS}}
                 for m in expected_methods}
    for method, expected in pooled.items():
        compare_score(scores["pooled_equal_bundles"][method], expected, "fold-normalized pooled:" + method)
        close(scores["equal_physical_site"][method]["combined"], aggregate[method]["combined"], "mean site combined")
        for h in HEADS:
            close(scores["equal_physical_site"][method]["components"][h], aggregate[method]["components"][h], "mean site component")
    comparisons = {}
    for candidate in ("fixed:conditional", "fixed:maskonly", "fixed:metadataonly"):
        comparisons[candidate] = {}
        assert set(scores["comparisons"][candidate]) == expected_methods
        for reference in expected_methods:
            differences = {s: bysite[s][candidate]["combined"] - bysite[s][reference]["combined"] for s in sorted(SITES)}
            expected = {"site_differences": differences, "mean_difference": mean(differences.values()),
                "component_differences": {h: aggregate[candidate]["components"][h] - aggregate[reference]["components"][h] for h in HEADS},
                "pooled_component_differences": {h: pooled[candidate]["components"][h] - pooled[reference]["components"][h] for h in HEADS},
                "leave_one_site_out_mean_differences": {s: mean(d for t, d in differences.items() if s != t) for s in sorted(SITES)}}
            actual = scores["comparisons"][candidate][reference]
            close(actual["mean_difference"], expected["mean_difference"], "mean paired difference")
            for field in expected.keys() - {"mean_difference"}:
                assert set(actual[field]) == set(expected[field])
                for key_, value in expected[field].items():
                    close(actual[field][key_], value, "comparison " + field)
            comparisons[candidate][reference] = expected
    ordinary_methods = {"fixed:" + f for f in ORDINARY_FAMILIES} | {"fixed:mixture", "fixed:portfolio"}
    strongest = min(ordinary_methods, key=lambda m: (aggregate[m]["combined"], m))
    assert scores["best_prespecified_ordinary_comparator"] == strongest
    gates = {}
    for reference in (strongest, "fixed:maskonly", "fixed:metadataonly"):
        c = comparisons["fixed:conditional"][reference]
        gates[reference] = {
            "absolute_gain_at_least_0.005": c["mean_difference"] <= Decimal("-.005"),
            "pooled_components_nonworse_epsilon_1e-12": all(d <= Decimal("1e-12") for d in c["pooled_component_differences"].values()),
            "at_least_four_sites_better": sum(d < Decimal("-1e-12") for d in c["site_differences"].values()) >= 4,
            "every_delete_one_site_mean_better": all(d < Decimal("-1e-12") for d in c["leave_one_site_out_mean_differences"].values())}
    gate = all(all(checks.values()) for checks in gates.values())
    assert scores["information_gate_by_reference"] == gates and scores["information_gate"] == gate
    assert scores["score_after_forecast_seal"] is True
    ledger = audit_ledger(read("FIT_COUNTS.json"), choices, programs, targets, all_configs)
    report = {"status": "PASS", "freeze_sha256": EXPECTED_FREEZE, "auditor_sha256": digest(Path(__file__)),
        "method": "50-digit Decimal, individual source-only raw decimal strings; no predictor import, refit, or aggregate bundle-target decoding",
        "frozen_files_verified": freeze_count, "forecast_and_score_seals": "PASS", "terminal_bundles": len(pooled_ids),
        "methods": len(pooled), "independent_physical_sites": 5, "contexts": 10, "raw_exported_rows": 5997,
        "inner_folds": 20, "inner_configurations_per_fold": 34, "outer_selected_families": 10,
        "all_inner_prediction_scores_and_family_selection": "PASS", "all_portfolio_prediction_scores_and_choice": "PASS",
        "source_boundary_ledger_enumeration": "PASS", "preprocessing_and_IQR_reconstruction": "PASS",
        "explicit_float_constant_column_exceptions": CONSTANT_COLUMN_ROUNDOFF,
        "paid_feedback_and_pool_identity": "PASS", "fit_accounting": ledger,
        "max_absolute_numerical_difference": max(DIFFS), "relative_tolerance": TOL,
        "mean_site_combined": {m: aggregate[m]["combined"] for m in sorted(expected_methods)},
        "pooled_combined": {m: pooled[m]["combined"] for m in sorted(expected_methods)},
        "best_prespecified_ordinary_comparator": strongest, "information_gate_by_reference": gates, "information_gate": gate,
        "primary_comparisons": comparisons["fixed:conditional"],
        "limits": "No independent model refits. Saved scores, selection, transforms, masks, exact schedules and bound source exclusions were reconstructed. Sealed code flow supports prediction provenance; this is exploratory reuse of five source sites, not independent biological confirmation, a novel architecture, or RSI."}
    with (OUT / "SCORE_INDEPENDENT_AUDIT.json").open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, default=lambda value: str(value) if isinstance(value, Decimal) else value)
    primary = comparisons["fixed:conditional"][strongest]
    text = ("# Independent postrun review\n\n"
        "Disposition: **PASS — independent raw-row reconstruction agrees with the sealed run.**\n\n"
        f"Verified freeze `{EXPECTED_FREEZE}`, all {freeze_count} frozen files, predecessor input/artifact seals, forecast seal and score seal. "
        "Original workbooks and predecessor source/dev containers were hashed as bytes without decoding their outcome fields. No frozen file was changed.\n\n"
        f"Independently reconstructed 5997 source-only exported rows into 1119 bundles and checked all {len(pooled)} outer methods over five physical sites, ten contexts and 959 terminal bundles. "
        "E/M use within-bundle individual-row Brier; H uses the finite bundle mean and each outer training fold's independently reconstructed IQR (with declared SD/1 fallback). "
        "Pooled H normalizes each bundle before pooling; equal-site combined and pooled combined were reconstructed separately. Missing H never became zero truth. "
        f"Maximum absolute numerical discrepancy {max(DIFFS)}; relative tolerance {TOL}.\n\n"
        "Every saved inner validation prediction was independently rescored across 20 folds and 34 configurations, including coverage and raw H MAE. "
        "All ten per-family outer configurations, strongest refit and updater aliases derive from inner scores alone. "
        "Each acquired-control portfolio's four two-bundle SHA256 folds, seven candidates, saved predictions, common validity masks, scores and lexical winner were independently reconstructed. "
        "Ordered paid feedback, 16-bundle legal pools, eight paid bundles per context, terminal exclusions, the one authenticated missing condition and fixed 50/50 mixtures agree.\n\n"
        f"Exact enumeration matches {ledger['ordinary_head_solver_fits']} ordinary head fits, {ledger['conditional_head_constructions']} conditional head constructions with dispatches {ledger['conditional_dispatches']}, "
        f"{ledger['conditional_preprocessing_records']} fold-specific preprocessing records and {ledger['summary_constructions']} source summary constructions. "
        "Actual ridge solves are counted separately from single-valid intercept and zero-valid global fallback dispatches. "
        "Every head's valid sample count, nonrenormalized valid weight, fold source-site set, source-summary exclusion and scale, feature imputation, means and population standard deviations agrees. "
        f"Tree convention: {ledger['tree_head_fits']} head fits ×128 trees; seed104729, jobs2, BLAS1.\n\n"
        f"Explicit numerical preprocessing exception: {len(CONSTANT_COLUMN_ROUNDOFF)} mathematically constant imputed input column(s) retained a tiny nonzero floating-point standard deviation rather than the mathematical zero-std fallback1. "
        "The audit reports each saved value, independently reproduces its sequential float mean/std, and checks every response-valid subset's weighted-centered column is exactly zero in float arithmetic. "
        "Thus its centered cross-products and transpose-design contribution to ridge coefficients are zero in the specified solver path, even when held-out standardized inputs become large. "
        "This is reported as a floating-point exception, not exact agreement with mathematical standard deviation. Coefficients were not saved and no predictive solver was rerun. Full column and held-out input details appear in the audit JSON.\n\n"
        f"Strongest predefined ordinary benchmark by outer equal-site loss: `{strongest}`. Primary mean-site difference: {primary['mean_difference']}. "
        f"Frozen information progression gate: **{gate}**. Every paired-site difference, pooled component difference, delete-one-site influence and gate clause matches. "
        "The strongest ordinary benchmark is deliberately selected after aggregate evaluation as the frozen conservative reference; deployable family configurations and portfolios remain selected only with inner or paid-control validation.\n\n"
        "Limits: no predictive solver was rerun. The audit establishes arithmetic, transform, selection and accounting agreement with sealed code; it does not establish biological stationarity or independent confirmation. "
        "Five physical sites remain five units. This remains a classical conditional-information diagnostic, with no rank1 necessity, architectural novelty, clinical utility, C4 or RSI claim. The predecessor multivariate STOP remains unchanged.\n")
    (OUT / "POSTRUN_REVIEW.md").open("x", encoding="utf-8").write(text)
    print(json.dumps({"status": "PASS", "information_gate": gate, "strongest_ordinary": strongest,
                      "ordinary_head_fits": ledger["ordinary_head_solver_fits"], "conditional_dispatches": ledger["conditional_dispatches"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--score-complete", action="store_true", required=True,
                        help="Run only after root explicitly confirms separate terminal scoring is complete.")
    parser.parse_args()
    run()

