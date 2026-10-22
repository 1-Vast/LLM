"""One retained, credential-safe proposal request; outputs are untrusted leads."""
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.agent.llm import DeepSeekChatClient, MAESTROSettings
OUT=ROOT/'log/20261022/contrast_mechanism_scout'/(sys.argv[1] if len(sys.argv)>1 else 'api')
prompt=(OUT/'PROMPT.md').read_text(encoding='utf-8')
record=dict(start_utc=datetime.now(timezone.utc).isoformat(),logical_requests=1,
            prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),generated_code_executed=False,
            transport_attempts='NOT_EXPOSED_BY_MAINTAINED_CLIENT')
with (OUT/'STARTED.json').open('x',encoding='utf-8') as f:json.dump(record,f,indent=2)
start=time.monotonic()
client=None
try:
    client=DeepSeekChatClient(replace(MAESTROSettings.from_workspace(ROOT),timeout_seconds=300,log_directory=OUT/'provider'))
    response=client.complete([dict(role='system',content='You are a rigorous scientific mechanism scout. Propose precise falsifiable operations, not architectures. Label unverified citations and data availability. Do not invent source access or experiments.'),dict(role='user',content=prompt)],temperature=.8,max_tokens=4500 if len(sys.argv)>1 else 12000,thinking_enabled=len(sys.argv)==1)
    with (OUT/'RESPONSE.md').open('x',encoding='utf-8') as f:f.write(response.content)
    record.update(status='COMPLETE' if response.finish_reason=='stop' else 'INCOMPLETE',model=response.model,finish_reason=response.finish_reason,response_sha256=hashlib.sha256(response.content.encode()).hexdigest())
except Exception as exc:
    record.update(status='FAILED',error_type=type(exc).__name__,error_code=getattr(exc,'code',None))
record.update(end_utc=datetime.now(timezone.utc).isoformat(),elapsed_seconds=time.monotonic()-start,usage=client.provider_usage if client else {},monetary_cost='NOT_RETURNED_BY_PROVIDER; token usage retained')
with (OUT/'RECEIPT.json').open('x',encoding='utf-8') as f:json.dump(record,f,indent=2)
print(json.dumps(record))
