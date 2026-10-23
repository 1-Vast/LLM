"""Summarize only already-open HCT116 gate results and seal the report."""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json

ROOT = Path('D:/MAESTRO')
OUT = ROOT/'log/20261022/ptpc_update_opportunity/source'
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
for seal_name in ('PROTOCOL_SEAL.json', 'RESULT_SEAL.json'):
    for item in json.loads((OUT/seal_name).read_text(encoding='utf-8'))['files']:
        assert sha(ROOT/item['path']) == item['sha256']
result = json.loads((OUT/'LABEL_GATE_RESULT.json').read_text(encoding='utf-8'))
groups = json.loads((OUT/'HCT116_CONDITION_GROUPS.json').read_text(encoding='utf-8'))
assert sum(g['rows'] for g in groups) == result['all_HCT116']['rows']
assert len(groups) == result['condition_groups']
usable = [g for g in groups if g['strict_complete_candidate']]
classes = Counter(next(k for k in g['labels'] if k in ('0', '1')) for g in usable)
coverage = Counter(tuple(g['times']) for g in usable)
paired = [g for g in usable if set(g['times']) == {'6', '24'}]
paired_classes = Counter(next(k for k in g['labels'] if k in ('0', '1')) for g in paired)
assert not result['unknown_groups'] and not result['conflicting_groups']
assert result['controls_HCT116']['rows'] == result['all_HCT116']['labels']['missing']
strata = '\n'.join(f"| {'control' if s['control'] else 'drug'} | {s['time']} | {s['Rep'] or '(blank)'} | {s['rows']} | {s['labels'].get('0', 0)} | {s['labels'].get('1', 0)} | {s['labels'].get('missing', 0)} |" for s in result['strata'])
report = f'''# HCT116-only PTPC label qualification

Decision: recognized author-annotation encoding and usable development condition groups. This is a source/type/grouping gate, not a model experiment, efficacy assay authentication or positive innovation result.

The protocol and source_gate.py were hashed before values were accessed. PROTOCOL_SEAL SHA256: `{result['protocol_seal_sha256']}`. Exactly one local S8 workbook access followed. The prior identity-stage seal SHA256 is `{result['prior_seal_sha256']}`; all {result['prior_sealed_files_verified']} listed files rehashed unchanged. Archive SHA256: `{result['source_archive_sha256']}`. Member `{result['S8_member']}` SHA256: `{result['S8_member_sha256']}`. No source archive or earlier sealed artifact was changed.

## Actual HCT116 tokens and grouping

HCT116 has 1,289 metadata rows. Actual Efficacy values are shared-string `N` (1,195 rows), shared-string `Y` (69 rows), or an absent cell (25 rows). All missing cells are explicit controls; all 1,264 noncontrol rows have recognized Y/N labels. No other token or storage type occurred. The predeclared annotation encoding is N=0, Y=1. This does not establish a viability horizon, threshold, dose or clinical meaning.

Grouping all 6/24h and Rep rows by `(Cell_line, Pert_ID)` yields 603 conditions including one all-missing control condition and {len(usable)} complete-label noncontrol conditions: {classes['0']} N and {classes['1']} Y. There are no conflicting known-class groups, mixed-missing groups or unknown groups. Thus the 69 Y rows represent {classes['1']} condition annotations; they are not 69 independent functional measurements. The class imbalance is material for any later metric and split definition.

Time coverage among noncontrols: {dict(coverage)}. Requiring both molecular times would retain {len(paired)} conditions ({paired_classes['0']} N, {paired_classes['1']} Y). This coverage result is descriptive; no favorable subset is selected here. Keep the distinction between an all-condition annotation task and a paired-time state task in the next protocol.

| Kind | Actual hours | Rep | Rows | N | Y | Missing |
|---|---:|---|---:|---:|---:|---:|
{strata}

## Deduplication and later partition constraints

There are 1,242 distinct Sample_IDs and 47 technical-repeat rows; each of the 47 duplicated IDs occurs twice. Removing technical-repeat rows leaves 1,242 records, but these remain measurements across time and biological repeats, not independent outcome tasks. The result JSON separately lists the duplicated IDs and workbook row identities. One duplicated ID is a biorep+techrep pair; the others are blank-Rep+techrep. No many-to-many Sample_ID merge is permitted.

Use `(Cell_line, Pert_ID)` as the minimum indivisible later partition group and bind every 6/24h, plate and Rep row to it. If a subsequent chemical-identity audit finds multiple Pert_IDs for the same compound, merge those partition groups too. Treat technical repeats as replicate measurements of one sample; retain authenticated workbook row mapping before any aggregation. Biological repeats and two molecular times must not purchase additional functional labels or independent active-learning/RSI tasks. The measured function's actual replicate/assay independence is unknown.

Exclude explicit controls from supervised annotation training. For this HCT116 gate, all 602 noncontrol groups satisfy the prespecified complete/consistent-label rule; no unknown or inconsistent group needs removal. This does not authorize downstream split design based on test outcomes. Any later paired-time restriction or replicate aggregation must be frozen before state values are opened. With only {classes['1']} positive condition groups, use grouped splits and metrics that expose minority-class performance; a majority-label accuracy alone would be uninformative.

## Retained blindness and scientific limits

Cell_line was resolved before Efficacy. All 928 non-HCT116 rows were directly skipped before resolving their Efficacy cells: A375 216; NCI-H1975 249; NCI-H2170 255; Panc1005 208. Shared-string nodes were an in-memory lookup table only; no non-HCT116 label values were resolved or displayed. No protein worksheet or abundance was opened. HCT116 is development only; A375 remains selection-unopened; the other three backgrounds remain final-unopened.

The released target is author Efficacy. Its apparent Y/N format does not authenticate the PTNC assay contract for PTPC. Actual molecular/control times remain 6/24h while the Legend says controls were assigned 0h; do not recode them or claim a measured pretreatment baseline. No same-culture trajectory, early decision timing, prospective label-acquisition sequence, drug utility or RSI gain has been demonstrated. No API call, fit or search occurred. Stop at this gate; a separate frozen numerical protocol is required for further work.
'''
path = OUT/'LABEL_GATE_RESULT.md'
assert not path.exists()
path.write_text(report, encoding='utf-8')
files = [p for p in sorted(OUT.iterdir()) if p.is_file() and p.name != 'LABEL_GATE_SEAL.json']
files += [Path(__file__).resolve(), ROOT/'research/ptpc_update_opportunity_20261022/source_gate.py']
seal = OUT/'LABEL_GATE_SEAL.json'
assert not seal.exists()
seal.write_text(json.dumps(dict(created_utc=datetime.now(timezone.utc).isoformat(),
    files=[dict(path=str(p.relative_to(ROOT)), bytes=p.stat().st_size, sha256=sha(p)) for p in files]), indent=2), encoding='utf-8')
print(json.dumps(dict(report_sha256=sha(path), seal_sha256=sha(seal), files=len(files),
                     noncontrol_conditions=len(usable), condition_classes=dict(classes), paired_conditions=len(paired), paired_classes=dict(paired_classes)), indent=2))
