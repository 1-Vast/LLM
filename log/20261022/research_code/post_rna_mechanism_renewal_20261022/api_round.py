"""Independent direct-provider research contexts and sealed actual cross exchange."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timezone
import hashlib,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.agent.llm import DeepSeekChatClient,MAESTROSettings
P=ROOT/'log/20261022/post_rna_mechanism_renewal'
ROLES={
 'constructive':'建设方：独立提出一个最值得检验的新机制。优先寻找有生物结构约束的状态/功能预测和更新机制，并给一个允许它失败的明确实验。不要只给流程、模块名称或新缩写。',
 'skeptic':'反方：独立探索最可能成立的创新方向，再尽力反驳自己。重点区分真正等价实现与仅仅更强表达能力；给出最强普通对照、最廉价判别实验，并说明什么证据会改变你的判断。',
 'application':'应用/数据方：独立从药物发现的实际决策出发提出最小机制。不要强行使用新论文数据；可提出另一个可核查的公共主源线索但标未核实。明确可观测数据、真实任务和反馈菜单、哪些缺口会阻止拟合。'}

def digest(raw):return hashlib.sha256(raw).hexdigest()

def prepare():
    evidence=(P/'SOURCE_READING.md').read_text(encoding='utf-8')
    for role,instruction in ROLES.items():
        dest=P/'api_reviews'/role;dest.mkdir(parents=True)
        prompt=instruction+'\n这是一轮真正独立首评，你尚未看到其他角色输出。你可以提出不在证据包中的可证伪假说，但不能编造数据或查证结果。最多给一个主候选，必要时说没有可信候选。中文，约2500字，写出关键公式/伪代码。请先自由探索，再按证据约束筛选；不要把所有历史阴性当作普遍否定。\n\n'+evidence
        with (dest/'PROMPT.md').open('x',encoding='utf-8',newline='\n') as f:f.write(prompt)
    with (P/'PROPOSAL_INPUT_SEAL.json').open('x',encoding='utf-8') as f:json.dump(dict(utc=datetime.now(timezone.utc).isoformat(),evidence_sha256=digest(evidence.encode()),roles=list(ROLES),same_provider_contexts_not_replication=True),f,indent=2)

def call(role):
    dest=P/'api_reviews'/role
    prompt=(dest/'PROMPT.md').read_text(encoding='utf-8')
    with (dest/'EXACT_REQUEST.txt').open('x',encoding='utf-8',newline='\n') as f:f.write(prompt)
    receipt=dict(utc_started=datetime.now(timezone.utc).isoformat(),logical_requests=1,request_logical_utf8_sha256=digest(prompt.encode()),request_raw_sha256=digest((dest/'EXACT_REQUEST.txt').read_bytes()),generated_code_executed=False,transport_attempts='NOT_EXPOSED_BY_MAINTAINED_CLIENT')
    with (dest/'STARTED.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,indent=2)
    client=None;start=time.monotonic()
    try:
        client=DeepSeekChatClient(replace(MAESTROSettings.from_workspace(ROOT),timeout_seconds=300,log_directory=P/'provider'))
        result=client.complete([dict(role='system',content='严谨科研探索与独立审查；证据、假说和已执行结果必须分清，不编造引文和实验。'),dict(role='user',content=prompt)],temperature=.7,max_tokens=18000,thinking_enabled=True)
        with (dest/'RESPONSE.md').open('x',encoding='utf-8',newline='\n') as f:f.write(result.content)
        receipt.update(status='VALID_RESPONSE' if result.content.strip() and result.finish_reason=='stop' else 'INCOMPLETE_RESPONSE_RETAINED',model=result.model,finish_reason=result.finish_reason,content_characters=len(result.content))
    except Exception as e:receipt.update(status='FAILED_RETAINED',error_type=type(e).__name__,error_code=getattr(e,'code',None))
    receipt.update(usage=client.provider_usage if client else {},elapsed_seconds=time.monotonic()-start,utc_finished=datetime.now(timezone.utc).isoformat())
    with (dest/'RECEIPT.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,indent=2)
    return dict(role=role,**receipt)

def seal():
    rows={}
    for role in ROLES:
        d=P/'api_reviews'/role;r=json.loads((d/'RECEIPT.json').read_text())
        assert r['status']=='VALID_RESPONSE',(role,r['status'])
        rows[role]=dict(response_sha256=digest((d/'RESPONSE.md').read_bytes()),receipt_sha256=digest((d/'RECEIPT.json').read_bytes()))
    with (P/'INDEPENDENT_RESPONSE_SEAL.json').open('x',encoding='utf-8') as f:json.dump(dict(utc=datetime.now(timezone.utc).isoformat(),roles=rows),f,indent=2)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','run','seal']);parser.add_argument('--roles',nargs='+');args=parser.parse_args()
    if args.action=='prepare':prepare()
    elif args.action=='seal':seal()
    else:
        with ThreadPoolExecutor(max_workers=3) as pool:
            for receipt in pool.map(call,args.roles or ROLES):print(json.dumps(receipt),flush=True)
