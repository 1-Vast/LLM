"""Development-only metadata diagnostic; no response arrays, API calls, or new measurements.

Resolve a requested drug/dose to the exact existing source well. Missing requested conditions
are clarification actions, not permission to choose a convenient dose. Plate identity identifies
the source; it is never smuggled into STATE as a supported intervention feature.
"""
from __future__ import annotations

import ast
import argparse
from collections import Counter
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from agent.context import TaskIntent
from agent.memory import RunLogger
from agent.prediction import PredictionCoordinator
from maestro.models import EvidenceAction, MechanismContrast
from virtual_cell.interface import SystemContext, VirtualCellQueryTemplate

STUDY = HERE.parent / "zeroshot_context_20261007"
DEVELOPMENT = {"PANC-1": "c20.h5ad", "HepG2/C3A": "c27.h5ad"}


@dataclass(frozen=True)
class Source:
    context: str
    label: str
    drug: str
    dose: float
    unit: str
    plate: str
    cell_count: int

    @property
    def identifier(self):
        return json.dumps([self.context, self.label, self.plate], separators=(",", ":"))


def resolve(sources, *, drug, dose=None, unit=None, plate=None):
    """Return exact matches and an actionable ambiguity; never pick the first matching well."""
    candidates = tuple(s for s in sources if s.drug == drug
                       and (dose is None or s.dose == dose)
                       and (unit is None or s.unit == unit)
                       and (plate is None or s.plate == plate))
    if not candidates:
        return candidates, "no_registered_source"
    if dose is None or unit is None:
        return candidates, "clarify_requested_dose_and_unit"
    if len(candidates) > 1:
        return candidates, "resolve_source_plate"
    return candidates, "resolved"


def load_sources(context, file):
    path = STUDY / "census" / f"{file}.json"
    raw = path.read_bytes()
    census = json.loads(raw)
    sources = []
    controls = 0
    for label, plate, count in census["condition_plate_counts"]:
        components = ast.literal_eval(label)
        if len(components) != 1 or len(components[0]) != 3:
            raise ValueError(f"Unsupported source label: {label}")
        drug, dose, unit = components[0]
        if drug == "DMSO_TF":
            controls += 1
            continue
        sources.append(Source(context, label, drug, dose, unit, str(plate), count))
    assert len({s.identifier for s in sources}) == len(sources)
    return sources, {"path": path.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(raw).hexdigest(),
                     "revision": census["revision"], "control_source_groups_excluded": controls}


def diagnose(context, sources, output_directory):
    by_drug = {}
    for source in sources:
        by_drug.setdefault(source.drug, []).append(source)
    coordinator = PredictionCoordinator(None, RunLogger(output_directory / "diagnostic_logs"))
    intent = TaskIntent("analysis_planning", "Resolve the requested existing RNA source", (), (),
                        context, "RNA", (), (), (), False)
    incomplete = Counter()
    ambiguous_labels = set()
    first_source_correct = first_label_correct = bound = resolved = 0
    examples = []
    for index, source in enumerate(sources):
        group = by_drug[source.drug]
        _, next_action = resolve(group, drug=source.drug)
        incomplete[next_action] += 1
        candidates, next_action = resolve(group, drug=source.drug, dose=source.dose, unit=source.unit)
        if len(candidates) > 1:
            ambiguous_labels.add(source.label)
        complete, status = resolve(group, drug=source.drug, dose=source.dose, unit=source.unit, plate=source.plate)
        assert status == "resolved" and complete == (source,)
        resolved += 1
        # A deliberately naive baseline for masked-request stress testing, not a production policy.
        first_source_correct += group[0].identifier == source.identifier
        first_label_correct += candidates[0].identifier == source.identifier

        action = EvidenceAction(f"source-{index}", "Retrieve registered source metadata", 0.0, (),
                                execution_context=context, time_hours=24,
                                expected_conditions={"intervention": source.label,
                                                     "dose": f"{source.dose} {source.unit}"},
                                source_ids=(source.identifier,))
        template = VirtualCellQueryTemplate(source.label, "drug", SystemContext(context, "development line"),
                                            ("RNA_profile",), "STATE-final-checkpoint", time_hours=None)
        answers = coordinator.query(MechanismContrast("source-resolution", (), (), action, (), ()),
                                    intent, None, f"metadata:{context}", f"source-{index}", (action,),
                                    prediction_request=None, template=template)
        request = answers.requests[action.identifier]
        assert (request.intervention.identifier, request.intervention.dose, request.intervention.dose_unit,
                request.intervention.time_hours, request.context.identifier) == (
                    source.label, source.dose, source.unit, 24, context)
        assert not answers.predictions  # This is request construction, never STATE inference.
        bound += 1
        if len(examples) < 3 and ("," in source.drug or len(candidates) > 1):
            examples.append({"source": asdict(source), "label_only_next_action": next_action,
                             "same_label_source_count": len(candidates),
                             "bound_dose": request.intervention.dose, "source_id": source.identifier})
    assert resolve(sources, drug="__absent_from_census__")[1] == "no_registered_source"
    return {
        "source_groups": len(sources), "drugs": len(by_drug), "labels": len({s.label for s in sources}),
        "multiple_doses_drugs": sum(len({(s.dose, s.unit) for s in rows}) > 1 for rows in by_drug.values()),
        "multi_source_labels": len(ambiguous_labels),
        "comma_containing_drug_source_groups": sum("," in s.drug for s in sources),
        "drug_only_masked_requests": dict(incomplete),
        "first_source_per_drug_exact_matches": first_source_correct,
        "first_source_per_label_exact_matches": first_label_correct,
        "complete_scope_exact_matches": resolved,
        "production_requests_bound": bound,
        "examples": examples,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=HERE, help="Fresh output location; existing results/logs are refused.")
    output_directory = parser.parse_args().output.resolve()
    output_path = output_directory / "condition_source_results.json"
    if output_path.exists() or (output_directory / "diagnostic_logs").exists():
        parser.error("Output already contains diagnostic artifacts; use --output with a fresh directory.")
    started = time.perf_counter()
    inputs, results = {}, {}
    for context, file in DEVELOPMENT.items():
        sources, inputs[context] = load_sources(context, file)
        results[context] = diagnose(context, sources, output_directory)
    output = {
        "design": "development-only metadata enumeration and masked-condition engineering stress test",
        "not_tested": ["LLM contribution", "biological decision utility", "forecast accuracy", "new replicate value"],
        "inputs": inputs, "results": results,
        "costs": {"provider_calls": 0, "provider_tokens": 0, "new_measurements": 0,
                  "response_array_reads": 0, "evaluation_context_reads": 0, "state_inferences": 0,
                  "local_elapsed_seconds": time.perf_counter() - started, "money": "unmetered local CPU"},
        "next_action_contract": {
            "clarify_requested_dose_and_unit": "Obtain intended dose/unit from the request owner; source availability cannot choose it.",
            "resolve_source_plate": "Read source provenance or a declared screen/validation role; retain all candidates until bound.",
            "resolved": "Retrieve only the chosen source and retain context, exact label, plate, revision and hash.",
            "no_registered_source": "Return missing source; do not fabricate a label or borrow another condition.",
        },
    }
    with output_path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(output, indent=2, allow_nan=False) + "\n")
    print(json.dumps({key: {k: v for k, v in value.items() if k != "examples"} for key, value in results.items()}, indent=2))


if __name__ == "__main__":
    main()
