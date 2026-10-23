"""Bind independent biological audit and reused sources; no assay values read."""
from pathlib import Path
import hashlib
import json

root = Path('D:/MAESTRO')
out = root / 'log/20261023/action_rule_search/biology'
sources = [
    'C:/Users/59964/.codex/attachments/45d9c2f9-b12a-4e71-bd4a-9f6cc5eb5ce9/goal-objective.md',
    'log/20261023/observation_law_search/DECISION.md',
    'log/20261023/observation_law_search/ROOT_SOURCE_ASSESSMENT.md',
    'log/20261022/early_update_mechanism/biology/INDEPENDENT.md',
    'log/20261022/early_update_mechanism/biology/PRIMARY_QUOTES.json',
    'log/20261022/early_update_mechanism/DECISION.md',
    'research/action_substitution_20261019/REPORT.md',
    'research/kinobeads_substitution_20261019/REPORT.md',
    'log/20261022/decrypte_feedback_pilot/DECISION.md',
    'log/20261022/decrypte_molecular_increment/key_correction/DECISION.md',
    'log/20261022/native_operation/biology/INDEPENDENT_POSITION.md',
]

def record(name):
    p = Path(name)
    if not p.is_absolute():
        p = root / p
    data = p.read_bytes()
    return {'path': str(p), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}

receipt = {'kind': 'local_source_reuse_not_network', 'new_http_requests': 0,
           'scope': 'text/design audit only; no numeric dataset payloads',
           'sources': [record(s) for s in sources]}
(out / 'SOURCE_RECEIPTS.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
seal = {'independent_before_peer_reading': True, 'files': [record(str(p)) for p in
        [out / 'INDEPENDENT.md', out / 'SOURCE_RECEIPTS.json', Path(__file__)]]}
(out / 'INDEPENDENT_SEAL.json').write_text(json.dumps(seal, ensure_ascii=False, indent=2), encoding='utf-8')
print('Sealed independent biological audit; 11 local source receipts; no biological experiment.')
