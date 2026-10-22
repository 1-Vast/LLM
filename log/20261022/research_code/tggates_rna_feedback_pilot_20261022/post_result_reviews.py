"""One-shot opposing API reviews after sealed scoring and separate assembly audit succeed."""
import argparse,json,subprocess,sys,time,hashlib
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from pathlib import Path
import psutil
ROOT=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent
P=ROOT/'log/20261022/tggates_rna_feedback_pilot'


def write(path,value):
    with path.open('x',encoding='utf-8') as f:json.dump(value,f,indent=2,ensure_ascii=False)


def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def read_finished(path):
    if not path.exists():return None
    try:return json.loads(path.read_text(encoding='utf-8'))
    except json.JSONDecodeError:return None


def live_identity(pid,script):
    process=psutil.Process(pid)
    assert script in ' '.join(process.cmdline())
    return process.create_time()


def still_live(pid,created):
    try:return psutil.Process(pid).create_time()==created and psutil.Process(pid).is_running()
    except psutil.NoSuchProcess:return False


def call(role,prompt):
    directory=P/'api_reviews'/role;directory.mkdir()
    with (directory/'PROMPT.md').open('x',encoding='utf-8') as f:f.write(prompt)
    with (directory/'CALL.log').open('x',encoding='utf-8') as out:
        process=subprocess.run([sys.executable,'-B',str(C/'call_review.py'),role,
            '--no-thinking','--no-append-drafts','--max-tokens','6000'],cwd=ROOT,stdout=out,stderr=subprocess.STDOUT)
    receipt=read_finished(directory/'RECEIPT.json')
    assert process.returncode==0 and receipt and receipt['status']=='RESPONSE_RETAINED',role
    assert receipt['finish_reason']=='stop','Partial review retained; root inspection required: '+role
    response=(directory/'RESPONSE.md').read_text(encoding='utf-8')
    assert response.strip(),role
    return role,response,receipt


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--pilot-pid',type=int,required=True)
    parser.add_argument('--reference-pid',type=int,required=True);args=parser.parse_args()
    pilot_created=live_identity(args.pilot_pid,'run_when_ready.py')
    reference_created=live_identity(args.reference_pid,'reference_assembly.py')
    record=dict(status='WAITING_FOR_SCORED_PILOT_AND_REFERENCE_AUDIT',utc_started=datetime.now(timezone.utc).isoformat(),
        pilot_pid=args.pilot_pid,pilot_create_time=pilot_created,reference_pid=args.reference_pid,
        reference_create_time=reference_created,script_sha256=sha(Path(__file__)),
        provider='Same DeepSeek model, separate contexts and explicit opposing roles; not biological replication.',reviews=[])
    write(P/'POST_RESULT_REVIEW_STARTED.json',record)
    try:
        while True:
            terminal=read_finished(P/'AUTONOMOUS_PILOT_TERMINAL.json')
            reference=read_finished(P/'REFERENCE_ASSEMBLY_AUDIT.json')
            if terminal and terminal['status']!='PILOT_COMPLETE_REQUIRES_RESULT_REVIEW':
                raise RuntimeError('Pilot technical failure retained; no empirical-performance review')
            if (P/'REFERENCE_ASSEMBLY_FAILURE.json').exists():raise RuntimeError('Reference assembly failure; inspect before review')
            if terminal and reference:break
            if not terminal and not still_live(args.pilot_pid,pilot_created):raise RuntimeError('Pilot missing without terminal receipt')
            if not reference and not still_live(args.reference_pid,reference_created):raise RuntimeError('Reference auditor missing without completed receipt')
            time.sleep(5)
        assert reference['status']=='PASS'
        seal=json.loads((P/'PREDICTION_SEAL.json').read_text())
        for relative,digest in dict(seal['files'],**seal['code']).items():assert sha(ROOT/relative)==digest
        files=['RNA_PILOT_RESULT.json','NUMERICAL_RECEIPT.json','REFERENCE_ASSEMBLY_AUDIT.json',
            'GATE_GEOMETRY_AUDIT.json','NUMERICAL_AMENDMENTS.md','GATE_GEOMETRY_INTERPRETATION.md','APPLICATION_SCOPE_NOTE.md']
        context=''
        hashes={}
        for name in files:
            path=P/name;hashes[name]=sha(path)
            context+='\n\n--- '+name+' ---\n'+path.read_text(encoding='utf-8')
        selected=json.loads((P/'SOURCE_SELECTION.json').read_text())['selected']
        context+='\n\n--- source-selected configurations (selection-exposed source scores) ---\n'+json.dumps(selected,ensure_ascii=False)
        write(P/'POST_RESULT_REVIEW_EVIDENCE.json',dict(files_sha256=hashes,prediction_seal_sha256=sha(P/'PREDICTION_SEAL.json')))
        common='只依据下列实测结果及冻结文档评审，最多1500中文字符。精确引用数字；无证据写未知。不得编造因果或统计显著性，不要求换端点/删样本/开保留集/放宽门槛。不把先前失败配置当所有世界模型不可能。此候选线性结构已认定是普通受约束联合预测，不是新算法。单独回答：预测有无增量及实际意义；RNA/路由贡献；是否存在普通解释；新颖性；world/agent/继承/联合/RSI哪些未测；支持证据、反对证据、未决分歧和最小后续验证。明确与原冻结STOP/GO判定是否一致，以及门槛和mixture限制影响解释而非修改判定。\n'
        roles=[('post_result_support','你是建设性支持方，尽力识别结果中可保留的真实能力，但不得替失败主门槛找借口。'),
               ('post_result_skeptic','你是独立质疑方，优先检查普通基线解释、受限样本、预筛先验、选择暴露及过度创新/RSI主张；也不得否认实际存在的小增量。')]
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures=[pool.submit(call,role,position+common+context) for role,position in roles]
            first=[f.result() for f in futures]
        record['reviews']+=[dict(role=r,usage=receipt['usage']) for r,_,receipt in first]
        replies=[]
        for own,peer in [(first[0],first[1]),(first[1],first[0])]:
            prompt='你继续原立场。最多1000中文字符，明确回应对方具体意见：同意、反对、真实未决问题和最小验证。纠正双方任何错数或过度断言。不得假装双方共识是实证，也不得换门槛或开保留集。\n'
            prompt+='自己的首轮原文：\n'+own[1]+'\n对方首轮原文：\n'+peer[1]+context
            replies.append((own[0]+'_cross',prompt))
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures=[pool.submit(call,role,prompt) for role,prompt in replies]
            crossed=[f.result() for f in futures]
        record['reviews']+=[dict(role=r,usage=receipt['usage']) for r,_,receipt in crossed]
        record.update(status='REVIEWS_AND_ACTUAL_CROSS_REPLIES_COMPLETE_ROOT_DECISION_PENDING',
                      total_tokens=sum(r['usage'].get('total_tokens',0) for r in record['reviews']))
    except Exception as e:
        record.update(status='FAILED_RETAINED',error=f'{type(e).__name__}: {e}')
    record['utc_finished']=datetime.now(timezone.utc).isoformat()
    write(P/'POST_RESULT_REVIEW_TERMINAL.json',record)
    print(json.dumps(record,ensure_ascii=False),flush=True)
    return int(record['status']!='REVIEWS_AND_ACTUAL_CROSS_REPLIES_COMPLETE_ROOT_DECISION_PENDING')

if __name__=='__main__':raise SystemExit(main())
