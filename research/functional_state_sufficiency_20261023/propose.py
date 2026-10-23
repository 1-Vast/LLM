"""One evidence-grounded API construction attempt; generated code is never executed."""
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.agent.llm import DeepSeekChatClient, MAESTROSettings

OUT = ROOT/'log/20261023/functional_state_sufficiency/api'

if __name__ == '__main__':
    target = OUT/'RECEIPT.json'
    if target.exists():
        raise FileExistsError(target)
    prompt_path = OUT/'PROMPT.md'
    receipt = dict(status='INITIATED', utc=datetime.now(timezone.utc).isoformat(),
                   logical_requests=1, thinking_enabled=False, max_tokens=5500,
                   prompt_sha256=hashlib.sha256(prompt_path.read_bytes()).hexdigest(),
                   transport_attempts='NOT_EXPOSED', generated_code_executed=False)
    target.write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    client = DeepSeekChatClient(replace(MAESTROSettings.from_workspace(ROOT),
                                       timeout_seconds=180.))
    try:
        response = client.complete([
            dict(role='system', content='提出具体可验证更新机制，坦白先例与信息边界，不虚构来源或实验。直接完整回答。'),
            dict(role='user', content=prompt_path.read_text(encoding='utf-8'))],
            temperature=.9, max_tokens=5500, thinking_enabled=False)
        (OUT/'PROPOSAL.md').write_text(response.content, encoding='utf-8')
        receipt.update(status='RESPONSE_RETAINED', model=response.model,
                       finish_reason=response.finish_reason, content_chars=len(response.content))
    except Exception as error:
        receipt.update(status='FAILED_RETAINED', error_type=type(error).__name__,
                       error_code=getattr(error, 'code', None))
    finally:
        receipt.update(ended_utc=datetime.now(timezone.utc).isoformat(),
                       provider_usage=client.provider_usage)
        target.write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps(receipt, indent=2))
