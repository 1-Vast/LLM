"""Freeze the completed skeptic API/cross role before the separate numerical phase."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / 'log/20261022/api_evidence_innovation/skeptic'


def main():
    files = {}
    for path in sorted(LOG.iterdir()):
        if path.is_file():
            files[path.name] = {'bytes': path.stat().st_size,
                                'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    payload = {'utc': datetime.now(timezone.utc).isoformat(), 'status': 'ROLE_SEALED',
               'files': files, 'logical_provider_calls': 1, 'provider_reported_tokens': 16775,
               'new_http': 0, 'new_biological_numerical_conversion': 0, 'new_fits': 0,
               'generated_code_executed': False,
               'decision': 'Conditional GO only to separately frozen source/dev functional headroom; no new core promoted.'}
    with (LOG / 'ROLE_FINAL.json').open('x', encoding='utf-8') as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'status': payload['status'], 'inventoried_files': len(files),
                      'independent_sha256': files['INDEPENDENT.md']['sha256'],
                      'cross_sha256': files['CROSS.md']['sha256']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
