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

import numpy as np

getcontext().prec = 50
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/cipa_calibration_probe"
HEADS = ("E", "M", "H")
CONTROLS = {"Dofetilide", "Nifedipine", "Mexiletine", "Ranolazine"}
EXPECTED_FREEZE = "781bdecf95e0a34b23c0abe4ce531371560dda9482b3a38b4eff98c3bb8d9cb1"
ZERO, ONE = Decimal(0), Decimal(1)
TOL = Decimal("1e-9")
DIFFS = []


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
    for row in read("SOURCE_DEV_ROWS.json")["rows"]:
        assert row["site"] in "1234567"
        assert row["split"] == ("source" if row["site"] in "12345" else "dev")
        for field in ("ead", "ddfpdc"):
            assert row[field + "_status"] in ("valid", "missing")
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
            pieces["H"].append(error / scale)
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


def verify_seals():
    assert digest(OUT / "FREEZE.json") == EXPECTED_FREEZE
    freeze = read("FREEZE.json")
    for name, expected in freeze["files"].items():
        assert digest(ROOT / name) == expected, name
    for name, expected in read("ENDPOINT_ARTIFACT_SEAL.json").items():
        assert digest(OUT / name) == expected, name
    for record in read("ENDPOINT_INPUT_SEAL.json").values():
        assert digest(ROOT / record["path"]) == record["sha256"], record["path"]
    audit = read("ENDPOINT_SCHEMA_AUDIT.json")
    assert audit["status"] == "PASS"
    for k in ("later_outcome_contacts", "excluded_outcome_contacts", "later_outcome_numeric_casts", "excluded_outcome_numeric_casts"):
        assert audit[k] == 0, k
    forecast_seal = read("FORECAST_SEAL.json")
    assert forecast_seal["freeze_sha256"] == EXPECTED_FREEZE
    assert forecast_seal["terminal_truth_extracted"] is False
    for name, expected in forecast_seal["files"].items():
        assert digest(OUT / name) == expected, name
    score_seal = read("SCORE_SEAL.json")
    assert score_seal["forecast_seal_sha256"] == digest(OUT / "FORECAST_SEAL.json")
    assert score_seal["scores_sha256"] == digest(OUT / "TERMINAL_SCORES.json")
    return len(freeze["files"])


def balanced(ids):
    ordered = sorted(ids, key=lambda bid: (sha256(bid.encode()).hexdigest(), bid))
    return [ordered[f::4] for f in range(4)]


def check_source_choices(choices, configs, targets, manifest):
    scores = choices["scores"]
    for cid, sites in scores.items():
        assert set(sites) == set("12345")
        for site, loss in sites.items():
            close(loss["combined"], mean(x for x in loss["components"].values() if x is not None), "cv combined")
            ids = [bid for ctx, cm in manifest["contexts"].items() if ctx.split("|")[0] == site for bid in cm["terminal"]]
            assert loss["coverage"] == {name: {"valid": sum(targets[bid][h] is not None for bid in ids), "total": len(ids)} for h, name in enumerate(HEADS)}
            if loss["components"]["H"] is not None:
                close(loss["raw_H_MAE"], loss["components"]["H"] * source_scale(targets, set("12345") - {site}), "cv raw H scaling")
        close(choices["mean_physical_site_combined"][cid], mean(x["combined"] for x in sites.values()), "cv mean")
    def best(candidates):
        return min(candidates, key=lambda c: (choices["mean_physical_site_combined"][c["id"]], c["id"]))
    for family, config in choices["families"].items():
        assert config == best(c for c in configs if c["family"] == family)
    assert choices["sourcebest"] == choices["families"]["lookup"]
    assert choices["strongrefit"] == best(c for c in configs if c["family"] in ("ridge", "augmented", "trees"))
    assert choices["overallupdater"] == best(c for c in configs if c["family"] != "lookup")
    assert choices["selection_uses_dev_labels"] is False


def audit_ledger(ledger, choices, configs, manifest, queries, programs, targets):
    expected = Counter()
    def add(stage, ctx, config, paid_ids, source_sites):
        if config["family"] == "lookup":
            return
        for head, name in enumerate(HEADS):
            paid_n = sum(targets[bid][head] is not None for bid in paid_ids)
            n = paid_n
            if config["family"] in ("ridge", "augmented", "trees"):
                n += sum(y[head] is not None for bid, y in targets.items() if bid.split("|")[0] in source_sites)
            if n:
                expected[(stage, ctx, config["id"], name, n)] += 1
    for ctx, cm in manifest["contexts"].items():
        site = ctx.split("|")[0]
        if site in "12345":
            for config in configs:
                add("source_cv", ctx, config, cm["metadata_policies"]["fixed"], set("12345") - {site})
    candidates = list(choices["families"].values())
    for ctx, policies in queries.items():
        fixed = policies["fixed"]
        for config in {c["id"]: c for c in candidates + [choices["strongrefit"], choices["overallupdater"]]}.values():
            add("dev_fixed", ctx, config, fixed, set("12345"))
        for config in candidates:
            for f, fold in enumerate(balanced(fixed)):
                add(f"portfolio_fold_{f}", ctx, config, [bid for bid in fixed if bid not in fold], set("12345"))
        add("portfolio_final", ctx, programs[ctx]["choice"], fixed, set("12345"))
        for policy, ids in policies.items():
            if policy != "fixed":
                add("dev_" + policy, ctx, choices["overallupdater"], ids, set("12345"))
    actual = Counter((r["stage"], r["context"], r["config"], r["head"], r["n_training_valid"]) for r in ledger["fits"])
    assert actual == expected, {"missing": list((expected - actual).items()), "extra": list((actual - expected).items())}
    assert len(ledger["fits"]) == ledger["head_solver_fit_count"] <= 978
    assert dict(Counter(r["stage"] for r in ledger["fits"])) == ledger["counts_by_stage"]
    for r in ledger["fits"]:
        assert r["physical_site"] == r["context"].split("|")[0]
        assert r["cpu_seconds"] >= 0 and r["wall_seconds"] >= 0
        assert r["seed"] == (104729 if r["config"].startswith("trees:") else None)
    summaries = ledger["summary_constructions"]
    assert len(summaries) == 31
    for summary in summaries:
        stage = summary["stage"]
        sites = set("12345")
        if stage.startswith("source_cv_hold_"):
            sites.remove(stage[len("source_cv_hold_")])
        if ":nested_exclude_" in stage:
            sites.remove(stage.rsplit("_", 1)[1])
        assert set(summary["source_sites"]) == sites
        assert summary["bundles"] == sum(bid.split("|")[0] in sites for bid in targets)
        close(summary["scale"], source_scale(targets, sites), "summary scale")
    assert ledger["source_cv_query_cost_per_physical_site"] == {s: 16 for s in "12345"}
    assert ledger["development_policy_cost_per_physical_site"] == {s: 8 for s in "67"}


def run():
    sealed_files = verify_seals()
    grouped, targets = endpoint_rows()
    manifest = read("QUERY_MANIFEST.json")
    forecasts = read("FORECASTS.json")
    scores = read("TERMINAL_SCORES.json")
    choices = read("SOURCE_CHOICES.json")
    queries = read("QUERY_LISTS.json")
    feedback = read("QUERY_FEEDBACK.json")
    programs = read("PORTFOLIO_CHOICES.json")
    ledger = read("FIT_COUNTS.json")
    configs = read("PREPARE_AUDIT.json")["configs"]
    check_source_choices(choices, configs, targets, manifest)
    scale = source_scale(targets, set("12345"))
    close(forecasts["scale"], scale, "all-source scale")
    assert forecasts["head_order"] == list(HEADS)
    assert {ctx.split("|")[0] for ctx in forecasts["contexts"]} == set("67")
    assert len(forecasts["contexts"]) == 2
    bysite, pooled_ids, pooled_predictions = {}, [], defaultdict(list)
    for ctx, item in forecasts["contexts"].items():
        cm = manifest["contexts"][ctx]
        assert item["bundle_ids"] == cm["terminal"] and len(cm["terminal"]) == 96
        assert len(cm["pool"]) == 16 and not set(cm["terminal"]) & set(cm["pool"])
        expected_methods = {"fixed:" + family for family in choices["families"]} | {"fixed:strongrefit", "fixed:overallupdater", "fixed:mixture", "fixed:portfolio"}
        expected_methods |= {policy + ":overallupdater" for policy in queries[ctx] if policy != "fixed"}
        assert set(item["predictions"]) == expected_methods and len(expected_methods) == 18
        pooled_ids.extend(item["bundle_ids"])
        for policy, ids in queries[ctx].items():
            assert len(set(ids)) == len(ids) == 8 and set(ids) <= set(cm["pool"])
            if policy in cm["metadata_policies"]:
                assert ids == cm["metadata_policies"][policy]
            actual_feedback = feedback[ctx + ":" + policy]
            assert [r["bundle_id"] for r in actual_feedback] == ids
            for r in actual_feedback:
                for actual, expected in zip(r["targets_EMH"], targets[r["bundle_id"]]):
                    close(actual, expected, "paid row reconstruction")
        folds = balanced(queries[ctx]["fixed"])
        program = programs[ctx]
        assert program["folds"] == folds and all(len(f) == 2 for f in folds)
        assert set(program["candidate_scores"]) == {c["id"] for c in choices["families"].values()}
        for cid, entry in program["candidate_scores"].items():
            assert len(entry["folds"]) == 4
            for ids, fold in zip(folds, entry["folds"]):
                assert fold["coverage"] == {name: {"valid": sum(targets[bid][h] is not None for bid in ids), "total": 2} for h, name in enumerate(HEADS)}
                close(fold["combined"], mean(x for x in fold["components"].values() if x is not None), "portfolio combined")
                if fold["components"]["H"] is not None:
                    close(fold["raw_H_MAE"], fold["components"]["H"] * scale, "portfolio raw H scaling")
            close(entry["mean"], mean(f["combined"] for f in entry["folds"]), "portfolio mean")
        winner = min(program["candidate_scores"], key=lambda cid: (program["candidate_scores"][cid]["mean"], cid))
        assert program["choice"]["id"] == winner
        bysite[ctx] = {}
        for method, prediction in item["predictions"].items():
            reconstructed = row_scores(item["bundle_ids"], prediction, grouped, scale)
            compare_score(scores["by_context_physical_site"][ctx][method], reconstructed, ctx + ":" + method)
            bysite[ctx][method] = reconstructed
            pooled_predictions[method].extend(prediction)
        mixture = item["predictions"]["fixed:mixture"]
        source = item["predictions"]["fixed:lookup"]
        refit = item["predictions"]["fixed:strongrefit"]
        for m, a, b in zip(mixture, source, refit):
            for h in range(3):
                close(m[h], (a[h] + b[h]) / 2, "50/50 mixture")
    pooled = {}
    comparisons = {}
    for method, prediction in pooled_predictions.items():
        pooled[method] = row_scores(pooled_ids, prediction, grouped, scale)
        compare_score(scores["pooled_equal_bundles"][method], pooled[method], "pooled:" + method)
    baseline = "fixed:lookup"
    for method in pooled:
        differences = {ctx: bysite[ctx][method]["combined"] - bysite[ctx][baseline]["combined"] for ctx in bysite}
        delta = mean(differences.values())
        components = {h: pooled[method]["components"][h] - pooled[baseline]["components"][h] for h in HEADS}
        gate = delta < 0 and all(v <= 0 for v in components.values())
        actual = scores["comparisons_to_frozen_sourcebest"][method]
        for ctx, difference in differences.items():
            close(actual["paired_site_combined_difference"][ctx], difference, "site delta")
        close(actual["mean_site_combined_difference"], delta, "mean delta")
        for h, difference in components.items():
            close(actual["pooled_component_difference"][h], difference, "component delta")
        assert actual["opportunity_gate"] == gate
        comparisons[method] = {"mean_site_difference": delta, "pooled_component_difference": components, "gate": gate}
    audit_ledger(ledger, choices, configs, manifest, queries, programs, targets)
    report = {"status": "PASS", "freeze_sha256": EXPECTED_FREEZE, "auditor_sha256": digest(Path(__file__)),
        "method": "50-digit Decimal; individual exported rows; equal bundle weights; independent of model_probe and aggregate bundle target file",
        "scored_contexts": sorted(bysite), "terminal_bundles": len(pooled_ids), "methods": len(pooled),
        "source_scale": scale, "max_absolute_numerical_difference": max(DIFFS), "relative_tolerance": TOL,
        "freeze_files_verified": sealed_files, "forecast_and_score_seals": "PASS", "source_selection_and_portfolio_ranking": "PASS",
        "actual_head_fits": ledger["head_solver_fit_count"], "head_fit_ceiling": 978, "exact_expected_fit_ledger": "PASS",
        "summary_constructions": len(ledger["summary_constructions"]), "source_summaries_and_scales": "PASS",
        "paid_feedback_and_query_budgets": "PASS", "later_and_excluded_numerical_rows": 0,
        "comparisons": comparisons,
        "limits": "Portfolio validation predictions and source-CV predictions were not serialized; audit verifies their recorded masks, aggregation and winner, not those unrecorded prediction values. No model refits were made. File seals and code flow establish computational provenance, not independent biological confirmation."}
    def encode(value):
        if isinstance(value, Decimal):
            return str(value)
        raise TypeError(type(value).__name__)
    with (OUT / "SCORE_INDEPENDENT_AUDIT.json").open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, default=encode)
    primary = comparisons["fixed:overallupdater"]
    text = ("# Independent postrun review\n\n"
        "Disposition: **PASS — row-based Decimal score reconstruction and sealed-run accounting agree.**\n\n"
        f"Verified freeze `{EXPECTED_FREEZE}` and every bound input/code hash, endpoint input/artifact seals, forecast seal and score seal. "
        "No frozen file was edited. Raw workbook verification hashes bytes without decoding later/excluded outcomes. "
        "The individual-row artifact contains only source/development sites1–7.\n\n"
        f"Recomputed all {len(pooled)} methods on two sites/{len(pooled_ids)} terminal bundles directly from individual EAD/H raw records using50-digit Decimal arithmetic. "
        "E/M scores average row Brier within each bundle, then weight bundles equally. H scores average finite H within a bundle and score only conditional available means; source scale and coverage were independently reconstructed. "
        f"Maximum absolute discrepancy: {max(DIFFS)}; relative tolerance1e-9.\n\n"
        f"Primary source-CV-best updater mean site combined difference versus the frozen sourcebest: {primary['mean_site_difference']}; opportunity gate: {primary['gate']}. "
        "The audit independently reproduces every method's paired-site differences, three pooled component differences and gate. "
        "This checks the stated opportunity criterion; it does not itself assert superiority over every conventional comparator.\n\n"
        f"Actual head-solver fits: {ledger['head_solver_fit_count']} (ceiling978); all individual config/context/head/training-valid-count ledger entries match the independently enumerated expected schedule. "
        "There are31 source-only summary constructions with correct physical-site exclusions and independently verified scales. "
        "Paid feedback matches individual-row targets, policy budgets/pools are legal, fixed50/50 mixtures agree, and portfolio balanced folds, validity masks, recorded score aggregation and selected winners agree.\n\n"
        "Limit: portfolio-validation and source-CV predictions were not serialized, so their underlying prediction values cannot be independently rescored without refitting. "
        "Their recorded aggregation/selection and fit boundaries were checked; no model fits were performed by this audit. "
        "The result remains an ordinary two-site development screen and establishes neither a novel mechanism nor clinical/C4 evidence.\n")
    with (OUT / "POSTRUN_REVIEW.md").open("x", encoding="utf-8") as handle:
        handle.write(text)
    print(json.dumps({"status": "PASS", "methods": len(pooled), "head_fits": ledger["head_solver_fit_count"], "primary_gate": primary["gate"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--score-complete", action="store_true", required=True,
                        help="Use only after root confirms terminal scoring is complete.")
    parser.parse_args()
    run()
