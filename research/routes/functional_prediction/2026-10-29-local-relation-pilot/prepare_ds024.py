"""Assign only frozen decision-loss arithmetic on the first16 task entries."""
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
TASK = HERE.parent / "deepseek/tasks/DS024"
TASK.mkdir(exist_ok=False)
(TASK / "workspace").mkdir()
source = HERE / "arithmetic_packet.json"
items = json.loads(source.read_text(encoding="utf-8"))["items"]
rows = [{"id": r["id"], "active_indices": [i for i, value in enumerate(r["actual_active_flags"]) if value],
         "normalized_log_doses": r["normalized_log_doses"], "A": r["choice_A"], "L": r["choice_L"]} for r in items]
packet = {"source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
          "selection": "First16 frozen task-order entries, never selected by responses or outcomes",
          "rows": rows,
          "fixed_formula": "first=min(active_indices) or -1 when empty. loss(j)=int(first>=0) if j==-1; else 1 if j not in active_indices; else normalized_log_doses[j]-normalized_log_doses[first]. delta=loss_A-loss_L."}
(TASK / "source_packet.json").write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
instruction = """你是工具禁用的固定算术辅助。仅按INPUT给出的固定公式逐行计算，不选择假设、指标、方法或生物裁决。不解释算法优劣，不搜索或读取外部文件。输出且仅输出JSON对象，字段rows,totals。rows依输入顺序16项，每项仅id,first_active,loss_A,loss_L,delta；first_active用整数，loss和delta算到小数6位（最终一次四舍五入，不先舍入坐标）。totals仅rows,sum_loss_A,sum_loss_L,sum_delta，用未舍入单项加和后最终6位。空active_indices且弃权损失0，活性不存在但推荐任何点损失1；已活性推荐按给定normalized_log_doses差。遇歧义在该行增ambiguity并继续其他行，不能自改公式。没有quote字段。
一次隔离headless，180s/2048输出tokens/12000B stdin，声明USD.025、硬美元cap及实付未知；0工具/下载/重试/后端替换。旧15+本轮1累计上限16。每小步后由外层查新task，有则优先，无则在有packet/预算时恢复support关联、导出vs拟合、time/控制/重复和source键；无额度保存断点不虚称后台。
INPUT:
"""
prompt = (instruction + json.dumps(packet, ensure_ascii=False, separators=(",", ":"))).encode("utf-8")
assert len(prompt) <= 12000
(TASK / "prompt.txt").write_bytes(prompt)
task = {"task_id": "DS024", "task_version": "v1", "status": "assigned_ready_for_execution", "is_execution_authorization": True,
        "transport": "isolated_headless_stdin_no_tools", "objective": "Recompute prescribed minimum-tested-dose decision loss on fixed16 injected entries, no interpretation",
        "inputs": [{"path": str(TASK / "source_packet.json"), "sha256": hashlib.sha256((TASK / "source_packet.json").read_bytes()).hexdigest()}],
        "prompt_sha256": hashlib.sha256(prompt).hexdigest(),
        "budget": {"wall_seconds": 180, "max_output_tokens": 2048, "max_stdin_bytes": 12000, "model_calls": 1,
                   "automatic_retries": 0, "new_downloads": 0, "declared_cost_cap_usd": 0.025, "hard_dollar_cap_verified": False},
        "agent_permissions": "All tools disabled; injected fixed packet only; read-only isolated workspace; new isolated DSH_HOME prepared by runner",
        "allowed_write_root": str(TASK), "deliverables": ["events.jsonl", "final.md", "usage.json", "receipt.json"],
        "acceptance_criteria": ["Exact16 IDs and fixed output fields", "Prescribed first-active and loss/delta match independent coordinator decimal arithmetic within1e-6", "Four fixed totals agree within1e-6", "No scientific judgement"],
        "stop_conditions": ["Uncertain result: no automatic retry or backend substitution"], "requires_main_agent_review": True,
        "mainline": "support joins, exported versus fitted response, time/control/replicate/source units; check new task after each small step"}
(TASK / "task.json").write_text(json.dumps(task, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"task_id": "DS024", "stdin_bytes": len(prompt), "rows": len(rows), "prior_calls": 15, "cumulative_cap": 16}))
