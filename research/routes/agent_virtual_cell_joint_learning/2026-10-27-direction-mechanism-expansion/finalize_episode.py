"""Save provenance and check artifact integrity; no scientific calculations."""
import hashlib
import json
import pathlib
import re
import subprocess
import sys
from datetime import datetime, timezone

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
LIB = ROOT / "reference"
TOOL = pathlib.Path(r"D:\CodexData\.codex\skills\lit-survey\scripts\reference_library.py")

usage = {
    "date": "2026-10-27", "scope": "direction and mechanism discovery, no effect experiments",
    "ancestral_queries_reported": 21,
    "ancestral_exact_query_gap": "4 queries in an earlier round lacked preserved original text; not reconstructed",
    "new_query_budget": 16, "new_queries_used": 14,
    "passes": {"P1_structural": 4, "P2_biological_priors": 4, "P3_mechanism": 2, "P4_independent_challenge": 4},
    "revision_limit_per_new_candidate": 2,
    "material_revisions": {"I-EX1": 2, "I-EX2": 1, "I-EX3": 1, "I-EX4": 2},
    "old_candidate_I_CD1_revisions": "2 already used; no reset",
    "agents": [
        {"handle": "/root/expansion_structural_mechanisms", "role": "independent early structural scout and proposer", "requested_model": "gpt-6.1-sol", "requested_effort": "high"},
        {"handle": "/root/expansion_latest_evidence", "role": "current raw-record audit", "requested_model": "gpt-6.1-sol", "requested_effort": "medium"},
        {"handle": "/root/expansion_mechanism_challenge", "role": "fresh-context frozen-candidate challenge and v2 check", "requested_model": "gpt-6-astra", "requested_effort": "high"},
        {"handle": "/root/expansion_final_logic_check", "role": "bounded final v3 logic check after runtime agent disappearance", "requested_model": "gpt-6-astra", "requested_effort": "high"},
    ],
    "scientific_experiments": 0, "training_runs": 0, "simulations": 0,
    "datasets_downloaded": 0, "weights_downloaded": 0, "installs": 0,
    "production_code_edits": 0, "scientific_code_promotions": 0,
    "primary_jats_saved": 6, "new_library_papers": 7, "new_library_main_html": 6,
    "new_official_code_snapshots": 1,
    "known_identifier_metadata_and_primary_retrievals": "receipts in primary; not counted as new thematic queries",
    "native_web": "Added mid-run; opened known sources and searched within their text only, no new thematic query",
    "final_logic_check_present": (HERE / "final_logic_check.md").is_file(),
}
for item in usage["agents"]:
    item.update(effective_model="unknown", effective_effort="unknown", fresh_context=True)
(HERE / "usage.json").write_text(json.dumps(usage, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

readme = """# 本轮定向来源检索

这是方向/机制探索的来源缓存，不是完整领域综述。报告在[../report.md](../report.md)，原文读取与访问边界在[../evidence_notes.md](../evidence_notes.md)。

窗口2025-01-01—2026-10-27；更早直接新意威胁另外保留。P2四条/P3两条原样查询在00_index/searched_queries.tsv；P1四条在../sources/P1_structural/；P4四条在p4_challenge/。合计14/16条新主题查询。两个宽arXiv查询噪声高、未翻完；P1和P4部分只取首页，不声称穷尽。未启动OpenAlex/OpenReview完整流程。

共享资料库为D:/MAESTRO/reference/，不在此建副本。初始化产生的三份空analysis/field_survey/novelty模板已删除；所有真实原始响应、query日志保留。最终统计见../library_verify_final.json。
"""
(HERE / "search" / "README.md").write_text(readme, encoding="utf-8")
(HERE / "search" / "PROCESS.md").write_text("# 来源工作过程\n\n研究范围和预算见../BRIEF.md；实际查询、原文、限制和故障见../evidence_notes.md、../source_challenge.md及原始receipts。这里只使用init_survey的存储与查询日志，不声称完成它的完整survey流程。\n", encoding="utf-8")

verify = subprocess.run([sys.executable, str(TOOL), "verify", str(LIB), "--json"], capture_output=True, text=True, encoding="utf-8", check=True)
stats = json.loads(verify.stdout)
(HERE / "library_verify_final.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

inputs = [
    ROOT / "research/2026-10-27-c130-audit/r196_v2.json",
    ROOT / "research/2026-10-27-q-structure/r197_v2.json",
    ROOT / "research/2026-10-27-innovation-scouting/conflict_signal/stage0/real_run/relations_check.json",
    ROOT / "research/2026-10-27-core-module-design/qualification/q0.json",
    LIB / "papers.tsv", LIB / "repositories.tsv",
]
tracked = inputs + list(HERE.glob("*.md")) + list((HERE / "primary").rglob("*.xml"))
snapshot = {"recorded_utc": datetime.now(timezone.utc).isoformat(), "purpose": "current bytes/provenance, not scientific validation", "files": []}
for path in sorted(set(tracked)):
    data = path.read_bytes()
    snapshot["files"].append({"path": str(path.relative_to(ROOT)).replace("\\", "/"), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
expected = {
    "r196_v2.json": "bd0ada7be102df430209422995609c1411cbcb6a231f763e6f96121cb4b952a4",
    "r197_v2.json": "b0dbe7982677fe9269b47ea39c83659166d4e4a5bff04e8f590fc04ba64435cb",
    "relations_check.json": "9ae302b8749cd992d3201e00e322c683486d6b4c1bffc03163da967ba1026552",
    "q0.json": "f952ccf3418cdd994d58412de56e8ea3c3af23c0e48a9c45147e7edc91da786b",
}
for path in inputs[:4]:
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected[path.name], path
(HERE / "source_snapshot.json").write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

broken = []
for filename in ("report.md", "mechanisms_v3.md", "record.md", "evidence_notes.md"):
    path = HERE / filename
    for target in re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
        if not re.match(r"https?://|#", target) and not (HERE / target.split("#")[0]).exists():
            broken.append({"file": filename, "target": target})
for path in HERE.rglob("*.json"):
    json.loads(path.read_text(encoding="utf-8-sig"))
assert not broken, broken
summary = {"library": stats, "broken_local_links": broken, "all_episode_json_parse": True, "four_frozen_result_hashes_unchanged": True, "science_validated": False}
(HERE / "artifact_check.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"unique_papers": stats["papers"]["unique"], "main_files": stats["papers"]["files"], "official_code": stats["papers_with_official_code_stored"], "errors": stats["errors"], "warnings": stats["warnings"], "broken_links": broken, "final_logic_check_present": usage["final_logic_check_present"]}, ensure_ascii=False))
