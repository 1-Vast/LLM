"""Shorten current navigation; historical report bytes are already retained in log."""
import json
from pathlib import Path
import shutil
import os

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/report_consolidation'

if __name__ == '__main__':
    originals = OUT / 'original_entrypoints'
    originals.mkdir(exist_ok=True)
    for relative in ('log/README.md', 'log/20261023/PROGRESS_SUMMARY.md'):
        source = ROOT / relative
        target = originals / relative.replace('/', '__')
        if not target.exists():
            shutil.copyfile(source, target)
    studies = json.loads((ROOT / 'research/STUDIES.json').read_text(encoding='utf-8'))['studies']
    report = '''# MAESTRO research report

The current evidence supports bounded ordinary prediction, calibration and functional-feedback utility. A general transferable update mechanism and recursive improvement of the improvement strategy remain unestablished. World-model, agent, inherited-updater, joint and improved-improver contributions require separate fair comparisons.

The [consolidated scientific summary](../log/20261023/report_consolidation/RESEARCH_SUMMARY.md) distinguishes task-level positive results, scoped stops and data qualification. The [registered-study summary](../log/20261023/report_consolidation/LUNA_EARLY_SUMMARY.md) and [recent decision index](../log/20261023/report_consolidation/STUDY_INDEX.md) link to authoritative records, including later amendments.

Eight-drug BeatAML feedback improves ordinary covariance predictions on exposed development data. CDK composition gains have not established functional benefit. The CD14 source rationale failed its preset continuation gate. CellHealth membership qualification is complete, but no new predictive fit or RSI gain follows from it. Existing study-level stops remain binding within their stated scope.

Durable reports and key results live in `log/`; datasets, external sources and detailed numeric artifacts live in the appropriate `data/` subtree. Experimental code lives in `research/`, which is a disposable work area. Only validated implementations with an explicit promotion decision enter `src/` or `tools/`. See [storage policy](../log/STORAGE_POLICY.md) and [consolidation records](../log/20261023/report_consolidation/START.md).

The previous full report is retained in [log/research_records/REPORT.md](../log/research_records/REPORT.md). [EVIDENCE.md](EVIDENCE.md) is the compact evidence index; [STUDIES.json](STUDIES.json) remains the implementation registry. Cleanup changes storage and navigation, not scientific conclusions.
'''
    (ROOT / 'research/REPORT.md').write_text(report, encoding='utf-8')
    rows = ['# Research evidence index', '',
            'Durable study records are linked below. Later audits supersede earlier optimistic claims; consult the [reviewed summary](../log/20261023/report_consolidation/LUNA_EARLY_SUMMARY.md) for the reconciled conclusions.', '',
            '| Study | Registry status | Retained record |', '|---|---|---|']
    locations_file = OUT / 'ARCHIVE_LOCATIONS.json'
    locations = {r['original_research_path']: r['current_path'] for r in json.loads(locations_file.read_text(encoding='utf-8'))['records']} if locations_file.exists() else {}
    for study in studies:
        original = f"research/{study['path']}/{study['evidence']}"
        current = locations.get(original, f"log/research_records/{study['path']}/{study['evidence']}")
        link = os.path.relpath(ROOT / current, ROOT / 'research').replace('\\', '/')
        rows.append(f"| `{study['path']}` | {study['status']} | [record]({link}) |")
    rows.extend(['', 'Additional evidence:', '',
                 '- [Recent grouped conclusions](../log/20261023/report_consolidation/LUNA_RECENT_SUMMARY.md).',
                 '- [Every recent study root, including missing-final-report cases](../log/20261023/report_consolidation/STUDY_INDEX.md).',
                 '- [Previous full evidence register](../log/research_records/EVIDENCE.md), retained as historical context.',
                 '- [Code retirement and data migration records](../log/20261023/report_consolidation/START.md).',
                 '', 'Record/data preservation does not by itself reproduce a retired implementation or establish independent biological confirmation.'])
    (ROOT / 'research/EVIDENCE.md').write_text('\n'.join(rows) + '\n', encoding='utf-8')
    (ROOT / 'log/README.md').write_text('''# Research log

`log/` stores key research reports, result summaries, failures and decisions. Datasets and external source artifacts belong in the corresponding `data/` subtree; experimental code belongs in `research/`. See [storage policy](STORAGE_POLICY.md).

- [Current scientific summary](20261023/report_consolidation/RESEARCH_SUMMARY.md).
- [Registered-study summaries and amendments](20261023/report_consolidation/LUNA_EARLY_SUMMARY.md).
- [Recent grouped conclusions](20261023/report_consolidation/LUNA_RECENT_SUMMARY.md) and [complete decision index](20261023/report_consolidation/STUDY_INDEX.md).
- [Retained historical study reports](research_records/README.md).
- [Consolidation, code-retirement and data-location records](20261023/report_consolidation/START.md).

Original dated study decisions remain authoritative. Their scoped negative results and uncertainty are preserved. The full research objective remains active; this maintenance operation provides no new biological performance or RSI result.
''', encoding='utf-8')
    (ROOT / 'log/20261023/PROGRESS_SUMMARY.md').write_text('''# 2026-10-23 research progress

Read the [concise scientific synthesis](report_consolidation/RESEARCH_SUMMARY.md), [recent grouped summary](report_consolidation/LUNA_RECENT_SUMMARY.md) and [study decision index](report_consolidation/STUDY_INDEX.md). These replace repetitive entry-point prose while retaining original study decisions and later amendments.

Ordinary functional feedback is useful in some bounded tasks. No general update core or RSI success has been established. The latest CellHealth work qualifies identities and source structure; it does not establish predictive benefit. Datasets and source artifacts have separate `data/` locations recorded in the consolidation manifest.

The previous progress index is retained in [original entry points](report_consolidation/original_entrypoints/log__20261023__PROGRESS_SUMMARY.md).
''', encoding='utf-8')
    print(json.dumps({'registry_entries': len(studies), 'navigation_written': 4}))
