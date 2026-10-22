"""Run one retained independent API context selected by its log subdirectory."""
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.agent.llm import DeepSeekChatClient, MAESTROSettings


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    role = sys.argv[1]
    assert role in ('recursive_context', 'opposing_context')
    out = ROOT / 'log/20261022/mechanism_gap' / role
    prompt = (out / 'PROMPT.md').read_text(encoding='utf-8')
    system = 'You are an exact constructive scientific researcher. Separate evidence, hypotheses and deductions. Give a minimal concrete operation or say none survives. Do not fabricate data, paper citations, model calls or experiments. State the strongest faithful ordinary comparator and what could refute you.'
    with (out / 'SYSTEM.md').open('x', encoding='utf-8', newline='\n') as handle:
        handle.write(system)
    record = {'start_utc': datetime.now(timezone.utc).isoformat(), 'logical_requests': 1,
        'prompt_sha256': sha(out / 'PROMPT.md'), 'code_sha256': sha(Path(__file__)),
        'max_tokens': 8000, 'thinking_enabled': False, 'generated_code_executed': False,
        'transport_attempts': 'NOT_EXPOSED_BY_MAINTAINED_CLIENT'}
    with (out / 'STARTED.json').open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(record, handle, indent=2)
    client = None
    started = time.monotonic()
    try:
        client = DeepSeekChatClient(replace(MAESTROSettings.from_workspace(ROOT),
            timeout_seconds=300, log_directory=out / 'provider'))
        response = client.complete([{'role': 'system', 'content': system},
            {'role': 'user', 'content': prompt}], temperature=.7, max_tokens=8000,
            thinking_enabled=False)
        with (out / 'RESPONSE.md').open('x', encoding='utf-8', newline='\n') as handle:
            handle.write(response.content)
        record.update(status='COMPLETE' if response.finish_reason == 'stop' else 'INCOMPLETE',
            finish_reason=response.finish_reason, model=response.model,
            returned_content_sha256=hashlib.sha256(response.content.encode()).hexdigest(),
            exact_file_sha256=sha(out / 'RESPONSE.md'))
    except Exception as exc:
        record.update(status='FAILED', error_type=type(exc).__name__, error_code=getattr(exc, 'code', None))
    record.update(end_utc=datetime.now(timezone.utc).isoformat(), elapsed_seconds=time.monotonic()-started,
        usage=client.provider_usage if client else {}, monetary_cost='NOT_RETURNED; usage retained')
    with (out / 'RECEIPT.json').open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(record, handle, indent=2)
    print(json.dumps(record))


if __name__ == '__main__':
    main()
