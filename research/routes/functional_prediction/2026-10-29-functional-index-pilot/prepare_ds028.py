"""Prescribed OOF arithmetic and stage ledger; no hypothesis decisions."""
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
TASK = HERE.parent / "deepseek/tasks/DS028"
summary = json.loads((HERE / "primary_summary.json").read_text(encoding="utf-8"))
selection = json.loads((HERE / "primary_training_selection.json").read_text(encoding="utf-8"))
assert summary["status"] == "training_precondition_absent"
n = 2 * selection["training_cells"]
errors = summary["best_training_candidate"][0]["errors"]
rows = []
for name, numerator in list(errors.items()) + [("min_direct_gain", min(errors["direct_a"], errors["direct_b"]) - errors["reference"])]:
    ratio = (Decimal(numerator) / Decimal(n)).quantize(Decimal(".000001"), rounding=ROUND_HALF_EVEN)
    rows.append({"id": name, "numerator": numerator, "denominator": n, "ratio6": str(ratio),
                 "unit": "OOF_label_loss" if name != "min_direct_gain" else "OOF_loss_reduction",
                 "stage": "training_only", "qualification": "not_development_or_biological_effect"})
packet = {"rows": rows, "calculation": "ratio6=ROUND_HALF_EVEN(numerator/denominator,6 decimals); denominator=2*529=1058",
          "ratio_source": "Canonical ratios independently calculated by coordinator Decimal; assistant transcribes and flags fixed-formula disagreement only",
          "run_status": summary["status"], "H_status": summary["H_FI"],
          "source_sha256": {n: hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ["primary_summary.json", "primary_training_selection.json"]}}
instruction = """你是禁用工具的标准台账辅助。按INPUT五行逐字复制id,numerator,denominator,ratio6,unit,stage,qualification七字段，只输出JSON对象{rows:[五行],run_status:原值,H_status:原值,ambiguities:[]}。ratio6为主研究者按固定公式计算的canonical字符串，不自行更换科学指标、分母、单位或主张；若发现明确固定公式冲突仅写ambiguities，仍复制原值并继续其余行。所有数值只来自训练OOF，不能写成开发效应、真实药效/省孔或新算法通过。负margin不能改符号；truncated? 不补造缺字段。
一次新隔离headless，180s/2048输出tokens/12000B stdin，声明USD.025且硬美元cap/实付unknown。0工具/脚本/下载/重试/换后端，不选假说/方法/指标或裁决机制。历史19+本次1累计cap20。每小步外层查正式新任务，有则优先，无则在明确输入/规则/预算内续字段/单位/source-well/time/control/repeats台账，局部歧义不停止独立字段，无额度不虚称后台。
INPUT:
"""
prompt = (instruction + json.dumps(packet, ensure_ascii=False, separators=(",", ":"))).encode("utf-8")
assert len(prompt) <= 12000
TASK.mkdir(exist_ok=False)
(TASK / "workspace").mkdir()
(TASK / "source_packet.json").write_text(json.dumps(packet, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
(TASK / "prompt.txt").write_bytes(prompt)
job = {"task_id": "DS028", "task_version": "v1", "status": "assigned_ready_for_execution", "is_execution_authorization": True,
       "transport": "isolated_headless_stdin_no_tools", "objective": "Transcribe five fixed OOF arithmetic/unit rows and two predefined stage-status fields",
       "inputs": [{"path": str(TASK / "source_packet.json"), "sha256": hashlib.sha256((TASK / "source_packet.json").read_bytes()).hexdigest()}],
       "prompt_sha256": hashlib.sha256(prompt).hexdigest(),
       "budget": {"wall_seconds": 180, "max_output_tokens": 2048, "max_stdin_bytes": 12000, "model_calls": 1,
                  "automatic_retries": 0, "new_downloads": 0, "declared_cost_cap_usd": 0.025, "hard_dollar_cap_verified": False},
       "agent_permissions": "All tools disabled; fixed packet only; isolated workspace/new DSH_HOME; no scripts",
       "allowed_write_root": str(TASK), "deliverables": ["events.jsonl", "final.md", "usage.json", "receipt.json"],
       "acceptance_criteria": ["Five exact IDs and35 fixed fields; statuses copied exactly", "Canonical ratios independently checked against fixed Decimal formula", "Training-only scope and sign preserved, no scientific verdict"],
       "stop_conditions": ["Uncertain result: no automatic retry/backend substitution"], "requires_main_agent_review": True,
       "mainline": "Fixed stage/unit/source ledgers, predictions versus observations, source-well/time/control/repeats; check formal new task after each step"}
(TASK / "task.json").write_text(json.dumps(job, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
print(json.dumps({"task_id": "DS028", "stdin_bytes": len(prompt), "rows": 5, "history_calls": 19, "cumulative_cap": 20}))
