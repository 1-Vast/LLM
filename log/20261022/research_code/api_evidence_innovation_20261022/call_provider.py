"""Run one explicitly retained DeepSeek experiment from an exact saved prompt."""
import argparse
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / 'log/20261022/api_evidence_innovation'
sys.path.insert(0, str(ROOT))
from src.agent.llm import DeepSeekChatClient, MAESTROSettings


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, data):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('role')
    args = parser.parse_args()
    assert args.role.replace('_', '').isalnum()
    directory = LOG / args.role
    prompt_path = directory / 'PROMPT.md'
    prompt = prompt_path.read_text(encoding='utf-8')
    write(directory / 'STARTED.json', {'utc': datetime.now(timezone.utc).isoformat(),
          'logical_request': 1, 'prompt_sha256': sha(prompt_path), 'script_sha256': sha(Path(__file__))})
    client = None
    start = time.monotonic()
    receipt = {'logical_requests': 1, 'generated_code_executed': False,
               'transport_attempts': 'NOT_EXPOSED_BY_MAINTAINED_CLIENT'}
    try:
        client = DeepSeekChatClient(replace(MAESTROSettings.from_workspace(ROOT), timeout_seconds=240))
        response = client.complete([{'role': 'system', 'content': '你是严谨的科研合作者。以可执行、可证伪的细胞干预研究推导为主，不编造引用/数据，不把假设当实证。'},
                                    {'role': 'user', 'content': prompt}],
                                   temperature=0.8, max_tokens=18000, thinking_enabled=True)
        with (directory / 'RESPONSE.md').open('x', encoding='utf-8') as stream:
            stream.write(response.content)
        receipt.update(status='RESPONSE_RETAINED', model=response.model, finish_reason=response.finish_reason,
                       response_characters=len(response.content), response_sha256=sha(directory / 'RESPONSE.md'))
    except Exception as exc:
        receipt.update(status='FAILED_RETAINED', error_type=type(exc).__name__, error_code=getattr(exc, 'code', None))
    finally:
        receipt.update(ended_utc=datetime.now(timezone.utc).isoformat(), elapsed_seconds=time.monotonic() - start,
                       usage=client.provider_usage if client else {}, reasoning_text='NOT_EXPOSED_BY_CLIENT')
        write(directory / 'RECEIPT.json', receipt)
    print(json.dumps(receipt, ensure_ascii=False), flush=True)
    return 0 if receipt['status'] == 'RESPONSE_RETAINED' else 1


if __name__ == '__main__':
    raise SystemExit(main())
