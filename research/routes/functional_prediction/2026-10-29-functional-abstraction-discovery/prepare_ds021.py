"""Prepare an isolated fixed identity-bookkeeping packet, without model or scientific choices."""
from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
TASK = HERE.parent / "deepseek/tasks/DS021"
TASK.mkdir(exist_ok=False)
(TASK / "workspace").mkdir()
source = HERE / "sources/p3_domain_records.xml"
articles = ET.parse(source).getroot().findall("PubmedArticle")
wanted = {"42546632", "42780682", "42682083", "42622748", "42481604", "42429061", "42238271", "42086551"}
packet = []
for article in articles:
    pmid = article.findtext("MedlineCitation/PMID")
    if pmid not in wanted:
        continue
    packet.append({"record_pmid": pmid, "title": "".join(article.find("MedlineCitation/Article/ArticleTitle").itertext()),
                   "primary_article_id_list": [{"IdType": x.get("IdType"), "value": x.text}
                                               for x in article.findall("PubmedData/ArticleIdList/ArticleId")],
                   "nested_reference_ids_not_current_article": [{"IdType": x.get("IdType"), "value": x.text}
                                                               for x in article.findall("PubmedData/ReferenceList//ArticleId")][:4],
                   "source_locator": f"PubmedArticle[MedlineCitation/PMID={pmid}]/PubmedData/ArticleIdList",
                   "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest()})
assert len(packet) == 8
(TASK / "source_packet.json").write_bytes((json.dumps(packet, ensure_ascii=False, indent=2) + "\n").encode())
instruction = """你是来源身份/字段编目辅助，工具全部禁用。仅从primary_article_id_list逐条抄出当前论文doi/pmc/pubmed，不使用nested_reference_ids_not_current_article里的被引用文献ID，不凭题名猜ID。输出8行JSON数组，字段固定record_pmid,current_pubmed,doi,pmc,source_locator,quote,ambiguity。字段未明示=null。quote从title取连续短片段，最多80Unicode字符，不得复述改写。primary pubmed与record_pmid不一致时记录ambiguity，继续其他行；不自行纠正或换源。不得选择论文、假设、指标、方法、作机制裁决或解释结果；只做字段关联。
预算一次headless，180s/2048输出tokens/12000B stdin，USD0.025声明cap但实付/硬美元cap未知；0工具/下载/自动重试/换后端。历史12保留，累计上限13。每行一小步；packet后由外层检查新正式任务，无新packet/额度则保留支持关联、原始点vs拟合、时间/控制/重复的默认断点，不虚称后台。
INPUT:
"""
prompt = (instruction + json.dumps(packet, ensure_ascii=False, indent=2) + "\n").encode()
assert len(prompt) <= 12000
(TASK / "prompt.txt").write_bytes(prompt)
job = {"task_id": "DS021", "task_version": "v1", "status": "assigned_ready_for_execution", "is_execution_authorization": True,
       "transport": "isolated_headless_stdin_no_tools", "objective": "固定八条原PubMed记录的当前论文ID核对，排除嵌套参考ID",
       "inputs": [{"path": str(TASK / "source_packet.json"), "sha256": hashlib.sha256((TASK / "source_packet.json").read_bytes()).hexdigest()}],
       "prompt_sha256": hashlib.sha256(prompt).hexdigest(),
       "budget": {"wall_seconds": 180, "max_output_tokens": 2048, "max_stdin_bytes": 12000, "model_calls": 1,
                  "automatic_retries": 0, "new_downloads": 0, "declared_cost_cap_usd": .025, "hard_dollar_cap_verified": False},
       "agent_permissions": "all tools disabled; read-only isolated workspace; injected packet only", "allowed_write_root": str(TASK),
       "deliverables": ["events.jsonl", "final.md", "usage.json", "receipt.json"],
       "acceptance_criteria": ["exactly eight source records", "IDs match primary ArticleIdList", "nested references rejected", "literal quotes <=80 characters", "ambiguity logged, no scientific decisions"],
       "stop_conditions": ["uncertain outcome: no retry or backend substitution"], "requires_main_agent_review": True,
       "mainline": "common-assay identity/support/measurement-level bookkeeping only; check new packets each small step"}
(TASK / "task.json").write_bytes((json.dumps(job, ensure_ascii=False, indent=2) + "\n").encode())
print(json.dumps({"task": "DS021", "stdin_bytes": len(prompt), "rows": len(packet), "model_calls_used": 0}))
