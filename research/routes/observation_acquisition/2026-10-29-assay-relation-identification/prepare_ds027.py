"""Six prescribed source/mask fields; no scientific choices delegated."""
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
TASK = HERE.parent / "deepseek/tasks/DS027"
SOURCES = HERE / "sources"
pdf4 = (SOURCES / "l2m_p04.txt").read_text(encoding="utf-8")
pdf5 = (SOURCES / "l2m_p05.txt").read_text(encoding="utf-8")
masks = (SOURCES / "incomplete_S3.SS3.txt").read_text(encoding="utf-8")
theorem = (SOURCES / "incomplete_S4.SS3.txt").read_text(encoding="utf-8")
restore = (SOURCES / "incomplete_S4.SS2.txt").read_text(encoding="utf-8")
values = [
    ("L1", "L2M2026", "PDF p4 revelation", "Rj", "missingness_mask", "observed1_missing0", "revelation mechanism", "definition_not_assay_independence", pdf4),
    ("L2", "L2M2026", "PDF p4 assumption3.2", "no_direct_effect", "identification_assumption", "conditional_independence", "No Direct Effect", "not_validated_for_drug_assay", pdf4),
    ("L3", "L2M2026", "PDF p5 definition4.1", "blocked_policy", "training_action_support_gate", "Rj0_action_probability0", "Blocked Policy", "not_a_deployment_action_ban", pdf5),
    ("I1", "AFAITD2026v1", "S3.3", "mi", "missingness_mask", "observed0_missing1", "mi=1 indicates that feature i is missing", "opposite_code_to_L2M", masks),
    ("I2", "AFAITD2026v1", "S4.3 theorem1", "predictor", "theorem_assumption", "fixed_independent_of_training_instances", "Let f be a fixed predictor", "not_arbitrary_fitted_network_guarantee", theorem),
    ("I3", "AFAITD2026v1", "S4.2 definition3", "restoration", "model_transition_recovery", "conditional_probability", "acquisition dynamics", "generated_values_not_new_measurements", restore),
]
fields = ["id", "source_id", "locator", "field", "kind", "unit", "source_quote", "qualification"]
rows = []
for value in values:
    row = dict(zip(fields, value[:8]))
    quote, original = row["source_quote"], value[8]
    assert len(quote) <= 48 and quote in original
    at = original.index(quote)
    row["original_context"] = original[max(0, at-200):at+len(quote)+400]
    rows.append(row)
packet = {"context_method": "Literal saved primary-reading derivatives; classifications supplied by coordinator",
          "source_hashes": {n: hashlib.sha256((SOURCES/n).read_bytes()).hexdigest() for n in ["l2m_pdf.body", "incomplete_html.body"]},
          "rows": rows}
instruction = """你是工具禁用的来源/单位编目辅助。逐条复制主研究者预设的八字段id,source_id,locator,field,kind,unit,source_quote,qualification，并核source_quote是否为original_context连续字面片段，增加quote_literal布尔字段。只输出按原顺序六项JSON数组，不加正文。前八字段必须逐字复制，不修公式、掩码、空格或分类，quote不超过48字符。注意L2M的Rj=1表示已观测，另一篇mi=1表示缺失；unit已由主研究者统一指定，你不自行决定科学含义。qualification由主研究者给定，不是你独立科研裁决。一条不匹配就标false并继续其他条，不能伪造true或修改原quote。
预算一次新隔离headless，180s/2048输出tokens/12000B stdin；USD.025是声明且硬美元cap/实付unknown。0工具/下载/模型重试/后端替换，不执行脚本，不选假说/指标/方法、不作机制裁决。每小步外层查新任务，有则优先，无则在明确输入/规则/额度内续单位/来源/重复台账；局部歧义不停止独立字段，无额度不虚称后台。历史18次加本次1累计cap19。
INPUT:
"""
prompt = (instruction + json.dumps(packet, ensure_ascii=False, separators=(",", ":"))).encode("utf-8")
assert len(prompt) <= 12000
TASK.mkdir(exist_ok=False)
(TASK / "workspace").mkdir()
(TASK / "source_packet.json").write_text(json.dumps(packet, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
(TASK / "prompt.txt").write_bytes(prompt)
job = {"task_id": "DS027", "task_version": "v1", "status": "assigned_ready_for_execution", "is_execution_authorization": True,
       "transport": "isolated_headless_stdin_no_tools", "objective": "Copy six prescribed source/mask/qualification rows and literal flags",
       "inputs": [{"path": str(TASK / "source_packet.json"), "sha256": hashlib.sha256((TASK / "source_packet.json").read_bytes()).hexdigest()}],
       "prompt_sha256": hashlib.sha256(prompt).hexdigest(),
       "budget": {"wall_seconds": 180, "max_output_tokens": 2048, "max_stdin_bytes": 12000, "model_calls": 1, "automatic_retries": 0,
                  "new_downloads": 0, "declared_cost_cap_usd": 0.025, "hard_dollar_cap_verified": False},
       "agent_permissions": "All tools disabled; isolated workspace and new DSH_HOME; fixed packet only; no scripts",
       "allowed_write_root": str(TASK), "deliverables": ["events.jsonl", "final.md", "usage.json", "receipt.json"],
       "acceptance_criteria": ["Exactly six assigned IDs and48 exact fixed fields", "Six quote_literal flags independently checked; quote length<=48", "No new classification, algorithm, assay or mechanism claim"],
       "stop_conditions": ["Uncertain result: no automatic retry or backend substitution"], "requires_main_agent_review": True,
       "mainline": "Mask/measurement units, predictions versus observations, structure/source-well/time/control/repeats; check formal new task after each small step"}
(TASK / "task.json").write_text(json.dumps(job, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
print(json.dumps({"task_id": "DS027", "stdin_bytes": len(prompt), "rows": len(rows), "prior_calls": 18, "cumulative_cap": 19}))
