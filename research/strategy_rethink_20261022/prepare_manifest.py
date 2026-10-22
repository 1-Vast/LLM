"""Create the response-free exact episode manifest from the retained schema audit."""
import hashlib
import json
from pathlib import Path

ROOT = Path('D:/MAESTRO')
OUT = ROOT / 'log/20261022/strategy_rethink'


def main():
    schema = json.loads((OUT / 'SCHEMA_AUDIT.json').read_text())
    ids = schema['identifier_rows']
    groups = {'source': 0, 'later': 1}
    manifest = {'episodes': {}, 'scope': 'conditional_exposed_background',
                'seeds': [1729, 2718, 31415]}
    for phase, fold in groups.items():
        compounds = sorted({c for c, f in zip(ids['comp'], ids['fold']) if f == fold},
                           key=lambda c: hashlib.sha256(f'strategy-c4-split-v1:{c}'.encode()).hexdigest())
        assert len(compounds) >= 512
        manifest['episodes'][phase] = []
        for episode in range(8):
            chosen = compounds[episode * 64:(episode + 1) * 64]
            manifest['episodes'][phase].append({
                'id': f'{phase}_{episode}', 'fold': fold,
                'calibration': chosen[:16], 'development': chosen[16:32], 'evaluation': chosen[32:],
            })
    with (OUT / 'EPISODE_MANIFEST.json').open('x', encoding='utf-8') as handle:
        json.dump(manifest, handle, indent=2)
    print('Created 8 source and 8 later disjoint ID-only episodes.')


if __name__ == '__main__':
    main()
