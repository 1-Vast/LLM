"""Seal the independent constructive-skeptic position and post-prompt metadata exposure."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / 'log/20261022/api_evidence_innovation/skeptic'


def binding(path):
    return {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'bytes': path.stat().st_size}


def main():
    post = [
        'log/20261022/renewal_application/data/TGGATES_THREE_DOSE_IDENTITY.json',
        'log/20261022/tggates_functional_qualification/FUNCTIONAL_SCHEMA.json',
        'log/20261022/tggates_functional_qualification/EARLY_LATE_MENU_COUNTS.json',
        'log/20261022/tggates_functional_qualification/skeptic_sources/EARLY_TG_FULL.xml.txt',
        'src/agent/llm.py',
    ]
    payload = {'utc': datetime.now(timezone.utc).isoformat(),
               'new_peer_drafts_read': False,
               'post_prompt_inputs': {path: binding(ROOT / path) for path in post},
               'sealed_files': {path: binding(LOG / path) for path in [
                   'PROMPT.md', 'INPUT_BINDINGS.json', 'STARTED.json',
                   'RESPONSE.md', 'RECEIPT.json', 'INDEPENDENT.md', 'WORK_AND_FAILURES.md']}}
    with (LOG / 'INDEPENDENT_BINDINGS.json').open('x', encoding='utf-8') as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'independent': payload['sealed_files']['INDEPENDENT.md'],
                      'provider_receipt': payload['sealed_files']['RECEIPT.json'],
                      'post_prompt_input_count': len(post)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
