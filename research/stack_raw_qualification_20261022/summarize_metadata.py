"""Metadata-only overlap/collision diagnostics from already projected identities."""
from collections import defaultdict
import json

from inspect_identities import LOG, row_values


def main():
    projection = json.loads((LOG / 'IDENTITY_PROJECTION.json').read_text(encoding='utf-8'))
    library = row_values(projection['files'][0]['cells'])
    rows = {row: fields for row, fields in library.items() if row > 1 and fields.get('B')}
    collisions = {}
    for column, label in [('A', 'catalog'), ('F', 'CAS'), ('K', 'exact_SMILES')]:
        mapping = defaultdict(list)
        for row, fields in rows.items():
            literal = fields.get(column)
            if literal and literal not in {'N/A', '#N/A', 'NA', 'None'}:
                mapping[literal].append({'row': row, 'compound': fields['B']})
        collisions[label] = {'nonempty_metadata_rows': sum(map(len, mapping.values())),
                             'unique_literals': len(mapping),
                             'duplicate_literals': {key: value for key, value in mapping.items() if len(value) > 1}}
    screens = []
    for item in projection['files'][1:]:
        identity_rows = row_values(item['cells'])
        names = {fields['A']: row for row, fields in identity_rows.items() if row > 1 and fields.get('A')}
        screens.append({'filename': item['filename'], 'name_to_row': names})
    pairs = []
    for i, first in enumerate(screens):
        for second in screens[i+1:]:
            names1, names2 = set(first['name_to_row']), set(second['name_to_row'])
            pairs.append({'screens': [first['filename'], second['filename']],
                          'common_exact_names': len(names1 & names2),
                          'first_only': sorted(names1 - names2), 'second_only': sorted(names2 - names1)})
    report = {'library_compound_rows': len(rows), 'metadata_collisions': collisions,
              'cross_screen_exact_name_overlap': pairs, 'response_values_read': 0,
              'chemical_canonicalization_or_alias_merge_performed': False,
              'claim_scope': 'Exact records and identifier collisions, not distinct molecular entities or run identities'}
    with (LOG / 'METADATA_COLLISIONS.json').open('x', encoding='utf-8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'library_rows': len(rows), 'duplicates': {
        label: {'literal_groups': len(info['duplicate_literals']),
                'affected_rows': sum(map(len, info['duplicate_literals'].values()))}
        for label, info in collisions.items()}, 'cross_screen_overlap': pairs}, ensure_ascii=False))


if __name__ == '__main__':
    main()
