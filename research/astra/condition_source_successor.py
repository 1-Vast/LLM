"""Reproduce the frozen development metadata counts using the shared resolver.

No expression arrays, evaluation contexts, provider calls or STATE inference.
Run from the repository root: python -m research.astra.condition_source_successor.
"""
import ast
import hashlib
import json
from pathlib import Path

from tools.datasets.condition_sources import ConditionSource, resolve_condition_sources


def diagnose():
    root = Path(__file__).resolve().parents[2]
    results = {}
    for context, filename in (("PANC-1", "c20.h5ad.json"), ("HepG2/C3A", "c27.h5ad.json")):
        path = root / "research/astra/zeroshot_context_20261007/census" / filename
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        sources = []
        for label, plate, count in json.loads(raw)["condition_plate_counts"]:
            components = ast.literal_eval(label)
            if len(components) != 1 or len(components[0]) != 3:
                raise ValueError(f"Unsupported condition label: {label}")
            drug, dose, unit = components[0]
            if drug != "DMSO_TF":
                sources.append(ConditionSource(context, label, drug, dose, unit, str(plate),
                                               path.relative_to(root).as_posix(), digest))
        groups = {}
        for source in sources:
            groups.setdefault(source.drug, []).append(source)
        exact = missing = 0
        ambiguous = set()
        for source in sources:
            rows = groups[source.drug]
            request = dict(context=context, drug=source.drug)
            assert resolve_condition_sources(rows, **request).status == "clarify_requested_dose_and_unit"
            missing += 1
            request.update(dose=source.dose, unit=source.unit)
            if resolve_condition_sources(rows, **request).status == "resolve_source_identity":
                ambiguous.add(source.label)
            request.update(label=source.label, source_group=source.source_group,
                           source_reference=source.source_reference, source_sha256=digest)
            result = resolve_condition_sources(rows, **request)
            assert result.status == "resolved" and result.candidates == (source,)
            exact += 1
        results[context] = {"source_groups": len(sources), "complete_scope_exact_matches": exact,
                            "dose_unit_clarifications": missing, "multi_source_labels": len(ambiguous),
                            "source_reference": path.relative_to(root).as_posix(), "source_sha256": digest}
    return results


if __name__ == "__main__":
    print(json.dumps(diagnose(), indent=2, allow_nan=False))
