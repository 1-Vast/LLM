"""Prepare a bounded, tool-free glossary transcription packet, no scientific choices."""
from pathlib import Path
import hashlib
import json

from pypdf import PdfReader

HERE = Path(__file__).resolve().parent
TASK = HERE.parent / "deepseek/tasks/DS025"
SOURCE = HERE.parent / "2026-10-29-ordinary-dose-structure/sources/well_glossary.pdf"
source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
assert source_hash == "86a366aae5914322349613fe6610da5ffbf7359a45ae3bbf609633aaecb0dec1"
text = PdfReader(SOURCE).pages[0].extract_text()
entries = [
    ("F1", "PROJECT_ID", "project_identifier", None, "Numeric identifier of drug screening project.", "project_scope_only"),
    ("F2", "MASTER_CELL_ID", "cell_model_identifier", None, "Each cell model has a unique numeric identifier.", "model_not_culture_replicate"),
    ("F3", "lib1_drug_id / lib2_drug_id", "compound_identifier", None, "Identifier used for the library compound", "internal_database_identity_only"),
    ("F4", "lib1_drug / lib2_drug", "curve_reference_identifier", None, "Identifier for the drug used to fit", "not_a_compound_name_or_independent_well"),
    ("F5", "lib1_conc / lib2_conc", "physical_concentration", "uM", "Micromolar concentration of the library compound", "physical_dose_only"),
    ("F6", "CELL_ID", "stock_expansion_identifier", None, "Identifier for the expansion from stocks", "independent_culture_not_authenticated"),
    ("F7", "treatment", "treatment_flag", None, "alwaysC in this file.", "combination_rows_not_single_drug_wells"),
    ("F8", "lib1_x / lib2_x", "normalized_coordinate", "normalized_max9", "Concentration values normalized to a maximum", "not_physical_concentration"),
    ("F9", "BARCODE", "screening_plate_identifier", None, "Barcode identifier for screening plate.", "plate_not_source_well_or_independent_culture"),
]
rows = [dict(zip(("id", "field", "kind", "canonical_unit", "source_quote", "boundary"), entry)) for entry in entries]
for row in rows:
    assert row["source_quote"] in text and len(row["source_quote"]) <= 48
packet = {"source": str(SOURCE), "sha256": source_hash, "page": 1, "original_text": text,
          "rules": "Copy the assigned fields and literal quote candidates exactly; boundary is a prescribed audit label, not a model inference.", "rows": rows}
TASK.mkdir(exist_ok=False)
(TASK / "workspace").mkdir()
(TASK / "source_packet.json").write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
instruction = """你是固定字段抄录辅助，工具全禁用。只检查INPUT九行source_quote是否为original_text连续字面片段，然后按输入顺序输出一个JSON数组，每项仅id,field,kind,canonical_unit,source_quote,boundary,ambiguity。前六字段必须逐字复制已给值，空单位用null；不得改写/增补quote，quote已由主Agent限制≤48字。完全符合时ambiguity=null；若字段存在歧义，ambiguity记录该问题并继续其他行，不自行更改规则/数据。boundary是主Agent预设标签，不让你作科学判断。不能选择假说、方法、指标、MMP规则、判机制、推断缺失实验或读取其他文件。输出不带解释/markdown。
一次隔离headless，180s/2048输出tokens/12000B stdin，声明USD0.025，硬美元cap及实付未知；工具/下载/重试/后端替换0，历史16+本次1累计上限17。每完成小步由外层检查新正式task，有则优先，无则在有packet/预算时恢复support关联、导出vs拟合、time/控制/重复/source键；缺预算只保存断点，不虚称后台。
INPUT:
"""
prompt = (instruction + json.dumps(packet, ensure_ascii=False, separators=(",", ":"))).encode("utf-8")
assert len(prompt) <= 12000
(TASK / "prompt.txt").write_bytes(prompt)
task = {"task_id": "DS025", "task_version": "v1", "status": "assigned_ready_for_execution", "is_execution_authorization": True,
        "transport": "isolated_headless_stdin_no_tools", "objective": "Transcribe nine fixed original-glossary field/unit/source-boundary records, no scientific judgement",
        "inputs": [{"path": str(TASK / "source_packet.json"), "sha256": hashlib.sha256((TASK / "source_packet.json").read_bytes()).hexdigest()}],
        "prompt_sha256": hashlib.sha256(prompt).hexdigest(),
        "budget": {"wall_seconds": 180, "max_output_tokens": 2048, "max_stdin_bytes": 12000, "model_calls": 1,
                   "automatic_retries": 0, "new_downloads": 0, "declared_cost_cap_usd": 0.025, "hard_dollar_cap_verified": False},
        "agent_permissions": "All tools disabled; injected fixed packet only; isolated read-only workspace; new DSH_HOME; no script execution",
        "allowed_write_root": str(TASK), "deliverables": ["events.jsonl", "final.md", "usage.json", "receipt.json"],
        "acceptance_criteria": ["Exactly nine assigned IDs and exact copied fields", "Quotes literal in re-read original PDF and no more than48 characters", "No invented unit, culture, response or mechanism conclusion"],
        "stop_conditions": ["Uncertain result: no automatic retry or backend substitution"], "requires_main_agent_review": True,
        "mainline": "support joins, exported versus fitted response, time/control/replicate/source units; check new task after each small step"}
(TASK / "task.json").write_text(json.dumps(task, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"task_id": "DS025", "stdin_bytes": len(prompt), "rows": 9, "prior_calls": 16, "cumulative_cap": 17}))
