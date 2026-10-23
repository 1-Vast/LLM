"""Build a compact report-only publication without changing original experiment records."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/research_progress'
STUDY = ROOT / 'log/20261023/evidence_portfolio_optimization'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write(path, obj):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=True) + '\n', encoding='utf-8', newline='\n')


def main():
    summaries = ['RESULTS.json', 'SIMPLE_CONTROL_RESULTS.json', 'COST_SENSITIVITY.json',
                 'NUMERIC_EVIDENCE_AUDIT.json', 'DELIVERY_VERIFICATION.json']
    evidence = {name: json.loads((STUDY / name).read_text(encoding='utf-8')) for name in summaries}
    write(OUT / 'EVIDENCE.json', evidence)
    reports = sorted(STUDY.glob('*.md')) + [ROOT / 'log/20261023/report_consolidation/RESEARCH_SUMMARY.md']
    inputs = reports + [STUDY / n for n in summaries] + [STUDY / 'FREEZE.json', STUDY / 'CHOICES_FREEZE.json']
    write(OUT / 'SOURCE_INDEX.json', {'scope': 'Original local reports and key results; not all originals are included in this compact upload',
          'sources': [{'path': p.relative_to(ROOT).as_posix(), 'bytes': p.stat().st_size,
                       'sha256': sha(p.read_bytes())} for p in inputs]})
    files = [OUT / n for n in ('README.md', 'EVIDENCE.json', 'SOURCE_INDEX.json')]
    write(OUT / 'PACKAGE.json', {'date': '2026-10-23', 'scope': 'Concise research reports and numeric evidence only',
          'raw_data_included': False, 'experimental_code_included': False,
          'files': [{'path': p.name, 'bytes': p.stat().st_size, 'sha256': sha(p.read_bytes())} for p in files]})
    files.append(OUT / 'PACKAGE.json')
    for p in files:
        content = p.read_text(encoding='utf-8')
        assert p.stat().st_size < 100_000
        assert not re.search(r'(?i)-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----|\bsk-[A-Za-z0-9_-]{20,}', content)
    for target in re.findall(r'\]\(([^)]+)\)', (OUT / 'README.md').read_text(encoding='utf-8')):
        assert '://' in target or (OUT / target).is_file(), target
    r = evidence['RESULTS.json']
    assert r['K'] == 5390 and r['SIDM_clusters'] == 78
    assert [r['summary'][a]['0.1']['repeat_positive'] for a in ('fixed', 'feedback', 'mix', 'direct')] == [675, 919, 830, 876]
    assert {x['planned_reads'] for x in r['summary'].values()} == {3234}
    assert evidence['SIMPLE_CONTROL_RESULTS.json']['summary']['gate_original']['0.1']['repeat_positive'] == 898
    assert evidence['DELIVERY_VERIFICATION.json']['pytest_exit_code'] == 0
    payload = [{'path': p.relative_to(ROOT).as_posix(), 'content': p.read_text(encoding='utf-8')} for p in files]
    write(Path(__file__).with_name('github_report_payload.json'), payload)
    receipt = {'files': len(files), 'bytes': sum(p.stat().st_size for p in files),
               'original_reports_indexed': len(reports), 'sources_indexed': len(inputs),
               'local_links': 'PASS', 'selected_numeric_consistency': 'PASS', 'basic_secret_patterns': 'PASS',
               'original_records_modified': False, 'payload_paths': [x['path'] for x in payload]}
    write(OUT / 'PRE_UPLOAD_VERIFICATION.json', receipt)
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
