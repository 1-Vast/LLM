"""Read cached array headers and source identities; never decode X/Y/events/G."""
import hashlib
import json
from pathlib import Path
import zipfile

import numpy as np

ROOT = Path('D:/MAESTRO')
CACHE = ROOT / 'tmp/context_transfer_20261017/beataml_domain.npz'
OUT = ROOT / 'log/20261023/functional_error_renewal/critic/SCHEMA_ONLY.json'

headers = {}
with zipfile.ZipFile(CACHE) as archive:
    for name in archive.namelist():
        with archive.open(name) as stream:
            version = np.lib.format.read_magic(stream)
            if version == (1, 0):
                shape, order, dtype = np.lib.format.read_array_header_1_0(stream)
            elif version == (2, 0):
                shape, order, dtype = np.lib.format.read_array_header_2_0(stream)
            else:
                raise ValueError(f'Unsupported header {version}; no payload read')
            headers[name] = dict(shape=list(shape), fortran=order, dtype=str(dtype))

with np.load(CACHE, allow_pickle=False) as archive:
    groups = archive['groups'].astype(str)
    contexts = archive['contexts'].astype(str)
folds = np.array([int(hashlib.sha256(('context-transfer-subject:' + g).encode()).hexdigest(), 16) % 5 for g in groups])
source = folds != 0
result = dict(headers=headers, decoded_arrays=['groups', 'contexts'],
              forbidden_arrays_not_decoded=['Y', 'X', 'events', 'G'],
              source_rows=int(source.sum()), source_patients=len(set(groups[source])),
              source_identity_unique=len(set(contexts[source])) == int(source.sum()),
              scope='Header/schema and existing source identity; no response or expression values')
OUT.write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result))
