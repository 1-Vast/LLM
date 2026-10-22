"""Run one retained constructive API context; generated code is never executed."""
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/operator_renewal/api_constructive'
sys.path.insert(0, str(ROOT))
from src.agent.llm import DeepSeekChatClient, MAESTROSettings


def write(name, value):
    with (OUT / name).open('x', encoding='utf-8') as handle:
        json.dump(value, handle, indent=2)


def main():
    prompt = (OUT / 'PROMPT.md').read_text(encoding='utf-8')
    system = 'You are a constructive but exact research collaborator. Give one executable mechanism and its strongest faithful conventional comparator. Separate invented hypotheses from verified mathematics and sources. No fabricated citations, data access, biological results or experiments.'
    (OUT / 'SYSTEM.md').write_text(system, encoding='utf-8')
    record = {'start_utc': datetime.now(timezone.utc).isoformat(), 'logical_requests': 1,
        'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
        'code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'max_tokens': 6500, 'thinking_enabled': False, 'generated_code_executed': False,
        'transport_attempts': 'NOT_EXPOSED_BY_MAINTAINED_CLIENT'}
    write('STARTED.json', record)
    started = time.monotonic()
    client = None
    try:
        client = DeepSeekChatClient(replace(MAESTROSettings.from_workspace(ROOT),
            timeout_seconds=300, log_directory=OUT / 'provider'))
        response = client.complete([{'role': 'system', 'content': system},
                                    {'role': 'user', 'content': prompt}],
                                   temperature=.7, max_tokens=6500, thinking_enabled=False)
        with (OUT / 'RESPONSE.md').open('x', encoding='utf-8') as handle:
            handle.write(response.content)
        record.update(status='COMPLETE' if response.finish_reason == 'stop' else 'INCOMPLETE',
            finish_reason=response.finish_reason, model=response.model,
            response_sha256=hashlib.sha256(response.content.encode()).hexdigest())
    except Exception as exc:
        record.update(status='FAILED', error_type=type(exc).__name__, error_code=getattr(exc, 'code', None))
    record.update(end_utc=datetime.now(timezone.utc).isoformat(), elapsed_seconds=time.monotonic() - started,
                  usage=client.provider_usage if client else {}, monetary_cost='NOT_RETURNED; usage retained')
    write('RECEIPT.json', record)
    print(json.dumps(record))


if __name__ == '__main__':
    main()
