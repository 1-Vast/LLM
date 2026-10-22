"""Bind the skeptic's pre-provider input exposure without reading biological outcomes."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RELATIVE = [
    'log/20261022/api_evidence_innovation/PROTOCOL.md',
    'log/20261022/renewal_application/DECISION.md',
    'research/REPORT.md',
    'log/20261022/renewal_application/skeptic/INDEPENDENT.md',
    'log/20261022/renewal_application/skeptic/CROSS.md',
    'log/20261022/tggates_functional_qualification/DECISION.md',
    'log/20261022/tggates_functional_qualification/advocate_sources/tggates_early_response.json',
    'research/api_evidence_innovation_20261022/call_provider.py',
    'log/20261022/api_evidence_innovation/skeptic/PROMPT.md',
]


def main():
    entries = {}
    for relative in RELATIVE:
        path = ROOT / relative
        entries[relative] = {
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'bytes': path.stat().st_size,
        }
    target = ROOT / 'log/20261022/api_evidence_innovation/skeptic/INPUT_BINDINGS.json'
    with target.open('x', encoding='utf-8') as stream:
        json.dump({'utc': datetime.now(timezone.utc).isoformat(), 'inputs': entries,
                   'provider_prompt_is_exact_prompt_file': True,
                   'new_peer_drafts_read': False,
                   'biological_response_values_opened': False,
                   'note': 'Root task/past shared summary disclosed; no claim of fully blinded historical context.'},
                  stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'input_files': len(entries), 'output': str(target)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
