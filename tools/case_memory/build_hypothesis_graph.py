"""Build the production hypothesis graphs for the external evaluation problems.

File summary
- Path: tools/case_memory/build_hypothesis_graph.py
- Purpose: for every evaluation unit, construct the typed production hypothesis graph
  (intervention -> target -> pathway -> observable) with evidence classes on every edge and the
  unmeasured layers named, and write them to
  `outputs/case_memory_integration/hypothesis_graphs.json`. Curated annotations stay
  `curated_annotation`; nothing in these graphs is qualified experimental evidence.
- Run: `python -m tools.case_memory.build_hypothesis_graph`
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
    sys.path.insert(0, str(ROOT))

from research.case_memory_integration import external_data as XD  # noqa: E402


def main() -> int:
    from maestro import case_memory as CM
    from maestro import hypothesis_graph as HG

    pack, _ = XD.load_pack()
    graphs: dict[str, dict] = {}
    for block, unit in sorted(pack["units"].items()):
        klass = unit["moa"]
        signature_status = (CM.ScientificMeasurementStatus.QUALIFIED if unit["conditions"]
                            else CM.ScientificMeasurementStatus.NOT_PLANNED)
        nodes = (
            HG.GraphNode("intervention", HG.NodeKind.INTERVENTION, unit["cmap_name"],
                         CM.ScientificMeasurementStatus.QUALIFIED),
            HG.GraphNode("target", HG.NodeKind.TARGET, klass,
                         CM.ScientificMeasurementStatus.NOT_PLANNED),
            HG.GraphNode("engagement", HG.NodeKind.ENGAGEMENT, "target engagement",
                         CM.ScientificMeasurementStatus.NOT_PLANNED),
            HG.GraphNode("pathway", HG.NodeKind.PATHWAY, "pathway state",
                         CM.ScientificMeasurementStatus.AMBIGUOUS if unit["conditions"]
                         else CM.ScientificMeasurementStatus.NOT_PLANNED),
            HG.GraphNode("observable", HG.NodeKind.OBSERVABLE, "L1000 Level 5 signature",
                         signature_status),
        )
        edges = (
            HG.GraphEdge("intervention", "target", "annotated_mechanism", 0,
                         evidence_class=CM.EvidenceClass.CURATED_ANNOTATION,
                         source_ref="compoundinfo_beta.txt:moa"),
            HG.GraphEdge("target", "engagement", "prerequisite", 0,
                         evidence_class=CM.EvidenceClass.MECHANISTIC_INFERENCE),
            HG.GraphEdge("engagement", "pathway", "proximal_consequence", 0,
                         evidence_class=CM.EvidenceClass.MECHANISTIC_INFERENCE),
            HG.GraphEdge("pathway", "observable", "state_reflection", 0,
                         evidence_class=CM.EvidenceClass.MECHANISTIC_INFERENCE),
        )
        graph = HG.HypothesisGraph(
            nodes, edges, (),
            {f"class:{klass}": ("intervention", "target", "pathway", "observable"),
             "class:other": ("intervention", "pathway", "observable")},
            advisory=("advisory:annotation_error",))
        errors = HG.validate_graph(graph)
        graphs[block] = {
            "unmeasured_layers": graph.unmeasured_layers(),
            "validation_errors": list(errors),
            "edges": [{"source": e.source, "target": e.target, "relation": e.relation_type,
                       "evidence_class": e.evidence_class.value, "promotable": e.promotable}
                      for e in graph.edges],
            "promotable_edges": len(graph.promotable_edges()),
        }
    out = ROOT / "outputs/case_memory_integration/hypothesis_graphs.json"
    out.write_text(json.dumps(graphs, indent=1))
    print(json.dumps({"graphs": len(graphs),
                      "with_promotable_edges": sum(1 for g in graphs.values()
                                                   if g["promotable_edges"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
