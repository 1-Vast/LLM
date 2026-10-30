"""One bounded bookkeeping closure; no experiment, retrieval, API, deletion or publication."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DS = ROOT / "research/deepseek"


def read(relative):
    return json.loads((HERE / relative).read_text(encoding="utf-8"))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


assert not (HERE / "budget_usage.json").exists(), "closure already written: inspect before updating"
assert (HERE / "scientific_content_review.md").is_file()
main = read("q1_run/receipt.json")
ind = read("independent_q1/resource_receipt.json")
execution = read("independent_q1/execution_receipt.json")
freeze = read("preexecution_q1_freeze.json")
assert all(sha(HERE / name) == value for name, value in freeze["files"].items())
assert sha(HERE / "e_q1.py") == read("code_freeze_q1.json")["code_sha256"] == main["code_sha256"]
assert all(execution["frozen_hash_checks"].values()) and execution["independent_numerical_executions"] == 1
retrieval = [json.loads(line) for line in (HERE / "retrieval.jsonl").read_text(encoding="utf-8").splitlines()]
assert len(retrieval) <= 8 and sum(row["query"] for row in retrieval) <= 2
assert sum(row["bytes"] for row in retrieval) <= 20_000_000
for row in retrieval:
    assert sha(HERE / "sources" / row["name"]) == row["sha256"]
usage = json.loads((DS / "tasks/DS019/usage.json").read_text(encoding="utf-8"))

new_evidence = "> **2026-10-29 普通常见支持与Q1输出粗细计算：**[本轮报告](2026-10-29-common-assay-support/report.md)比较支持/剂量窗/化合物发现/处理史，核2026 CV缺模态、连续输出多峰MI-LB和LUDRP原文。唯一合成H主/独立均支持，B218叶、MI=.028474689392；最大核心差4.44e-16、B/B'432计算叶及214实际拆分一致，只证计算。主A先guard偏离冻结初始4叶顺序，独立按序仍支持H；原证据保留、不重跑。merged原分数与固定tau BALD也正确选B，因此停止Q1主创新推荐，无额外决策/药物/共同学习证据、0核心晋升。LUDRP既有60选测＋历史合并微调，MSE属训练折标准化log IC50尺度，不能重复认领骨架。普通免费功能优先，不把组学/救援作通用前提；累计17pass/11Harness封账，目标ACTIVE / NOT_ACHIEVED。\n\n"
path = ROOT / "research/EVIDENCE_REGISTER.md"
old = path.read_text(encoding="utf-8-sig")
assert not old.startswith(new_evidence)
path.write_text(new_evidence + old, encoding="utf-8")

ds_status = "# DS019 已完成并限定验收（2026-10-29）\n\n真实headless8.672s、1final/1step_end、stdin9364B、2566input/1423output/256cache-read；历史10+1=11/11封账。root拒收181/122字符quote、label regime误作evaluation_set及预算数字缺失的矛盾，原始输出/错误及canonical更正见[tasks/DS019/main_review.md](tasks/DS019/main_review.md)。effective型号/底层API请求数/实付unknown；0重试/换后端，无活进程。\n\n当前具体默认断点：普通功能support与响应join、原始剂量点vs拟合摘要、处理时间/控制/重复层级。每小步先检查正式新任务，有则优先；无则从有明确输入/规则/额度的断点继续，歧义记下后处理独立字段。本轮无新packet/调用额度，不虚称后台轮询；DS007/008旧断点保留，不自动重跑。以下均为历史状态。\n\n"
for name in ("CURRENT_TASK.md", "MAINLINE.md"):
    path = DS / name
    old = path.read_text(encoding="utf-8-sig")
    path.write_text(ds_status + old, encoding="utf-8")
path = DS / "TASK_QUEUE.md"
path.write_text("**2026-10-29当前状态：**DS019已真实完成并root限定验收，累计11/11封账；见[当前任务](CURRENT_TASK.md)。无新packet/额度，不自动重跑DS007/008；下表及其“当前正式任务”用词均为历史记录，不是新的执行授权。\n\n" + path.read_text(encoding="utf-8-sig"), encoding="utf-8")

with (HERE / "record.md").open("a", encoding="utf-8") as handle:
    handle.write("\n## pass2–3执行与本轮收口\n\nQ1.v1初判后仅修订v1.1一次，再冻结代码/协议；唯一主合成执行和fresh独立重写各一次，H1–3局部支持。root主A先guard违反v1.1先四叶顺序，独立按协议仍支持；不改冻结文件/不重跑。B/B'的432计算叶、218最终区间与214实际拆分一致，最大标量差4.44e-16；末行potential selection与实际拆分区分。merged源分数和固定阈值也选B，无新算法必要性或药物价值证据，停止Q1主推荐，不扫参。\n\n三个原件入共享库，105来源/92文件，verify空errors/warnings；阅读P级、JATS原主文generic槽非SI、新源码未取。DS019真实8.672s/1final，2566input/1423output/cache256，拒收两长quote与两个字段错误，累计11封账。一次比较探查KeyError及一次共享入口patch匹配失败均属工程编辑/读取失败，未额外数值运行；修正后只比较已存结果/维护入口。\n\n独立科学/内容审查见scientific_content_review.md，最终判断与范围见report。按organize-files综合及更新入口，无删除/搬移/提交。Terra前阶段401、本轮0重试/替代冒称，指定整理要求仍未实现。预算3/3、累计17/17，无功能响应读取、0核心晋升；整体目标ACTIVE / NOT_ACHIEVED。\n")

team = {"requested_model": "gpt-6.1-sol", "requested_effort": "high", "effective_model": None,
        "roles": [{"handle": "/root/assay_archive_neutral_scout", "role": "archive/alternative-question exploration", "candidate_blind_initially": True, "cannot_challenge_own_design": True},
                  {"handle": "/root/q1_independent_protocol", "role": "fresh protocol/primary-source challenge", "initial_assessment_saved": True},
                  {"handle": "/root/q1_independent_numeric", "role": "fresh independent one-shot rewrite", "root_code_or_numbers_read": False},
                  {"handle": "/root/q1_scientific_content", "role": "fresh scientific/content review", "initial_assessment_saved": True}],
        "root": "scientific choice, implementation, source verification and synthesis; not independent of own work",
        "Terra": {"requested": "6.1 Terra", "fulfilled": False, "prior_attempt": "401; research/2026-10-29-paid-feedback-reuse/budget_usage.json", "this_round_retries": 0},
        "DeepSeek": {"task": "DS019", "role": "fixed source-field bookkeeping only", "usage": usage, "main_review": "../deepseek/tasks/DS019/main_review.md"}}
write(HERE / "team_record.json", team)
budget = {"episode": HERE.name, "overall_goal": "ACTIVE / NOT_ACHIEVED",
          "status": "round_closed_local_H_supported_main_innovation_not_supported", "core_promotions": 0,
          "passes": {"prior_used": 14, "new_allowed": 3, "new_used": 3, "cumulative_used": 17, "cumulative_cap": 17,
                     "substantive_candidate_revisions": 1, "revision_cap": 2},
          "public_retrieval": {"actions_used": len(retrieval), "actions_cap": 8, "theme_queries_used": sum(row["query"] for row in retrieval),
                               "theme_queries_cap": 2, "saved_bytes": sum(row["bytes"] for row in retrieval), "byte_cap": 20000000,
                               "per_item_cap": 8000000, "timeout_seconds": 30, "automatic_retries": 0},
          "experiments": {"synthetic_main_runs": 1, "independent_rewrites_and_runs": 1, "additional_hypotheses_or_tuning": 0,
                          "real_functional_response_reads": 0, "dataset_downloads": 0, "GPU": 0, "installations": 0, "wet_experiments": 0,
                          "limit_each": {"cpu_seconds": 120, "memory_bytes": 1073741824, "output_bytes": 50000000},
                          "main_receipt": main, "independent_resource_receipt": ind,
                          "main_output_bytes_at_closure": sum(p.stat().st_size for p in (HERE / "q1_run").rglob("*") if p.is_file()),
                          "independent_directory_bytes_at_closure": sum(p.stat().st_size for p in (HERE / "independent_q1").rglob("*") if p.is_file()),
                          "root_execution_deviation": "A equality guard skips four initial leaves required by v1.1; independent run followed order; frozen evidence retained; no rerun"},
          "harness": {"prior_used": 10, "new_allowed": 1, "new_used": 1, "cumulative_used": 11, "cumulative_cap": 11,
                      "task": "DS019", "max_wall_seconds": 180, "max_output_tokens": 2048, "max_stdin_bytes": 12000,
                      "declared_cost_cap_usd": .025, "hard_dollar_cap_verified": False, "paid_cost_usd": None,
                      "automatic_retries": 0, "backend_substitutions": 0, "usage": usage},
          "organization": {"skill": "organize-files", "Terra_requested_but_unfulfilled": True, "Terra_this_round_calls": 0,
                           "actual": "root synthesis plus fresh independent scientific/content review", "deleted_or_moved_files": 0,
                           "scope_metrics": "closure_verification.json; final-synthesis maintenance only"},
          "library": read("library_verify_final.json"),
          "evidence_hashes": {name: sha(HERE / name) for name in ("report.md", "scientific_content_review.md", "preexecution_q1_freeze.json", "code_freeze_q1.json", "independent_comparison.json")}}
write(HERE / "budget_usage.json", budget)
before = read("organization_scope_before.json")
after = {name: {"exists": (ROOT / name).exists(), "bytes": (ROOT / name).stat().st_size if (ROOT / name).exists() else 0,
                "sha256": sha(ROOT / name) if (ROOT / name).is_file() else None} for name in before["files"]}
write(HERE / "closure_verification.json", {"created_utc": datetime.now(timezone.utc).isoformat(), "scope": before["scope"],
     "before": {key: before[key] for key in ("file_count", "directory_count", "bytes")},
     "after": {"file_count": sum(x["exists"] for x in after.values()), "directory_count": before["directory_count"], "bytes": sum(x["bytes"] for x in after.values())},
     "files": after, "frozen_protocol_code_source_hashes_unchanged": True,
     "scientific_scope": "local H only; simple methods suffice; no main-innovation recommendation or goal completion"})
print(json.dumps({"status": budget["status"], "passes": 17, "harness": 11,
                  "report_sha256": sha(HERE / "report.md"), "budget_sha256": sha(HERE / "budget_usage.json")}, ensure_ascii=False))
