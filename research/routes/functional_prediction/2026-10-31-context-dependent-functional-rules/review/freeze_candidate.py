"""Pin the scientific version before a genuinely fresh challenge."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

EP = Path(__file__).resolve().parent.parent
files = ['record.md', 'root/initial_questions.md', 'development/initial_reasoning.md',
         'development/common_coordinate_candidate_v1.md', 'investigator/evidence_handoff.md',
         'scout/initial_independent.md', 'scout/handoff.md']
output = EP/'candidate_freeze_v1.json'
assert not output.exists()
result = {'created_utc': datetime.now(timezone.utc).isoformat(), 'id': 'I054.v1',
          'scientific_status': 'UNTESTED; no numerical execution admitted',
          'files': {name: {'bytes': (EP/name).stat().st_size,
                           'sha256': hashlib.sha256((EP/name).read_bytes()).hexdigest()}
                    for name in files}}
output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result))
