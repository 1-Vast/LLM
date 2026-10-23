"""Delivery checks for this study's reports and research-code syntax; no outcome reads."""
import ast
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
LOG = ROOT / 'log/20261023/evidence_portfolio_optimization'


def main():
    parsed = []
    for base in (HERE, ROOT / 'research/certified_discovery_gates_20261023'):
        for path in sorted(base.glob('*.py')):
            ast.parse(path.read_text(encoding='utf-8-sig'), filename=str(path))
            parsed.append(str(path.relative_to(ROOT)))
    missing, links = [], 0
    for path in sorted(LOG.glob('*.md')):
        for target in re.findall(r'\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
            if '://' in target or target.startswith('#'):
                continue
            links += 1
            if not (path.parent / target.split('#')[0]).exists():
                missing.append({'file': path.name, 'target': target})
    test = subprocess.run([sys.executable, '-B', '-m', 'pytest', str(HERE), '-o', 'addopts=',
                           '-q', '-p', 'no:cacheprovider'], cwd=ROOT, capture_output=True, text=True)
    bulk = [p.name for p in LOG.iterdir() if p.suffix.lower() in {'.npz', '.npy', '.csv', '.pdf', '.html', '.zip'}]
    report = {'scope': 'source syntax, local report links, lightweight regression/integration tests and storage',
              'parsed_research_files': parsed, 'local_links_checked': links, 'missing_links': missing,
              'misplaced_bulk_artifacts': bulk, 'pytest_exit_code': test.returncode,
              'pytest_stdout': test.stdout, 'pytest_stderr': test.stderr,
              'full_gate0_gate1_campaign_run': False, 'scientific_certification': False}
    (LOG / 'DELIVERY_VERIFICATION.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return int(bool(missing or bulk or test.returncode))


if __name__ == '__main__':
    raise SystemExit(main())
