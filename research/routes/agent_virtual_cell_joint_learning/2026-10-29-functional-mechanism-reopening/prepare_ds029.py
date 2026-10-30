"""Give Harness a fixed, independently parser-checked source-status ledger."""
from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET
from pypdf import PdfReader

here = Path(__file__).resolve().parent
source = here / "sources/root"
task = here.parent / "deepseek/tasks/DS029"
receipts = {r["tag"]: r for r in map(json.loads, (source/"retrieval.jsonl").read_text().splitlines())}
tags = ["rl_mba_pdf", "rl_mba_pdf_full", "asking_pdf", "reap_jats", "polypharmacology_jats"]
rows = []
for tag in tags:
    r = receipts[tag]
    raw = (source/r["body_file"]).read_bytes()
    assert len(raw) == r["bytes"] and hashlib.sha256(raw).hexdigest() == r["sha256"]
    if r["status"] != 200:
        status, pages = "http_failure_not_method_evidence", None
    elif r.get("error"):
        status, pages = "truncated_inadmissible", None
    elif raw.startswith(b"%PDF-"):
        status, pages = "complete_pdf_partial_reading", len(PdfReader(source/r["body_file"]).pages)
    else:
        assert ET.fromstring(raw).tag == "article"
        status, pages = "complete_jats_partial_reading", None
    rows.append({"id": tag, "http_status": r["status"], "saved_bytes": len(raw),
                 "sha256": r["sha256"], "pages": pages, "artifact_status": status})
packet = {"rows": rows, "rules": "Copy all six fields exactly, including null and hashes; artifact_status is prescribed by coordinator parser/status checks, not a scientific verdict."}
prompt = ("Return JSON only: {rows:[all five input rows in order, all six fields exactly],ambiguities:[]}. "
          "No tools, scripts, new sources or hypothesis/metric/method choices. Do not equate complete artifacts with full reading or scientific validation. "
          "If an input ambiguity exists, record it and continue unaffected rows. One isolated call, 180 seconds, 2048 output tokens, 12000 bytes stdin, declared USD0.025; actual cost/hard dollar enforcement unknown. "
          "No automatic retry/backend change. After each outer task step check for a new formal task; otherwise resume only an authorized packet of source-well/time/control/repeat/unit checks. "
          "INPUT:\n" + json.dumps(packet, separators=(",", ":"))).encode()
assert len(prompt) <= 12000
task.mkdir(exist_ok=False)
(task/"workspace").mkdir()
(task/"source_packet.json").write_text(json.dumps(packet,indent=2)+"\n",encoding="utf-8")
(task/"prompt.txt").write_bytes(prompt)
job = {"task_id":"DS029","task_version":"v1","status":"assigned_ready_for_execution",
       "is_execution_authorization":True,"transport":"isolated_headless_stdin_no_tools",
       "objective":"Format five fixed source-status records without upgrading artifact or reading evidence",
       "inputs":[{"path":str(task/"source_packet.json"),"sha256":hashlib.sha256((task/"source_packet.json").read_bytes()).hexdigest()}],
       "prompt_sha256":hashlib.sha256(prompt).hexdigest(),
       "budget":{"wall_seconds":180,"max_output_tokens":2048,"max_stdin_bytes":12000,"model_calls":1,
                 "automatic_retries":0,"new_downloads":0,"declared_cost_cap_usd":0.025,"hard_dollar_cap_verified":False},
       "agent_permissions":"All tools disabled; fixed packet only; new workspace/DSH_HOME; no scripts",
       "allowed_write_root":str(task),"deliverables":["events.jsonl","final.md","usage.json","receipt.json"],
       "acceptance_criteria":["Five IDs and thirty fields exactly match source_packet","No artifact completeness upgraded to scientific or full-reading claim"],
       "stop_conditions":["Uncertain result: no automatic retry or backend substitution"],"requires_main_agent_review":True,
       "mainline":"Check new formal tasks each step; otherwise source-well/time/control/repeats/units only with explicit input/rules/budget"}
(task/"task.json").write_text(json.dumps(job,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"task_id":"DS029","stdin_bytes":len(prompt),"rows":len(rows),"history_calls":20,"authorized_new_calls":1}))
