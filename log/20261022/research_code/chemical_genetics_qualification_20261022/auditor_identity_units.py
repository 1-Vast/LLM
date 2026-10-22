"""Post-freeze census of already authorized string identities, never source numbers."""
from collections import Counter
import json
import re

import auditor_identity_followup as worker


def norm(value):
    return re.sub(r'\s+', '', value).casefold()


def cells(sheet):
    return {c['coordinate']: c['text'] for c in sheet['string_cells'] if 'text' in c}


def main():
    out = worker.OUT
    projection_path = out / 'STRING_IDENTITIES.json'
    projected_hash = worker.base.sha(projection_path)
    records = json.loads(projection_path.read_text(encoding='utf-8'))
    books = {worker.base.Path(b['source_path']).name: b for b in records}
    screen = books[worker.base.TARGETS[0]]['sheets'][0]
    feedback = books[worker.base.TARGETS[1]]['sheets'][0]
    longitudinal = next(s for s in books[worker.EXTRA]['sheets'] if s['sheet_name'] == 'Fig.5a')
    s, f, l = cells(screen), cells(feedback), cells(longitudinal)
    genes = [v for c, v in s.items() if re.fullmatch(r'A(?:[2-9]|\d{2,})', c)]
    drug_axis = {c: v for c, v in s.items() if re.fullmatch(r'(?:[B-Z]|A[A-O])1', c)}
    pair_records = []
    incomplete = []
    for row in range(2, 235):
        if f'C{row}' not in f or f'D{row}' not in f:
            incomplete.append(row)
        else:
            pair_records.append({'row': row, 'evolved_drug': f[f'C{row}'].strip(), 'tested_drug': f[f'D{row}'].strip()})
    directed = {(norm(r['evolved_drug']), norm(r['tested_drug'])) for r in pair_records}
    undirected = {tuple(sorted(pair)) for pair in directed}
    tokens = {norm(v) for v in drug_axis.values()}
    unmatched_drugs = sorted({d for pair in directed for d in pair if d not in tokens})
    lineage_records = []
    for coord, value in l.items():
        if not re.fullmatch(r'B(?:[2-9]|\d{2,})', coord):
            continue
        match = re.fullmatch(r'Tetracycline (\d+)/Azithromycin/(\d+)', value.strip())
        if match is None:
            raise RuntimeError('unexpected_longitudinal_string_identity')
        row = int(coord[1:])
        lineage, day = map(int, match.groups())
        if l.get(f'C{row}', '').strip() != f'Tetracycline {lineage}' or l.get(f'D{row}', '').strip() != 'Azithromycin':
            raise RuntimeError('longitudinal_string_identity_conflict')
        lineage_records.append({'row': row, 'strain_id_coordinate': coord, 'strain_id': value,
            'selection_drug': 'Tetracycline', 'test_drug': 'Azithromycin',
            'lineage_from_string': lineage, 'day_from_string': day,
            'numeric_day_coordinate_not_read': f'E{row}',
            'function_coordinates_not_read': [f'F{row}', f'G{row}']})
    keys = [(r['lineage_from_string'], r['day_from_string']) for r in lineage_records]
    lineages = sorted({k[0] for k in keys})
    days = sorted({k[1] for k in keys})
    expected = {(a, b) for a in lineages for b in days}
    registry_path = worker.base.OUT.parent / 'ZENODO_MANIFEST.json'
    registry_hash = worker.base.sha(registry_path)
    registry = json.loads(registry_path.read_text(encoding='utf-8'))
    state_keys = []
    for entry in registry['files']:
        match = re.fullmatch(r'Tetracycline_lineage(\d+)_day(\d+)\.fastq', entry['key'])
        if match:
            state_keys.append(tuple(map(int, match.groups())))
    overlaps = sorted(set(keys) & set(state_keys))
    fig5d = next(s for s in books[worker.EXTRA]['sheets'] if s['sheet_name'] == 'Fig.5d')
    ko = cells(fig5d)
    result = {
        'scope': 'DESIGN_SCHEMA_EXPOSED_STRING_IDENTITIES_ONLY', 'http_requests': 0,
        'input_projection_sha256': projected_hash, 'registry_manifest_sha256': registry_hash,
        'screen': {'gene_header': s['A1'], 'gene_identity_scope': 'A2:A3905',
            'gene_identity_count': len(genes), 'unique_gene_identities': len(set(genes)),
            'all_ECK_identifiers': all(re.fullmatch(r'ECK\d+', g) is not None for g in genes),
            'drug_identity_count': len(drug_axis), 'drug_axis': drug_axis,
            'response_scope_not_read': 'B2:AO3905'},
        'pair_feedback': {'exact_identity_columns': {'C': f['C1'], 'D': f['D1']},
            'rows_with_both_drug_strings': len(pair_records), 'incomplete_rows': incomplete,
            'unique_directed_pairs_from_strings': len(directed), 'unique_undirected_pairs_from_strings': len(undirected),
            'unique_evolved_drugs': sorted({r['evolved_drug'] for r in pair_records}),
            'unique_tested_drugs': sorted({r['tested_drug'] for r in pair_records}),
            'screen_axis_unmatched_normalized_drug_names': unmatched_drugs,
            'note': 'Rows can repeat a directed pair. Pair number B and all numerical fields remain unread; author grouping strings are design exposed, not independent tasks or raw lineage IC90.'},
        'longitudinal': {'sheet': 'Fig.5a', 'string_rows': len(lineage_records),
            'lineages_from_strings': lineages, 'days_from_strings': days,
            'unique_lineage_day_keys': len(set(keys)), 'duplicate_key_count': len(keys) - len(set(keys)),
            'missing_observed_cartesian_keys': sorted(expected - set(keys)),
            'all_C_D_strings_match_B_identity': True,
            'numeric_day_column_value_check_performed': False,
            'records': lineage_records,
            'numeric_identity_census_candidate': {'scope': 'Fig.5a!E2:E61', 'purpose': 'Cross-check explicit Day column against day encoded in authorized B strings; no F/G outcome values.'},
            'biological_limit': 'One continuous tetracycline selection regime, 12 lineages and five string-labelled dates; 60 records are not 60 tasks. Azithromycin is the assay challenge, not an authenticated switch-treatment branch.'},
        'state_manifest_candidate_join': {'raw_WGS_filename_keys': len(state_keys), 'overlap_keys': len(overlaps),
            'overlap_lineage_day_keys': overlaps, 'state_keys_missing_from_function_strings': sorted(set(state_keys) - set(keys)),
            'status': 'NOMINAL_IDENTITY_JOIN_ONLY; raw reads not downloaded, no mutation state extracted, no physical sample equality certified by filenames alone.'},
        'knockout_function': {'sheet': 'Fig.5d', 'drug_column': 'A', 'knockout_column': 'B', 'response_column_not_read': 'C',
            'drug_string_counts': dict(Counter(v for c, v in ko.items() if re.fullmatch(r'A(?:[2-9]|\d{2,})', c))),
            'knockout_string_counts': dict(Counter(v for c, v in ko.items() if re.fullmatch(r'B(?:[2-9]|\d{2,})', c))),
            'replicate_id_column_present_in_literal_headers': False,
            'note': 'Repeated strings do not certify biological-versus-technical replicate identity; source uses gene symbols, while main screen uses ECK IDs.'},
        'claim_limits': ['No source response numbers, XR/CS/neutral categorical cells or performance statistics evaluated.',
            'MOESM7 I/J/K Yes/No cells are published qualitative outcomes (Validated/Bi-directional/Monochromatic), and were exposed. This is not sealed confirmation.',
            'General headers, other author grouping strings and identity selection are deliberately design/schema exposed.',
            'Fig.5a F1 is a generic resistance fold-change header. Its target drug is not assigned merely because G1 explicitly names azithromycin.',
            'No causal continuation branches, independent research tasks, inheritance gains or RSI improvement are established.']}
    base_ok = worker.base.sha(projection_path) == projected_hash and worker.base.sha(registry_path) == registry_hash
    source_checks = [{'path': b['source_path'], 'sha256_unchanged': worker.base.sha(b['source_path']) == b['source_sha256']} for b in records]
    result['verification'] = {'approved_json_and_registry_unchanged': base_ok, 'source_checks': source_checks,
        'helper_scope': 'Post-freeze helper only reads approved string JSON and previously qualified registry manifest, plus source hashes.'}
    worker.base.write_json(out / 'EXACT_IDENTITY_UNITS_CORRECTED.json', result)
    compact = {k: v for k, v in result.items() if k not in {'longitudinal', 'screen', 'verification'}}
    compact['screen'] = {k: v for k, v in result['screen'].items() if k != 'drug_axis'}
    compact['longitudinal'] = {k: v for k, v in result['longitudinal'].items() if k != 'records'}
    print(json.dumps(compact, ensure_ascii=False))
    return 0 if base_ok and all(c['sha256_unchanged'] for c in source_checks) else 1


if __name__ == '__main__':
    raise SystemExit(main())
