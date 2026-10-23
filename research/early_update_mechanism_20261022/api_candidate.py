"""One direct independent provider proposal; retain request, response and cost."""
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

OUT = ROOT / 'log/20261022/early_update_mechanism/api'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    prompt = (OUT.parent / 'API_PROMPT.md').read_text('utf-8')
    with (OUT / 'EXACT_REQUEST.txt').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(prompt)
    receipt = {'started_utc': datetime.now(timezone.utc).isoformat(), 'logical_requests': 1,
               'request_sha256': hashlib.sha256((OUT / 'EXACT_REQUEST.txt').read_bytes()).hexdigest(),
               'transport_attempts': 'NOT_EXPOSED_BY_MAINTAINED_CLIENT',
               'citations': 'UNVERIFIED_MODEL_SUGGESTIONS', 'generated_code_executed': False}
    (OUT / 'STARTED.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    started, client = time.monotonic(), None
    try:
        settings = replace(MAESTROSettings.from_workspace(ROOT), timeout_seconds=300,
                           log_directory=OUT / 'provider')
        client = DeepSeekChatClient(settings)
        result = client.complete([{'role': 'system', 'content': '严谨算法研究。区分事实/假说/证据，不能编造查证或实验。'},
                                  {'role': 'user', 'content': prompt}],
                                 temperature=.7, max_tokens=18000, thinking_enabled=True)
        with (OUT / 'RESPONSE.md').open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(result.content)
        receipt.update(status='VALID_RESPONSE' if result.content.strip() and result.finish_reason == 'stop'
                       else 'INCOMPLETE_RESPONSE_RETAINED', model=result.model,
                       finish_reason=result.finish_reason, content_characters=len(result.content))
    except Exception as error:
        receipt.update(status='FAILED_RETAINED', error_type=type(error).__name__,
                       error_code=getattr(error, 'code', None))
    receipt.update(usage=client.provider_usage if client else {},
                   wall_seconds=time.monotonic() - started,
                   finished_utc=datetime.now(timezone.utc).isoformat())
    with (OUT / 'RECEIPT.json').open('x', encoding='utf-8') as stream:
        json.dump(receipt, stream, indent=2)
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
