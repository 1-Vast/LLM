"""Inspect selected identity metadata only; never emit reagent sequences or health values."""
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'data/external/research_sources/20261023/distribution_health_qualification/source'
OUT = ROOT / 'log/20261023/distribution_health_qualification/biology'

def selected_rows(name, fields, delimiter=','):
    with (SOURCE / name).open(encoding='utf-8-sig', newline='') as handle:
        return [{key: row[key] for key in fields} for row in csv.DictReader(handle, delimiter=delimiter)]

idr = selected_rows('idr_target_metadata.body', ['Plate', 'Well', 'Characteristics [Cell Line]', 'Reagent Identifier', 'Gene Identifier', 'Gene Symbol', 'Control Type'])
source = selected_rows('all_metadata.body', ['Metadata_gene_name', 'Metadata_pert_name', 'Metadata_cell_line', 'Metadata_Plate'], '\t')
guides = defaultdict(lambda: {'ids': set(), 'symbols': set(), 'controls': set(), 'lines': set()})
for row in idr:
    entry = guides[row['Reagent Identifier']]
    for target, key in [('ids', 'Gene Identifier'), ('symbols', 'Gene Symbol'), ('controls', 'Control Type'), ('lines', 'Characteristics [Cell Line]')]:
        if row[key]:
            entry[target].add(row[key])

source_guides = sorted({row['Metadata_pert_name'] for row in source})
resolved, unresolved, controls, absent = {}, {}, {}, []
for guide in source_guides:
    if guide not in guides:
        absent.append(guide)
        continue
    record = {key: sorted(value) for key, value in guides[guide].items()}
    if record['controls']:
        controls[guide] = record
    elif len(record['ids']) == 1:
        resolved[guide] = record
    else:
        unresolved[guide] = record

id_symbols = defaultdict(set)
for record in resolved.values():
    id_symbols[record['ids'][0]].update(record['symbols'])

result = {
    'scope': 'selected metadata identity fields only; no sequence output, no target values',
    'source_sha256': {name: hashlib.sha256((SOURCE / name).read_bytes()).hexdigest() for name in ['idr_target_metadata.body', 'all_metadata.body']},
    'idr_row_count': len(idr),
    'idr_distinct_plate_labels': len({row['Plate'] for row in idr}),
    'idr_lines': sorted({row['Characteristics [Cell Line]'] for row in idr}),
    'idr_control_row_counts': dict(Counter(row['Control Type'] for row in idr)),
    'source_row_count': len(source),
    'source_distinct_selected_metadata_rows': len({tuple(row.values()) for row in source}),
    'source_distinct_guide_line_conditions': len({(row['Metadata_pert_name'], row['Metadata_cell_line']) for row in source}),
    'source_distinct_gene_strings': len({row['Metadata_gene_name'] for row in source}),
    'source_guide_count': len(source_guides),
    'source_guides_resolved_by_single_id_count': len(resolved),
    'source_resolved_gene_id_count': len({record['ids'][0] for record in resolved.values()}),
    'source_resolved_id_multiple_symbols': {key: sorted(value) for key, value in id_symbols.items() if len(value) > 1},
    'source_unresolved_noncontrol_guides': unresolved,
    'source_control_guides': controls,
    'source_guides_absent_from_idr_reagent_ids': absent,
    'braf_source_identity': {guide: resolved[guide] for guide in ['BRAF1-1', 'BRAF-2'] if guide in resolved},
}
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'IDENTITY_AUDIT.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps({key: result[key] for key in ['idr_row_count', 'idr_distinct_plate_labels', 'source_row_count', 'source_distinct_guide_line_conditions', 'source_distinct_gene_strings', 'source_guide_count', 'source_guides_resolved_by_single_id_count', 'source_resolved_gene_id_count', 'source_resolved_id_multiple_symbols', 'source_unresolved_noncontrol_guides', 'source_guides_absent_from_idr_reagent_ids']}, indent=2))
