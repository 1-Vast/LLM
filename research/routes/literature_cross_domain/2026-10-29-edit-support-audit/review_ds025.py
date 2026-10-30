"""Verify only fixed transcription against the re-read original glossary."""
from pathlib import Path
import json

from pypdf import PdfReader

HERE = Path(__file__).resolve().parent
TASK = HERE.parent / "deepseek/tasks/DS025"
packet = json.loads((TASK / "source_packet.json").read_text(encoding="utf-8"))
actual = json.loads((TASK / "final.md").read_text(encoding="utf-8"))
original = PdfReader(packet["source"]).pages[0].extract_text()
assert packet["original_text"] == original
assert isinstance(actual, list) and len(actual) == 9
checks, annotations = [], []
fields = ("id", "field", "kind", "canonical_unit", "source_quote", "boundary")
for expected, row in zip(packet["rows"], actual):
    checks.append({"id": expected["id"], "fixed_fields_equal": all(row[k] == expected[k] for k in fields),
                   "literal_original_quote": row["source_quote"] in original,
                   "quote_length": len(row["source_quote"]), "no_unassigned_fields": set(row) == set(fields) | {"ambiguity"}})
    if row["ambiguity"] is not None:
        annotations.append({"id": row["id"], "model_annotation": row["ambiguity"],
                            "adopted_as_measurement_ambiguity": False})
assert all(r["fixed_fields_equal"] and r["literal_original_quote"] and r["quote_length"] <= 48 and r["no_unassigned_fields"] for r in checks)
receipt = json.loads((TASK / "receipt.json").read_text(encoding="utf-8"))
usage = json.loads((TASK / "usage.json").read_text(encoding="utf-8"))
result = {"accepted_scope": "Nine fixed field/unit/quote/boundary transcriptions only",
          "fixed_field_checks": 54, "all_fixed_fields_equal": True, "checks": checks,
          "model_annotations_not_adopted": annotations, "real_harness_final_events": receipt["final_events"],
          "model_execution_seconds": usage["seconds"], "scientific_validation": False,
          "raw_outcomes_or_chemical_support_independently_validated": False,
          "prior_harness_calls": 16, "new_calls": 1, "cumulative_calls": 17, "cumulative_cap": 17}
(TASK / "format_checks.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(TASK / "main_review.md").write_text("""# DS025逐原文限定验收

2026-10-29。真实本机隔离headless一次，4.531s、exit0、1final/1step_end，stdin6049B；1838input/612output/256cache-read，reported total2706。累计17/17封账；实际后端型号、底层API请求数、实付未知。工具全部禁用，隔离workspace/DSH_HOME，0重试/后端替换，进程已退出。此前packet预检F5 quote49字超48，发生在task目录创建与模型调用前；改成原文连续48字，非模型重试。

root重新读取原PDF第一页，逐条核九个ID、54个固定字段、九段连续原文字面quote及长度。固定抄录全部一致。boundary全部由主Agent事前给定，不能称辅助模型发现或独立证明。六条非空ambiguity是模型对短quote或成对字段的附加说明，原输出保留；不把它们升级为数据矛盾或新增测量条件。尤其F8完整原文明确max9，F4完整原文明确monotherapy curve-fitting目的；F5不据“未描述stock/dilution”否定原文给定µM单位或猜测实际配液。

只采纳固定字段/单位/来源台账。不是化学支持、独立培养、原始well身份、药效或共学机制验证。每个小步后已检查正式任务，当前最高DS025且本轮无剩余额度；无新可执行packet时保存断点，不虚称后台轮询。默认下一步是结构ID来源联结后再核单药参照源well、time/control/repeats；DS007/008及DS024负结果原位保留、不重跑。
""", encoding="utf-8")
print(json.dumps({"rows": 9, "fixed_fields": 54, "equal": True, "annotations_not_adopted": len(annotations), "scientific_validation": False}))
