"""Identity-only counts and joins from the saved exact-scope stage2 JSON."""
from collections import Counter, defaultdict
import json

import ap1_identity_stage1 as first


def main():
    source = first.OUT/'STAGE2_IDENTITIES.json'
    result = json.loads(source.read_text(encoding='utf-8'))
    sheets = result['sheets']
    field_counts = {}
    for name, sheet in sheets.items():
        grouped = defaultdict(list)
        for item in sheet['cells'].values():
            if item['value_opened']:
                grouped[item['field']].append(item['value'])
        field_counts[name] = {field: {'opened': len(values), 'unique': len(set(values)),
                                     'value_counts': dict(Counter(values)) if len(set(values)) <= 40 else None}
                              for field, values in grouped.items()}

    def value(sheet, coordinate):
        return sheets[sheet]['cells'].get(coordinate, {}).get('value')

    raw_groups = Counter((value('Figure 3b', f'B{r}'), value('Figure 3b', f'S{r}'), value('Figure 3b', f'T{r}')) for r in range(3, 10869))
    raw_pairs = {(group[2], group[1]) for group in raw_groups}
    summary_pairs = {(value('Figure 3b summary', f'D{r}'), value('Figure 3b summary', f'E{r}')) for r in range(5, 101)}
    normalize = lambda pair: tuple(v.replace('\u00a0', ' ') if isinstance(v, str) else v for v in pair)
    exp_datasets = defaultdict(set)
    for exp, sample, dataset in raw_groups:
        exp_datasets[exp].add(dataset)
    reporter = {}
    for name, last in [('Figure 5b', 241), ('Figure 5c', 226)]:
        keys = Counter(tuple(value(name, f'{c}{r}') for c in 'CDEF') for r in range(2, last+1))
        by_xy = defaultdict(set)
        for condition, xy, z, time in keys:
            by_xy[(condition, xy, z)].add(time)
        reporter[name] = {'rows': last-1, 'unique_condition_XY_Z_Time_keys': len(keys),
                          'duplicate_composite_key_rows': sum(n-1 for n in keys.values()),
                          'distinct_condition_XY_Z_groups': len(by_xy),
                          'time_counts_per_group': sorted(len(times) for times in by_xy.values()),
                          'not_independent_runs': True, 'persistent_object_identity_not_proven': True}
    paired = {}
    for label, rows in [('starting_cell_section', range(6, 54)), ('final_colony_section', range(56, 103))]:
        keys = Counter((value('Figure 4e', f'I{r}'), value('Figure 4e', f'E{r}')) for r in rows)
        paired[label] = {'rows': len(rows), 'keys': [{'file_id_string': key[0], 'lineage_or_generation_string': key[1], 'rows': n} for key, n in keys.items()]}
    first_keys = {(x['file_id_string'], x['lineage_or_generation_string']) for x in paired['starting_cell_section']['keys']}
    final_keys = {(x['file_id_string'], x['lineage_or_generation_string']) for x in paired['final_colony_section']['keys']}
    alignment_coordinates = [f'{c}{r}' for r in [4, 5, 6, 54, 55, 56, 57, 58] for c in 'DEFGHI']
    alignment_strings = {coordinate: value('Figure 4e', coordinate) for coordinate in alignment_coordinates
                         if value('Figure 4e', coordinate) is not None}
    identities = {'utc': first.utc(), 'status': 'IDENTITY_ONLY_QUALIFICATION_NO_RESPONSE_READ',
                  'input_sha256': first.sha(source), 'field_counts': field_counts,
                  'Figure3b_groups': [{'exp_id': g[0], 'sample_identifier': g[1], 'dataset_identifier': g[2], 'annotation_rows': count} for g, count in raw_groups.items()],
                  'exp_to_dataset_labels': {exp: sorted(values) for exp, values in exp_datasets.items()},
                  'raw_summary_pairs': {'raw_pairs': len(raw_pairs), 'summary_pairs': len(summary_pairs),
                                        'exact_match': raw_pairs == summary_pairs,
                                        'match_after_explicit_NBSP_to_ASCII_space': {normalize(p) for p in raw_pairs} == {normalize(p) for p in summary_pairs},
                                        'original_values_preserved': True},
                  'reporter_composites': reporter, 'Figure4e_string_alignment': alignment_strings,
                  'Figure4e_partial_keys': paired, 'Figure4e_shared_string_keys_count': len(first_keys & final_keys),
                  'limits': ['Counts are annotation/field/frame/source identities, not biological run counts.',
                             'Figure4e numeric generation/annotationID remains closed; file/label matches do not prove unique cell descendants.',
                             'No functional response or fluorescence/growth value used.']}
    first.write('STAGE2_IDENTITY_SUMMARY.json', identities)
    frozen = json.loads((first.OUT/'STAGE2_FREEZE.json').read_text(encoding='utf-8'))
    checks = [{'path': f['path'], 'unchanged': first.sha(f['path']) == f['sha256']} for f in frozen['files']]
    first.write('STAGE2_FINAL_CHECKS.json', {'utc': first.utc(), 'frozen_checks': checks,
                'all_frozen_unchanged': all(c['unchanged'] for c in checks),
                'source_sha256': first.sha(first.RAW), 'source_hash_matches': first.sha(first.RAW) == first.EXPECTED,
                'response_values_interpreted': False, 'numeric_identity_literals_permitted': True,
                'stage1_response_NA_exposure_retained': True, 'summary_code_sha256': first.sha(__file__), 'network_requests': 0})
    print(json.dumps({key: identities[key] for key in ['field_counts', 'exp_to_dataset_labels', 'raw_summary_pairs',
                      'reporter_composites', 'Figure4e_string_alignment', 'Figure4e_shared_string_keys_count']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
