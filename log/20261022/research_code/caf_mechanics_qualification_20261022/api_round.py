"""Independent direct-API mechanism exploration with exact retained inputs."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime,timezone
import argparse,hashlib,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.agent.llm import DeepSeekChatClient,MAESTROSettings
P=ROOT/'log/20261022/caf_mechanics_qualification'
ROLES={
 'mechanism':'建设方：独立探索最简的生物机制或模型更新结构。优先寻找能区分状态恢复与功能恢复、干预历史与混杂的可证伪操作，但不必限于当前物理数据。最多一个候选；区别于先验与普通结构正则化，允许候选失败。',
 'skeptic':'反方：独立提出最有希望的新方向并构造最强反驳。尤其审查科学假设、精确机制必要性、与直接预测/CL/AL/混合/等预算搜索/已知RSI的实质差异。没有足够依据就不晋级，但不要把普适表达能力当等价证明。',
 'data':'应用与数据方：独立从药物发现实际决策出发，评估当前资产是否值得继续；最多推荐一个机制/新公共一手资产。给真实可核查主源标识与任务/反馈契约，明确未核实细节，不把时间点/电极/像素假装独立任务。'}

def sha(raw):return hashlib.sha256(raw).hexdigest()

def prepare():
    context=(P/'RESEARCH_PACKET.md').read_text(encoding='utf-8')
    for role,instruction in ROLES.items():
        d=P/'api_reviews'/role;d.mkdir(parents=True)
        prompt=instruction+'\n独立首评，尚无其他角色观点。中文约2500字。先探索，再基于证据筛选。请给最有希望的具体机制（若有），普通解释、数据缺口、最廉价判别步骤、成功/停止条件，以及world/agent/继承/联合/C4分别如何归因。不要只输出审查清单、流程或模块名称。\n\n'+context
        with (d/'PROMPT.md').open('x',encoding='utf-8',newline='\n') as f:f.write(prompt)
    with (P/'API_INPUT_SEAL.json').open('x',encoding='utf-8') as f:json.dump(dict(utc=datetime.now(timezone.utc).isoformat(),packet_logical_sha256=sha(context.encode()),roles=list(ROLES)),f,indent=2)

def call(role):
    d=P/'api_reviews'/role;prompt=(d/'PROMPT.md').read_text(encoding='utf-8')
    with (d/'EXACT_REQUEST.txt').open('x',encoding='utf-8',newline='\n') as f:f.write(prompt)
    receipt=dict(utc_started=datetime.now(timezone.utc).isoformat(),logical_requests=1,request_logical_sha256=sha(prompt.encode()),request_raw_sha256=sha((d/'EXACT_REQUEST.txt').read_bytes()),transport_attempts='NOT_EXPOSED',generated_code_executed=False)
    with (d/'STARTED.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,indent=2)
    start=time.monotonic();client=None
    try:
        client=DeepSeekChatClient(replace(MAESTROSettings.from_workspace(ROOT),timeout_seconds=300,log_directory=P/'provider'))
        r=client.complete([dict(role='system',content='严谨科研探索和独立评审；明确证据与假说，不编造文献、数据或已执行结果。'),dict(role='user',content=prompt)],temperature=.7,max_tokens=18000,thinking_enabled=True)
        with (d/'RESPONSE.md').open('x',encoding='utf-8',newline='\n') as f:f.write(r.content)
        receipt.update(status='VALID_RESPONSE' if r.content.strip() and r.finish_reason=='stop' else 'INCOMPLETE_RETAINED',model=r.model,finish_reason=r.finish_reason,content_characters=len(r.content))
    except Exception as e:receipt.update(status='FAILED_RETAINED',error_type=type(e).__name__,error_code=getattr(e,'code',None))
    receipt.update(usage=client.provider_usage if client else {},elapsed_seconds=time.monotonic()-start,utc_finished=datetime.now(timezone.utc).isoformat())
    with (d/'RECEIPT.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,indent=2)
    return dict(role=role,**receipt)

def seal():
    rows={}
    for role in ROLES:
        d=P/'api_reviews'/role;r=json.loads((d/'RECEIPT.json').read_text());assert r['status']=='VALID_RESPONSE'
        rows[role]=dict(response_sha256=sha((d/'RESPONSE.md').read_bytes()),receipt_sha256=sha((d/'RECEIPT.json').read_bytes()))
    with (P/'INDEPENDENT_RESPONSE_SEAL.json').open('x',encoding='utf-8') as f:json.dump(dict(utc=datetime.now(timezone.utc).isoformat(),roles=rows),f,indent=2)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','run','seal']);parser.add_argument('--roles',nargs='+');args=parser.parse_args()
    if args.action=='prepare':prepare()
    elif args.action=='seal':seal()
    else:
        with ThreadPoolExecutor(max_workers=3) as pool:
            for receipt in pool.map(call,args.roles or ROLES):print(json.dumps(receipt),flush=True)
