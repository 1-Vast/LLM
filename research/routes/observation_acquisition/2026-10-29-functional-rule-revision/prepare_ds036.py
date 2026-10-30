"""Advance the saved fixed P3/P4 fields checkpoint; no scientific delegation."""
from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET

episode = Path(__file__).resolve().parent
aux = episode.parent / "deepseek"
task = aux / "tasks/DS036"
assert not task.exists(), "Never replace an existing task or replay its call"
(task / "workspace").mkdir(parents=True)
prior = episode.parent / "2026-10-29-common-function-mechanism-renewal/evidence"
plain = lambda e: " ".join("".join(e.itertext()).split())
sources = []
for name, ids in [("p3_transition.xml", {"Sec12", "Sec14"}), ("p4_collateral_sarcoma.xml", {"Sec12", "Sec16"})]:
    path = prior / name
    root = ET.parse(path).getroot()
    entry = {"file": name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
             "doi": next(plain(e) for e in root.findall(".//article-meta/article-id") if e.get("pub-id-type") == "doi"),
             "passages": {e.get("id"): plain(e) for e in root.iter("sec") if e.get("id") in ids}}
    if name.startswith("p4"):
        entry["figure4_caption"] = next(plain(e.find("caption")) for e in root.iter("fig") if plain(e.find("label")) == "Fig. 4")
    sources.append(entry)
packet = {"sources": sources, "literal_flags": ["P3_P4_CTG_are_distinct_protocols", "P4_pretreatment_dose_conflict_unresolved", "n2_does_not_name_replicate_kind", "no_raw_response_values_supplied"]}
(task / "source_packet.json").write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
rules = """Supplied-source literal fields and exact arithmetic only. No tools or lookup. Do not select hypotheses/metrics/methods, resolve conflicts scientifically, or issue PASS/mechanism advice. Return JSON only with exactly these keys:
p3: {seed_cells_per_well,pre_assay_wait_hours,CTG_treatment_hours,CTG_treatment_seconds,repeated_drug_segment_hours,resting_first_drug_hours,resting_no_drug_hours,resting_second_drug_hours,sustained_total_hours,readout}; numeric scalars or null; readout copy as 'CellTiter-Glo'. Sustained total not supplied -> null and list its key under missing_fields. Infer no duration from other regimens.
p4: {seed_cells_per_well,pre_assay_wait_hours,CTG_treatment_hours,CTG_treatment_seconds,screen_inhibitor_uM,temporal_pretreatment_days,temporal_pretreatment_seconds,temporal_pretreatment_methods_uM,temporal_pretreatment_caption_uM,figure4_n,figure4_replicate_kind,readout}; numbers as scalars, figure4_replicate_kind='unspecified in supplied caption', readout='CellTiter-Glo'. Distinguish main screen concentration from temporal pretreatment doses.
conflicts: [{field:'P4 temporal pretreatment concentration',caption_uM:<number>,methods_uM:<number>,status:'unresolved; no choice made'}]. Preserve both source values.
flags: copy literal_flags exactly in supplied order.
missing_fields: list absent key paths only; continue all unambiguous fields.
Prescribed conversions: hours*3600,days*86400. No unit conversion of concentrations or replicates. No scientific inference or extra prose. At each small-step boundary check new formal task first, otherwise continue supplied source/unit/time/replicate checkpoint; missing/conflicting fields do not stop independent fields.
One call/toolsdisabled/180s/2048outputtokens/12000Bstdin/declaredUSD0.025(hard dollar cap unknown)/0retry/backendchange.
INPUT:
"""
prompt = (rules + json.dumps(packet, ensure_ascii=False, indent=2)).encode("utf-8")
assert len(prompt) <= 12000, len(prompt)
(task / "prompt.txt").write_bytes(prompt)
job = {"task_id": "DS036", "task_version": "v1", "status": "assigned_ready_for_execution",
       "is_execution_authorization": True, "transport": "isolated_headless_stdin_no_tools",
       "objective": "Resume P3/P4 literal time/readout/replicate fields and preserve dose conflict",
       "inputs": [{"path": str(task / "source_packet.json"), "sha256": hashlib.sha256((task / "source_packet.json").read_bytes()).hexdigest()}],
       "prompt_sha256": hashlib.sha256(prompt).hexdigest(),
       "budget": {"wall_seconds": 180, "max_output_tokens": 2048, "max_stdin_bytes": 12000, "model_calls": 1, "automatic_retries": 0, "new_downloads": 0, "declared_cost_cap_usd": 0.025, "hard_dollar_cap_verified": False},
       "agent_permissions": "All tools disabled; isolated workspace/DSH_HOME; supplied original methods/caption only",
       "allowed_write_root": str(task), "deliverables": ["receipt.json", "events.jsonl", "final.md", "usage.json"],
       "acceptance_criteria": ["Literal fields and scalar types match named original clauses", "Exact prescribed time conversions", "Both conflicting pretreatment doses retained without choosing", "Missing sustained total marked; no scientific inference"],
       "requires_main_agent_review": True,
       "mainline": "New formal task first; otherwise source/unit/time/replicate fields within supplied inputs/rules/budget. Continue unaffected fields if local ambiguity."}
(task / "task.json").write_text(json.dumps(job, indent=2) + "\n", encoding="utf-8")
status = """# DS036 assigned — advance the saved P3/P4 field checkpoint (2026-10-29)

One newly authorized fixed-rule packet resumes the explicit default after DS035. Supplied P3/P4 methods and Fig4 caption only; preserve both 0.5 and 1 micromolar temporal pretreatment statements without choosing a scientific resolution. Exact time conversions and missing-duration formatting only. One tool-disabled isolated call, 180s / 2048outputtokens / 12000Bstdin / declaredUSD0.025 (hard dollar cap unverified), no retry/backendchange. Historical attempts27 retained. No raw outcomes, hypothesis/method/metric choice or mechanism verdict.

Check new formal tasks first at each small-step boundary; otherwise finish this supplied field packet, record conflict/missing fields and continue unaffected fields. Main review is required before adoption. No earlier task replay or live background process is inferred. Historical completed entries below remain historical.

"""
for name in ["CURRENT_TASK.md", "MAINLINE.md", "TASK_QUEUE.md"]:
    target = aux / name
    target.write_text(status + target.read_text(encoding="utf-8"), encoding="utf-8")
print(json.dumps({"task": "DS036", "stdin_bytes": len(prompt), "source_files": [s["file"] for s in sources]}))
