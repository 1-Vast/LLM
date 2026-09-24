"""The section 37 score table: six strategy rows, decision metrics only, every gap named.

File summary
- Path: src/evaluation/score_table.py
- Purpose: turn evaluation reports into the governing report's section 37 table and apply
  its section 29 exit conditions to a prediction input, so both are computed rather than
  written by hand.
- Core points:
  - The six rows are fixed. A row with no evaluated arm is `not_run` with a reason and is
    never dropped: the report says a table missing a row supports no comparison, and the
    table's `conclusion` says so mechanically.
  - Wrong action counts wrong advancement, premature abandonment and a wrong revision,
    each also reported alone. Over-deferral and the absence of a valid decision are
    separate columns, so neither refusing everything nor failing to submit can hide.
  - Intervals: Wilson at the case level, and a seeded cluster bootstrap over target
    clusters, because cases on one target are not independent evidence.
  - Cost to reach the evidence standard counts only cases where an arm reached a licensed
    non-deferral decision, in wells and turnaround days where priced and by named refusal
    where not; abstract cost units are kept beside them, labelled as such.
  - Without blind adjudication the table is never evidence for the core claim, however
    complete it is.
- Interfaces: `SECTION_37_ROWS`, `DEFAULT_ROW_ARMS`, `wilson_interval`,
  `cluster_bootstrap_interval`, `row_metrics`, `build_score_table`, `exit_verdict`,
  `render_text`, `main`
- Depends on: evaluation.lab_cost (constants only); reads report dictionaries
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from math import ceil, sqrt
from pathlib import Path
from random import Random
from typing import Mapping, Sequence

from .lab_cost import TURNAROUND_CONVENTION

Z_95 = 1.959963984540054
BOOTSTRAP_SEED = 20260914
BOOTSTRAP_RESAMPLES = 2000

SECTION_37_ROWS: tuple[tuple[str, str], ...] = (
    ("fixed_expert_rule_flow", "Fixed expert rule flow"),
    ("simple_model_plus_voi", "Simple response model with EIG/VOI"),
    ("retrieval_single_agent", "Retrieval-based single agent"),
    ("same_llm_explicit_hypotheses", "Same LLM, MDA-style explicit hypothesis decision"),
    ("full_system", "Full system"),
    ("full_system_shuffled_predictions", "Full system with shuffled model predictions"),
)

# Declared, not inferred: which evaluated arm stands for which row. An arm that does not
# implement a row's strategy is not assigned to it merely because it exists.
DEFAULT_ROW_ARMS: Mapping[str, str] = {
    "fixed_expert_rule_flow": "fixed_expert",
    "simple_model_plus_voi": "simple_model_voi",
    "retrieval_single_agent": "ordinary_llm",
    "same_llm_explicit_hypotheses": "explicit_hypotheses_llm",
    "full_system": "maestro_core",
    "full_system_shuffled_predictions": "maestro_core_shuffled_predictions",
}

NOT_RUN_REASONS: Mapping[str, str] = {
    "fixed_expert_rule_flow": "the fixed_expert arm was not evaluated in this run",
    "simple_model_plus_voi": (
        "the simple_model_voi arm was not evaluated in this run; it fits its outcome model on a "
        "declared development split and is refused rather than run unfitted"
    ),
    "retrieval_single_agent": "the provider-backed ordinary_llm arm was not evaluated in this run",
    "same_llm_explicit_hypotheses": (
        "the provider-backed explicit_hypotheses_llm arm was not evaluated in this run; the row "
        "requires an arm that states a posterior over the registered explanations and selects by "
        "its own value of information, and that contract is enforced rather than requested"
    ),
    "full_system": "the maestro_core arm was not evaluated in this run",
    "full_system_shuffled_predictions": (
        "the maestro_core_shuffled_predictions arm was not evaluated in this run; where it is, an "
        "identity with the full system means the prediction input is not read, not that it was harmless"
    ),
}

WRONG_VERDICTS = ("wrong_advance", "wrong_abandon", "wrong_direction")
NO_VALID_VERDICTS = ("no_decision", "invalid_submission")


def wilson_interval(successes: int, trials: int, z: float = Z_95) -> tuple[float, float] | None:
    """Wilson score interval for a binomial rate; None when there is nothing to estimate."""

    if trials <= 0:
        return None
    rate = successes / trials
    denominator = 1.0 + z * z / trials
    centre = (rate + z * z / (2.0 * trials)) / denominator
    half = z * sqrt(rate * (1.0 - rate) / trials + z * z / (4.0 * trials * trials)) / denominator
    return (round(max(0.0, centre - half), 6), round(min(1.0, centre + half), 6))


def cluster_bootstrap_interval(
    events_by_cluster: Mapping[str, tuple[int, int]],
    *,
    resamples: int = BOOTSTRAP_RESAMPLES,
    seed: int = BOOTSTRAP_SEED,
) -> tuple[float, float] | None:
    """Percentile interval of a pooled rate, resampling whole clusters with replacement."""

    clusters = sorted(events_by_cluster)
    if len(clusters) < 2 or resamples < 2:
        return None
    rng = Random(seed)
    rates: list[float] = []
    for _ in range(resamples):
        events = 0
        trials = 0
        for _ in clusters:
            hit, count = events_by_cluster[clusters[rng.randrange(len(clusters))]]
            events += hit
            trials += count
        rates.append(events / trials if trials else 0.0)
    rates.sort()
    low = rates[int(0.025 * (resamples - 1))]
    high = rates[int(ceil(0.975 * (resamples - 1)))]
    return (round(low, 6), round(high, 6))


def _value(entry: object) -> str | None:
    """A decision or verdict as plain text, whether it arrived as an enum or from JSON."""

    if entry is None:
        return None
    return str(getattr(entry, "value", entry))


def row_metrics(report: Mapping[str, object], clusters: Mapping[str, str]) -> dict[str, object]:
    """Decision-level metrics for one evaluated arm, with the statistical unit stated."""

    results = list(report.get("results", ()))  # type: ignore[arg-type]
    total = len(results)
    verdicts = Counter(_value(item["verdict"]) for item in results)

    def share(count: int) -> dict[str, object]:
        return {"count": count, "rate": round(count / total, 6) if total else None}

    by_cluster: dict[str, tuple[int, int]] = {}
    for item in results:
        key = clusters.get(str(item["case_id"]), str(item["case_id"]))
        hit, count = by_cluster.get(key, (0, 0))
        by_cluster[key] = (hit + (1 if _value(item["verdict"]) in WRONG_VERDICTS else 0), count + 1)
    wrong = sum(verdicts[name] for name in WRONG_VERDICTS)

    eligible = [item for item in results if not ({str(x) for x in item.get("reachable_decisions", ())} - {"defer"})]
    deferred = [
        item for item in eligible if _value(item.get("decision")) == "defer" and _value(item["verdict"]) == "correct"
    ]
    reached = [
        item
        for item in results
        if _value(item["verdict"]) == "correct" and _value(item.get("decision")) not in (None, "defer")
    ]
    priced = [item for item in reached if item.get("lab_cost_refusal") is None and item.get("wells_spent") is not None]
    fully_priced = len(priced) == len(reached)
    return {
        "arm": report.get("policy"),
        "cases": total,
        "clusters": len(by_cluster),
        "reliability": share(verdicts["correct"]),
        "wrong_action": {
            **share(wrong),
            "wilson_95": wilson_interval(wrong, total),
            "cluster_bootstrap_95": cluster_bootstrap_interval(by_cluster),
        },
        "wrong_advance": share(verdicts["wrong_advance"]),
        "premature_abandon": share(verdicts["wrong_abandon"]),
        "wrong_direction": share(verdicts["wrong_direction"]),
        "over_deferral": share(verdicts["over_deferral"]),
        "no_valid_decision": share(sum(verdicts[name] for name in NO_VALID_VERDICTS)),
        "appropriate_deferral": {
            "eligible": len(eligible),
            "deferred_correctly": len(deferred),
            "rate": round(len(deferred) / len(eligible), 6) if eligible else None,
        },
        "cost_to_evidence_standard": {
            "cases": len(reached),
            "declared_cost_units": round(sum(float(item.get("spent", 0.0)) for item in reached), 6),
            "wells": sum(int(item["wells_spent"]) for item in priced) if fully_priced else None,
            "turnaround_days": (
                round(sum(float(item["turnaround_days_spent"]) for item in priced), 6) if fully_priced else None
            ),
            "lab_cost_refused": len(reached) - len(priced),
            "new_measurements": sum(int(item.get("new_measurements", 0)) for item in reached),
            "record_retrievals": sum(int(item.get("record_retrievals", 0)) for item in reached),
            "turnaround_convention": TURNAROUND_CONVENTION,
        },
        "prospective_hit_rate": {
            "status": "not_registered",
            "reason": "no arm registered a discriminating prediction before its reveal",
        },
        "final_test": dict(sorted(Counter(str(item.get("final_test_verdict", "partition_absent")) for item in results).items())),
        "refusal_codes": dict(sorted(Counter(str(item["refusal_code"]) for item in results if item.get("refusal_code")).items())),
    }


def build_score_table(
    reports: Sequence[Mapping[str, object]],
    *,
    clusters: Mapping[str, str] | None = None,
    row_arms: Mapping[str, str] | None = None,
    blind_adjudication: bool = False,
    provenance: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Assemble the six rows, keep every other arm as a supplementary row, and state the verdict."""

    cluster_map = dict(clusters or {})
    by_arm = {str(report["policy"]): report for report in reports}
    assignment = dict(DEFAULT_ROW_ARMS if row_arms is None else row_arms)
    rows: list[dict[str, object]] = []
    used: set[str] = set()
    for key, label in SECTION_37_ROWS:
        arm = assignment.get(key)
        if arm is not None and arm in by_arm:
            rows.append({"row": key, "label": label, "status": "run", **row_metrics(by_arm[arm], cluster_map)})
            used.add(arm)
        else:
            rows.append({"row": key, "label": label, "status": "not_run", "arm": arm, "reason": NOT_RUN_REASONS[key]})
    supplementary = [
        {"row": f"supplementary:{name}", "label": name, "status": "run", **row_metrics(report, cluster_map)}
        for name, report in sorted(by_arm.items())
        if name not in used
    ]
    missing = [str(row["row"]) for row in rows if row["status"] == "not_run"]
    table: dict[str, object] = {
        "schema": "maestro.score_table.v1",
        "section": "governing report section 37",
        "statistical_unit": "case; intervals also resample whole target clusters",
        "cluster_map_supplied": bool(cluster_map),
        "bootstrap": {"seed": BOOTSTRAP_SEED, "resamples": BOOTSTRAP_RESAMPLES},
        "rows": rows,
        "supplementary_rows": supplementary,
        "conclusion": {
            "all_rows_run": not missing,
            "missing_rows": missing,
            "blind_adjudication": blind_adjudication,
            "evidence_for_core_claim": bool(not missing and blind_adjudication),
            "reading": (
                "A table missing a row supports no comparison between strategies, and a complete table "
                "without adjudication blind to the strategies' outputs is not evidence for the core claim."
            ),
        },
    }
    if provenance:
        table["provenance"] = dict(provenance)
    return table


def _incorrect(report: Mapping[str, object]) -> int:
    return sum(1 for item in report.get("results", ()) if _value(item["verdict"]) != "correct")  # type: ignore[union-attr]


def _sequences(report: Mapping[str, object]) -> dict[str, tuple[str, ...]]:
    return {str(item["case_id"]): tuple(item.get("selected_actions", ())) for item in report.get("results", ())}  # type: ignore[union-attr]


def exit_verdict(
    *,
    input_name: str,
    informed: Mapping[str, object],
    removed: Mapping[str, object],
    shuffled: Mapping[str, object],
    declaration_reader: Mapping[str, object] | None = None,
    prediction_quality_improved: bool | None = None,
    confident_out_of_domain_errors: int | None = None,
) -> dict[str, object]:
    """Apply the four section 29 exit conditions, in their written order, to one input.

    ``informed`` is the arm that reads the input, ``removed`` the same arm with it switched
    off, ``shuffled`` the same arm with it assigned to the wrong actions, and
    ``declaration_reader`` an arm that reads only the public declarations the input could
    have been derived from. A condition whose input was not supplied is `not_assessable`
    by name; nothing is filled in.
    """

    informed_wrong, removed_wrong, shuffled_wrong = _incorrect(informed), _incorrect(removed), _incorrect(shuffled)
    informed_sequences = _sequences(informed)
    moved_by_removal = sum(1 for case, sequence in informed_sequences.items() if _sequences(removed).get(case) != sequence)
    moved_by_shuffle = sum(1 for case, sequence in informed_sequences.items() if _sequences(shuffled).get(case) != sequence)
    improves = informed_wrong < removed_wrong and informed_wrong < shuffled_wrong

    conditions: list[dict[str, object]] = [
        {
            "condition": "remove_from_loop",
            "rule": "triggered unless the informed arm has strictly fewer incorrect verdicts than both the removed and the shuffled control",
            "status": "not_triggered" if improves else "triggered",
            "evidence": {
                "incorrect_informed": informed_wrong,
                "incorrect_removed": removed_wrong,
                "incorrect_shuffled": shuffled_wrong,
                "acquisitions_changed_by_removal": moved_by_removal,
                "acquisitions_changed_by_shuffle": moved_by_shuffle,
            },
        }
    ]
    if prediction_quality_improved is None:
        conditions.append(
            {
                "condition": "demote_to_feature_provider",
                "rule": "triggered when prediction quality improved while no acquisition changed",
                "status": "not_assessable",
                "reason": "no scored prediction quality was supplied for this input",
            }
        )
    else:
        conditions.append(
            {
                "condition": "demote_to_feature_provider",
                "rule": "triggered when prediction quality improved while no acquisition changed",
                "status": "triggered" if prediction_quality_improved and moved_by_removal == 0 else "not_triggered",
                "evidence": {"prediction_quality_improved": prediction_quality_improved, "acquisitions_changed_by_removal": moved_by_removal},
            }
        )
    if declaration_reader is None:
        conditions.append(
            {
                "condition": "record_as_external_information_gain",
                "rule": "triggered when an arm reading only the public declarations does at least as well as the informed arm",
                "status": "not_assessable",
                "reason": "no declaration-reading arm was supplied",
            }
        )
    elif not improves:
        conditions.append(
            {
                "condition": "record_as_external_information_gain",
                "rule": "triggered when an arm reading only the public declarations does at least as well as the informed arm",
                "status": "not_applicable",
                "reason": "the input improved nothing, so there is no gain to attribute",
            }
        )
    else:
        reader_wrong = _incorrect(declaration_reader)
        conditions.append(
            {
                "condition": "record_as_external_information_gain",
                "rule": "triggered when an arm reading only the public declarations does at least as well as the informed arm",
                "status": "triggered" if reader_wrong <= informed_wrong else "not_triggered",
                "evidence": {"incorrect_declaration_reader": reader_wrong, "incorrect_informed": informed_wrong, "reader": declaration_reader.get("policy")},
            }
        )
    if confident_out_of_domain_errors is None:
        conditions.append(
            {
                "condition": "tighten_applicability_domain",
                "rule": "triggered by any confident prediction outside the declared domain that proved wrong",
                "status": "not_assessable",
                "reason": "the input declares no applicability domain, so no confident out-of-domain error can be counted",
            }
        )
    else:
        conditions.append(
            {
                "condition": "tighten_applicability_domain",
                "rule": "triggered by any confident prediction outside the declared domain that proved wrong",
                "status": "triggered" if confident_out_of_domain_errors > 0 else "not_triggered",
                "evidence": {"confident_out_of_domain_errors": confident_out_of_domain_errors},
            }
        )
    triggered = [str(item["condition"]) for item in conditions if item["status"] == "triggered"]
    return {
        "schema": "maestro.exit_verdict.v1",
        "section": "governing report section 29",
        "input": input_name,
        "arms": {
            "informed": informed.get("policy"),
            "removed": removed.get("policy"),
            "shuffled": shuffled.get("policy"),
            "declaration_reader": declaration_reader.get("policy") if declaration_reader else None,
        },
        "conditions": conditions,
        "triggered": triggered,
        "consequence": triggered[0] if triggered else "retain",
    }


def render_text(table: Mapping[str, object]) -> str:
    """A compact plain-text view of the table for a terminal; the JSON is the record."""

    lines = ["row | status | cases | wrong action [Wilson 95] | over-deferral | appropriate deferral | wells to standard"]
    for row in list(table["rows"]) + list(table["supplementary_rows"]):  # type: ignore[arg-type]
        if row["status"] != "run":
            lines.append(f"{row['row']} | not_run | - | - | - | - | - ({row['reason']})")
            continue
        wrong = row["wrong_action"]
        deferral = row["appropriate_deferral"]
        cost = row["cost_to_evidence_standard"]
        lines.append(
            f"{row['row']} | run | {row['cases']} | {wrong['count']} {wrong['wilson_95']} | "
            f"{row['over_deferral']['count']} | {deferral['deferred_correctly']}/{deferral['eligible']} | "
            f"{cost['wells'] if cost['wells'] is not None else 'refused:' + str(cost['lab_cost_refused'])}"
        )
    conclusion = table["conclusion"]
    lines.append(f"all rows run: {conclusion['all_rows_run']}; evidence for core claim: {conclusion['evidence_for_core_claim']}")  # type: ignore[index]
    return "\n".join(lines)


def load_clusters(manifest: Path | None) -> dict[str, str]:
    """Case-to-cluster map from an evaluator-owned manifest; empty when none is given."""

    if manifest is None or not manifest.is_file():
        return {}
    data = json.loads(manifest.read_text(encoding="utf-8"))
    return {str(entry["case_id"]): str(entry.get("source_cluster") or entry["case_id"]) for entry in data.get("cases", ())}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the section 37 score table from a maestro-evaluate payload.")
    parser.add_argument("--evaluation", type=Path, required=True, help="JSON written by maestro-evaluate.")
    parser.add_argument("--manifest", type=Path, help="Evaluator-owned manifest carrying source_cluster per case.")
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args(argv)
    payload = json.loads(arguments.evaluation.read_text(encoding="utf-8"))
    table = build_score_table(
        payload["reports"],
        clusters=load_clusters(arguments.manifest),
        provenance={"evaluation": str(arguments.evaluation), "run_id": payload.get("run_id")},
    )
    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    arguments.out.write_text(json.dumps(table, indent=2, sort_keys=False, default=str) + "\n", encoding="utf-8")
    print(render_text(table))
    print(arguments.out)
    return 0


if __name__ == "__main__":  # pragma: no cover - direct script execution
    raise SystemExit(main())
