"""Independently check final phase file bindings without rewriting evidence."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PHASE = ROOT / 'log/20261022/almanac_feedback_pilot'


def main():
    manifest = json.loads((PHASE / 'root/FINAL_BINDINGS.json').read_text())
    failed = []
    for rel, expected in manifest['bindings'].items():
        h = hashlib.sha256()
        with (ROOT / rel).open('rb') as f:
            for block in iter(lambda: f.read(1024 * 1024), b''):
                h.update(block)
        if h.hexdigest() != expected:
            failed.append(rel)
    assert not failed, failed
    result = {'status': 'PASS', 'files_verified': len(manifest['bindings']),
              'scope': 'final local phase bindings; not scientific model correctness or historical global provenance'}
    path = PHASE / 'root/FINAL_VERIFICATION.json'
    assert not path.exists()
    path.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
