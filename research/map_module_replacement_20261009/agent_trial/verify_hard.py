"""Independent offline raw/source-access reconstruction of the hard trial."""
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import re

from rdkit import Chem
from rdkit.Chem import inchi

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = ROOT / "outputs/map_module_replacement_20261009/agent_trial/hard"
OLD = OUT.parent
MODES = {"inhibit": "INHIBITOR", "activate": "ACTIVATOR", "agonist": "AGONIST", "antagonist": "ANTAGONIST"}
ARMS = ("production_lexical_llm", "source_typed_map_llm", "deterministic_same_tools")
SEEDS = (11, 23, 47)
CONDITIONS = ("scarce_sources", "noisy_conflicting_prior")
TOOL_ORDER = ("exact_identity", "mechanism", "assay", "target", "reference")


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def jhash(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def equal(left, right, what):
    if left != right:
        raise AssertionError(what)


def canonical(smiles):
    molecule = Chem.MolFromSmiles(smiles)
    if molecule is None:
        raise AssertionError("Invalid declared full structure")
    return Chem.MolToSmiles(molecule, canonical=True, isomericSmiles=True)


def tokens(text):
    return set(re.findall(r"[A-Za-z0-9_]{2,}|[\u4e00-\u9fff]{2,}", text.lower()))


def original_pool(case, condition, audit):
    unique = {}
    for drug in audit:
        unique.setdefault((drug["smiles"], drug["cid"]), drug)
    original = unique[(case["smiles"], case["cid"])]

    def row(drug, edge):
        return {"id": f"MAP:{drug['cid']}:{edge['source_row']}", "drug": drug["drug"], "cid": drug["cid"], "smiles": drug["smiles"], "gene_id": edge["gene"],
                "gene_symbols": sorted({n["Gene name"] for n in edge["gene_node_matches"]}), "relation_text": edge["relation"], "parsed_mode": edge["direction"], "source_row": edge["source_row"],
                "source_asset": edge["source_asset"], "source_sha256": "3b4edcab5c98c441cadcb7a3e4c61cbc3048c065223c555694f9c9313c225aa4", "conditions": None, "external_source_independence": "unknown"}

    material = [row(original, edge) for edge in original["edges"]]
    if condition == "noisy_conflicting_prior":
        candidates = [row(drug, edge) for drug in unique.values() if (drug["smiles"], drug["cid"]) != (case["smiles"], case["cid"])
                      for edge in drug["edges"] if case["requested_gene"] in {n["Gene name"] for n in edge["gene_node_matches"]}]
        material.extend(sorted(candidates, key=lambda r: (r["source_row"], r["drug"]))[:8])
    return list({r["id"]: r for r in material}.values())


def expected_prior(case, rows, arm, seed):
    if arm == "source_typed_map_llm":
        chosen = sorted([r for r in rows if r["cid"] == case["cid"] and r["smiles"] == case["smiles"] and case["requested_gene"] in r["gene_symbols"]], key=lambda r: (r["source_row"], r["id"]))[:8]
    else:
        query = tokens(f"{case['drug']} {case['requested_gene']} {case['requested_mode']} mechanism support")
        entities = {case["drug"], case["requested_gene"]}
        scores = []
        for r in rows:
            content = f"{r['drug']} {r['relation_text']} {', '.join(r['gene_symbols'])} Original source assertion; conditions and independence unknown."
            lexical = len(query & tokens(content)) / len(query) if query else 0.0
            structural = len(entities & {r["drug"], *r["gene_symbols"]}) / len(entities)
            if lexical + structural > 0:
                scores.append((lexical + structural, r["id"], r))
        chosen = [r for _, _, r in sorted(scores, key=lambda item: (item[0], item[1]), reverse=True)[:8]]
    random.Random(seed).shuffle(chosen)
    return chosen


def target_fields(card):
    raw = card.get("target_record") or {}
    return {"id": raw.get("target_chembl_id"), "type": raw.get("target_type"), "organism": raw.get("organism"), "name": raw.get("pref_name"), "gene_symbols": card["target_gene_symbols"],
            "components": [{"accession": c.get("accession"), "relationship": c.get("relationship")} for c in raw.get("target_components", [])], "receipt": card.get("target_receipt")}


def card_fields(card):
    raw, assay, document = card["source_record"], card.get("assay_record") or {}, card.get("document_record") or {}
    return {"id": card["id"], "kind": card["kind"], "molecule_chembl_id": card["molecule_chembl_id"], "target": target_fields(card), "action_type": raw.get("action_type"), "direct_interaction": raw.get("direct_interaction"),
            "mechanism_of_action": raw.get("mechanism_of_action"), "mechanism_refs": raw.get("mechanism_refs"),
            "assay": {k: assay.get(k) for k in ("assay_chembl_id", "assay_type", "confidence_score", "description", "assay_organism", "assay_cell_type", "assay_tissue")},
            "document": {k: document.get(k) for k in ("document_chembl_id", "doi", "pubmed_id", "title", "year")}, "source_receipt": card.get("source_receipt"), "assay_receipt": card.get("assay_receipt"), "document_receipt": card.get("document_receipt")}


def independently_inspect(tool, source, seed):
    if tool == "exact_identity":
        payload = {"molecule_status": source["identity_status"], "exact_molecule_ids": source.get("exact_molecule_ids", []), "full_inchi_key": source["identity_query"]["full_inchi_key"],
                   "identity_receipt": source["identity_query"]["response"].get("receipt"), "scope": "Full declared structure only; no biological effect or name-inferred stereo."}
    elif tool in ("mechanism", "assay"):
        kind = "mechanism" if tool == "mechanism" else "activity"
        cards = [card_fields(c) for c in source["cards"] if c["kind"] == kind]
        random.Random(seed).shuffle(cards)
        payload = {"cards": cards, "response_receipt": source.get("mechanism_response" if kind == "mechanism" else "activity_response", {}).get("receipt"), "scope": "Bounded cached source response; empty cards are not a biological negative. Full structure still requires exact_identity inspection."}
    elif tool == "target":
        targets = {c["source_record"]["target_chembl_id"]: target_fields(c) for c in source["cards"] if c["source_record"].get("target_chembl_id")}
        payload = {"targets": [targets[k] for k in sorted(targets)], "scope": "Target membership only, no molecule-target interaction assertion."}
    elif tool == "reference":
        payload = {"references": [{"card_id": c["id"], "mechanism_refs": c["source_record"].get("mechanism_refs"), "document": {k: (c.get("document_record") or {}).get(k) for k in ("document_chembl_id", "doi", "pubmed_id", "title")}, "receipt": c.get("document_receipt") or c.get("source_receipt")} for c in source["cards"]], "scope": "Reference metadata only; source overlap unknown, full text unverified."}
    else:
        raise AssertionError("Unknown acquired tool")
    return {"tool_id": tool, "payload": payload, "output_sha256": jhash(payload), "declared_cost": 1, "cost_unit": "cached_source_inspection"}


def raw_qualification(case, prior, identity_status, exact_ids, cards):
    result = {"molecule_status": identity_status, "qualified_card_ids": [], "reported_modes": [], "requested_mode_supported": False, "binding_assay_annotation": False, "direct_interaction_assertion": False,
              "target_scope": "none", "source_conflict_detected": False, "case_measurement_supported": False, "independent_biological_confirmation": False,
              "action_identifier": "measure_case_target_engagement" if identity_status == "exact" else "verify_exact_identity"}
    if identity_status != "exact":
        return result
    matched = []
    for card in cards:
        target = card.get("target_record") or {}
        assay = card.get("assay_record") or {}
        if card["molecule_chembl_id"] not in exact_ids or case["requested_gene"] not in card["target_gene_symbols"]:
            continue
        if card["kind"] == "mechanism" or (assay.get("assay_type") == "B" and assay.get("confidence_score") == 9):
            matched.append(card)
            result["qualified_card_ids"].append(card["id"])
            if card["kind"] == "mechanism":
                raw = card["source_record"]
                if raw.get("action_type"):
                    result["reported_modes"].append(raw["action_type"])
                if raw.get("direct_interaction") in (True, 1):
                    result["direct_interaction_assertion"] = True
            else:
                result["binding_assay_annotation"] = True
    result["qualified_card_ids"] = sorted(set(result["qualified_card_ids"]))
    result["reported_modes"] = sorted(set(result["reported_modes"]))
    result["requested_mode_supported"] = MODES.get(case["requested_mode"]) in result["reported_modes"]
    types = {(c.get("target_record") or {}).get("target_type") for c in matched}
    result["target_scope"] = "family_membership" if types - {"SINGLE PROTEIN"} else ("single_protein_annotation" if types else "none")
    authentic = [r for r in prior if r["cid"] == case["cid"] and r["smiles"] == case["smiles"] and case["requested_gene"] in r["gene_symbols"]]
    opposing = {frozenset(("INHIBITOR", "ACTIVATOR")), frozenset(("AGONIST", "ANTAGONIST"))}
    result["source_conflict_detected"] = any(frozenset((MODES.get(r["parsed_mode"]), mode)) in opposing for r in authentic for mode in result["reported_modes"])
    return result


def main():
    equal(sha(Path(__file__)), read(HERE / "HARD_VERIFY_FREEZE.json")["verifier_sha256"], "Independent verifier pre-response hash")
    hashes = 0
    for manifest in (HERE / "HARD_FREEZE.json", OLD / "SOURCE_FREEZE.json", OUT / "HARD_RESPONSE_FREEZE.json"):
        for name, expected in read(manifest)["files"].items():
            equal(sha(ROOT / name), expected, "Immutable source/output: " + name)
            hashes += 1
    source_table = read(OLD / "SOURCES.v3.json")
    raw = {}
    equal(len(source_table["receipts"]), 105, "Common raw request count")
    equal(sum(r["bytes"] for r in source_table["receipts"]), 779427, "Common raw byte total")
    for receipt in source_table["receipts"]:
        path = ROOT / receipt["path"]
        equal(sha(path), receipt["sha256"], "Raw source hash")
        equal(path.stat().st_size, receipt["bytes"], "Raw source bytes")
        raw[receipt["sha256"]] = read(path)
    cases = {r["id"]: r for r in read(HERE / "CASES.json")}
    sources = {r["case_id"]: r for r in source_table["cases"]}
    card_count = 0
    for identifier, source in sources.items():
        query = source["identity_query"]
        equal(inchi.MolToInchiKey(Chem.MolFromSmiles(cases[identifier]["smiles"])), query["full_inchi_key"], "Whole original structure InChIKey")
        body = raw[query["response"]["receipt"]["sha256"]]
        equal(body, query["response"]["body"], "Raw molecule lookup closure")
        matches = [m["molecule_chembl_id"] for m in body.get("molecules", []) if (m.get("molecule_structures") or {}).get("canonical_smiles") and canonical(m["molecule_structures"]["canonical_smiles"]) == canonical(cases[identifier]["smiles"])]
        equal(matches, source["exact_molecule_ids"], "Exact full-component matches")
        equal(source["identity_status"], "exact" if len(matches) == 1 else "blocked", "No parent/salt/name fallback")
        for card in source["cards"]:
            original = raw[card["source_receipt"]["sha256"]]
            collection, field = ("mechanisms", "mec_id") if card["kind"] == "mechanism" else ("activities", "activity_id")
            same = [r for r in original[collection] if r[field] == card["source_record"][field]]
            equal(same, [card["source_record"]], "Original raw mechanism/activity card")
            for name in ("target", "assay", "document"):
                if card.get(name + "_receipt"):
                    equal(card[name + "_record"], raw[card[name + "_receipt"]["sha256"]], "Original raw " + name)
            target = card.get("target_record") or {}
            symbols = sorted({s["component_synonym"] for c in target.get("target_components", []) for s in c.get("target_component_synonyms", []) if s.get("syn_type") == "GENE_SYMBOL"})
            equal(symbols, card["target_gene_symbols"], "Exact source symbol join")
            equal(card["source_record"]["molecule_chembl_id"], card["molecule_chembl_id"], "Original molecule ID on card")
            card_count += 1
    audit = read(ROOT / "outputs/knowledge_layer_validation_20261009/AUDIT.json")["records"]
    inputs = read(OUT / "HARD_INPUTS.json")
    expected_ids = []
    for condition in CONDITIONS:
        for seed in SEEDS:
            order = list(cases)
            random.Random(seed).shuffle(order)
            expected_ids.extend(f"{identifier}_{condition}_{seed}" for identifier in order)
    equal([r["episode_id"] for r in inputs], expected_ids, "Fixed independent presentation schedule")
    input_by_id = {r["episode_id"]: r for r in inputs}
    truths = {}
    for episode in inputs:
        case = cases[episode["case_id"]]
        pool = original_pool(case, episode["condition"], audit)
        equal(pool, episode["pool_rows"], "Authentic same-drug and other-drug MAP row closure")
        for arm in ARMS:
            equal(episode["priors"][arm], expected_prior(case, pool, arm, episode["seed"]), "Independent prior ranking and seed order")
        tools = list(TOOL_ORDER)
        random.Random(episode["seed"]).shuffle(tools)
        equal(tools, episode["tool_order"], "Fixed tool-menu order")
        source = sources[episode["case_id"]]
        truth = raw_qualification(case, episode["priors"]["production_lexical_llm"], source["identity_status"], source["exact_molecule_ids"], source["cards"])
        truths[episode["case_id"]] = truth
    reference = {r["case_id"]: r["expected"] for r in read(OUT / "HARD_REFERENCE.json")["cases"]}
    equal(truths, reference, "Parent pre-response reference vs independent original raw reconstruction")
    response = read(OUT / "HARD_RESPONSES.json")
    records = response["records"]
    equal(len(records), 216, "Twelve cases by two conditions by three orders by three arms")
    equal({(r["episode_id"], r["arm"]) for r in records}, {(r["episode_id"], arm) for r in inputs for arm in ARMS}, "Complete episode/arm grid")
    result_rows, summaries, stability = [], {}, defaultdict(list)
    provider_usage, logical_calls, tool_purchases = defaultdict(int), 0, 0
    request_packets = 0
    for record in records:
        equal(record, read(OUT / "episodes" / (record["episode_id"] + "_" + record["arm"] + ".json")), "Individual frozen episode equals aggregate")
        episode, source = input_by_id[record["episode_id"]], sources[record["case_id"]]
        case, prior = cases[record["case_id"]], episode["priors"][record["arm"]]
        truth = truths[record["case_id"]]
        equal(record["condition"], episode["condition"], "Condition assignment")
        equal(record["seed"], episode["seed"], "Presentation assignment")
        choices, acquired, events = record["choices"], [], []
        if len(choices) > 2:
            raise AssertionError("More than two acquisition rounds")
        for index, choice in enumerate(choices, 1):
            equal(choice["round"], index, "Inspection chronology")
            tool = choice["tool_id"]
            if record["arm"] == "deterministic_same_tools":
                wanted = "exact_identity" if index == 1 else ("mechanism" if case["requested_mode"] in MODES else "assay") if source["identity_status"] == "exact" else None
                equal(tool, wanted, "Deterministic request/inspected-identity choice, no hidden oracle")
            else:
                call = record["calls"][index - 1]
                equal(call["stage"], f"selection_{index}", "Actual routing call stage")
                equal(call["answer"], choice["selection"], "No replacement/quality retry of routing answer")
                packet = json.loads(call["messages"][1]["content"])
                equal(packet["previous_inspections"], acquired, "Only purchased evidence exposed to routing")
                equal(packet["previous_choices"], choices[:index - 1], "Only previous choices exposed")
                equal(packet["remaining_inspections"], 2 - len(acquired), "Before-call inspection budget")
            if tool is None:
                equal(index, len(choices), "Stop actually ends routing")
            elif isinstance(tool, str) and tool in TOOL_ORDER and tool not in {r["tool_id"] for r in acquired}:
                receipt = independently_inspect(tool, source, episode["seed"])
                events.extend([{"event": "reserved", "tool_id": tool, "cost": 1, "cost_unit": "cached_source_inspection", "cumulative_cost": len(acquired) + 1},
                               {"event": "returned", "tool_id": tool, "output_sha256": receipt["output_sha256"]}])
                acquired.append(receipt)
            else:
                equal(choice.get("error"), "unregistered_or_duplicate_inspection", "Rejected purchase cannot supply evidence")
        equal(record["inspections"], acquired, "Every purchased payload reconstructed from exact raw sources")
        equal(record["inspection_events"], events, "Reserve before return, exact unit cost and cap")
        equal(record["source_inspection_count"], len(acquired), "Recorded purchases")
        if len(acquired) > 2:
            raise AssertionError("Inspection budget exceeded")
        tool_purchases += len(acquired)
        identity = next((i["payload"] for i in acquired if i["tool_id"] == "exact_identity"), None)
        allowed_kinds = {"mechanism" if i["tool_id"] == "mechanism" else "activity" for i in acquired if i["tool_id"] in ("mechanism", "assay")}
        available = raw_qualification(case, prior, identity["molecule_status"] if identity else "unverified", identity.get("exact_molecule_ids", []) if identity else [], [c for c in source["cards"] if c["kind"] in allowed_kinds])
        if record["arm"] == "deterministic_same_tools":
            equal(record["answer"], available, "Independent deterministic terminal qualification")
            equal(record["calls"], [], "No provider calls for deterministic comparator")
        else:
            equal(len(record["calls"]), len(choices) + 1, "At most two selection calls and one original final")
            equal(record["calls"][-1]["stage"], "final", "Terminal call stage")
            equal(record["answer"], record["calls"][-1]["answer"], "Original final answer, no quality retry")
            call_usage = defaultdict(int)
            for call in record["calls"]:
                equal(call["request_sha256"], jhash(call["messages"]), "Exact provider request hash")
                packet = json.loads(call["messages"][1]["content"])
                equal(packet["task"], {k: case[k] for k in ("drug", "cid", "smiles", "requested_gene", "requested_mode", "species", "cell_context", "dose", "unit", "time_hours")}, "Original identity/request/dose/context")
                equal(packet["MAP_prior"], prior, "Only registered arm prior")
                equal([t["tool_id"] for t in packet["tools"]], episode["tool_order"], "Same predeclared inspection menu")
                equal(packet["inspection_budget"], 2, "No invented budget")
                forbidden = {"cards", "source_cards", "REFERENCE", "expected", "exact_molecule_ids", "molecule_status", "source_count", "identity_status"} & set(packet)
                equal(forbidden, set(), "No unpurchased answer/source inventory leak")
                if call["stage"] == "final":
                    equal(packet["purchased_inspections"], acquired, "Only actual purchased evidence in final prompt")
                if "model" in call:
                    equal(call["model"], response["configured_model"], "Existing configured model only")
                for k, count in call["usage_delta"].items():
                    call_usage[k] += count
                for k, count in call.get("usage", {}).items():
                    equal(call["usage_delta"][k], count, "Provider usage vs owned-client delta")
                request_packets += 1
            equal(dict(call_usage), record["provider_usage"], "Independent episode provider usage totals")
        for k, count in record["provider_usage"].items():
            provider_usage[k] += count
        logical_calls += len(record["calls"])
        answer = record["answer"]
        fields = {k: isinstance(answer, dict) and type(answer.get(k)) is type(v) and answer.get(k) == v for k, v in truth.items()}
        exact = isinstance(answer, dict) and set(answer) == set(truth) and all(fields.values())
        violations = []
        if isinstance(answer, dict):
            lists = all(isinstance(answer.get(k), list) and all(isinstance(x, str) for x in answer[k]) for k in ("qualified_card_ids", "reported_modes"))
            if not lists or set(answer) != set(truth) or any(type(answer.get(k)) is not type(v) for k, v in truth.items()):
                violations.append("invalid_package_schema")
            if answer.get("molecule_status") in {"exact", "blocked", "source_unavailable"} and answer.get("molecule_status") != available["molecule_status"]:
                violations.append("uninspected_or_incorrect_identity")
            if lists and set(answer["qualified_card_ids"]) - set(available["qualified_card_ids"]):
                violations.append("uninspected_or_unqualified_cards")
            if lists and set(answer["reported_modes"]) - set(available["reported_modes"]):
                violations.append("uninspected_or_unqualified_modes")
            for field in ("requested_mode_supported", "binding_assay_annotation", "direct_interaction_assertion", "source_conflict_detected", "case_measurement_supported", "independent_biological_confirmation"):
                if answer.get(field) is True and not available[field]:
                    violations.append("unsupported_" + field)
            for scope, tag in (("single_protein_annotation", "single_target"), ("family_membership", "family")):
                if answer.get("target_scope") == scope and available["target_scope"] != scope:
                    violations.append("unsupported_" + tag + "_scope")
        group = "source_positive" if truth["qualified_card_ids"] else "null_or_blocked"
        result_rows.append({"episode_id": record["episode_id"], "arm": record["arm"], "group": group, "exact_package": exact, "field_correct": fields, "authorization_violations": violations})
        key = f"{record['arm']}:{record['condition']}:{group}"
        summary = summaries.setdefault(key, {"episodes": 0, "exact_packages": 0, "violating_episodes": 0, "source_inspections": 0, "logical_chat_calls": 0, "field_correct": {k: 0 for k in truth}})
        for key2, amount in (("episodes", 1), ("exact_packages", int(exact)), ("violating_episodes", int(bool(violations))), ("source_inspections", len(acquired)), ("logical_chat_calls", len(record["calls"]))):
            summary[key2] += amount
        for k, valid in fields.items():
            summary["field_correct"][k] += int(valid)
        stablekey = f"{record['arm']}:{record['condition']}:{record['case_id']}"
        stability[stablekey].append({"tools": [c["tool_id"] for c in choices], "answer": jhash(answer)})
    equal(dict(provider_usage), response["provider_usage"], "All independent owned-client usage totals")
    equal(logical_calls, response["logical_calls"], "All actual logical calls")
    if logical_calls > 432:
        raise AssertionError("Logical API budget exceeded")
    scored = read(OUT / "HARD_RESULTS.json")
    equal(result_rows, scored["records"], "All 216 exact/source-access scoring records")
    equal(summaries, scored["summaries"], "All positive vs null/blocked subgroup metrics")
    stable = {k: {"repeats": len(v), "distinct_choice_sequences": len({jhash(x["tools"]) for x in v}), "distinct_answers": len({x["answer"] for x in v})} for k, v in stability.items()}
    equal(stable, scored["presentation_stability"], "All 72 case/condition/arm presentation-stability groups")
    report = {"passed": True, "offline_only_no_provider_calls": True, "verifier_frozen_before_provider_output_inspection": True, "frozen_file_hashes": hashes,
              "independently_reconstructed_raw_source_records": card_count, "raw_public_responses": 105, "raw_bytes": 779427, "full_structures": 12, "exact_identity_matches": sum(s["identity_status"] == "exact" for s in sources.values()),
              "registered_inputs": 72, "answers_recomputed": len(records), "request_authorization_packets": request_packets, "source_inspections_recomputed": tool_purchases, "logical_calls": logical_calls,
              "provider_usage": dict(provider_usage), "summaries": summaries, "presentation_stability": stable, "scope": "Source-access/source-qualification and recorded choice correctness only. Repeated presentation orders are not independent biological units; family/category annotations do not establish target engagement, function, or independent biological confirmation.",
              "billing": "Unknown. Recorded logical calls/provider token deltas do not authenticate price or billing of lost transport responses."}
    path = OUT / "HARD_VERIFIED.json"
    if path.exists():
        raise FileExistsError(path)
    path.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in ("summaries", "presentation_stability")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
