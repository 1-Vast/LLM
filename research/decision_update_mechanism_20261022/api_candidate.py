"""One direct API proposal, recorded as unverified hypothesis; no generated code run."""
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

OUT = ROOT / 'log/20261022/decision_update_mechanism/api'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    prompt = (OUT.parent / 'API_PROMPT.md').read_text(encoding='utf-8')
    with (OUT / 'EXACT_REQUEST.txt').open('x', encoding='utf-8') as stream:
        stream.write(prompt)
    receipt = {'started_utc': datetime.now(timezone.utc).isoformat(), 'logical_requests': 1,
               'request_sha256': hashlib.sha256(prompt.encode('utf-8')).hexdigest(),
               'transport_attempts': 'NOT_EXPOSED_BY_MAINTAINED_CLIENT', 'generated_code_executed': False}
    start = time.monotonic()
    settings = replace(MAESTROSettings.from_workspace(ROOT), timeout_seconds=300, log_directory=OUT / 'provider')
    client = DeepSeekChatClient(settings)
    try:
        result = client.complete([{'role': 'system', 'content': '严谨科研：输出具体可证伪假说或NO_CANDIDATE，不虚构实验与来源。'},
                                  {'role': 'user', 'content': prompt}], temperature=.7,
                                 max_tokens=6500, thinking_enabled=False)
        with (OUT / 'RESPONSE.md').open('x', encoding='utf-8') as stream:
            stream.write(result.content)
        receipt.update(status='VALID_RESPONSE' if result.content.strip() and result.finish_reason == 'stop'
                       else 'INCOMPLETE_RESPONSE_RETAINED', model=result.model, finish_reason=result.finish_reason)
    except Exception as error:
        receipt.update(status='FAILED_RETAINED', error_type=type(error).__name__, error_code=getattr(error, 'code', None))
    receipt.update(usage=client.provider_usage, wall_seconds=time.monotonic() - start,
                   finished_utc=datetime.now(timezone.utc).isoformat())
    with (OUT / 'RECEIPT.json').open('x', encoding='utf-8') as stream:
        json.dump(receipt, stream, indent=2)
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
