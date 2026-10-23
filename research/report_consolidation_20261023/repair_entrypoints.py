"""Repair active summary links using the recorded storage migration; preserve old reports."""
import json
import os
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/report_consolidation'

if __name__ == '__main__':
    moved = {}
    for name in ('DATA_MIGRATION_RECEIPT.json', 'DATA_MIGRATION_SUPPLEMENT_RECEIPT.json'):
        receipt = json.loads((OUT / name).read_text(encoding='utf-8-sig'))
        moved.update({r['old_path']: r['data_path'] for r in receipt['files']})
    pages = [ROOT / 'research/EVIDENCE.md', OUT / 'LUNA_EARLY_SUMMARY.md', OUT / 'STUDY_INDEX.md']
    fixes = []
    for page in pages:
        def replace(match):
            old = match[1]
            resolved = (page.parent / old).resolve()
            if resolved.exists():
                return match[0]
            key = resolved.relative_to(ROOT).as_posix()
            destination = moved.get(key)
            if old == '../log/20261022/mechanism_gap/root/DECISION.md':
                destination = 'log/20261022/mechanism_gap/root/DECISION.md'
            if not destination:
                return match[0]
            new = os.path.relpath(ROOT / destination, page.parent).replace('\\', '/')
            fixes.append({'page': page.relative_to(ROOT).as_posix(), 'old_target': old, 'new_target': new})
            return '](' + new + ')'
        text = page.read_text(encoding='utf-8')
        page.write_text(re.sub(r'\]\(([^\n)]+)\)', replace, text), encoding='utf-8')
    coverage = OUT / 'COVERAGE_EARLY.json'
    value = json.loads(coverage.read_text(encoding='utf-8-sig'))
    value['data_path_migration'] = 'DATA_MIGRATION_RECEIPT.json'
    value['moved_evidence_links'] = fixes
    coverage.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    (OUT / 'LINK_REPAIRS.json').write_text(json.dumps(fixes, indent=2), encoding='utf-8')
    print(json.dumps({'repaired_links': len(fixes)}))
