"""Retain a bounded proposal/critique through the maintained provider client."""
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.agent.llm import DeepSeekChatClient, MAESTROSettings

name = sys.argv[1]
if name not in {'api_constructive', 'api_critique'}:
    raise ValueError('Only the two registered calls are allowed')
out = ROOT / 'log/20261022/mse_mechanism_renewal' / name
prompt = (out / 'PROMPT.md').read_text(encoding='utf-8')
system = 'You are a rigorous scientific mechanism scout. Give exact operations and honest novelty boundaries. Mark unverifiable citations. No invented experiments, source access, biological state or results.'
record = dict(start_utc=datetime.now(timezone.utc).isoformat(), logical_requests=1,
              prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
              generated_code_executed=False, thinking_enabled=False, max_tokens=5000,
              transport_attempts='NOT_EXPOSED_BY_MAINTAINED_CLIENT')
with (out / 'STARTED.json').open('x', encoding='utf-8') as f:
    json.dump(record, f, indent=2)
with (out / 'SYSTEM.md').open('x', encoding='utf-8', newline='\n') as f:
    f.write(system)
started = time.monotonic()
client = None
try:
    client = DeepSeekChatClient(replace(MAESTROSettings.from_workspace(ROOT), timeout_seconds=300,
                                       log_directory=out / 'provider'))
    response = client.complete([dict(role='system', content=system), dict(role='user', content=prompt)],
                               temperature=.7 if name == 'api_constructive' else .2,
                               max_tokens=5000, thinking_enabled=False)
    with (out / 'RESPONSE.md').open('x', encoding='utf-8', newline='\n') as f:
        f.write(response.content)
    record.update(status='COMPLETE' if response.finish_reason == 'stop' else 'INCOMPLETE',
                  model=response.model, finish_reason=response.finish_reason,
                  response_sha256=hashlib.sha256(response.content.encode()).hexdigest())
except Exception as exc:
    record.update(status='FAILED', error_type=type(exc).__name__, error_code=getattr(exc, 'code', None))
record.update(end_utc=datetime.now(timezone.utc).isoformat(), elapsed_seconds=time.monotonic() - started,
              usage=client.provider_usage if client else {}, monetary_cost='NOT_RETURNED_BY_PROVIDER; tokens retained')
with (out / 'RECEIPT.json').open('x', encoding='utf-8') as f:
    json.dump(record, f, indent=2)
print(json.dumps(record))
