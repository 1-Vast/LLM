"""Frozen, source-level retrieval trial; no biological outcome or production edits."""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import time
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))
HERE = Path(__file__).resolve().parent
OUT = ROOT / "outputs/map_module_replacement_20261009/agent_trial"
AUDIT = ROOT / "outputs/knowledge_layer_validation_20261009/AUDIT.json"
MODE = {"inhibit": "INHIBITOR", "activate": "ACTIVATOR", "agonist": "AGONIST", "antagonist": "ANTAGONIST"}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path, value):
    path = Path(path)
    if path.exists():
        raise FileExistsError(str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def prepare():
    records = read(AUDIT)["records"]
    unique = {}
    for record in records:
        unique.setdefault((record["smiles"], record["cid"]), record)
    available = sorted(unique.values(), key=lambda r: r["drug"])
    selected, used = [], set()
    for stratum, count in [("inhibit", 4), ("antagonist", 2), ("agonist", 2), ("unparsed_binding", 2), ("no_edge", 2)]:
        eligible = []
        for record in available:
            if record["drug"] in used:
                continue
            edges = record["edges"]
            if stratum in MODE:
                matching = [e for e in edges if e["direction"] == stratum]
            elif stratum == "unparsed_binding":
                matching = [e for e in edges if e["relation"] == "exhibits strong binding to the protein target encoded by"] if all(e["direction"] == "unknown" for e in edges) else []
            else:
                matching = []
            if matching or (stratum == "no_edge" and not edges):
                eligible.append((record, min(matching, key=lambda e: e["source_row"]) if matching else None))
        if len(eligible) < count:
            raise ValueError("Insufficient registered stratum: " + stratum)
        for record, edge in eligible[:count]:
            used.add(record["drug"])
            symbols = sorted({n["Gene name"] for n in edge["gene_node_matches"]}) if edge else ["MAPK1"]
            selected.append({"id": f"case_{len(selected) + 1:02d}", "stratum": stratum,
                             "drug": record["drug"], "cid": record["cid"], "smiles": record["smiles"],
                             "original_candidate": record["candidate"], "dose": record["dose"], "unit": record["unit"],
                             "species": "Homo sapiens", "cell_context": "A549", "time_hours": 24,
                             "requested_gene": symbols[0], "requested_mode": stratum if stratum in MODE else ("bind" if edge else "untyped"),
                             "selected_map_edge": edge, "all_map_edges": record["edges"]})
    write(HERE / "CASES.json", selected)
    protocol = {
        "question": "Does source-typed MAP prior improve an actual source-qualification responsibility over current lexical retrieval and a deterministic same-evidence qualifier?",
        "scope": "ContextBuilder/EvidenceLedger evidence context responsibility only. Raw public assertions are the endpoint; no biological ground truth, target engagement, RNA outcome, functional utility, unseen-edge generalization, or module promotion.",
        "selection": "Deduplicate full canonical-isomeric structure plus CID; retain first original dose row; sort exact original names; sequential distinct strata: 4 inhibitor, 2 antagonist, 2 agonist, 2 exclusively-unparsed binding, 2 no-edge. Selected edge lowest original source_row; requested symbol sorted exact gene-node symbols. No-edge request MAPK1/untyped. No source-answer-based replacements.",
        "identity": "RDKit full-structure InChIKey exact ChEMBL molecule query, limit5 sorted molecule ID, then full RDKit canonical isomeric SMILES equality. No salt stripping, fuzzy/name/parent fallback. Zero or multiple full matches blocked; network failures source_unavailable; all 12 remain denominators.",
        "external_sources": "ChEMBL status; exact molecules; mechanisms limit100; ChEMBL-category-B activities assay_type=B target_organism=Homo sapiens limit3 ordered activity_id; original targets/assays/documents for those records. Small responses capped1MB. ChEMBL may overlap MAP provenance/training: independence unknown.",
        "cards": "All returned mechanisms and up to3 ChEMBL-category-B assay records; original target gene synonyms/action_type/direct_interaction, assay type/confidence/conditions, document IDs/DOIs/PubMed refs and response hashes retained. Missing action/condition remains null. No source outcome transformed into a cellular measurement.",
        "tools": "All arms receive SAME public cards and SAME actual existing table_filter invocation: requested_gene contains exact symbol, max_rows100. One common tool call per case, shared unchanged across all arms, zero declared tool cost; public fetches common offline source acquisition. Model does not choose tools; tests context interpretation, not tool selection or autonomy.",
        "arms": ["production_lexical_llm", "source_typed_map_llm", "deterministic_same_cards"],
        "priors": "Both LLM arms access same original MAP pool. Baseline actual EvidenceLedger.retrieve top8 with query/requested entities, deterministic timestamps/IDs. Typed prior retains only exact requested gene rows, source-row sorted top8, with parsed relation class and full source text. No learned MAP embedding arm; those were previously audited separately.",
        "endpoint": "Exact JSON package: molecule_status; qualified_card_ids (exact requested gene in curated mechanism or ChEMBL B assay confidence9); reported_modes (original uppercase mechanism action types of qualified cards, any unknowns excluded); requested_mode_supported (controlled exact action mapping); binding_assay_annotation (source B/confidence9 category); direct_interaction_assertion (curated mechanism flag); case_measurement_supported=false; independent_biological_confirmation=false; action_identifier=verify_exact_identity if blocked/unavailable else measure_case_target_engagement.",
        "oracle": "Separate offline source-card/raw-response review writes REFERENCE.json and reference hash before LLM responses. Deterministic classifier reads only same visible tool cards/prior, no reference. Freeze all responses before evaluating. The endpoint is explicit source qualification, not independent experimental proof.",
        "model": "Existing agent.llm.MAESTROSettings/ChatClient configured deepseek-flash; no provider/model override. Max24 chat calls=12cases*2 arms, temperature0, max_tokens1400. Per-call latency/model/usage/finish_reason; no repeat for answer quality. Existing transport retries bounded; lost-response billing unknown. Actual dollars only if provider authenticates cost, otherwise null.",
        "acceptance": "No promotion. MAP source role considered useful only if exact source-package accuracy exceeds BOTH baseline LLM and deterministic, without increased unsupported claims; report per-case outcomes even failed/blocked. Same-field aggregate and safety separately; case-measurement abstention alone is not a win.",
        "verification": "Independent recomputation of selection/raw identity/card closure/tool payload/oracle qualification/results/provider24-call bounds; immutable hashes before acquisition and before evaluation. No new RNA arrays or large assets.",
    }
    write(HERE / "PROTOCOL.json", protocol)
    paths = [AUDIT, HERE / "CASES.json", HERE / "PROTOCOL.json", Path(__file__), ROOT / "src/agent/knowledge.py", ROOT / "src/agent/llm.py", ROOT / "src/maestro/tool_analysis.py", ROOT / "tools/analysis/table_filter.manifest.json"]
    write(HERE / "FREEZE.json", {"utc": datetime.now(timezone.utc).isoformat(), "phase": "before_new_external_relation_reads", "files": {str(p.relative_to(ROOT)).replace("\\", "/"): sha(p) for p in paths}})
    print(json.dumps({"prepared_cases": len(selected), "drugs": [c["drug"] for c in selected]}, ensure_ascii=False))


def check_freeze():
    for path, digest in read(HERE / "FREEZE.json")["files"].items():
        if sha(ROOT / path) != digest:
            raise ValueError("Frozen source changed: " + path)


def acquire():
    import requests
    from rdkit import Chem
    from rdkit.Chem import inchi
    check_freeze()
    rawdir = OUT / "raw"
    rawdir.mkdir(parents=True, exist_ok=False)
    receipts, cache = [], {}

    def fetch(resource, params=None):
        url = "https://www.ebi.ac.uk/chembl/api/data/" + resource + ".json"
        if params:
            url += "?" + urlencode(params)
        if url in cache:
            return cache[url]
        index = len(receipts)
        try:
            response = requests.get(url, timeout=35)
            body = response.content
            if len(body) > 1_000_000:
                raise ValueError("Response exceeds frozen small-source cap")
            path = rawdir / f"response_{index:03d}.json"
            path.write_bytes(body)
            receipt = {"url": url, "status": response.status_code, "bytes": len(body), "sha256": sha(path), "path": str(path.relative_to(ROOT)).replace("\\", "/")}
            receipts.append(receipt)
            response.raise_for_status()
            result = {"body": response.json(), "receipt": receipt}
        except Exception as error:
            if len(receipts) == index:
                receipts.append({"url": url, "error_type": type(error).__name__})
            result = {"error_type": type(error).__name__}
        cache[url] = result
        return result

    status = fetch("status")
    cases = []
    for case in read(HERE / "CASES.json"):
        result = {"case_id": case["id"], "identity_status": "blocked", "cards": []}
        mol = Chem.MolFromSmiles(case["smiles"])
        key = inchi.MolToInchiKey(mol)
        identity = fetch("molecule", {"molecule_structures__standard_inchi_key": key, "limit": 5, "order_by": "molecule_chembl_id"})
        result["identity_query"] = {"full_inchi_key": key, "response": identity}
        if "body" not in identity:
            result["identity_status"] = "source_unavailable"
            cases.append(result)
            continue
        full_matches = []
        for match in identity["body"].get("molecules", []):
            structure = (match.get("molecule_structures") or {}).get("canonical_smiles")
            decoded = Chem.MolFromSmiles(structure or "")
            if decoded is not None and Chem.MolToSmiles(decoded, canonical=True, isomericSmiles=True) == Chem.MolToSmiles(mol, canonical=True, isomericSmiles=True):
                full_matches.append(match)
        result["exact_molecule_ids"] = [m["molecule_chembl_id"] for m in full_matches]
        if len(full_matches) != 1:
            cases.append(result)
            continue
        result["identity_status"] = "exact"
        cid = full_matches[0]["molecule_chembl_id"]
        mechanisms = fetch("mechanism", {"molecule_chembl_id": cid, "limit": 100, "order_by": "mec_id"})
        activities = fetch("activity", {"molecule_chembl_id": cid, "assay_type": "B", "target_organism": "Homo sapiens", "limit": 3, "order_by": "activity_id"})
        result["mechanism_response"], result["activity_response"] = mechanisms, activities
        if "body" not in mechanisms or "body" not in activities:
            result["identity_status"] = "source_unavailable"
        for kind, response, collection in [("mechanism", mechanisms, "mechanisms"), ("activity", activities, "activities")]:
            for item in response.get("body", {}).get(collection, []):
                target = fetch("target/" + item["target_chembl_id"]) if item.get("target_chembl_id") else {}
                assay = fetch("assay/" + item["assay_chembl_id"]) if kind == "activity" and item.get("assay_chembl_id") else {}
                document = fetch("document/" + item["document_chembl_id"]) if kind == "activity" and item.get("document_chembl_id") else {}
                genes = sorted({s["component_synonym"] for t in target.get("body", {}).get("target_components", []) for s in t.get("target_component_synonyms", []) if s.get("syn_type") == "GENE_SYMBOL"})
                ident = item.get("mec_id") if kind == "mechanism" else item["activity_id"]
                if (item.get("target_chembl_id") and "body" not in target) or (kind == "activity" and item.get("assay_chembl_id") and "body" not in assay):
                    result["identity_status"] = "source_unavailable"
                result["cards"].append({"id": f"{kind}:{ident}", "kind": kind, "molecule_chembl_id": cid, "target_gene_symbols": genes,
                                        "source_record": item, "target_record": target.get("body"), "assay_record": assay.get("body"), "document_record": document.get("body"),
                                        "source_receipt": response.get("receipt"), "target_receipt": target.get("receipt"), "assay_receipt": assay.get("receipt"), "document_receipt": document.get("receipt")})
        cases.append(result)
        write(OUT / "source_cases" / (case["id"] + ".json"), result)
        print(json.dumps({"acquired_case": case["id"], "status": result["identity_status"], "cards": len(result["cards"])}), flush=True)
    write(OUT / "SOURCES.json", {"status": status, "receipts": receipts, "cases": cases})
    write(OUT / "SOURCE_FREEZE.json", {"utc": datetime.now(timezone.utc).isoformat(), "phase": "sources_before_reference_and_responses", "files": {str(p.relative_to(ROOT)).replace("\\", "/"): sha(p) for p in sorted(OUT.rglob("*.json"))}})
    print(json.dumps({"public_requests": len(receipts), "cases": len(cases)}), flush=True)


def prior(case, arm):
    edges = case["all_map_edges"]
    if arm == "source_typed_map_llm":
        chosen = [e for e in edges if any(n["Gene name"] == case["requested_gene"] for n in e["gene_node_matches"])]
        chosen.sort(key=lambda e: e["source_row"])
        return chosen[:8]
    from agent.knowledge import EvidenceLedger, EvidenceStatus
    with tempfile.TemporaryDirectory(prefix="map_trial_ledger_") as directory:
        ledger = EvidenceLedger(Path(directory) / "ledger.sqlite")
        for edge in edges:
            entities = (case["drug"], *sorted({n["Gene name"] for n in edge["gene_node_matches"]}))
            ledger.add_evidence(f"{case['drug']} {edge['relation']} {', '.join(entities[1:])}", source="MAP-KG:frozen_raw", context="Original MAP source assertion; conditions and original external provenance unknown.", status=EvidenceStatus.RETRIEVED,
                                entities=entities, identifier=f"map:{edge['source_row']:09d}", payload={"original_edge": edge})
        with sqlite3.connect(ledger.path) as connection:
            connection.execute("UPDATE evidence SET created_at='2000-01-01T00:00:00+00:00'")
        result = ledger.retrieve(f"{case['drug']} {case['requested_gene']} {case['requested_mode']} mechanism support", entities=(case["drug"], case["requested_gene"]), limit=8)
        return [r.payload["original_edge"] for r in result]


def visible_tool_cards(case, source):
    import csv
    from maestro.tool_analysis import table_filter
    path = OUT / "tool_cards" / (case["id"] + ".csv")
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=["id", "target_gene_symbols", "card_json"])
            writer.writeheader()
            for card in source["cards"]:
                visible = dict(card)
                target = card.get("target_record") or {}
                visible["target_record"] = {k: target.get(k) for k in ["target_chembl_id", "target_type", "pref_name", "organism"]}
                visible["target_record"]["target_components"] = [{"accession": c.get("accession"), "relationship": c.get("relationship"), "gene_symbols": [s["component_synonym"] for s in c.get("target_component_synonyms", []) if s.get("syn_type") == "GENE_SYMBOL"]} for c in target.get("target_components", [])]
                writer.writerow({"id": card["id"], "target_gene_symbols": "|".join(card["target_gene_symbols"]), "card_json": json.dumps(visible, ensure_ascii=False)})
    arguments = {"dataset_path": str(path), "column": "target_gene_symbols", "operator": "contains", "value": case["requested_gene"], "max_rows": 100}
    result = table_filter(arguments)
    rows = result["payload"]["sample_rows"]
    return [json.loads(row["card_json"]) for row in rows], {"tool_id": "table_filter", "arguments": arguments, "input_sha256": sha(path), "output": result, "declared_tool_cost": 0.0}


def deterministic(case, source, cards):
    result = {"molecule_status": source["identity_status"], "qualified_card_ids": [], "reported_modes": [], "requested_mode_supported": False, "binding_assay_annotation": False, "direct_interaction_assertion": False, "case_measurement_supported": False,
              "independent_biological_confirmation": False, "action_identifier": "measure_case_target_engagement" if source["identity_status"] == "exact" else "verify_exact_identity"}
    modes = set()
    if source["identity_status"] == "exact":
        for card in cards:
            if case["requested_gene"] not in card["target_gene_symbols"]:
                continue
            raw = card["source_record"]
            assay = card.get("assay_record") or {}
            if card["kind"] == "mechanism":
                result["qualified_card_ids"].append(card["id"])
                if raw.get("action_type"):
                    modes.add(raw["action_type"])
                result["direct_interaction_assertion"] |= raw.get("direct_interaction") in (True, 1)
            elif assay.get("assay_type") == "B" and assay.get("confidence_score") == 9:
                result["qualified_card_ids"].append(card["id"])
                result["binding_assay_annotation"] = True
    result["qualified_card_ids"].sort()
    result["reported_modes"] = sorted(modes)
    result["requested_mode_supported"] = MODE.get(case["requested_mode"]) in modes
    return result


SYSTEM = """You qualify source evidence for MAESTRO's bounded context/planning responsibility. Return exactly one JSON object. Original MAP rows are priors, not measurements or independently verified biological truth. ChEMBL may share original sources with MAP; neither a curated action nor a binding assay establishes the requested cellular target engagement, exact dose/time/context, RNA sign, causal effect, or independent biological replication. Use only the returned public cards and registered actions.
Schema (all keys required): molecule_status: exact|blocked|source_unavailable; qualified_card_ids: sorted IDs of exact requested-gene curated mechanism cards or ChEMBL assay_type B cards with confidence_score=9; reported_modes: sorted distinct ORIGINAL uppercase ChEMBL action_type from qualified mechanism cards; requested_mode_supported: true iff requested inhibit/activate/agonist/antagonist maps EXACTLY to INHIBITOR/ACTIVATOR/AGONIST/ANTAGONIST in reported_modes (bind/untyped always false); binding_assay_annotation: true iff a qualified ChEMBL assay_type B/confidence9 record exists (source category, not proof of physical binding); direct_interaction_assertion: true iff qualified curated mechanism direct_interaction=true or integer1 (curated flag, not a case measurement); case_measurement_supported: boolean; independent_biological_confirmation: boolean; action_identifier: verify_exact_identity|measure_case_target_engagement. Identity blocked/unavailable makes support/card/mode sets empty and action verify_exact_identity; exact identity needs measure_case_target_engagement. Do not invent missing assay conditions or treat an unparsed MAP phrase as no biological relation. Missing MAP edge is unknown. Preserve agonist/antagonist rather than gene expression up/down. Select source assertions, not effects in this case."""


def run():
    from agent.llm import MAESTROSettings, DeepSeekChatClient
    check_freeze()
    reference_freeze = read(OUT / "REFERENCE_FREEZE.json")
    if reference_freeze["reference_sha256"] != sha(OUT / "REFERENCE.json"):
        raise ValueError("Reference changed before responses")
    settings = MAESTROSettings.from_workspace(ROOT)
    client = DeepSeekChatClient(settings)
    sources = {s["case_id"]: s for s in read(OUT / "SOURCES.v3.json")["cases"]}
    response_dir = OUT / "responses"
    response_dir.mkdir(parents=True, exist_ok=False)
    records = []
    for case in read(HERE / "CASES.json"):
        source = sources[case["id"]]
        cards, tool = visible_tool_cards(case, source)
        for arm in ["production_lexical_llm", "source_typed_map_llm", "deterministic_same_cards"]:
            start = time.perf_counter()
            record = {"case_id": case["id"], "arm": arm, "tool_receipt": tool}
            if arm == "deterministic_same_cards":
                record["answer"] = deterministic(case, source, cards)
            else:
                request = {k: v for k, v in case.items() if k not in {"all_map_edges", "selected_map_edge"}}
                packet = {"task": request, "molecule_status": source["identity_status"], "exact_chembl_molecule_ids": source.get("exact_molecule_ids", []),
                          "MAP_prior": prior(case, arm), "MAP_provenance": "Frozen official raw CSV/source rows; external original reference and assay conditions unknown; graph repetition not independent.",
                          "public_tool_cards": cards, "registered_actions": ["verify_exact_identity", "measure_case_target_engagement"], "source_independence": "unknown"}
                messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": json.dumps(packet, ensure_ascii=False)}]
                record["request_sha256"] = hashlib.sha256(json.dumps(messages, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
                write(response_dir / (case["id"] + "_" + arm + "_request.json"), messages)
                before = client.provider_usage
                try:
                    answer, reply = client.complete_json(messages, max_tokens=1400)
                    record.update({"answer": answer, "reply_model": reply.model, "finish_reason": reply.finish_reason, "usage": reply.usage})
                except Exception as error:
                    record.update({"error_type": type(error).__name__, "answer": None})
                after = client.provider_usage
                record["usage_delta"] = {k: after.get(k, 0) - before.get(k, 0) for k in set(before) | set(after)}
            record["latency_seconds"] = time.perf_counter() - start
            records.append(record)
            write(response_dir / (case["id"] + "_" + arm + ".json"), record)
            print(json.dumps({"completed": case["id"], "arm": arm, "error": record.get("error_type"), "latency_seconds": record["latency_seconds"]}), flush=True)
    write(OUT / "RESPONSES.json", {"records": records, "configured_model": settings.chat_model, "provider_usage": client.provider_usage, "provider_reported_cost": None, "cost_status": "No authenticated tariff/cost field; exact billing unknown, including lost transport responses."})
    write(OUT / "RESPONSE_FREEZE.json", {"utc": datetime.now(timezone.utc).isoformat(), "phase": "responses_before_evaluation", "reference_sha256": sha(OUT / "REFERENCE.json"), "files": {str(p.relative_to(ROOT)).replace("\\", "/"): sha(p) for p in sorted(response_dir.glob("*.json")) + [OUT / "RESPONSES.json"]}})


def evaluate():
    frozen = read(OUT / "RESPONSE_FREEZE.json")
    for p, digest in frozen["files"].items():
        if sha(ROOT / p) != digest:
            raise ValueError("Frozen response changed: " + p)
    oracle = {r["case_id"]: r["expected"] for r in read(OUT / "REFERENCE.json")["cases"]}
    results, summaries = [], {}
    for record in read(OUT / "RESPONSES.json")["records"]:
        expected, answer = oracle[record["case_id"]], record["answer"]
        fields = {k: isinstance(answer, dict) and answer.get(k) == v for k, v in expected.items()}
        exact = isinstance(answer, dict) and set(answer) == set(expected) and all(fields.values())
        unsafe = isinstance(answer, dict) and (answer.get("case_measurement_supported") is not False or answer.get("independent_biological_confirmation") is not False)
        results.append({"case_id": record["case_id"], "arm": record["arm"], "exact_package": exact, "field_correct": fields, "unsafe_claim": unsafe})
        summary = summaries.setdefault(record["arm"], {"cases": 0, "exact_packages": 0, "unsafe_claims": 0, "errors": 0, "latency_seconds": 0.0, "field_correct": {k: 0 for k in expected}})
        summary["cases"] += 1
        summary["exact_packages"] += int(exact)
        summary["unsafe_claims"] += int(unsafe)
        summary["errors"] += int(record.get("error_type") is not None)
        summary["latency_seconds"] += record["latency_seconds"]
        for k, correct in fields.items():
            summary["field_correct"][k] += int(correct)
    write(OUT / "RESULTS.json", {"summaries": summaries, "records": results, "scope": read(HERE / "PROTOCOL.json")["scope"], "MAP_benefit_acceptance": summaries["source_typed_map_llm"]["exact_packages"] > max(summaries[a]["exact_packages"] for a in ["production_lexical_llm", "deterministic_same_cards"]) and summaries["source_typed_map_llm"]["unsafe_claims"] <= min(summaries[a]["unsafe_claims"] for a in ["production_lexical_llm", "deterministic_same_cards"])})
    print(json.dumps(summaries, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["prepare", "acquire", "run", "evaluate"])
    globals()[parser.parse_args().command]()
