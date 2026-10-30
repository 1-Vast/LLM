"""Source-exact new-field packet. The auxiliary model makes no scientific choices."""
from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
task = Path(r"D:\MAESTRO\research\deepseek\tasks\DS014")
assert not task.exists(), "Never replace a previous packet"
task.mkdir()
(task / "workspace").mkdir()
paper = HERE / "sources/root/P2_drp2026.xml"
manifest = HERE / "sources/root/P3_gdsc20_manifest.json"
root = ET.parse(paper).getroot()
method = next(s for s in root.findall('.//sec') if s.find('title') is not None and ''.join(s.find('title').itertext()) == '2 Methods')
paragraphs = [''.join(p.itertext()) for p in method.findall('p')]

def quote(starts):
    chosen = [(i+1,p) for i,p in enumerate(paragraphs) if any(p.startswith(x) for x in starts)]
    return {"path":str(paper),"sha256":hashlib.sha256(paper.read_bytes()).hexdigest(),
            "locator":"2 Methods, direct paragraphs " + ','.join(str(i) for i,_ in chosen),
            "quotes":[p for _,p in chosen]}

data = json.loads(manifest.read_text(encoding='utf-8'))
records = [
 {"id":"D_SOURCE","source":{"path":str(manifest),"sha256":hashlib.sha256(manifest.read_bytes()).hexdigest(),
   "locator":"title/doi/version/license/files","quote":{k:data[k] for k in ('title','doi','version','license','files')}},
  "fields":["release_name","original_filename","file_bytes","license","not_Sanger_2023_xlsx"]},
 {"id":"D_PANEL","source":quote(['Panel Selection:','DRPs and cell line panels']),
  "fields":["descriptor_endpoint","panel_selection_information","typical_drug_panel_size","not_novel_first_claim"]},
 {"id":"D_TEST","source":quote(['Machine Learning:','Hyperparameter Optimisation']),
  "fields":["cell_split","target_endpoint","training_panel_scope","GDSC_and_CCLE_settings"]},
 {"id":"D_WET","source":quote(['Compound plate preparation:','Viability Assay:']),
  "fields":["raw_concentrations","duration","measurement","cannot_transfer_to_GDSC20_time_or_replicates"]}
]
packet={"task_id":"DS014","records":records}
source_packet=task/'source_packet.json'
source_packet.write_text(json.dumps(packet,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
instructions='''你是只读辅助编目员，仅从以下片段按固定字段抽取，不选研究假设/指标/算法，不裁决机制。输出严格JSON数组恰好4行，保留id、fields及原locator，每行values/ambiguities。缺失用真正JSON null。不计算、不补造单位/独立培养/实验重复。D_SOURCE是作者Figshare比较CSV，不是27Oct23 Sanger XLSX；D_WET是论文新做MCF7/MCF10A实验，不可移植成GDSC20时长/重复认证。保留所有浓度小数原字符，禁止无来源数字插话。D_PANEL只编目已知先例，不判原创性。无工具/网络/其他文件读取，歧义上报继续其他行。\n'''
prompt=(instructions+json.dumps(packet,ensure_ascii=False,separators=(',',':'))).encode('utf-8')
assert len(prompt)<=12000,len(prompt)
(task/'prompt.txt').write_bytes(prompt)
job={"task_id":"DS014","task_version":"v1","status":"assigned_ready_for_execution",
 "is_execution_authorization":True,"transport":"isolated_headless_stdin_no_tools",
 "objective":"新GDSC2作者发布与DRP2026原文的字段/单位/作用时长及来源隔离编目",
 "inputs":[{"path":str(source_packet),"sha256":hashlib.sha256(source_packet.read_bytes()).hexdigest()}],
 "prompt_sha256":hashlib.sha256(prompt).hexdigest(),
 "budget":{"wall_seconds":180,"max_output_tokens":2048,"max_stdin_bytes":12000,"model_calls":1,"automatic_retries":0,"new_downloads":0,"declared_cost_cap_usd":0.025},
 "agent_permissions":"all tools disabled; read-only isolated workspace; injected source snippets only",
 "allowed_write_root":str(task),"deliverables":["receipt.json","events.jsonl","final.md","usage.json"],
 "acceptance_criteria":["four exact ids and locators","CSV/XLSX and author/Sanger releases separated","no GDSC time/repeat fabrication","raw dose decimals exact","valid JSON null and no mechanism claim"],
 "stop_conditions":["uncertain call no retry or backend change","ambiguities logged, independent rows continue"],
 "requires_main_agent_review":True,"mainline":"common functional-data endpoint/dose/time/repeat/version ledger; next-task check at packet boundary"}
(task/'task.json').write_text(json.dumps(job,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
coord=task.parent.parent
(coord/'CURRENT_TASK.md').write_text('''# 当前辅助任务状态

2026-10-29：DS014 v1已建，尚待实回执。本轮新增1次调用，历史5次保留，累计上限6；不重跑旧task。只核新GDSC2作者CSV与DRP2026片段4条记录，无功能值/工具/网络。180s、2048输出tokens、12000B stdin、声明成本$0.025，0重试/换后端。
root并行做科学问题/协议；返回后核receipt/events/final/usage及来源，不以启动代完成。默认主线是常见功能数据字段/剂量/时长/重复与版本编目。每小步检查新正式任务，有则优先，无则恢复已授权新原件的缺字段；没有新原件/无预算则保存断点结束，不虚称后台轮询。
旧DS013单位插话/DS012上游截断/DS011算术拒收、DS007/008无回执等历史在原task保留，均不自动重跑；不读sealed/confirmation/.env或自行选择科学问题。
''',encoding='utf-8')
print(json.dumps({'task_id':'DS014','stdin_bytes':len(prompt),'records':len(records)}))
