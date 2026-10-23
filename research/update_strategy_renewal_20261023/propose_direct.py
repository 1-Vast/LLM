"""One explicit output-mode correction after an empty budget-limited response."""
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.agent.llm import DeepSeekChatClient, MAESTROSettings

OUT = ROOT/'log/20261023/update_strategy_renewal/api'

if __name__ == '__main__':
    target = OUT/'DIRECT_RECEIPT.json'
    assert not target.exists()
    assert (OUT/'PROPOSAL.md').read_text(encoding='utf-8') == ''
    prompt = (OUT/'PROMPT.md').read_text(encoding='utf-8')
    receipt = dict(status='INITIATED', utc=datetime.now(timezone.utc).isoformat(),
                   logical_requests=1, thinking_enabled=False, max_tokens=4000,
                   prompt_sha256=hashlib.sha256((OUT/'PROMPT.md').read_bytes()).hexdigest(),
                   transport_attempts='NOT_EXPOSED', generated_code_executed=False)
    target.write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    client = DeepSeekChatClient(replace(MAESTROSettings.from_workspace(ROOT), timeout_seconds=180.))
    try:
        response = client.complete([{'role':'system','content':'直接给出简洁完整回答，不要隐藏思考；如果没有候选就答NONE及具体原因。'},
                                    {'role':'user','content':prompt}], temperature=.8, max_tokens=4000, thinking_enabled=False)
        (OUT/'DIRECT_PROPOSAL.md').write_text(response.content, encoding='utf-8')
        receipt.update(status='RESPONSE_RETAINED', model=response.model,
                       finish_reason=response.finish_reason, content_chars=len(response.content))
    except Exception as error:
        receipt.update(status='FAILED_RETAINED', error_type=type(error).__name__, error_code=getattr(error,'code',None))
    finally:
        receipt.update(ended_utc=datetime.now(timezone.utc).isoformat(), provider_usage=client.provider_usage)
        target.write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps(receipt, indent=2))
