"""Complete a retained length-truncated proposal once, with visible-output budget."""
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
OUT = ROOT / 'log/20261022/update_rule_renewal/api_completion'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    prior = json.loads((OUT.parent / 'api/RECEIPT.json').read_text())
    assert prior['finish_reason'] == 'length'
    original = (OUT.parent / 'API_PROMPT.md').read_text('utf-8')
    partial = (OUT.parent / 'api/RESPONSE.md').read_text('utf-8')
    prompt = original + '\n\n上一逻辑调用达到length，只保留如下不完整提案。请不要换方案，完成这个提案的伪代码、具体最近ordinary对手与操作差异、最小证伪。可以承认它有错误或与具体普通方法相同并给NO_CANDIDATE。不虚构已做实验。限中文1500字，不能只输出内部思考。\n\n' + partial
    with (OUT / 'EXACT_REQUEST.txt').open('x', encoding='utf-8') as f:
        f.write(prompt)
    settings = replace(MAESTROSettings.from_workspace(ROOT), timeout_seconds=300, log_directory=OUT / 'provider')
    client = DeepSeekChatClient(settings)
    receipt = {'started_utc': datetime.now(timezone.utc).isoformat(), 'logical_requests': 1,
               'reason': 'Complete retained length-truncated proposal, not a new candidate search',
               'request_sha256': hashlib.sha256((OUT / 'EXACT_REQUEST.txt').read_bytes()).hexdigest(),
               'transport_attempts': 'NOT_EXPOSED_BY_MAINTAINED_CLIENT', 'generated_code_executed': False}
    started = time.monotonic()
    try:
        response = client.complete([{'role': 'user', 'content': prompt}], temperature=.3,
                                   max_tokens=5000, thinking_enabled=False)
        with (OUT / 'RESPONSE.md').open('x', encoding='utf-8') as f:
            f.write(response.content)
        receipt.update(model=response.model, finish_reason=response.finish_reason,
                       status='VALID_RESPONSE' if response.finish_reason == 'stop' and response.content.strip() else 'INCOMPLETE_RESPONSE_RETAINED')
    except Exception as error:
        receipt.update(status='FAILED_RETAINED', error_type=type(error).__name__, error_code=getattr(error, 'code', None))
    receipt.update(usage=client.provider_usage, wall_seconds=time.monotonic() - started,
                   finished_utc=datetime.now(timezone.utc).isoformat())
    with (OUT / 'RECEIPT.json').open('x', encoding='utf-8') as f:
        json.dump(receipt, f, indent=2)
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
