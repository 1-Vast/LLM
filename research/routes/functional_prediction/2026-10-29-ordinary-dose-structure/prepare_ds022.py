"""Prepare a fixed unit/field-copying packet; the auxiliary makes no scientific choices."""
from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
TASK = HERE.parent / "deepseek/tasks/DS022"
TASK.mkdir(exist_ok=False)
(TASK / "workspace").mkdir()
pages = json.loads((HERE / "sources/well_glossary_text.json").read_text(encoding="utf-8"))
glossary = "\n".join(x["text"] for x in pages)
paper = HERE.parent / "2026-10-28-blocked-conclusion-review/PMC11061612.xml"
screening = " ".join("".join(ET.parse(paper).getroot().find('.//sec[@id="S15"]').itertext()).split())
packet = {
    "source_identity": {
        "glossary_sha256": hashlib.sha256((HERE / "sources/well_glossary.pdf").read_bytes()).hexdigest(),
        "paper_sha256": hashlib.sha256(paper.read_bytes()).hexdigest(),
        "paper_locator": "PMC11061612 S15"
    },
    "glossary_pages": pages,
    "screening_original": screening,
    "rows": [
        {"id": "D1", "field": "lib1_conc", "rule_kind": "physical_concentration", "rule": "copy micromolar; canonical_unit=uM; si_factor=0.000001; converted_value=null"},
        {"id": "D2", "field": "lib2_conc", "rule_kind": "physical_concentration", "rule": "copy micromolar; canonical_unit=uM; si_factor=0.000001; converted_value=null"},
        {"id": "D3", "field": "lib1_x", "rule_kind": "normalized_coordinate", "rule": "normalized dose scale with maximum9; canonical_unit=normalized_max9; si_factor=null; converted_value=null"},
        {"id": "D4", "field": "lib1_IC50", "rule_kind": "log_concentration", "rule": "natural log micromolar; canonical_unit=ln_uM; no linear SI factor, si_factor=null; converted_value=null"},
        {"id": "D5", "field": "lib1_y", "rule_kind": "functional_reference", "rule": "inhibitory response fraction; canonical_unit=fraction; si_factor=null; converted_value=null; do not infer independent measurement identity"},
        {"id": "D6", "field": "lib1_yhat", "rule_kind": "fitted_reference", "rule": "fitted inhibitory response; canonical_unit=fraction; si_factor=null; converted_value=null"},
        {"id": "D7", "field": "CELL_ID", "rule_kind": "stock_expansion_id", "rule": "identifier only; canonical_unit=null; si_factor=null; converted_value=null; do not infer independent culture"},
        {"id": "D8", "field": "treatment", "rule_kind": "combination_flag", "rule": "copy always C from this glossary; canonical_unit=null; si_factor=null; converted_value=null"},
        {"id": "D9", "field": "study_treatment_duration", "rule_kind": "study_level_duration", "rule": "S15 states72 hours; canonical_unit=h; si_factor=3600; converted_value=72*3600 seconds; do not invent per-row time field"},
        {"id": "D10", "field": "INTENSITY", "rule_kind": "source_wording_conflict", "rule": "glossary says Fluorescence, S15 says luminescence; canonical_unit=null; si_factor=null; converted_value=null; ambiguity=glossary_fluorescence_vs_paper_luminescence; do not resolve conflict"}
    ]
}
(TASK / "source_packet.json").write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
instruction = """你是重复性字段/单位编目辅助，工具全部禁用。只按每行已给rule复制/归一，不选择科学假设、指标、方法或裁决机制。输出且仅输出10行JSON数组；字段固定id,field,kind,canonical_unit,si_factor,converted_value,source_quote,ambiguity。kind逐字复制rule_kind；其余按rule给定值，missing=null。source_quote必须是所附原文中的连续字面片段，最多64Unicode字符；不可改写。D10只需从glossary给短quote，另保留预设冲突标记，不纠正原文。D9唯一计算=72*3600，以秒输出converted_value；其他行均null。不得把log/normalized coordinate线性转换成摩尔，不把参照行当独立测量。歧义写ambiguity，继续其他行。
预算：一次headless，180s、2048输出tokens、12000B stdin，USD0.025为声明上限、硬美元cap/实付未知；0工具/下载/自动重试/换后端。历史13保留，本轮1次累计上限14。每行一小步；之后由外层查正式新task，有则优先，无则续有输入/预算的support关联、原始点vs拟合、time/控制/重复字段主线。无packet/额度保存断点，不虚称后台。
INPUT:
"""
prompt = (instruction + json.dumps(packet, ensure_ascii=False, separators=(",", ":"))).encode("utf-8")
assert len(prompt) <= 12_000
(TASK / "prompt.txt").write_bytes(prompt)
job = {
    "task_id": "DS022", "task_version": "v1", "status": "assigned_ready_for_execution",
    "is_execution_authorization": True, "transport": "isolated_headless_stdin_no_tools",
    "objective": "Ten fixed raw-field/unit entries, one prescribed time conversion and one preserved wording conflict",
    "inputs": [{"path": str(TASK / "source_packet.json"), "sha256": hashlib.sha256((TASK / "source_packet.json").read_bytes()).hexdigest()}],
    "prompt_sha256": hashlib.sha256(prompt).hexdigest(),
    "budget": {"wall_seconds": 180, "max_output_tokens": 2048, "max_stdin_bytes": 12000,
               "model_calls": 1, "automatic_retries": 0, "new_downloads": 0,
               "declared_cost_cap_usd": 0.025, "hard_dollar_cap_verified": False},
    "agent_permissions": "all tools disabled; injected packet only; read-only isolated workspace",
    "allowed_write_root": str(TASK),
    "deliverables": ["events.jsonl", "final.md", "usage.json", "receipt.json"],
    "acceptance_criteria": ["10 exact IDs and fixed fields", "units and nulls match supplied rules", "72*3600=259200", "literal quotes <=64", "conflict preserved, no scientific inference"],
    "stop_conditions": ["Uncertain result: no automatic retry or backend replacement"],
    "requires_main_agent_review": True,
    "mainline": "Support joins; raw points versus fit fields; time/control/replicate-unit ledger; inspect new task after each small step"
}
(TASK / "task.json").write_text(json.dumps(job, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"task_id": "DS022", "stdin_bytes": len(prompt), "rows": len(packet["rows"])}))
