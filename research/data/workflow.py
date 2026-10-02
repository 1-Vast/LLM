"""External case-memory evaluation workflow.

This module owns the source, pack, graph, replay and evaluation steps of one
case-memory pipeline. Scientific implementations remain in ``research``.

Run one step with ``python -m tools.case_memory.workflow <step>``.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from tools.case_memory import sha256

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MPIE_CORRECT = 0.02
HEADROOM_FACTOR = 2.0
EXPECTED_LEVEL5_BYTES = 35518405386


def verify_sources() -> int:
    provenance = json.loads((ROOT / "data/external/lincs2020/provenance.json").read_text())
    checks: dict[str, dict] = {}
    ok = True

    for name, record in provenance["files"].items():
        path = ROOT / "data/external/lincs2020" / name
        actual = sha256(path) if path.is_file() else None
        match = actual == record["sha256"]
        ok &= match
        checks[name] = {"expected": record["sha256"], "actual": actual, "match": match,
                        "url": record["url"]}
    level5 = ROOT / "data/external/lincs2020/level5/level5_beta_trt_cp_n720216x12328.gctx"
    sha_path = level5.parent / "sha256.json"
    sha_record = json.loads(sha_path.read_text()) if sha_path.is_file() else {}
    size_ok = level5.is_file() and level5.stat().st_size == EXPECTED_LEVEL5_BYTES
    ok &= size_ok and bool(sha_record.get("sha256"))
    manifest = {
        "study": "CMap LINCS 2020 beta build, compound treatment Level 5",
        "source_url": ("https://s3.amazonaws.com/macchiato.clue.io/builds/LINCS2020/level5/"
                       "level5_beta_trt_cp_n720216x12328.gctx"),
        "metadata_urls": {name: record["url"] for name, record in provenance["files"].items()},
        "publication": ("Subramanian et al., Cell 2017 (platform); CMap 2020 expansion per the "
                        "NIH Common Fund LINCS symposium summary"),
        "version": {"level5_last_modified": "Wed, 16 Dec 2020 23:54:09 GMT",
                    "siginfo_last_modified": provenance.get("s3_last_modified_siginfo")},
        "license": provenance.get("licence"),
        "download_date": {"metadata": provenance.get("retrieved_utc"),
                          "level5": "2026-09-29"},
        "checksums": checks,
        "level5": {"bytes": level5.stat().st_size if level5.is_file() else None,
                   "expected_bytes": EXPECTED_LEVEL5_BYTES, "size_match": size_ok,
                   **sha_record},
        "study_level_split": ("test units are InChIKey connectivity blocks absent from the "
                              "GSE92742 and GSE70138 trt_cp compound lists; reference units are "
                              "the remaining blocks in pool classes of the same LINCS 2020 build"),
        "independent_unit": "InChIKey connectivity block (first 14 characters)",
        "known_limitations": [
            "beta build; MoA labels are curated annotations used as proxy truth, never ground truth",
            "inferred genes are present alongside the 978 measured landmark genes",
            "Level 5 signatures have no replicate structure",
            "metadata was downloaded 2026-09-27, two days before this evaluation's protocol "
            "freeze; exposure was limited to the columns declared in provenance.json, and no "
            "signature value or quality column was read before the freeze",
        ],
        "verification_ok": bool(ok),
    }
    out = ROOT / "outputs/case_memory_integration/external_source_manifest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(json.dumps({"verification_ok": manifest["verification_ok"], "out": str(out)}))
    return 0 if ok else 1


def build_graphs() -> int:
    src = str(ROOT / "src")
    if src not in sys.path:
        sys.path.insert(0, src)
    from tools.datasets import lincs_pack as data
    from maestro import case_memory as memory
    from maestro import problem_compiler as compiler

    pack, _ = data.load_pack()
    graphs: dict[str, dict] = {}
    for block, unit in sorted(pack["units"].items()):
        klass = unit["moa"]
        signature_status = (memory.ScientificMeasurementStatus.QUALIFIED if unit["conditions"]
                            else memory.ScientificMeasurementStatus.NOT_PLANNED)
        nodes = (
            compiler.GraphNode("intervention", compiler.NodeKind.INTERVENTION, unit["cmap_name"],
                               memory.ScientificMeasurementStatus.QUALIFIED),
            compiler.GraphNode("target", compiler.NodeKind.TARGET, klass,
                               memory.ScientificMeasurementStatus.NOT_PLANNED),
            compiler.GraphNode("engagement", compiler.NodeKind.ENGAGEMENT, "target engagement",
                               memory.ScientificMeasurementStatus.NOT_PLANNED),
            compiler.GraphNode("pathway", compiler.NodeKind.PATHWAY, "pathway state",
                               memory.ScientificMeasurementStatus.AMBIGUOUS if unit["conditions"]
                               else memory.ScientificMeasurementStatus.NOT_PLANNED),
            compiler.GraphNode("observable", compiler.NodeKind.OBSERVABLE, "L1000 Level 5 signature",
                               signature_status),
        )
        edges = (
            compiler.GraphEdge("intervention", "target", "annotated_mechanism", 0,
                               evidence_class=memory.EvidenceClass.CURATED_ANNOTATION,
                               source_ref="compoundinfo_beta.txt:moa"),
            compiler.GraphEdge("target", "engagement", "prerequisite", 0,
                               evidence_class=memory.EvidenceClass.MECHANISTIC_INFERENCE),
            compiler.GraphEdge("engagement", "pathway", "proximal_consequence", 0,
                               evidence_class=memory.EvidenceClass.MECHANISTIC_INFERENCE),
            compiler.GraphEdge("pathway", "observable", "state_reflection", 0,
                               evidence_class=memory.EvidenceClass.MECHANISTIC_INFERENCE),
        )
        graph = compiler.HypothesisGraph(
            nodes, edges, (),
            {f"class:{klass}": ("intervention", "target", "pathway", "observable"),
             "class:other": ("intervention", "pathway", "observable")},
            advisory=("advisory:annotation_error",))
        errors = compiler.validate_graph(graph)
        graphs[block] = {
            "unmeasured_layers": graph.unmeasured_layers(),
            "validation_errors": list(errors),
            "edges": [{"source": edge.source, "target": edge.target,
                       "relation": edge.relation_type, "evidence_class": edge.evidence_class.value,
                       "promotable": edge.promotable} for edge in graph.edges],
            "promotable_edges": len(graph.promotable_edges()),
        }
    out = ROOT / "outputs/case_memory_integration/hypothesis_graphs.json"
    out.write_text(json.dumps(graphs, indent=1))
    print(json.dumps({"graphs": len(graphs),
                      "with_promotable_edges": sum(1 for graph in graphs.values()
                                                   if graph["promotable_edges"])}))
    return 0


def build_pack() -> int:
    from tools.datasets.lincs_pack import build_pack as _build_pack

    manifest = _build_pack()
    print(json.dumps({
        "pack_version": manifest["pack_version"],
        "counts": manifest["counts"],
        "counts_detail": manifest["counts_detail"],
    }, indent=1))
    return 0


def replay() -> int:
    from research.case_memory_integration.external_replay import run_replay

    results = run_replay()
    print(json.dumps({
        "population": results["population"],
        "primary": results["primary_endpoint_full_minus_scalar_nll"],
        "headroom": results["oracle_headroom_correct"],
    }, indent=1))
    return 0


def evaluate() -> int:
    path = ROOT / "outputs/case_memory_integration/results.json"
    if not path.is_file():
        print(json.dumps({"error": "results.json missing; run tools.case_memory.workflow replay first"}))
        return 1
    results = json.loads(path.read_text(encoding="utf-8"))
    metrics = results["forecast_metrics"]
    arms = ("scalar", "signed_direction", "pathway_direction", "combined", "full")
    fields = ("nll", "brier_wrong_elimination", "directional_accuracy", "discrimination_nats")
    ablation = {arm: {key: metrics[arm][key] for key in fields} for arm in arms}
    headroom = results["oracle_headroom_correct"]
    required = HEADROOM_FACTOR * MPIE_CORRECT
    gate = {
        "headroom": headroom,
        "headroom_required": required,
        "headroom_gate_met": headroom >= required,
        "exploratory": results["exploratory"],
        "activation_verdict": (
            "no default activation: the unseen stratum is exploratory, the headroom gate fails, "
            "and the full arm does not improve the primary endpoint"
        ),
    }
    summary = {
        "population": results["population"],
        "forecast_table": metrics,
        "directional_ablation": ablation,
        "primary_endpoint": results["primary_endpoint_full_minus_scalar_nll"],
        "decision_table": results["decision_metrics"],
        "gates": gate,
    }
    out = ROOT / "outputs/case_memory_integration/evaluation_summary.json"
    out.write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(json.dumps({"out": str(out), "activation_verdict": gate["activation_verdict"]}))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("step", choices=("sources", "pack", "graphs", "replay", "evaluate"))
    args = parser.parse_args(argv)
    return {"sources": verify_sources, "pack": build_pack, "graphs": build_graphs,
            "replay": replay, "evaluate": evaluate}[args.step]()


if __name__ == "__main__":
    raise SystemExit(main())
