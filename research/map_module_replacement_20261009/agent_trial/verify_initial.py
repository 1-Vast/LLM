"""Offline independent closure of the initial 12-case source qualification trial."""
import csv,hashlib,json,tempfile,sqlite3,gc,sys
from collections import defaultdict
from pathlib import Path
from rdkit import Chem
from rdkit.Chem import inchi
import numpy as np

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
OUT=ROOT/"outputs/map_module_replacement_20261009/agent_trial"
sys.path[:0]=[str(ROOT/"src"),str(ROOT)]
MODES={"inhibit":"INHIBITOR","activate":"ACTIVATOR","agonist":"AGONIST","antagonist":"ANTAGONIST"}
def read(p):return json.loads(p.read_text(encoding="utf-8"))
def sha(p):return hashlib.file_digest(p.open("rb"),"sha256").hexdigest()
def check(a,b,what):
    if a!=b:raise AssertionError(what)
def canonical(s):
    m=Chem.MolFromSmiles(s)
    if m is None:raise ValueError("Invalid preserved source structure")
    return Chem.MolToSmiles(m,canonical=True,isomericSmiles=True)

def main():
    frozen=read(HERE/"VERIFY_FREEZE.json")
    check(sha(Path(__file__)),frozen["verifier_sha256"],"Verifier freeze")
    frozen_count=0
    for p in [HERE/"FREEZE.json",OUT/"SOURCE_FREEZE.json",OUT/"RESPONSE_FREEZE.json"]:
        for name,value in read(p)["files"].items():
            check(sha(ROOT/name),value,"Frozen file "+name)
            frozen_count+=1
    repair=read(OUT/"SOURCE_REPAIR_FREEZE.json")
    check(sha(OUT/"SOURCES.json"),repair["source_sha256"],"Original sources retained")
    check(sha(OUT/"SOURCES.v3.json"),repair["repaired_sha256"],"Repaired source digest")
    refreeze=read(OUT/"REFERENCE_FREEZE.json")
    check(sha(OUT/"REFERENCE.json"),refreeze["reference_sha256"],"Reference before answers")
    check(sha(HERE/"PROTOCOL.json"),refreeze["protocol_sha256"],"Protocol before answers")
    check(sha(HERE/"trial.py"),refreeze["code_sha256"],"Runner before answers")
    audit=read(ROOT/"outputs/knowledge_layer_validation_20261009/AUDIT.json")["records"]
    cases=read(HERE/"CASES.json")
    # Reconstruct frozen stratum selection independently.
    first={}
    for row in audit:first.setdefault((row["smiles"],row["cid"]),row)
    pool=sorted(first.values(),key=lambda r:r["drug"])
    selection=[]
    seen=set()
    for label,count in [("inhibit",4),("antagonist",2),("agonist",2),("unparsed_binding",2),("no_edge",2)]:
        options=[]
        for r in pool:
            if r["drug"] in seen:continue
            if label in MODES:eligible=[e for e in r["edges"] if e["direction"]==label]
            elif label=="unparsed_binding":
                eligible=[e for e in r["edges"] if e["relation"]=="exhibits strong binding to the protein target encoded by"] if all(e["direction"]=="unknown" for e in r["edges"]) else []
            else:eligible=[]
            if eligible or label=="no_edge" and not r["edges"]:
                options.append((r,min(eligible,key=lambda x:x["source_row"]) if eligible else None))
        for r,edge in options[:count]:
            seen.add(r["drug"])
            symbol=sorted({n["Gene name"] for n in edge["gene_node_matches"]})[0] if edge else "MAPK1"
            selection.append((r,label,edge,symbol))
    check(len(selection),12,"Registered cases")
    for i,((r,label,edge,symbol),c) in enumerate(zip(selection,cases)):
        for key in ["drug","cid","smiles","dose","unit"]:check(c[key],r[key],"Selected "+key)
        check(c["id"],f"case_{i+1:02d}","Stable case IDs")
        check(c["stratum"],label,"Selection stratum")
        check(c["selected_map_edge"],edge,"Selected lowest source row")
        check(c["requested_gene"],symbol,"Selected gene symbol")
        check(c["all_map_edges"],r["edges"],"Original MAP pool")
    sources=read(OUT/"SOURCES.v3.json")
    check(len(sources["receipts"]),105,"Bounded public calls")
    raw_by_sha={}
    for r in sources["receipts"]:
        payload=(ROOT/r["path"]).read_bytes()
        check(len(payload),r["bytes"],"Source byte count")
        check(hashlib.sha256(payload).hexdigest(),r["sha256"],"Source SHA256")
        check(r["status"],200,"Source HTTP success")
        raw_by_sha[r["sha256"]]=json.loads(payload)
    def raw_response(container):
        check(container["body"],raw_by_sha[container["receipt"]["sha256"]],"Derived response vs immutable raw body")
        return container["body"]
    source_by_case={s["case_id"]:s for s in sources["cases"]}
    reference={r["case_id"]:r["expected"] for r in read(OUT/"REFERENCE.json")["cases"]}
    response=read(OUT/"RESPONSES.json")
    records=response["records"]
    check(len(records),36,"Three-arm answer packages")
    by_case_arm={(r["case_id"],r["arm"]):r for r in records}
    arms=["production_lexical_llm","source_typed_map_llm","deterministic_same_cards"]
    derived={}
    exact_identity_count=0
    source_cards=0
    actual_source_lines=0
    family_cards=[]
    for case in cases:
        source=source_by_case[case["id"]]
        body=raw_response(source["identity_query"]["response"])
        check(source["identity_query"]["full_inchi_key"],inchi.MolToInchiKey(Chem.MolFromSmiles(case["smiles"])),"Full structure identity query")
        matches=[m["molecule_chembl_id"] for m in body.get("molecules",[]) if (m.get("molecule_structures") or {}).get("canonical_smiles") and canonical(m["molecule_structures"]["canonical_smiles"])==canonical(case["smiles"])]
        check(matches,source["exact_molecule_ids"],"Exact full salt/stereo molecule matches")
        check(source["identity_status"],"exact" if len(matches)==1 else "blocked","No fallback identity status")
        exact_identity_count+=int(len(matches)==1)
        if len(matches)==1:
            raw_response(source["mechanism_response"])
            raw_response(source["activity_response"])
        for card in source["cards"]:
            source_cards+=1
            collection="mechanisms" if card["kind"]=="mechanism" else "activities"
            source_body=raw_by_sha[card["source_receipt"]["sha256"]]
            if card["kind"]=="mechanism":
                same=[x for x in source_body[collection] if x["mec_id"]==card["source_record"]["mec_id"]]
            else:same=[x for x in source_body[collection] if x["activity_id"]==card["source_record"]["activity_id"]]
            check(len(same),1,"Unique raw source card")
            check(card["source_record"],same[0],"Raw mechanism/activity equality")
            for name in ["target","assay","document"]:
                if card.get(name+"_receipt"):
                    check(card[name+"_record"],raw_by_sha[card[name+"_receipt"]["sha256"]],"Raw "+name+" equality")
            target=card["target_record"] or {}
            symbols=sorted({s["component_synonym"] for part in target.get("target_components",[]) for s in part.get("target_component_synonyms",[]) if s.get("syn_type")=="GENE_SYMBOL"})
            check(card["target_gene_symbols"],symbols,"Actual target_component_synonyms GENE_SYMBOL closure")
            if "FAMILY" in target.get("target_type",""):family_cards.append({"case":case["id"],"target":target.get("target_chembl_id"),"symbols":symbols,"type":target["target_type"]})
            actual_source_lines+=1
        expected={"molecule_status":source["identity_status"],"qualified_card_ids":[],"reported_modes":[],
                  "requested_mode_supported":False,"binding_assay_annotation":False,"direct_interaction_assertion":False,
                  "case_measurement_supported":False,"independent_biological_confirmation":False,
                  "action_identifier":"measure_case_target_engagement" if source["identity_status"]=="exact" else "verify_exact_identity"}
        if source["identity_status"]=="exact":
            for card in source["cards"]:
                if case["requested_gene"] not in card["target_gene_symbols"]:continue
                raw=card["source_record"]
                assay=card.get("assay_record") or {}
                if card["kind"]=="mechanism":
                    expected["qualified_card_ids"].append(card["id"])
                    if raw.get("action_type"):expected["reported_modes"].append(raw["action_type"])
                    if raw.get("direct_interaction") in [True,1]:expected["direct_interaction_assertion"]=True
                elif assay.get("assay_type")=="B" and assay.get("confidence_score")==9:
                    expected["qualified_card_ids"].append(card["id"])
                    expected["binding_assay_annotation"]=True
        expected["qualified_card_ids"].sort()
        expected["reported_modes"]=sorted(set(expected["reported_modes"]))
        expected["requested_mode_supported"]=MODES.get(case["requested_mode"]) in expected["reported_modes"]
        check(expected,reference[case["id"]],"Independent raw qualification vs manually frozen reference")
        derived[case["id"]]=expected
        # Verify the common tool payload from its immutable CSV using actual table_filter.
        from maestro.tool_analysis import table_filter
        csvpath=OUT/"tool_cards"/(case["id"]+".csv")
        visible_rows=list(csv.DictReader(csvpath.open(encoding="utf-8",newline="")))
        check(len(visible_rows),len(source["cards"]),"Raw-to-visible card count")
        for savedrow,card in zip(visible_rows,source["cards"]):
            visible=dict(card)
            target=card.get("target_record") or {}
            visible["target_record"]={k:target.get(k) for k in ["target_chembl_id","target_type","pref_name","organism"]}
            visible["target_record"]["target_components"]=[{"accession":part.get("accession"),"relationship":part.get("relationship"),"gene_symbols":[s["component_synonym"] for s in part.get("target_component_synonyms",[]) if s.get("syn_type")=="GENE_SYMBOL"]} for part in target.get("target_components",[])]
            check(json.loads(savedrow["card_json"]),visible,"Visible compact card vs raw source")
            check(savedrow["target_gene_symbols"],"|".join(card["target_gene_symbols"]),"Visible target filter symbols")
        from agent.knowledge import EvidenceLedger,EvidenceStatus
        with tempfile.TemporaryDirectory(prefix="map_verify_initial_ledger_") as directory:
            ledger=EvidenceLedger(Path(directory)/"ledger.sqlite")
            for e in case["all_map_edges"]:
                entities=(case["drug"],*sorted({n["Gene name"] for n in e["gene_node_matches"]}))
                ledger.add_evidence(f"{case['drug']} {e['relation']} {', '.join(entities[1:])}",source="MAP-KG:frozen_raw",context="Original MAP source assertion; conditions and original external provenance unknown.",status=EvidenceStatus.RETRIEVED,entities=entities,identifier=f"map:{e['source_row']:09d}",payload={"original_edge":e})
            with sqlite3.connect(ledger.path) as connection:connection.execute("UPDATE evidence SET created_at='2000-01-01T00:00:00+00:00'")
            connection.close()
            fetched=ledger.retrieve(f"{case['drug']} {case['requested_gene']} {case['requested_mode']} mechanism support",entities=(case["drug"],case["requested_gene"]),limit=8)
            lexical=[r.payload["original_edge"] for r in fetched]
            gc.collect()
        common=None
        for arm in arms:
            saved=by_case_arm[(case["id"],arm)]
            receipt=saved["tool_receipt"]
            check(sha(Path(receipt["arguments"]["dataset_path"])),receipt["input_sha256"],"Tool CSV digest")
            check(table_filter(receipt["arguments"]),receipt["output"],"Actual table_filter replay")
            if common is None:common=receipt
            else:check(receipt,common,"Same actual common tool execution payload")
            check(saved["answer"],expected,"Saved answer exact source package")
            if arm!="deterministic_same_cards":
                messages=read(OUT/"responses"/f"{case['id']}_{arm}_request.json")
                digest=hashlib.sha256(json.dumps(messages,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
                check(digest,saved["request_sha256"],"Provider request hash")
                task=json.loads(messages[1]["content"])
                for key,value in case.items():
                    if key not in ["all_map_edges","selected_map_edge"]:check(task["task"][key],value,"Case/task exact dose and context")
                visible=[json.loads(r["card_json"]) for r in common["output"]["payload"]["sample_rows"]]
                check(task["public_tool_cards"],visible,"Identical returned source tool cards")
                if arm=="source_typed_map_llm":
                    chosen=sorted([e for e in case["all_map_edges"] if any(n["Gene name"]==case["requested_gene"] for n in e["gene_node_matches"])],key=lambda e:e["source_row"])[:8]
                    check(task["MAP_prior"],chosen,"Source-typed prior exact query-gene rows")
                else:check(task["MAP_prior"],lexical,"Production lexical retrieval replay")
                check(saved["reply_model"],response["configured_model"],"Frozen configured model")
                check(saved["finish_reason"],"stop","Provider completion")
    llm=[r for r in records if r["arm"]!="deterministic_same_cards"]
    check(len(llm),24,"LLM call bound")
    usage={key:sum(r["usage"][key] for r in llm) for key in ["prompt_tokens","completion_tokens","total_tokens","prompt_cache_hit_tokens","prompt_cache_miss_tokens"]}
    for key,value in usage.items():check(value,response["provider_usage"][key],"Provider token totals")
    check(response["provider_usage"]["calls"],24,"Recorded provider calls")
    for r in llm:
        check(r["usage_delta"]["calls"],1,"One completion per fixed case/arm")
        for key,value in r["usage"].items():check(r["usage_delta"][key],value,"Provider usage delta")
    scored=read(OUT/"RESULTS.json")
    expected_record=[]
    for r in records:
        truth=derived[r["case_id"]]
        answer=r["answer"]
        fields={k:answer.get(k)==v for k,v in truth.items()}
        expected_record.append({"case_id":r["case_id"],"arm":r["arm"],"exact_package":set(answer)==set(truth) and all(fields.values()),
                                "field_correct":fields,"unsafe_claim":answer.get("case_measurement_supported") is not False or answer.get("independent_biological_confirmation") is not False})
    check(expected_record,scored["records"],"All36 scoring records")
    for arm in arms:
        rows=[r for r in records if r["arm"]==arm]
        s=scored["summaries"][arm]
        check(s["cases"],12,"Arm denominator")
        check(s["exact_packages"],sum(r["answer"]==derived[r["case_id"]] for r in rows),"Arm exact packages")
        check(s["unsafe_claims"],0,"Unsupported case/independence claims")
        np.testing.assert_allclose(s["latency_seconds"],sum(r["latency_seconds"] for r in rows),atol=1e-12)
    check(scored["MAP_benefit_acceptance"],False,"No accuracy advantage")
    report={"passed":True,"offline_only_no_provider_calls":True,"frozen_file_hashes_checked":frozen_count,
            "raw_public_responses_checked":len(sources["receipts"]),"raw_source_bytes":sum(r["bytes"] for r in sources["receipts"]),
            "cases_independently_reselected":12,"full_structure_matches":exact_identity_count,"blocked_full_structures":12-exact_identity_count,
            "raw_cards_closed":source_cards,"target_synonym_schema_verified":True,"manual_reference_equal_to_raw_reconstruction":True,
            "answer_packages_recomputed":36,"common_tool_case_payloads":12,"recorded_LLM_calls":24,"provider_usage_recomputed":usage,
            "exact_packages_per_arm":{a:scored["summaries"][a]["exact_packages"] for a in arms},
            "family_membership_cards":family_cards,"scope":"Source-qualification equality only; family membership is not selective engagement, B/confidence9 is assignment metadata not physical-binding proof, no independent/cellular/causal confirmation or MAP advantage.",
            "money_cost":"Unknown; no authenticated tariff/cost field; provider usage counts do not prove transport retry billing."}
    (OUT/"VERIFIED.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k!="family_membership_cards"},indent=2))

if __name__=="__main__":main()

