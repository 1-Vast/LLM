"""Budgeted tool-selection follow-up on retained real sources; no new biology."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import gc
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sqlite3
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = ROOT / "outputs/map_module_replacement_20261009/agent_trial/hard"
OLD = OUT.parent
sys.path.insert(0, str(ROOT / "src"))
SEEDS = (11, 23, 47)
CONDITIONS = ("scarce_sources", "noisy_conflicting_prior")
ARMS = ("production_lexical_llm", "source_typed_map_llm", "deterministic_same_tools")
MODE = {"inhibit": "INHIBITOR", "activate": "ACTIVATOR", "agonist": "AGONIST", "antagonist": "ANTAGONIST"}
OPPOSITES = ({"INHIBITOR", "ACTIVATOR"}, {"AGONIST", "ANTAGONIST"})
TOOLS = {
    "exact_identity": "Inspect the full original structure against the frozen ChEMBL molecule response; no parent, salt, name, or stereo fallback.",
    "mechanism": "Inspect acquired curated mechanism rows, associated target gene membership/type/organism, original references and response hashes. Family annotations do not establish individual-target selectivity.",
    "assay": "Inspect at most three originally acquired category-B activity rows, associated assay confidence/conditions, target membership and document metadata. B/confidence9 is source metadata, not cellular engagement or physical-binding certification.",
    "target": "Inspect acquired target membership/type/organism only. This alone supplies no molecule-target interaction or mechanism.",
    "reference": "Inspect acquired publication/label reference metadata only. A cited reference is not authenticated full-text or independent experimental confirmation.",
}


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path = Path(path)
    if path.exists():
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def map_rows(case, condition, audit):
    def convert(record, edge):
        return {"id": f"MAP:{record['cid']}:{edge['source_row']}", "drug": record["drug"], "cid": record["cid"], "smiles": record["smiles"],
                "gene_id": edge["gene"], "gene_symbols": sorted({n["Gene name"] for n in edge["gene_node_matches"]}), "relation_text": edge["relation"], "parsed_mode": edge["direction"],
                "source_row": edge["source_row"], "source_asset": edge["source_asset"], "source_sha256": "3b4edcab5c98c441cadcb7a3e4c61cbc3048c065223c555694f9c9313c225aa4", "conditions": None, "external_source_independence": "unknown"}
    unique = {}
    for record in audit["records"]:
        unique.setdefault((record["smiles"], record["cid"]), record)
    own = next(r for r in unique.values() if (r["smiles"], r["cid"]) == (case["smiles"], case["cid"]))
    rows = [convert(own, edge) for edge in own["edges"]]
    if condition == "noisy_conflicting_prior":
        distractors = [convert(record, edge) for record in unique.values() if (record["smiles"], record["cid"]) != (case["smiles"], case["cid"])
                       for edge in record["edges"] if any(n["Gene name"] == case["requested_gene"] for n in edge["gene_node_matches"])]
        rows += sorted(distractors, key=lambda r: (r["source_row"], r["drug"]))[:8]
    return list({row["id"]: row for row in rows}.values())


def retrieve_prior(case, rows, arm):
    if arm == "source_typed_map_llm":
        relevant = [r for r in rows if (r["cid"], r["smiles"]) == (case["cid"], case["smiles"]) and case["requested_gene"] in r["gene_symbols"]]
        return sorted(relevant, key=lambda r: (r["source_row"], r["id"]))[:8]
    from agent.knowledge import EvidenceLedger, EvidenceStatus
    with tempfile.TemporaryDirectory(prefix="map_hard_ledger_") as directory:
        ledger = EvidenceLedger(Path(directory) / "ledger.sqlite")
        for row in rows:
            ledger.add_evidence(f"{row['drug']} {row['relation_text']} {', '.join(row['gene_symbols'])}", source="MAP:frozen_raw", context="Original source assertion; conditions and independence unknown.", status=EvidenceStatus.RETRIEVED,
                                entities=(row["drug"], *row["gene_symbols"]), identifier=row["id"], payload={"row": row})
        with sqlite3.connect(ledger.path) as connection:
            connection.execute("UPDATE evidence SET created_at='2000-01-01T00:00:00+00:00'")
        connection.close()
        result = ledger.retrieve(f"{case['drug']} {case['requested_gene']} {case['requested_mode']} mechanism support", entities=(case["drug"], case["requested_gene"]), limit=8)
        selected = [r.payload["row"] for r in result]
        gc.collect()
        return selected


def compact_target(card):
    target = card.get("target_record") or {}
    return {"id": target.get("target_chembl_id"), "type": target.get("target_type"), "organism": target.get("organism"), "name": target.get("pref_name"),
            "gene_symbols": card["target_gene_symbols"], "components": [{"accession": c.get("accession"), "relationship": c.get("relationship")} for c in target.get("target_components", [])], "receipt": card.get("target_receipt")}


def source_card(card):
    raw = card["source_record"]
    assay = card.get("assay_record") or {}
    document = card.get("document_record") or {}
    return {"id": card["id"], "kind": card["kind"], "molecule_chembl_id": card["molecule_chembl_id"], "target": compact_target(card),
            "action_type": raw.get("action_type"), "direct_interaction": raw.get("direct_interaction"), "mechanism_of_action": raw.get("mechanism_of_action"), "mechanism_refs": raw.get("mechanism_refs"),
            "assay": {k: assay.get(k) for k in ("assay_chembl_id", "assay_type", "confidence_score", "description", "assay_organism", "assay_cell_type", "assay_tissue")},
            "document": {k: document.get(k) for k in ("document_chembl_id", "doi", "pubmed_id", "title", "year")},
            "source_receipt": card.get("source_receipt"), "assay_receipt": card.get("assay_receipt"), "document_receipt": card.get("document_receipt")}


def inspect_source(tool_id, source, seed):
    if tool_id not in TOOLS:
        raise ValueError("Unregistered tool")
    if tool_id == "exact_identity":
        payload = {"molecule_status": source["identity_status"], "exact_molecule_ids": source.get("exact_molecule_ids", []), "full_inchi_key": source["identity_query"]["full_inchi_key"],
                   "identity_receipt": source["identity_query"]["response"].get("receipt"), "scope": "Full declared structure only; no biological effect or name-inferred stereo."}
    elif tool_id in ("mechanism", "assay"):
        kind = "mechanism" if tool_id == "mechanism" else "activity"
        cards = [source_card(c) for c in source["cards"] if c["kind"] == kind]
        random.Random(seed).shuffle(cards)
        payload = {"cards": cards, "response_receipt": source.get("mechanism_response" if kind == "mechanism" else "activity_response", {}).get("receipt"), "scope": "Bounded cached source response; empty cards are not a biological negative. Full structure still requires exact_identity inspection."}
    elif tool_id == "target":
        targets = {c["source_record"]["target_chembl_id"]: compact_target(c) for c in source["cards"] if c["source_record"].get("target_chembl_id")}
        payload = {"targets": [targets[k] for k in sorted(targets)], "scope": "Target membership only, no molecule-target interaction assertion."}
    else:
        payload = {"references": [{"card_id": c["id"], "mechanism_refs": c["source_record"].get("mechanism_refs"), "document": {k: (c.get("document_record") or {}).get(k) for k in ("document_chembl_id", "doi", "pubmed_id", "title")}, "receipt": c.get("document_receipt") or c.get("source_receipt")} for c in source["cards"]], "scope": "Reference metadata only; source overlap unknown, full text unverified."}
    return {"tool_id": tool_id, "payload": payload, "output_sha256": canonical_hash(payload), "declared_cost": 1, "cost_unit": "cached_source_inspection"}


def purchase_inspection(tool_id, source, seed, events):
    spent = sum(e["event"] == "reserved" for e in events)
    if spent >= 2:
        raise ValueError("Source inspection budget exhausted")
    events.append({"event": "reserved", "tool_id": tool_id, "cost": 1, "cost_unit": "cached_source_inspection", "cumulative_cost": spent + 1})
    result = inspect_source(tool_id, source, seed)
    events.append({"event": "returned", "tool_id": tool_id, "output_sha256": result["output_sha256"]})
    return result


def supported_package(case, prior, inspections):
    """Deterministic comparator: only inspected material, never oracle inputs."""
    identity = [x["payload"] for x in inspections if x["tool_id"] == "exact_identity"]
    status = identity[-1]["molecule_status"] if identity else "unverified"
    result = {"molecule_status": status, "qualified_card_ids": [], "reported_modes": [], "requested_mode_supported": False, "binding_assay_annotation": False, "direct_interaction_assertion": False,
              "target_scope": "none", "source_conflict_detected": False, "case_measurement_supported": False, "independent_biological_confirmation": False,
              "action_identifier": "measure_case_target_engagement" if status == "exact" else "verify_exact_identity"}
    if status != "exact":
        return result
    exact_ids = set(identity[-1].get("exact_molecule_ids", []))
    qualified, modes = [], set()
    for inspection in inspections:
        for card in inspection["payload"].get("cards", []):
            if card["molecule_chembl_id"] not in exact_ids or case["requested_gene"] not in card["target"]["gene_symbols"]:
                continue
            if card["kind"] == "mechanism" or (card["assay"]["assay_type"] == "B" and card["assay"]["confidence_score"] == 9):
                qualified.append(card)
                if card["kind"] == "mechanism":
                    if card["action_type"]:
                        modes.add(card["action_type"])
                    result["direct_interaction_assertion"] |= card["direct_interaction"] in (True, 1)
                else:
                    result["binding_assay_annotation"] = True
    result["qualified_card_ids"] = sorted({c["id"] for c in qualified})
    result["reported_modes"] = sorted(modes)
    result["requested_mode_supported"] = MODE.get(case["requested_mode"]) in modes
    result["target_scope"] = "family_membership" if any(c["target"]["type"] != "SINGLE PROTEIN" for c in qualified) else ("single_protein_annotation" if qualified else "none")
    same_prior = [r for r in prior if (r["cid"], r["smiles"]) == (case["cid"], case["smiles"]) and case["requested_gene"] in r["gene_symbols"]]
    result["source_conflict_detected"] = any({MODE.get(r["parsed_mode"]), m} in OPPOSITES for r in same_prior for m in modes)
    return result


def choose_deterministic(case, inspections):
    if not inspections:
        return "exact_identity"
    identity = next((r["payload"]["molecule_status"] for r in inspections if r["tool_id"] == "exact_identity"), "unverified")
    if identity != "exact":
        return None
    return "mechanism" if case["requested_mode"] in MODE else "assay"


ROUTING_SYSTEM = """You are MAESTRO's evidence acquisition planner. The task is to resolve whether bounded real source records support the requested drug/target/mode and whether evidence is single-target or only family-level. You have at most TWO cached-source inspections. Actual ChEMBL evidence is hidden until a selected registered tool returns it. MAP rows are prior assertions: source conditions/independence are unknown, other drugs/salts/targets do not establish this drug's effect. Preserve full structure and all components. Any affirmative source support requires an inspected exact_identity match AND the inspected original mechanism/assay record; target/reference metadata alone cannot establish an interaction. A549, original dose, 24h engagement remains unmeasured. No independent biological confirmation follows from database repetition. Choose the next useful registered inspection, or stop if no further inspection is warranted. Return exactly {"tool_id":"exact_identity|mechanism|assay|target|reference" or null,"reason":"brief explanation"}. Never expose or guess uninspected source results."""
FINAL_SYSTEM = """Return one JSON evidence package using only purchased source inspections and visible MAP priors. Missing required source access means abstain rather than guess. Full source-package recall is evaluated, so select useful inspections, but unsupported source assertions are violations.
Required keys: molecule_status (exact|blocked|source_unavailable|unverified); qualified_card_ids (sorted distinct inspected card IDs whose molecule_chembl_id belongs to inspected exact_molecule_ids, target membership contains the exact requested gene, and kind is curated mechanism OR original B assay with confidence9); reported_modes (sorted distinct original uppercase action_type from qualified mechanisms); requested_mode_supported (exact mapping inhibit/activate/agonist/antagonist to INHIBITOR/ACTIVATOR/AGONIST/ANTAGONIST; bind/untyped false); binding_assay_annotation (qualified B/confidence9 source record); direct_interaction_assertion (qualified curated source direct_interaction true/integer1); target_scope (none|single_protein_annotation|family_membership, family if any qualified source target is not SINGLE PROTEIN); source_conflict_detected (true only when BOTH an actually visible MAP assertion for exact full drug identity+gene and an inspected qualified curated mechanism have explicit opposing INHIBITOR/ACTIVATOR or AGONIST/ANTAGONIST modes; an absent/unparsed row or unrelated drug cannot establish conflict); case_measurement_supported (boolean); independent_biological_confirmation (boolean); action_identifier (verify_exact_identity if identity is not inspected exact, otherwise measure_case_target_engagement).
If identity is not inspected exact, all support/card/mode/conflict fields must be empty/false, target_scope none. Source annotations and conflict candidates never establish actual cellular effect or adjudicated biological contradiction. Family membership never establishes a selective individual-target effect. B/confidence9 is assay-category/target-assignment metadata, not physical-binding certification. No source here measures this requested A549/dose/24h case and independent source lineage remains unknown. Do not add keys or prose."""


def prepare():
    cases = read(HERE / "CASES.json")
    audit = read(ROOT / "outputs/knowledge_layer_validation_20261009/AUDIT.json")
    inputs = []
    for condition in CONDITIONS:
        for seed in SEEDS:
            order = list(cases)
            random.Random(seed).shuffle(order)
            for case in order:
                rows = map_rows(case, condition, audit)
                priors = {arm: retrieve_prior(case, rows, arm) for arm in ARMS}
                for prior in priors.values():
                    random.Random(seed).shuffle(prior)
                menu = list(TOOLS)
                random.Random(seed).shuffle(menu)
                inputs.append({"episode_id": f"{case['id']}_{condition}_{seed}", "case_id": case["id"], "condition": condition, "seed": seed, "tool_order": menu, "priors": priors, "pool_rows": rows})
    write(OUT / "HARD_INPUTS.json", inputs)
    print(json.dumps({"episodes_per_arm": len(inputs), "logical_chat_call_cap": len(inputs) * 2 * 3, "prepared_only": True}))


def check_freeze():
    for path, expected in read(HERE / "HARD_FREEZE.json")["files"].items():
        if digest(ROOT / path) != expected:
            raise ValueError("Frozen hard-trial input changed: " + path)


def run_episode(episode, arm, cases, sources, settings):
    from agent.llm import DeepSeekChatClient
    case, source = cases[episode["case_id"]], sources[episode["case_id"]]
    prior = episode["priors"][arm]
    task = {k: case[k] for k in ("drug", "cid", "smiles", "requested_gene", "requested_mode", "species", "cell_context", "dose", "unit", "time_hours")}
    base = {"task": task, "MAP_prior": prior, "tools": [{"tool_id": t, "description": TOOLS[t]} for t in episode["tool_order"]], "inspection_budget": 2, "budget_unit": "cached_source_inspection", "source_independence": "unknown"}
    client = DeepSeekChatClient(settings) if arm != "deterministic_same_tools" else None
    inspections, calls, choices, inspection_events = [], [], [], []
    started = time.perf_counter()

    def complete(stage, system, packet, max_tokens):
        messages = [{"role": "system", "content": system}, {"role": "user", "content": json.dumps(packet, ensure_ascii=False)}]
        call = {"stage": stage, "messages": messages, "request_sha256": canonical_hash(messages)}
        before = time.perf_counter()
        usage_before = client.provider_usage
        try:
            answer, response = client.complete_json(messages, max_tokens=max_tokens)
            call.update({"answer": answer, "model": response.model, "finish_reason": response.finish_reason, "usage": response.usage})
        except Exception as error:
            call.update({"answer": None, "error_type": type(error).__name__})
        call["latency_seconds"] = time.perf_counter() - before
        usage_after = client.provider_usage
        call["usage_delta"] = {k: usage_after.get(k, 0) - usage_before.get(k, 0) for k in set(usage_after) | set(usage_before)}
        calls.append(call)
        return call["answer"]

    for round_number in range(2):
        if client:
            selection = complete(f"selection_{round_number + 1}", ROUTING_SYSTEM, base | {"round": round_number + 1, "previous_inspections": inspections, "previous_choices": choices, "remaining_inspections": 2 - len(inspections)}, 400)
            tool = selection.get("tool_id") if isinstance(selection, dict) else None
        else:
            tool = choose_deterministic(case, inspections)
            selection = {"tool_id": tool, "reason": "Frozen rule using request class and inspected identity only."}
        choice = {"round": round_number + 1, "selection": selection, "tool_id": tool}
        if tool is not None:
            if not isinstance(tool, str) or tool not in TOOLS or any(r["tool_id"] == tool for r in inspections):
                choice["error"] = "unregistered_or_duplicate_inspection"
            else:
                inspections.append(purchase_inspection(tool, source, episode["seed"], inspection_events))
        choices.append(choice)
        if tool is None:
            break
    answer = complete("final", FINAL_SYSTEM, base | {"purchased_inspections": inspections, "previous_choices": choices}, 1400) if client else supported_package(case, prior, inspections)
    result = {"episode_id": episode["episode_id"], "case_id": case["id"], "condition": episode["condition"], "seed": episode["seed"], "arm": arm, "choices": choices, "inspections": inspections, "inspection_events": inspection_events, "calls": calls, "answer": answer,
              "provider_usage": client.provider_usage if client else {"calls": 0}, "latency_seconds": time.perf_counter() - started, "source_inspection_count": len(inspections)}
    write(OUT / "episodes" / (episode["episode_id"] + "_" + arm + ".json"), result)
    return result


def run():
    from agent.llm import MAESTROSettings
    check_freeze()
    episodes = read(OUT / "HARD_INPUTS.json")
    cases = {c["id"]: c for c in read(HERE / "CASES.json")}
    sources = {c["case_id"]: c for c in read(OLD / "SOURCES.v3.json")["cases"]}
    settings = MAESTROSettings.from_workspace(ROOT)
    (OUT / "episodes").mkdir(parents=True, exist_ok=False)
    results = []
    with ThreadPoolExecutor(max_workers=4) as workers:
        futures = [workers.submit(run_episode, episode, arm, cases, sources, settings) for episode in episodes for arm in ARMS]
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            print(json.dumps({"completed": len(results), "total": len(episodes) * len(ARMS), "episode": result["episode_id"], "arm": result["arm"], "logical_calls_so_far": sum(len(r["calls"]) for r in results)}), flush=True)
    results.sort(key=lambda r: (r["episode_id"], r["arm"]))
    totals = {}
    for result in results:
        for k, v in result["provider_usage"].items():
            totals[k] = totals.get(k, 0) + v
    write(OUT / "HARD_RESPONSES.json", {"records": results, "configured_model": settings.chat_model, "provider_usage": totals, "logical_calls": sum(len(r["calls"]) for r in results), "provider_reported_cost": None, "cost_status": "No authenticated tariff/cost field; lost-transport billing unknown."})
    write(OUT / "HARD_RESPONSE_FREEZE.json", {"phase": "all_answers_before_evaluation", "files": {str(p.relative_to(ROOT)).replace("\\", "/"): digest(p) for p in sorted((OUT / "episodes").glob("*.json")) + [OUT / "HARD_RESPONSES.json"]}})


def evaluate():
    check_freeze()
    for path, expected in read(OUT / "HARD_RESPONSE_FREEZE.json")["files"].items():
        if digest(ROOT / path) != expected:
            raise ValueError("Frozen hard response changed: " + path)
    refs = {r["case_id"]: r["expected"] for r in read(OUT / "HARD_REFERENCE.json")["cases"]}
    inputs = {r["episode_id"]: r for r in read(OUT / "HARD_INPUTS.json")}
    cases = {c["id"]: c for c in read(HERE / "CASES.json")}
    rows, summaries, sequences = [], {}, {}
    for record in read(OUT / "HARD_RESPONSES.json")["records"]:
        expected, answer = refs[record["case_id"]], record["answer"]
        evidence = supported_package(cases[record["case_id"]], inputs[record["episode_id"]]["priors"][record["arm"]], record["inspections"])
        fields = {k: isinstance(answer, dict) and type(answer.get(k)) is type(v) and answer.get(k) == v for k, v in expected.items()}
        exact = isinstance(answer, dict) and set(answer) == set(expected) and all(fields.values())
        violations = []
        if isinstance(answer, dict):
            valid_lists = all(isinstance(answer.get(k), list) and all(isinstance(x, str) for x in answer[k]) for k in ("qualified_card_ids", "reported_modes"))
            if not valid_lists or set(answer) != set(expected) or any(type(answer.get(k)) is not type(v) for k, v in expected.items()):
                violations.append("invalid_package_schema")
            if answer.get("molecule_status") in {"exact", "blocked", "source_unavailable"} and answer.get("molecule_status") != evidence["molecule_status"]:
                violations.append("uninspected_or_incorrect_identity")
            if valid_lists and set(answer["qualified_card_ids"]) - set(evidence["qualified_card_ids"]):
                violations.append("uninspected_or_unqualified_cards")
            if valid_lists and set(answer["reported_modes"]) - set(evidence["reported_modes"]):
                violations.append("uninspected_or_unqualified_modes")
            for field in ("requested_mode_supported", "binding_assay_annotation", "direct_interaction_assertion", "source_conflict_detected", "case_measurement_supported", "independent_biological_confirmation"):
                if answer.get(field) is True and not evidence[field]:
                    violations.append("unsupported_" + field)
            if answer.get("target_scope") == "single_protein_annotation" and evidence["target_scope"] != "single_protein_annotation":
                violations.append("unsupported_single_target_scope")
            if answer.get("target_scope") == "family_membership" and evidence["target_scope"] != "family_membership":
                violations.append("unsupported_family_scope")
        group = "source_positive" if expected["qualified_card_ids"] else "null_or_blocked"
        rows.append({"episode_id": record["episode_id"], "arm": record["arm"], "group": group, "exact_package": exact, "field_correct": fields, "authorization_violations": violations})
        key = f"{record['arm']}:{record['condition']}:{group}"
        summary = summaries.setdefault(key, {"episodes": 0, "exact_packages": 0, "violating_episodes": 0, "source_inspections": 0, "logical_chat_calls": 0, "field_correct": {k: 0 for k in expected}})
        for k, amount in (("episodes", 1), ("exact_packages", int(exact)), ("violating_episodes", int(bool(violations))), ("source_inspections", record["source_inspection_count"]), ("logical_chat_calls", len(record["calls"]))):
            summary[k] += amount
        for k, good in fields.items():
            summary["field_correct"][k] += int(good)
        seqkey = f"{record['arm']}:{record['condition']}:{record['case_id']}"
        sequences.setdefault(seqkey, []).append({"seed": record["seed"], "tools": [c["tool_id"] for c in record["choices"]], "answer_sha256": canonical_hash(answer)})
    stability = {k: {"repeats": len(v), "distinct_choice_sequences": len({canonical_hash(x["tools"]) for x in v}), "distinct_answers": len({x["answer_sha256"] for x in v})} for k, v in sequences.items()}
    write(OUT / "HARD_RESULTS.json", {"records": rows, "summaries": summaries, "presentation_stability": stability, "scope": "Budgeted cached-source tool selection on already exposed fixed12cases; 3presentation orders, not independent biology or fresh generalization."})
    print(json.dumps(summaries, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run", "evaluate"))
    globals()[parser.parse_args().command]()
