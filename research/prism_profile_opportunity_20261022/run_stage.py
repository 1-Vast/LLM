"""Write-once executions and freeze, never redirect an inventoried running log."""
import argparse
from datetime import datetime, timezone
import json
import subprocess
import sys
import time

from prepare import LOG, ROOT, sha, write


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=('tests', 'freeze', 'coverage'))
    stage = parser.parse_args().stage
    if stage == 'freeze':
        tests = json.loads((LOG / 'TEST_EXECUTION.json').read_text(encoding='utf-8'))
        assert tests['exit_code'] == 0
        paths = [LOG / name for name in ('PROTOCOL.md', 'MANIFEST.json', 'MANIFEST_v2.json', 'TEST_EXECUTION.json',
                  'ROOT_PROTOCOL_RESPONSE.md', 'advocate/INDEPENDENT.md', 'advocate/CROSS.md',
                  'skeptic/INDEPENDENT_PROTOCOL_REVIEW.md', 'skeptic/CROSS.md', 'skeptic/SYNTHETIC_TESTS.json',
                  'skeptic/PRE_RUN_BINDINGS.json', 'data/INDEPENDENT.md', 'data/CROSS.md', 'data/MANIFEST_COMPARISON.json')]
        paths += sorted((ROOT / 'research/prism_profile_opportunity_20261022').glob('*.py'))
        paths += [ROOT / 'log/20261022/update_value_qualification/data' / name for name in
                  ('PRISM_METADATA_QUALIFICATION.json', 'MANIFEST_GEOMETRY.json')]
        write(LOG / 'COVERAGE_FREEZE.json', {'utc': datetime.now(timezone.utc).isoformat(),
              'stage': 'BEFORE_REAL_FINITE_CONVERSION',
              'files': {path.relative_to(ROOT).as_posix(): sha(path) for path in paths}})
        print(json.dumps({'frozen_files': len(paths)}))
        return
    target = LOG / ('TEST_EXECUTION.json' if stage == 'tests' else 'COVERAGE_EXECUTION_01.json')
    assert not target.exists()
    script = 'test_coverage.py' if stage == 'tests' else 'coverage.py'
    start = time.perf_counter()
    process = subprocess.run([sys.executable, '-B', str(ROOT / 'research/prism_profile_opportunity_20261022' / script)],
                             cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
    result = {'utc': datetime.now(timezone.utc).isoformat(), 'exit_code': process.returncode,
              'elapsed_seconds': time.perf_counter() - start, 'stdout': process.stdout, 'stderr': process.stderr}
    write(target, result)
    print(json.dumps(result))
    if process.returncode:
        raise SystemExit(process.returncode)


if __name__ == '__main__':
    main()
