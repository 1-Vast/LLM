"""Record exact pre-proposal evidence hashes without opening response values."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FILES = [
    'log/20261022/api_evidence_innovation/PROTOCOL.md',
    'log/20261022/api_evidence_innovation/data/PROMPT.md',
    'log/20261022/renewal_application/DECISION.md',
    'log/20261022/renewal_application/data/INDEPENDENT.md',
    'log/20261022/renewal_application/data/TGGATES_THREE_DOSE_IDENTITY.json',
    'log/20261022/renewal_application/data/CROSS.md',
    'log/20261022/renewal_application/skeptic/INDEPENDENT.md',
    'log/20261022/tggates_functional_qualification/DECISION.md',
    'log/20261022/renewal_application/root_sources/author_blob_736fe4692410b437decf8bf919c4a414e3bbefb6.decoded.txt',
    'research/REPORT.md',
    'research/api_evidence_innovation_20261022/call_provider.py',
]
result = {
    'phase': 'api_evidence_innovation_20261022',
    'role': 'innovation_data',
    'exposure': 'Prior phase decisions and safe metadata only; no RNA/clone_size/functional values/new peer drafts.',
    'files': {name: {'bytes': len(data := (ROOT/name).read_bytes()),
                      'sha256': hashlib.sha256(data).hexdigest()} for name in FILES},
}
destination = ROOT/'log/20261022/api_evidence_innovation/data/INPUT_HASHES.json'
with destination.open('x', encoding='utf-8') as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps({'files': len(FILES), 'manifest_sha256': hashlib.sha256(destination.read_bytes()).hexdigest()}))
