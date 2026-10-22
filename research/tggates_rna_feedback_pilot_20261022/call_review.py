"""Retain one direct API review, without executing generated code."""
import argparse
from dataclasses import replace
from datetime import datetime,timezone
import hashlib,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.agent.llm import DeepSeekChatClient,MAESTROSettings
P=ROOT/'log/20261022/tggates_rna_feedback_pilot'

def main():
    parser=argparse.ArgumentParser();parser.add_argument('role')
    parser.add_argument('--no-thinking',action='store_true')
    parser.add_argument('--no-append-drafts',action='store_true')
    parser.add_argument('--max-tokens',type=int,default=18000);args=parser.parse_args()
    assert args.role.replace('_','').isalnum()
    dest=P/'api_reviews'/args.role;dest.mkdir(parents=True,exist_ok=True)
    prompt=(dest/'PROMPT.md').read_text(encoding='utf-8')
    inputs={}
    for name in ([] if args.no_append_drafts else ['ASTRA_METHOD_INDEPENDENT.md','ASTRA_PREPROCESS_INDEPENDENT.md']):
        raw=(P/name).read_bytes();inputs[name]=hashlib.sha256(raw).hexdigest()
        prompt+='\n\n--- '+name+' ---\n'+raw.decode('utf-8')
    (dest/'EXACT_REQUEST.txt').write_text(prompt,encoding='utf-8')
    receipt=dict(utc_started=datetime.now(timezone.utc).isoformat(),inputs=inputs,
        request_sha256=hashlib.sha256(prompt.encode()).hexdigest(),logical_requests=1,
        transport_attempts='NOT_EXPOSED_BY_MAINTAINED_CLIENT',generated_code_executed=False)
    (dest/'STARTED.json').write_text(json.dumps(receipt,indent=2))
    client=None;start=time.monotonic()
    try:
        client=DeepSeekChatClient(replace(MAESTROSettings.from_workspace(ROOT),timeout_seconds=300))
        result=client.complete([dict(role='system',content='严谨科研审查。仅依据所给材料推理，不编造实证或引用。'),
            dict(role='user',content=prompt)],temperature=.7,max_tokens=args.max_tokens,thinking_enabled=not args.no_thinking)
        with (dest/'RESPONSE.md').open('x',encoding='utf-8') as f:f.write(result.content)
        receipt.update(status='RESPONSE_RETAINED' if result.content.strip() else 'EMPTY_RESPONSE_RETAINED',
                       model=result.model,finish_reason=result.finish_reason,
                       content_characters=len(result.content),thinking_enabled=not args.no_thinking)
    except Exception as e:
        receipt.update(status='FAILED_RETAINED',error_type=type(e).__name__,error_code=getattr(e,'code',None))
    finally:
        receipt.update(usage=client.provider_usage if client else {},elapsed_seconds=time.monotonic()-start)
        with (dest/'RECEIPT.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,indent=2)
    print(json.dumps(receipt),flush=True)
    return int(receipt['status']!='RESPONSE_RETAINED')
if __name__=='__main__':raise SystemExit(main())
