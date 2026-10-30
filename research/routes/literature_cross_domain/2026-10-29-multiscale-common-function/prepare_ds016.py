"""Prepare a fixed, source-only clerical packet; no scientific choices delegated."""
from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
TASK = HERE.parent / "deepseek" / "tasks" / "DS016"
rows = json.loads((HERE / "reading_extracts.json").read_text(encoding="utf-8"))
ns = {"a": "http://www.w3.org/2005/Atom"}
entries = {}
for filename in ("q2_hierarchical_nlp.xml", "q3_missing_multimodal.xml"):
    for item in ET.parse(HERE / "sources" / filename).findall("a:entry", ns):
        entries[item.findtext("a:id", namespaces=ns).rsplit("/", 1)[-1]] = item

ids = ("2507.07955v2", "2603.06351v2", "2507.19264v2")
locations = (("S2.SS1.SSS2.Px2.p1.1", "S2.SS2.SSS1.Px1.p1.1"),
             ("S3.SS1.p2.1", "A1.SS2.p1.1"),
             ("S3.SS1.p1.1", "S3.SS4.p1.1"))
records = []
for paper, arxiv_id, locators in zip(rows, ids, locations):
    item = entries[arxiv_id]
    records.append({"id": arxiv_id, "title": " ".join(item.findtext("a:title", namespaces=ns).split()),
        "published": item.findtext("a:published", namespaces=ns),
        "source_file": paper["file"], "sha256": hashlib.sha256((HERE/"sources"/paper["file"]).read_bytes()).hexdigest(),
        "excerpts": [r for r in paper["rows"] if r["id"] in locators],
        "fields": ["arxiv_id_and_version", "first_public_date", "training_or_routing_input_scope_quote",
                   "cost_unit_if_explicit", "missing_modality_training_assumption_if_explicit"]})
prompt = ("按固定字段给三条原文做来源编目。仅返回JSON {records:[{id,fields:{...},ambiguities:[]}]}。"
          "每字段用来源原文短句或真正JSON null；日期保持published，不能把首发日期说成v2更新时间或正式接受日期。"
          "HTML标题/版本以packet记录为准，不查询外部。计算FLOPs与实验测量成本不能互换；某片段未提不等于整篇不存在。"
          "完整多模态训练和训练期随机丢模态按原句保留。不得选择机制/假设/方法/指标，不作科学迁移裁决。"
          "局部歧义记录后继续其他字段。无工具、无脚本、只此packet。\n"+json.dumps({"records": records}, ensure_ascii=False))
raw = prompt.encode("utf-8")
assert len(raw) <= 12000 and all(len(r["excerpts"]) == 2 for r in records)
TASK.mkdir()
(TASK/"workspace").mkdir()
(TASK/"source_packet.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
(TASK/"prompt.txt").write_bytes(raw)
job = {"task_id": "DS016", "task_version": "v1", "status": "assigned_ready_for_execution",
       "is_execution_authorization": True, "transport": "isolated_headless_stdin_no_tools",
       "objective": "三篇CV/NLP原文固定字段版本/训练可见信息/成本单位编目，不做机制判断",
       "inputs": [{"path": str(TASK/"source_packet.json"), "sha256": hashlib.sha256((TASK/"source_packet.json").read_bytes()).hexdigest()}],
       "prompt_sha256": hashlib.sha256(raw).hexdigest(),
       "budget": {"wall_seconds": 180, "max_output_tokens": 2048, "max_stdin_bytes": 12000,
                  "model_calls": 1, "automatic_retries": 0, "new_downloads": 0, "declared_cost_cap_usd": .025},
       "agent_permissions": "all tools disabled; read-only isolated workspace; injected snippets only",
       "allowed_write_root": str(TASK), "deliverables": ["receipt.json", "events.jsonl", "final.md", "usage.json"],
       "acceptance_criteria": ["three exact ids", "dates not upgraded to venue/version dates", "quotes source-scoped", "unprovided fields null", "no scientific adjudication"],
       "stop_conditions": ["uncertain outcome no retry/backend switch", "report local ambiguity and continue unaffected fields"],
       "requires_main_agent_review": True, "mainline": "common functional-data/source ledger; check next formal task at every small-step boundary"}
(TASK/"task.json").write_text(json.dumps(job, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"task": "DS016", "stdin_B": len(raw), "records": len(records)}))
