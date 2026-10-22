"""Write-once pre-open registration after code review and synthetic checks."""
from datetime import datetime, timezone
import json
from pathlib import Path

from prepare import LOG, ROOT, digest, write
from preserve import verify


def main():
    manifest = json.loads((LOG / 'MANIFEST.json').read_text(encoding='utf-8'))
    tests = json.loads((LOG / 'TEST_EXECUTION.json').read_text(encoding='utf-8'))
    assert tests['exit_code'] == 0
    assert tests['code_sha256'] == digest(Path(__file__).with_name('run_headroom.py'))
    prior = verify()
    assert prior['passed'] and len(prior['checks']) == 1340
    write(LOG / 'PREOPEN_PRESERVATION.json', prior)
    files = [LOG / 'PROTOCOL.md', LOG / 'PROTOCOL_DRAFT.md', LOG / 'MANIFEST.json', LOG / 'TEST_EXECUTION.json',
             LOG / 'review/DATA_MANIFEST_AUDIT.json', LOG / 'review/MECHANISM_FINAL_PREOPEN_REVIEW.json',
             Path(__file__), Path(__file__).with_name('prepare.py'), Path(__file__).with_name('run_headroom.py'),
             Path(__file__).with_name('test_headroom.py')]
    files += [ROOT / relative for relative in manifest['inputs_sha256']]
    files += [Path(__file__).with_name('data_independent_conversion.py'),
              LOG / 'review/DATA_CONVERSION_AUDIT_PROTOCOL.md',
              LOG / 'review/DATA_CONVERSION_SYNTHETIC_TESTS.md']
    review = json.loads((LOG / 'review/MECHANISM_FINAL_PREOPEN_REVIEW.json').read_text(encoding='utf-8'))
    assert review['passed'] and review['code_sha256'] == digest(Path(__file__).with_name('run_headroom.py'))
    write(LOG / 'FREEZE.json', {'utc': datetime.now(timezone.utc).isoformat(),
          'status': 'FROZEN_BEFORE_RAW_FUNCTIONAL_ACCESS', 'raw_permission': 'source/development treatment rows only',
          'later_numeric_permission': False, 'controls_numeric_permission': False,
          'sha256': {path.relative_to(ROOT).as_posix(): digest(path) for path in sorted(set(files))}})
    print(json.dumps({'status': 'FROZEN_BEFORE_RAW_FUNCTIONAL_ACCESS', 'files': len(set(files)),
                      'source_dev_assay_values': 372, 'later_values_permitted': 0}))


if __name__ == '__main__':
    main()
