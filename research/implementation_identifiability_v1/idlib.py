"""G0 rules: condition binding, unit eligibility, dependence graph, effective counts.

The eligibility rules below are the frozen G0 rules of PROTOCOL.md. They are applied to metadata
(conditions, controls, lineage, whether numbers were extracted), never to outcome values.
"""
from __future__ import annotations

from itertools import combinations

LEVEL_NAMES = {
    1: "ANNOTATION_ONLY",
    2: "PARTIAL_PAIRED_EVIDENCE",
    3: "QUALIFIED_IMPLEMENTATION_UNIT",
    4: "INDEPENDENT_CONFIRMATION_UNIT",
}
SCALAR_FIELDS = ("cell", "genotype", "time_h", "readout")


def _fmt(value):
    return value


def bind_conditions(a: dict, b: dict) -> dict:
    """Return whether two observed records may be compared, and why not.

    `strict` binding needs identical cell, genotype, time, readout and dose. `descriptive` binding
    allows a dose difference (both recorded) but nothing else. Anything else is refused.
    """

    reasons = []
    for field in SCALAR_FIELDS:
        if a.get(field) != b.get(field):
            reasons.append(f"{field}: {_fmt(a.get(field))!r} vs {_fmt(b.get(field))!r}")
    if reasons:
        return {"bound": False, "mode": "refused", "reasons": reasons}
    da, db = a.get("dose_uM"), b.get("dose_uM")
    unknown = {"series_not_extracted", None}
    if da == db and da not in unknown:
        return {"bound": True, "mode": "strict", "reasons": []}
    if da in unknown or db in unknown:
        return {"bound": True, "mode": "descriptive", "reasons": [f"dose not comparable: {da!r} vs {db!r}"]}
    return {"bound": True, "mode": "descriptive", "reasons": [f"dose: {da!r} vs {db!r}"]}


def _by_id(records):
    return {r["id"]: r for r in records}


def _pairs_by_readout(recs, compounds):
    """Matched pairs of observed records for different implementations of the same readout."""
    out = []
    for a, b in combinations(recs, 2):
        if a["compound"] == b["compound"] or a["compound"] not in compounds or b["compound"] not in compounds:
            continue
        bd = bind_conditions(a, b)
        if bd["bound"]:
            out.append((a["id"], b["id"], bd["mode"]))
    return out


def classify_unit(unit: dict, records: list[dict]) -> dict:
    """Apply the frozen G0 level rules to one unit and return the failing criteria."""

    by_id = _by_id(records)
    recs = [by_id[i] for i in unit["record_ids"]]
    observed = [r for r in recs if r["evidence_type"] == "OBSERVED_EXPERIMENTAL_RESULT"]
    impls = unit["implementations"]
    term_readout = unit["primary_terminal_endpoint"]["readout"]
    term_time = unit["primary_terminal_endpoint"]["time_h"]
    terminal = [r for r in observed if r["level"] == "terminal" and r["time_h"] == term_time
                and r["compound"] in impls and term_readout.split(" / ")[0].split(" ")[0] in r["readout"]]
    term_pairs = _pairs_by_readout(terminal, impls)
    strict_term_pairs = [p for p in term_pairs if p[2] == "strict"]
    covered_terminal = {c for a, b, _ in strict_term_pairs for c in (by_id[a]["compound"], by_id[b]["compound"])}
    proximal = [r for r in observed if r["level"] == "proximal" and r["compound"] in impls]
    prox_pairs = [p for p in _pairs_by_readout(proximal, impls) if p[2] == "strict"]
    covered_proximal = {c for a, b, _ in prox_pairs for c in (by_id[a]["compound"], by_id[b]["compound"])}

    any_matched = bool(_pairs_by_readout([r for r in observed if r["level"] in ("proximal", "terminal")], impls))
    criteria = {
        "L2_matched_contrast_exists": any_matched,
        "L3a_all_implementations_share_primary_terminal_endpoint": set(impls) <= covered_terminal,
        "L3b_all_implementations_share_strict_proximal_readout": set(impls) <= covered_proximal,
        "L3c_discriminating_controls_and_genetic_reference_present": bool(unit["discriminating_control_records"])
        and bool(unit["genetic_reference_records"]),
        "L3d_numeric_values_with_uncertainty_for_primary_and_proximal": all(
            r["numeric_extracted"] and r["uncertainty_reported"] for r in terminal + proximal) and bool(terminal) and bool(proximal),
        "L3e_lineage_reported_to_batch_or_plate": all(r["lineage"]["batch"] != "not_reported" or r["lineage"]["plate"] != "not_reported"
                                                      for r in terminal + proximal) and bool(terminal),
        "L3f_genetic_reference_on_primary_terminal_endpoint": any(
            by_id[i]["readout"] == term_readout.split(" / ")[0] or term_readout.split(" ")[0] in by_id[i]["readout"]
            for i in unit["genetic_reference_records"]),
    }
    l3 = all(v for k, v in criteria.items() if k.startswith("L3"))
    level = 3 if l3 else (2 if criteria["L2_matched_contrast_exists"] else 1)
    return {
        "unit_id": unit["unit_id"], "level": level, "level_name": LEVEL_NAMES[level],
        "criteria": criteria, "failed": sorted(k for k, v in criteria.items() if not v),
        "terminal_pairs": term_pairs, "proximal_pairs": prox_pairs,
        "implementations_without_primary_terminal_record": sorted(set(impls) - covered_terminal),
        "independence": "KNOWN_CASE_LOGIC_ONLY; level 4 not assignable: outcomes were read by the designer",
    }


def effective_counts(units: list[dict], classes: list[dict], compounds: dict, records: list[dict]) -> dict:
    """Distinct generalisation units; wells, replicates and seeds are never counted."""

    levels = {c["unit_id"]: c["level"] for c in classes}
    eligible = [u for u in units if levels[u["unit_id"]] >= 3]
    with_terminal = [r for r in records if r.get("level") == "terminal"]
    impl_term = sorted({r["compound"] for r in with_terminal if r["compound"] in compounds})
    modes = sorted({compounds[c]["mode"] for c in impl_term})
    cells_term = sorted({r["cell"] for r in with_terminal})
    return {
        "level3_or_higher_units": len(eligible),
        "targets": 1, "target_families": 1,
        "implementations_with_terminal_records": impl_term,
        "modes_of_action_with_terminal_records": modes,
        "cell_backgrounds_with_terminal_records": cells_term,
        "independent_source_families": 1,
        "independent_source_papers": 2,
        "note": "two papers share the target, the compound JB170 and the field; they count as one generalisation family",
    }


def dependence_graph(records: list[dict], units: list[dict]) -> dict:
    """Nodes and edges for lineage, shared controls, shared compounds and generalisation units."""

    nodes, edges = [], []
    for sid in ("S1", "S2"):
        nodes.append({"id": sid, "type": "source"})
    for r in records:
        if r["evidence_type"] != "OBSERVED_EXPERIMENTAL_RESULT":
            continue
        nodes.append({"id": r["id"], "type": "record", "source": r["source"], "cell": r["cell"], "compound": r["compound"]})
        edges.append({"from": r["id"], "to": r["source"], "type": "reported_in"})
    batch = {}
    for r in records:
        b = r.get("lineage", {}).get("batch")
        if b and b != "not_reported":
            batch.setdefault(b, []).append(r["id"])
    for b, ids in batch.items():
        nodes.append({"id": "BATCH:" + b, "type": "shared_batch"})
        for i in ids:
            edges.append({"from": i, "to": "BATCH:" + b, "type": "shares_batch_and_controls"})
    by_compound = {}
    for r in records:
        if r["evidence_type"] == "OBSERVED_EXPERIMENTAL_RESULT" and r["compound"]:
            by_compound.setdefault((r["compound"], r["source"]), []).append(r["id"])
    for (c, s), ids in by_compound.items():
        nodes.append({"id": f"COMPOUND:{c}@{s}", "type": "implementation_in_source"})
        for i in ids:
            edges.append({"from": i, "to": f"COMPOUND:{c}@{s}", "type": "same_implementation_repeat_not_independent"})
    edges.append({"from": "COMPOUND:JB170@S1", "to": "COMPOUND:JB170@S2", "type": "same_molecule_cross_source_bridge",
                  "note": "same compound and MV4-11; different labs and protocols; not a technical replicate and not an independent implementation"})
    for u in units:
        nodes.append({"id": u["unit_id"], "type": "unit", "generalisation_family": "AURKA_aurora_kinase"})
        for rid in u["record_ids"]:
            edges.append({"from": rid, "to": u["unit_id"], "type": "member_of_unit"})
    return {"nodes": nodes, "edges": edges,
            "lineage_notes": [
                "cell stock, culture initiation and treatment batch are not reported for any record except the S1 TMT batch",
                "multiple records of one compound inside a source are one implementation, not several",
                "S1 and S2 are separate papers on one target family and share JB170; they are not two independent target families",
            ]}


def cost_total(actions: list[dict], selected: list[str]) -> dict:
    """Wells and days for a set of bundles; missing prices stay missing instead of becoming zero."""
    by = {a["action_id"]: a for a in actions}
    wells = sum(by[s]["wells_min"] for s in selected)
    days = [by[s]["turnaround_days"] for s in selected]
    currency = [by[s]["cost_currency"] for s in selected]
    return {"wells": wells,
            "days": None if any(d is None for d in days) else max(days),
            "currency": None if any(c is None for c in currency) else sum(currency),
            "missing_price_fields": sum(c is None for c in currency)}
