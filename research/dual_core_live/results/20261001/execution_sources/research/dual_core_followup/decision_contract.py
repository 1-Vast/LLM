"""Read frozen R2 forecasts to diagnose Bayes-value versus validator-value scope.

No model is fitted, no policy is executed, and no hidden reading or truth is used.
The OutcomeForecast adapter is for the calculation API; the bank does not record
an outcome_mode or establish real-world attempted-experiment QC calibration.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from maestro.acquisition import OutcomeBranch, OutcomeForecast, expected_terminal_decision_value, outcome_consequences
from maestro.models import EvidenceAction
from research.acquisition_link.evaluate import registered_rules
from research.belief_planning.planner import plan_measurement

BANK = ROOT / "outputs/identifiability_round2_20260930/interventions"
TASKS = ("sciplex3_B", "l1000_LT")
PRICE = 0.02  # Existing belief planner's per-measurement price, not a day price.
TOLERANCE = 1e-12


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def file_hash(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def reference_probes(path: Path):
    """Stream reference/available/empty-history/probe rows; retain only hash dedup state."""
    seen = {}
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if (row["forecast"] != "reference" or row["channel"] != "probe"
                    or not row["available"] or row["history"] or row["refusal"]):
                continue
            query = {key: row[key] for key in
                     ("task_input", "forecast", "compound", "h1", "h2", "action", "history")}
            if digest(query) != row["input_sha256"] or digest(row["content"]) != row["output_sha256"]:
                raise ValueError("frozen_query_hash_mismatch")
            previous = seen.get(row["input_sha256"])
            if previous is not None:
                if previous != row["output_sha256"]:
                    raise ValueError("same_query_different_forecast")
                continue
            seen[row["input_sha256"]] = row["output_sha256"]
            yield {key: row[key] for key in
                   ("task", "episode", "compound", "h1", "h2", "action", "input_sha256",
                    "output_sha256", "content")}


def forecast_from_query(row) -> OutcomeForecast:
    content = row["content"]
    return OutcomeForecast(
        row["action"], tuple(OutcomeBranch(b["hypothesis"], b["probabilities"], b["support"])
                             for b in content["branches"]),
        basis=content["basis"], model_version=content["version"], refusal=content["refusal"],
        outcome_mode="attempted_experiment",  # API adapter only; see module-level scope.
    )


def diagnose(forecast: OutcomeForecast, candidates, consequences, *, days=1.0, price=PRICE) -> dict:
    """Compare objectives with the identical forecast and uniform prior at one step."""
    bayes = expected_terminal_decision_value(candidates, forecast, consequences, measurement_cost=price)
    action = EvidenceAction(forecast.action_identifier, forecast.action_identifier, days, tuple(candidates))
    plan = plan_measurement(candidates, None, lambda history: () if history else (action,),
                            lambda action, history: forecast, consequences, horizon=1, price=price)
    attempted = plan.evaluations[action.identifier]
    # For two hypotheses, uniform prior, wrong loss 2 and defer loss 1,
    # each non-eliminating label reduces Bayes risk by |P(label|h1)-P(label|h2)|/2.
    branches = [forecast.branch_for(h) for h in candidates]
    probabilities = [{label: value / sum(branch.probabilities.values())
                      for label, value in branch.probabilities.items()} for branch in branches]
    labels = set().union(*(p.keys() for p in probabilities))
    noneliminating_gain = sum(abs(probabilities[0].get(label, 0.0) - probabilities[1].get(label, 0.0)) / 2
                             for label in labels if not consequences.get(label))
    return {
        "bayes_value": bayes.expected_value, "bayes_net_value": bayes.net_value,
        "bayes_loss_before": bayes.expected_loss_before, "bayes_loss_after": bayes.expected_loss_after,
        "bayes_decision_sensitivity": bayes.decision_sensitivity,
        "bayes_expected_wrong": bayes.expected_wrong_decision,
        "noneliminating_bayes_gain": noneliminating_gain,
        "registered_attempt_gross_utility": attempted.utility + price,
        "registered_attempt_net_utility": attempted.utility,
        "registered_attempt_p_correct": attempted.p_correct,
        "registered_attempt_p_wrong": attempted.p_wrong,
        "registered_chosen": plan.chosen,
        "registered_best_utility": plan.value.utility,
        "registered_stop_reason": plan.reason,
        "bayes_positive_registered_stops": bayes.admissible and plan.chosen is None,
    }


def episode_units(path: Path) -> dict:
    units = {}
    with path.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            value = row["independent_unit"], row["chemical_unit_kind"]
            if row["episode"] in units and units[row["episode"]] != value:
                raise ValueError("episode_unit_conflict")
            units[row["episode"]] = value
    return units


def run(output: Path):
    sources = [Path(__file__), ROOT / "src/maestro/acquisition.py", ROOT / "src/maestro/models.py",
               ROOT / "src/maestro/outcome.py", ROOT / "research/belief_planning/planner.py",
               ROOT / "research/acquisition_link/evaluate.py", ROOT / "research/dynamic_world_model/common.py",
               ROOT / "tests/test_decision_value_scope.py"]
    source_hashes = {str(p.relative_to(ROOT)): file_hash(p) for p in sources}
    output.mkdir(parents=True, exist_ok=False)
    inputs, summary = {}, []
    for task in TASKS:
        bank, freeze_path, unit_path = (BANK / f"{task}{suffix}" for suffix in
                                       ("_forecasts.jsonl.gz", "_freeze.json", "_path_attribution.csv"))
        for path in (bank, freeze_path, unit_path):
            inputs[str(path.relative_to(ROOT))] = file_hash(path)
        freezes = {row["fold"]: row for row in json.loads(freeze_path.read_text(encoding="utf-8"))}
        units = episode_units(unit_path)
        totals = defaultdict(lambda: defaultdict(float))
        with (output / f"{task}_queries.csv").open("x", encoding="utf-8", newline="") as stream:
            writer = None
            for row in reference_probes(bank):
                fold = int(row["episode"].split("|", 1)[0])
                frozen = freezes[fold]
                days = frozen["days"][row["action"]]
                offered = {f"{k[0]}|{int(k[1]):03d}h|{int(k[2]):05d}nM"
                           for k in frozen["availability"][row["compound"]]}
                if (row["action"] not in offered or days > frozen["budget_days"]
                        or frozen["max_measurements"] < 1):
                    raise ValueError("query_outside_frozen_legal_menu")
                rules = outcome_consequences(registered_rules(row["h1"], row["h2"]))
                eliminates = frozen["validator"]["eliminates"]
                if not eliminates:
                    rules = {}  # Existing registered runner's structural no-elimination gate.
                result = diagnose(forecast_from_query(row), (row["h1"], row["h2"]), rules, days=days)
                unit, kind = units[row["episode"]]
                record = {"task": task, "fold": fold, "episode": row["episode"], "compound": row["compound"],
                          "independent_unit": unit, "chemical_unit_kind": kind, "action": row["action"],
                          "input_sha256": row["input_sha256"], "output_sha256": row["output_sha256"],
                          "backend": "reference", "version": row["content"]["version"],
                          "validator_eliminates": eliminates, "days": days,
                          "planner_price_per_measurement": PRICE, **result}
                if writer is None:
                    writer = csv.DictWriter(stream, fieldnames=list(record))
                    writer.writeheader()
                writer.writerow(record)
                counts = totals[fold]
                counts["queries"] += 1
                counts["bayes_positive"] += result["bayes_net_value"] > TOLERANCE
                counts["registered_stops"] += result["registered_chosen"] is None
                counts["bayes_positive_registered_stops"] += result["bayes_positive_registered_stops"]
                counts["noneliminating_gain_positive"] += result["noneliminating_bayes_gain"] > TOLERANCE
                for key in ("bayes_value", "noneliminating_bayes_gain", "registered_attempt_gross_utility"):
                    counts[key + "_sum"] += result[key]
        summary.extend({"task": task, "fold": fold, "validator_eliminates": freezes[fold]["validator"]["eliminates"],
                        **counts} for fold, counts in sorted(totals.items()))
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    if source_hashes != {str(p.relative_to(ROOT)): file_hash(p) for p in sources}:
        raise RuntimeError("source_changed_during_diagnostic")
    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "command": [sys.executable, *sys.argv], "working_directory": str(Path.cwd()),
        "environment": {"executable": sys.executable, "python": sys.version, "platform": platform.platform(),
                        **{name: importlib.metadata.version(name) for name in ("numpy", "scipy", "pandas", "pytest")}},
        "input_hashes": inputs, "source_hashes": source_hashes,
        "output_hashes": {p.name: file_hash(p) for p in sorted(output.iterdir())},
        "selection": "reference, probe, available, no refusal, empty history; deduplicate input_sha256",
        "scope": "Finite census of frozen query values, not policy performance or independent biological trials. "
                 "No fitting, hidden truth, hidden readings, QC calibration claim, or terminal evidence update. "
                 "The bank lacks outcome_mode; attempted_experiment is only a calculation API adapter. "
                 "One-step horizon, uniform prior, Bayes wrong loss 2/defer loss 1 versus registered +1/-2/0, "
                 "planner price 0.02 per measurement. Structural no-elimination folds use empty consequences. "
                 "All data and forecasts were exposed development artifacts; no new checkpoint was used.",
        "uncertainty": "Descriptive census counts/sums; no biological or causal CI. Chemical units are retained "
                       "without assuming query independence. Physical plate/batch inference is not estimated.",
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "folds": summary}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/dual_core_followup_20261001/decision_contract")
    run(parser.parse_args().output)
