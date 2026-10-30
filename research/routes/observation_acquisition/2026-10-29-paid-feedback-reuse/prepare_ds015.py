"""Create one source-only Harness packet; no response data or scientific choices."""
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "sources"
CODE = SOURCE / "drp_source_subset"
TASK = Path(r"D:\MAESTRO\research\deepseek\tasks\DS015")
assert not TASK.exists(), "New task only"


def excerpt(name, snippets):
    path = CODE / name
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    blocks = []
    for needle, before, after in snippets:
        line = next(i for i, text in enumerate(lines) if needle in text)
        start, stop = max(0, line-before), min(len(lines), line+after+1)
        blocks.append("\n".join(f"{i+1}: {lines[i]}" for i in range(start, stop)))
    return {"file": name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "blocks": blocks}


repo = json.loads((SOURCE / "drp_repo.json").read_text())
commit = json.loads((SOURCE / "drp_commit.json").read_text())
perf = "Results - predictive peroformance - drug panel and mRNA descriptors.py"
diff = "Results - MCF7 and MCF10A differential response prediction.py"
records = [
    {"id": "R_REPO", "locator": "GitHub API repository metadata, fixed commit and complete Git tree", "source": {
        "full_name": repo["full_name"], "default_branch": repo["default_branch"], "license": repo["license"],
        "commit": commit["sha"], "commit_date": commit["commit"]["committer"]["date"],
        "tree_contains_license_file": any(t["path"].lower().startswith('license') for t in json.loads((SOURCE/'drp_tree.json').read_text())["tree"]),
        "retrieved_source_files": [p.name for p in CODE.iterdir()], "excluded": "data CSVs and expression ZIP not downloaded; no package/environment snapshot"},
     "fields": ["commit", "commit_date", "license", "source_subset_scope"]},
    {"id": "R_SCALE", "locator": "README dataset descriptions", "source": excerpt("README.md", [("GDSC_1_2_non_redundant_drug_responses:", 0, 3)]),
     "fields": ["response_transform", "response_concentration_unit", "reference_profile_observed_or_predicted"]},
    {"id": "R_PERF", "locator": "predictive-performance script", "source": excerpt(perf, [("for drug in test_drugs[:5]", 1, 2), ("Xdtr =", 0, 4), ("rf=GradientBoostingRegressor", 0, 1)]),
     "fields": ["drug_loop_limit", "model_class", "n_estimators", "max_depth", "training_imputation", "validation_imputation"]},
    {"id": "R_DIFF", "locator": "differential-response script", "source": excerpt(diff, [("#Drug panel:", 0, 0), ("X.fillna(X.mean()", 1, 5), ("rf=GradientBoostingRegressor", 0, 1)]),
     "fields": ["reference_profile_observed_or_predicted", "model_class", "n_estimators", "max_depth", "imputation_before_test_drop"]},
    {"id": "R_EXPL", "locator": "explainability script", "source": excerpt("Results - explainability.py", [("rf=RandomForestRegressor", 0, 1), ("abs_idx=list", 0, 0)]),
     "fields": ["model_class", "n_estimators", "selected_gene_count", "role"]}
]
packet = {"task": "DS015", "source_version": commit["sha"], "records": records,
          "boundary": "Code/documentation only; source-file names/parameters are not actual model performance, efficacy, generality or mechanism evidence"}
prompt = ("任务：按每条fields清单逐字抽取本packet来源，保持原id、locator，未知写真正JSON null。只返回一个JSON对象{records:[{id,locator,fields:{字段:值},ambiguities:[]}]}。"
          "不得推断科学机制/价值、选择假设/方法/指标或心算。README的-log10(IC50)不能改写为LN_IC50，浓度单位原片段未写必须null。代码参数只归于指定脚本，不能替原论文所有实验定参数。"
          "区分预测与实测参考谱；缺失填补分别记录训练集均值、验证集自身均值和分割前全表均值。GitHub license=null且树无LICENSE不等于禁止阅读或已获复用许可，写unknown。"
          "局部歧义只列对应行，继续其余独立记录；五条全部返回。无工具/下载/脚本，输入只此packet，不读取其他workspace。\n"+
          json.dumps(packet, ensure_ascii=False))
raw = prompt.encode('utf-8')
assert len(raw) <= 12000, len(raw)
TASK.mkdir()
(TASK / "workspace").mkdir()
(TASK / "source_packet.json").write_text(json.dumps(packet, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
(TASK / "prompt.txt").write_bytes(raw)
job = {"task_id": "DS015", "task_version": "v1", "status": "assigned_ready_for_execution", "is_execution_authorization": True,
       "transport": "isolated_headless_stdin_no_tools", "objective": "固定官方DRP源码的版本/单位/参数/缺失处理及预测参考谱编目",
       "inputs": [{"path": str(TASK/'source_packet.json'), "sha256": hashlib.sha256((TASK/'source_packet.json').read_bytes()).hexdigest()}],
       "prompt_sha256": hashlib.sha256(raw).hexdigest(),
       "budget": {"wall_seconds": 180, "max_output_tokens": 2048, "max_stdin_bytes": 12000, "model_calls": 1,
                  "automatic_retries": 0, "new_downloads": 0, "declared_cost_cap_usd": .025},
       "agent_permissions": "all tools disabled; read-only isolated workspace; injected source snippets only",
       "allowed_write_root": str(TASK), "deliverables": ["receipt.json", "events.jsonl", "final.md", "usage.json"],
       "acceptance_criteria": ["five exact ids", "source-specific model parameters only", "unknown concentration unit not inferred", "observed/predicted and imputation scopes kept distinct", "no scientific judgment"],
       "stop_conditions": ["uncertain call no retry or backend change", "ambiguities reported while unaffected rows continue"],
       "requires_main_agent_review": True, "mainline": "common functional-data provenance/units/repeats and code-version ledger; check new tasks at packet boundary"}
(TASK / "task.json").write_text(json.dumps(job, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
print(json.dumps({"task_id": "DS015", "stdin_bytes": len(raw), "records": len(records)}))
