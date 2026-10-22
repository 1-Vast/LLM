"""Postchecks of saved stage2 identities; never opens the workbook."""
from collections import Counter, defaultdict
from itertools import combinations
import json

import ap1_identity_stage1 as first


def main():
    source = first.OUT / 'STAGE2_IDENTITIES.json'
    saved = json.loads(source.read_text(encoding='utf-8'))
    cells = saved['sheets']['Figure 4e']['cells']
    matrix = []
    for row in [4, 5, 6, 54, 55, 56, 57, 58]:
        items = []
        for column in 'DEFGHI':
            coordinate = f'{column}{row}'
            cell = cells.get(coordinate)
            if cell is None:
                items.append({'coordinate': coordinate, 'type': 'outside_saved_scope', 'value_opened': False})
            else:
                item = {key: cell[key] for key in ['coordinate', 'type', 'value_opened']}
                if cell['value_opened']:
                    item['string_value'] = cell['value']
                items.append(item)
        matrix.append({'row': row, 'cells': items})
    first.write('STAGE2_4E_STRING_TYPE_MATRIX.json', {
        'utc': first.utc(), 'input_sha256': first.sha(source), 'workbook_read': False,
        'numeric_bodies_decoded': False, 'rows': matrix,
        'interpretation_correction': 'D5/D55 are lineageId. E4/E54 are generation; lineage1/lineage2 are phase labels. Zero intersection of (file_id,E generation) is not a lineage-pairing test.'})

    raw = saved['sheets']['Figure 3b']['cells']

    def value(column, row):
        item = raw[f'{column}{row}']
        if not item['value_opened']:
            raise ValueError('required_saved_identity_closed')
        return item['value']

    # Dataset and exp_id identify the published grouping; compare every other
    # approved identity field as a multiset and retain exp_id mappings separately.
    groups = defaultdict(Counter)
    exp = defaultdict(lambda: defaultdict(set))
    for row in range(3, 10869):
        dataset = value('T', row)
        key = tuple(value(column, row) for column in 'SCEFG')
        groups[dataset][key] += 1
        exp[dataset][value('S', row)].add(value('B', row))
    pairs = []
    for left, right in combinations(groups, 2):
        overlap = groups[left] & groups[right]
        pairs.append({'left': left, 'right': right,
                      'left_rows': sum(groups[left].values()), 'right_rows': sum(groups[right].values()),
                      'matching_full_identity_rows_with_multiplicity': sum(overlap.values()),
                      'exact_multiset_match': groups[left] == groups[right]})
    first.write('STAGE2_FIG3_FULL_TUPLE_POSTCHECK.json', {
        'utc': first.utc(), 'input_sha256': first.sha(source), 'workbook_read': False,
        'tuple_fields': ['sample_identifier', 'Id', 'XY', 'Z', 'Time_design_frame'],
        'comparison': 'lexical identity values, no normalization, multiset including multiplicity',
        'grouping_fields': ['dataset_identifier', 'exp_id'],
        'dataset_exp_id_by_sample': {dataset: {sample: sorted(ids) for sample, ids in by_sample.items()}
                                     for dataset, by_sample in exp.items()},
        'groups': {dataset: {'rows': sum(counts.values()), 'distinct_full_identity_tuples': len(counts),
                             'duplicate_full_identity_rows_within_dataset': sum(counts.values()) - len(counts)}
                   for dataset, counts in groups.items()},
        'all_pair_comparisons': pairs,
        'limits': ['Identity-tuple reuse is evidence about published row identity, not proof that biological outcomes are duplicated.',
                   'Different dataset/exp_id labels may encode groupings of the same annotations; no deduplication or independent-run count is inferred.']})
    print(json.dumps({'header_matrix': matrix,
                      'exact_identity_multiset_pairs': [pair for pair in pairs if pair['exact_multiset_match']],
                      'nonzero_overlap_pairs': sum(pair['matching_full_identity_rows_with_multiplicity'] > 0 for pair in pairs)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
