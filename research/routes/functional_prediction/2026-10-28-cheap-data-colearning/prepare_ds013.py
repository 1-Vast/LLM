"""Build a source-exact, tools-disabled field-audit packet; no outcome values."""
from pathlib import Path
import hashlib
import json

root = Path(r"D:\MAESTRO")
episode = Path(__file__).resolve().parent
task = root / "research/deepseek/tasks/DS013"
assert not (task / "task.json").exists() and not (task / "receipt.json").exists(), "Do not replace a previous task"
task.mkdir(exist_ok=True)
(task / "workspace").mkdir(exist_ok=True)
old = root / "data/external/prism_19q4/raw/primary-screen-readme.txt"
new = episode / "sources/public_prism/Repurposing_Public_24Q2_Readme.txt"
article = episode / "sources/public_prism/release24q2.json"

def snippet(path, start, end):
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "locator": f"lines {start}-{end}", "quote": "\n".join(lines[start-1:end])}

old_lines = old.read_text(encoding="utf-8-sig").splitlines()
new_lines = new.read_text(encoding="utf-8-sig").splitlines()

def paragraph(path, lines, beginning):
    i = next(i for i, line in enumerate(lines) if line.startswith(beginning))
    j = i + 1
    while j < len(lines) and lines[j].strip():
        j += 1
    return snippet(path, i + 1, j)

def one_line(path, lines, beginning):
    i = next(i for i, line in enumerate(lines) if line.startswith(beginning))
    return snippet(path, i + 1, i + 1)

records = [
    {"id": "P19_ENDPOINT", "fields": ["endpoint", "normalization", "replicate_collapse", "time_or_unknown"],
     "sources": [snippet(old, 3, 14)]},
    {"id": "P19_KEYS", "fields": ["drug_identifier_meaning", "dose_unit"],
     "sources": [one_line(old, old_lines, "broad_id -"), one_line(old, old_lines, "dose -")]},
    {"id": "P24_COUNT_CONFLICT", "fields": ["readme_count", "article_count", "conflict_no_resolution"],
     "sources": [paragraph(new, new_lines, "This data release"),
                 {"path": str(article), "sha256": hashlib.sha256(article.read_bytes()).hexdigest(),
                  "locator": "JSON description", "quote": json.loads(article.read_text(encoding="utf-8"))["description"]}]},
    {"id": "P24_REPLICATES", "fields": ["authors_replicate_description", "qc_filter", "not_local_count_verification"],
     "sources": [paragraph(new, new_lines, "The screen is executed"),
                 paragraph(new, new_lines, "    3. For each")]},
    {"id": "P24_MATRIX", "fields": ["endpoint", "collapse", "old_release_concatenation"],
     "sources": [paragraph(new, new_lines, "    6. Log2-fold"),
                 paragraph(new, new_lines, "    7. Finally"),
                 paragraph(new, new_lines, "The final LFC values")]},
    {"id": "P24_MAPPING", "fields": ["identifier_multiplicity", "dose_unit", "culture_or_pool_duplicates"],
     "sources": [one_line(new, new_lines, "* broad_id: Unique identifier for each compound. Please note"),
                 one_line(new, new_lines, "* dose: Dose of the treatment"),
                 one_line(new, new_lines, "* pool_id:"), one_line(new, new_lines, "* culture: The cell set for each cell line.")]},
]
source_packet = {"task_id": "DS013", "records": records}
packet_path = task / "source_packet.json"
packet_path.write_text(json.dumps(source_packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
instruction = """你是只读资料辅助员。只按以下原始来源片段编目，不选择科学假设/指标/算法，不裁决机制。
输入是主Agent按完整行/段摘录，保留原字符和小数。输出严格JSON数组，恰好6行，id及fields名称原样。
每行给values对象、原locator、ambiguities数组。缺少信息用真正JSON null，不用字符串null。
不要补造时间/独立培养/实际QC样本数。把作者说的biological replicates与本地已核事实区分。
P24_COUNT_CONFLICT保留两个版本的数量，不自行选一个。P24_MATRIX明确旧primary拼接，不能称全新独立数据。
不要心算，不重算计数，不读其他文件，不用工具；歧义记录后继续其他行。最终简洁无Markdown围栏。
"""
prompt = instruction + json.dumps(source_packet, ensure_ascii=False, separators=(",", ":"))
prompt_raw = prompt.encode("utf-8")
assert len(prompt_raw) <= 12000, len(prompt_raw)
(task / "prompt.txt").write_bytes(prompt_raw)
job = {
    "task_id": "DS013", "task_version": "v1", "status": "assigned_ready_for_execution",
    "is_execution_authorization": True, "transport": "isolated_headless_stdin_no_tools",
    "objective": "常见PRISM发布的字段、单位、重复层级和新旧拼接核对；不接触响应",
    "inputs": [{"path": str(packet_path), "sha256": hashlib.sha256(packet_path.read_bytes()).hexdigest()}],
    "prompt_sha256": hashlib.sha256(prompt_raw).hexdigest(),
    "budget": {"wall_seconds": 180, "max_output_tokens": 2048, "max_stdin_bytes": 12000,
               "model_calls": 1, "automatic_retries": 0, "new_downloads": 0, "declared_cost_cap_usd": 0.025},
    "agent_permissions": "all tools disabled; read-only isolated workspace; injected source snippets only",
    "allowed_write_root": str(task),
    "deliverables": ["receipt.json", "events.jsonl", "final.md", "usage.json"],
    "acceptance_criteria": ["exact six ids and original locators", "uM and log2 endpoint copied accurately",
                            "1514/1522 and REP300 234/242 conflict retained", "old-data concatenation retained",
                            "no fabricated time/culture/count verification", "valid JSON null and no mechanism conclusion"],
    "stop_conditions": ["uncertain call no retry or backend change", "ambiguity does not block independent records"],
    "requires_main_agent_review": True,
    "mainline": "common low-cost functional-data field ledger; next-task check at packet boundary",
}
(task / "task.json").write_text(json.dumps(job, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
coord = root / "research/deepseek"
(coord / "CURRENT_TASK.md").write_text("""# 当前辅助任务状态

2026-10-28：DS013 v1已建，尚待headless实际回执。累计调用预算4/5已用，DS013占最后1次；不新增调用额度。
当前用户主线改为便宜、易得功能数据。DS013只核6条新PRISM字段记录，0响应/0工具/0网络，独立workspace/DSH_HOME，180s/2048输出tokens/12000B stdin，成本声明上限$0.025，0重试/换后端。
来源、权限、输出与验收条件在tasks/DS013/task.json。root并行做科学问题和实验协议，返回后核JSON事件/final/usage及原文，不能以启动成功代替完成。
旧DS012部分采纳及上游小数点截断、DS011算术拒收、DS007/008缺回执均保留，不重跑。无工具模型不承担计算。
本次packet完成后检查正式新任务；没有新任务则按MAINLINE具体断点恢复获准字段编目。无新来源/无预算时保存断点并结束本次执行，不宣称后台常驻。
""", encoding="utf-8")
mainline = coord / "MAINLINE.md"
mainline.write_text("""# 当前主线：便宜、常见功能数据（2026-10-28）

用户已改方向。优先维护cell/drug/dose/time/functional endpoint及重复来源的固定字段台账，无须配齐遗传/组学。当前DS013待回执；本轮只剩其1次调用，完成后累计5/5，不自行扩预算。
具体小步：核DS013六条PRISM原文记录→保存数量冲突/拼接/单位/重复歧义→主Agent验收。新正式任务优先；否则只处理台账中获准来源的未完成字段。24Q2响应保留确认盲态，所有sealed/confirmation及.env禁止。没有新原件时保存断点；不得自行选新论文、假说、方法或指标。工具禁用的headless只能见packet，下一步须由外层调度，不虚称持续轮询。

以下为旧主线历史记录，保护边界继续有效，科学选题不据此倒退。

""" + mainline.read_text(encoding="utf-8"), encoding="utf-8")
print(json.dumps({"task_id": "DS013", "stdin_bytes": len(prompt_raw), "records": len(records)}))
