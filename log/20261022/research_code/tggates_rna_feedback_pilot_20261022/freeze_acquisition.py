"""Pin authenticated acquisition inputs after local synthetic checks; no CEL read."""
import json
from pathlib import Path
import rna_archive_acquire as a

_, jobs, manifest_sha = a.load_inputs()
record = dict(status=a.AUTHORIZED_STATUS, manifest_sha256=manifest_sha,
    heads_sha256=a.sha256_file(a.HEADS), script_sha256=a.sha256_file(Path(a.__file__)),
    authorized_archive_count=len(jobs), expected_archive_bytes=sum(j['expected_bytes'] for j in jobs),
    authorization='User explicitly authorizes downloads and autonomous testing.',
    scope='31 source/development compound archives; compressed excluded time/dose bytes contacted. '
          'No later compound archive. No CEL parsing authorized by this acquisition freeze.',
    utc=a.utc_now())
path = a.PHASE/'ACQUISITION_FREEZE.json'
with path.open('x', encoding='utf-8') as f:
    json.dump(record, f, indent=2)
print(json.dumps(record))
