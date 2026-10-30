"""Freeze a response-free parameter projection and the specified Harness packet."""
from pathlib import Path
import ast
import hashlib
import json
import pandas as pd

ROOT = Path(__file__).resolve().parent
CODE = ROOT.parents[1] / "reference/code/yakavets-organoid-official/e38fc0ded24a"
if (ROOT / "metadata_inputs.json").exists():
    raise SystemExit("Frozen metadata inputs already exist; no overwrite.")

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

sources = []
tables = {}
scripts = []
for group, filename, stages in [
    ("FAC", "data_FAC_seq.csv", ["GS0-GS1", "GS2", "GS3"]),
    ("OLA-IBET", "data_OLA-IBET_seq.csv", ["GS0", "GS1-GS2"]),
]:
    path = CODE / group / "sequential/data" / filename
    with path.open(encoding="utf-8-sig") as stream:
        header = stream.readline().strip().split(",")
    allowed = ["seq", "t0", "t1", "gen", "number"]
    data = pd.read_csv(path, usecols=allowed)
    assert list(data.columns) == allowed and not data.isna().any().any()
    rows = json.loads(data.to_json(orient="records"))
    for line, row in enumerate(rows, 2):
        row["line"] = line
    tables[group] = {"source": str(path), "sha256": sha(path), "header_only": header,
                     "read_columns": allowed, "rows": rows}
    sources.append({"path": str(path), "sha256": sha(path)})
    for stage in stages:
        path = CODE / group / "sequential" / stage / "run_gryffin.py"
        code = path.read_text(encoding="utf-8")
        tree = ast.parse(code)
        config = next(ast.literal_eval(n.value) for n in tree.body
                      if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "CONFIG" for t in n.targets))
        convert = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "df_to_observations")
        time_lines = [{"line": i, "text": line.strip()} for i, line in enumerate(code.splitlines(), 1)
                      if "df_samples['t1']" in line or "d[col] = row[col]" in line]
        constraint = path.parent / "known_constraints.py"
        entry = {"group": group, "stage": stage, "source": str(path), "sha256": sha(path),
                 "parameters": config["parameters"], "conversion_function": ast.get_source_segment(code, convert),
                 "time_lines": time_lines}
        if constraint.exists():
            entry["constraint_source"] = str(constraint)
            entry["constraint_text"] = constraint.read_text(encoding="utf-8")
            sources.append({"path": str(constraint), "sha256": sha(constraint)})
        scripts.append(entry)
        sources.append({"path": str(path), "sha256": sha(path)})
for path in [ROOT / "metadata_protocol.md", ROOT / "sources/organoid_PMC12309667.xml"]:
    sources.append({"path": str(path), "sha256": sha(path)})
frozen = {"protocol": "Q001 v1", "date": "2026-10-28", "sources": sources,
          "tables": tables, "scripts": scripts, "functional_response_consumed": False}
save(ROOT / "metadata_inputs.json", frozen)
task = ROOT.parents[0] / "deepseek/tasks/DS011"
task.mkdir(exist_ok=False)
(task / "workspace").mkdir()
packet = {"scope": "metadata projection only; primary JATS selected anchors not whole paper",
          "tables": tables, "scripts": scripts,
          "primary_anchors": {"FAC": "JATS section[3]: total48h;GS0-2 4h step,GS3 2h step",
                              "PDO": "JATS section[4]: total96h;GS0 4h step,GS1-2 2h step;A OLA then IBET, B reverse",
                              "replication": "JATS:100 microwells per quadruplet,NOT per row;12 quadruplets=1200;CSV number not replicate ID"}}
save(task / "source_packet.json", packet)
prompt = """你是受限辅助Agent，只按固定规则核对参数，不选科学假设/方法/指标，不分析功能或机制。不联网、不运行工具。只读下列注入元数据，未见原文全篇或响应。每个原件用sha256绑定，line为CSV物理行号。输出一个紧凑JSON：tables每组row_count、gen_counts、sum_t0_t1_unique；pdo_swapped_pairs_same_gen列每个无序对的gen,line_i,line_j,number_i,number_j。固定公式：seq不同且同gen且t0_i=t1_j且t1_i=t0_j；每对一次。另pdo_swapped_pairs_cross_gen_count。FAC只计同gen不同seq且t0/t1完全相同的无序对数，不推导第三药时长或序列字典。按scripts所述low/high及constraint原坐标直代，列每个stage的违反行号；PDO GS0仅t0范围，later t0范围并thres<=t0<=48-thres；FAC两变量range及sum约束。不解释这种不符为错误数据。列units_or_mapping_unknown与exceptions。不得从96/48猜转换，不把number当生物重复，不将原坐标交换称实际暴露匹配。DS010曾把每quadruplet100微孔错写成每行100，已拒收；正确层级如source_packet所述。不做任何药效解释。不确定的列保留unknown并继续其他项。没有文件工具，所有写出由主Agent执行。\nSOURCE_PACKET:\n""" + json.dumps(packet, ensure_ascii=False, separators=(",", ":"))
encoded = prompt.encode("utf-8")
assert len(encoded) <= 18000
(task / "prompt.txt").write_bytes(encoded)
job = {"task_id": "DS011", "task_version": "v1", "status": "assigned_ready_for_execution",
       "is_execution_authorization": True, "transport": "isolated_headless_stdin_no_tools",
       "objective": "Q001固定元数据公式复算与单位歧义上报，不作科学裁决",
       "inputs": [{"path": str(task / "source_packet.json"), "sha256": sha(task / "source_packet.json")}],
       "prompt_sha256": hashlib.sha256(encoded).hexdigest(),
       "budget": {"wall_seconds": 180, "max_output_tokens": 2560, "max_stdin_bytes": 18000,
                  "model_calls": 1, "automatic_retries": 0, "new_downloads": 0},
       "agent_permissions": "all tools disabled; read-only isolated workspace; parent writes only task deliverables",
       "allowed_write_root": str(task),
       "deliverables": ["receipt.json", "events.jsonl", "final.md", "usage.json"],
       "acceptance_criteria": ["counts and all PDO pairs independently recomputed", "units not guessed", "no response or mechanism conclusions"],
       "stop_conditions": ["uncertain call no retry or backend change", "ambiguity reported while other fixed fields continue"],
       "requires_main_agent_review": True, "mainline": "fixed protocol/time-coordinate/exposure ledger; check tasks at packet boundary"}
save(task / "task.json", job)
print(json.dumps({"frozen_sources": len(sources), "stdin_bytes": len(encoded), "tables": {k: len(v["rows"]) for k,v in tables.items()}}))
