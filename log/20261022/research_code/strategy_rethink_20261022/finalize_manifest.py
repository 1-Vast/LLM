"""Add exact archive row indices before freezing, retaining the previous draft digest."""
import hashlib
import json

import numpy as np

from screen import OUT, SOURCE, write


path = OUT / 'EPISODE_MANIFEST.json'
original = path.read_bytes()
manifest = json.loads(original)
with np.load(SOURCE, allow_pickle=False) as archive:
    comp, regime = archive['comp'], archive['regime']
    for phase in manifest['episodes'].values():
        for episode in phase:
            episode['row_indices'] = {
                split: np.flatnonzero((regime == 'A') & np.isin(comp, episode[split])).tolist()
                for split in ('calibration', 'development', 'evaluation')}
path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
write('MANIFEST_PREFREEZE_REVISION.json', {
    'old_draft_sha256': hashlib.sha256(original).hexdigest(),
    'new_draft_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
    'change': 'Add identifier-derived exact archive row indices; no outcome scalar read.'})
print('Added exact row indices; retained pre-freeze draft digest.')
