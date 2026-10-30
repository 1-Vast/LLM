"""Assign fixed source-unit cataloguing; no method or hypothesis decisions."""
from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET

from pypdf import PdfReader

HERE = Path(__file__).resolve().parent
TASK = HERE.parent / "deepseek/tasks/DS026"
chem_path = HERE / "sources/chemical_methods/fulltext2023.body"
acs_path = HERE / "sources/root/sampling_innovation_pdf.body"
iso_path = HERE / "sources/root/supervision_level_pdf.body"
chem = ET.fromstring(chem_path.read_bytes())
acs, iso = PdfReader(acs_path), PdfReader(iso_path)


def paragraph(identity):
    return "".join(chem.find(f'.//p[@id="{identity}"]').itertext())


def window(text, quote, before=220, after=330):
    start = text.index(quote)
    return text[max(0, start - before):start + len(quote) + after]


entries = [
    ("M1", "chemical2023", "Par39-40", "Svalidity", "model_predicted_negative_fraction", "fraction", "predicted as Ames negative", "definition_only_not_experimental_success", paragraph("Par39") + " " + paragraph("Par40")),
    ("M2", "chemical2023", "Par38", "ID_gate", "model_applicability_domain", "Tanimoto_similarity", "all exceed the defined similarity threshold DT", "not_attachment_context_or_cell_effect", paragraph("Par38")),
    ("M3", "chemical2023", "Par31", "attachment_radius", "graph_environment_setting", "bond_radius", "with a radius from 0 to 5", "not_physical_dose", paragraph("Par31")),
    ("S1", "SIBACS2025", "PDF p5 section4.1", "SRinit", "initial_sampling_fraction", "fraction", "SRinit is defined to 0.02", "source_setting_not_drug_cost", acs.pages[4].extract_text()),
    ("S2", "SIBACS2025", "PDF p3 Eq1 context", "alpha", "reconstruction_change_squared", "squared_image_reconstruction_units", "innovation refers to", "not_automatically_realized_error_reduction", acs.pages[2].extract_text()),
    ("I1", "ISO2025", "PDF p6 section5.3", "Cf", "relative_annotation_cost", "relative_cost", "Cf was set to 1", "not_USD_or_measured_assay_price", iso.pages[5].extract_text()),
    ("I2", "ISO2025", "PDF p4 section4.2", "validation_budget", "author_stated_validation_allocation", "one_round_budget_context", "randomly sampled", "total_plotted_budget_deduction_unverified", iso.pages[3].extract_text()),
]
rows = []
for item in entries:
    row = dict(zip(("id", "source_id", "locator", "field", "kind", "unit", "source_quote", "qualification"), item[:8]))
    assert len(row["source_quote"]) <= 48
    row["original_context"] = window(item[8], row["source_quote"])
    assert row["source_quote"] in row["original_context"]
    rows.append(row)
packet = {"source_hashes": {"chemical2023": hashlib.sha256(chem_path.read_bytes()).hexdigest(),
                            "SIBACS2025": hashlib.sha256(acs_path.read_bytes()).hexdigest(),
                            "ISO2025": hashlib.sha256(iso_path.read_bytes()).hexdigest()},
          "context_method": "Literal JATS itertext or pypdf page extraction, line breaks preserved; excerpts are derived source-reading aids, not newly observed experiments",
          "rows": rows}
instruction = """你是工具禁用的来源/单位编目辅助。INPUT给七条已由主研究者指定的原文片段及分类；不得选科学假说、方法、指标、机理或改变分类。逐行核source_quote确为original_context连续字面片段；输出且仅输出JSON数组，按输入顺序七项，每项仅id,source_id,locator,field,kind,unit,source_quote,qualification,quote_literal。前八项必须逐字复制，quote_literal用true/false；不得补写或改写quote。PDF原文断行保留，不自动去连字符或重写公式。qualification是主研究者预设的证据边界，不是你独立作出的科学判断。有一条quote不匹配也继续其他条，不能擅改输入救true。不计算药效或声称真实实验成功/美元预算/机制成立。
预算一次隔离headless，180s/2048输出tokens/12000B stdin，声明USD.025、硬美元cap及实付未知；0工具/网络/下载/重试/后端替换。历史17加本次1累计上限18。小步后由外层查新正式task，有则优先，无则在有packet与预算时继续字段/单位/来源台账，局部歧义不停止独立字段，无额度不虚称后台。
INPUT:
"""
prompt = (instruction + json.dumps(packet, ensure_ascii=False, separators=(",", ":"))).encode("utf-8")
assert len(prompt) <= 12000
TASK.mkdir(exist_ok=False)
(TASK / "workspace").mkdir()
(TASK / "source_packet.json").write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(TASK / "prompt.txt").write_bytes(prompt)
task = {"task_id": "DS026", "task_version": "v1", "status": "assigned_ready_for_execution", "is_execution_authorization": True,
        "transport": "isolated_headless_stdin_no_tools", "objective": "Catalogue seven prescribed source/unit/qualification rows and verify literal quotations only",
        "inputs": [{"path": str(TASK / "source_packet.json"), "sha256": hashlib.sha256((TASK / "source_packet.json").read_bytes()).hexdigest()}],
        "prompt_sha256": hashlib.sha256(prompt).hexdigest(),
        "budget": {"wall_seconds": 180, "max_output_tokens": 2048, "max_stdin_bytes": 12000, "model_calls": 1,
                   "automatic_retries": 0, "new_downloads": 0, "declared_cost_cap_usd": 0.025, "hard_dollar_cap_verified": False},
        "agent_permissions": "All tools disabled; injected fixed packet only; isolated read-only workspace and new DSH_HOME; no script execution",
        "allowed_write_root": str(TASK), "deliverables": ["events.jsonl", "final.md", "usage.json", "receipt.json"],
        "acceptance_criteria": ["Exactly seven assigned IDs and exact copied eight fields", "Literal quote flags match coordinator check; quotes no longer than48 characters", "No new scientific classification, cost assumption or efficacy claim"],
        "stop_conditions": ["Uncertain result: no automatic retry or backend substitution"], "requires_main_agent_review": True,
        "mainline": "Prescribed source/measurement units, raw-versus-model-predicted evidence, time/control/replicate/source keys; check new task after each small step"}
(TASK / "task.json").write_text(json.dumps(task, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"task_id": "DS026", "stdin_bytes": len(prompt), "rows": 7, "prior_calls": 17, "cumulative_cap": 18}))
