"""Create a bounded fixed-formula deduplication packet, without scientific choices."""
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
TASK = HERE.parent / "deepseek/tasks/DS023"
TASK.mkdir(exist_ok=False)
(TASK / "workspace").mkdir()
rows = json.loads((HERE / "dq1_arithmetic_packet.json").read_text(encoding="utf-8"))
packet = {"selection": "First16 lexicographic exported keys from frozenDQ1, not response-selected",
          "source_packet_sha256": hashlib.sha256((HERE / "dq1_arithmetic_packet.json").read_bytes()).hexdigest(),
          "rows": rows,
          "rules": {"numeric_unique": "Count distinct exact decimal numeric values in distinct_raw_y_strings, no rounding",
                    "consistent": "numeric_unique==1 and invalid_y_count==0",
                    "exported_units": "1 when consistent else0; this is an exported-reference accounting unit, not an independent well/culture",
                    "duplicate_appearances": "appearance_count-1 when consistent else null"}}
(TASK / "source_packet.json").write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
instruction = """你是重复性去重/算术辅助，工具禁用。只用INPUT已给四个公式复算，不能选择假设、指标、方法或裁决机制。输出且仅输出JSON对象，字段rows和totals。rows必须按输入16项原顺序，每项字段固定id,numeric_unique,consistent,exported_units,duplicate_appearances；exact decimal相等不舍入，缺/非数按invalid_y_count规则。totals字段固定keys,sum_exported_units,sum_duplicate_appearances,sum_input_appearances，逐行加总，不能推广整个数据集。无quote字段，不需说明文字。出现歧义在该行加ambiguity字符串并继续其余行；禁止自改规则、估计独立生物样本数或判断科学成立。
一次headless，180s、2048输出tokens、12000B stdin，声明USD.025但硬美元cap/实付未知；0工具/下载/自动重试/换后端。历史14保留，本轮1次累计上限15。每行是一个小步；完成由外层检查新正式任务，有则优先，无则回到有packet/预算的support关联、导出响应vs拟合、time/控制/重复及单药来源键默认断点；无packet/额度保存断点，不虚称后台。
INPUT:
"""
prompt = (instruction + json.dumps(packet, ensure_ascii=False, separators=(",", ":"))).encode("utf-8")
assert len(prompt) <= 12000
(TASK / "prompt.txt").write_bytes(prompt)
job = {"task_id": "DS023", "task_version": "v1", "status": "assigned_ready_for_execution",
       "is_execution_authorization": True, "transport": "isolated_headless_stdin_no_tools",
       "objective": "Fixed16-key exact-decimal uniqueness and prescribed exported-unit arithmetic, no scientific interpretation",
       "inputs": [{"path": str(TASK / "source_packet.json"), "sha256": hashlib.sha256((TASK / "source_packet.json").read_bytes()).hexdigest()}],
       "prompt_sha256": hashlib.sha256(prompt).hexdigest(),
       "budget": {"wall_seconds": 180, "max_output_tokens": 2048, "max_stdin_bytes": 12000, "model_calls": 1,
                  "automatic_retries": 0, "new_downloads": 0, "declared_cost_cap_usd": 0.025, "hard_dollar_cap_verified": False},
       "agent_permissions": "all tools disabled; injected fixed packet only; read-only isolated workspace",
       "allowed_write_root": str(TASK), "deliverables": ["events.jsonl", "final.md", "usage.json", "receipt.json"],
       "acceptance_criteria": ["16 exact IDs in order", "exact decimal uniqueness matches original packet", "four prescribed totals match independent coordinator arithmetic", "no biological/scientific inference"],
       "stop_conditions": ["Uncertain outcome: no automatic retry or backend replacement"], "requires_main_agent_review": True,
       "mainline": "support joins, exported versus fitted responses, time/control/replicate/source units; check new task each small step"}
(TASK / "task.json").write_text(json.dumps(job, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"task_id": "DS023", "stdin_bytes": len(prompt), "rows": len(rows)}))
