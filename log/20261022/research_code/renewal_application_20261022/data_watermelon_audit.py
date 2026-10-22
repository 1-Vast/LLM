"""Independent named-field check; never access response, clone or barcode fields."""
from collections import Counter, defaultdict
import csv
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = ROOT / 'log/20261022/renewal_application/root_sources'
OUT = ROOT / 'log/20261022/renewal_application/data/WATERMELON_DESIGN_AUDIT.json'
SPECS = [
    ('GSE150949_metaData_with_lineage_txt_gz.body', '\t', True,
     ['nGene', 'nUMI', 'orig.ident', 'percent.mito', 'sample_id', 'time_point',
      'sample_name', 'sample_type', 'full_cell_barcode', 'lineage_barcode', 'clone_size'],
     ['orig.ident', 'sample_id', 'time_point', 'sample_name', 'sample_type']),
    ('GSE150949_pooled_watermelon_metadata_matrix_csv_gz.body', ',', False,
     ['cell', 'orig.ident', 'nCount_RNA', 'nFeature_RNA', 'sample_id', 'sample_type',
      'sample_pool', 'percent.mt', 'cell_line', 'droplet.type', 'best.LLK', 'experiment'],
     ['orig.ident', 'sample_id', 'sample_type', 'sample_pool', 'cell_line', 'droplet.type', 'experiment'])]


def main():
    assert not OUT.exists()
    reference_path = SOURCE_DIR / 'WATERMELON_DESIGN_RESULT.json'
    reference = json.loads(reference_path.read_text(encoding='utf-8'))
    results = []
    for filename, delimiter, rowname, expected_header, allowed in SPECS:
        source = SOURCE_DIR / filename
        counts = Counter()
        with gzip.open(source, 'rt', encoding='utf-8-sig', newline='') as stream:
            header = next(csv.reader(stream, delimiter=delimiter))
            assert header == expected_header
            columns = (['__ignored_rowname__'] if rowname else []) + header
            reader = csv.DictReader(stream, fieldnames=columns, delimiter=delimiter)
            for row in reader:
                assert None not in row and all(row[key] is not None for key in allowed)
                counts[tuple(row[key] for key in allowed)] += 1
        actual = [dict(zip(allowed, key), captured_rows=count)
                  for key, count in sorted(counts.items())]
        ref = next(item for item in reference if item['file'] == filename)
        assert actual == ref['design_tuples']
        assert sum(counts.values()) == ref['rows']
        result = {'file': filename, 'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                  'header': header, 'explicit_ignored_rowname': rowname,
                  'whitelist': allowed, 'tuple_count': len(counts),
                  'captured_row_count': sum(counts.values()), 'exact_root_tuple_count_match': True}
        if rowname:
            mapping = {}
            for key in counts:
                record = dict(zip(allowed, key))
                sample = record.pop('sample_id')
                assert sample not in mapping or mapping[sample] == record
                mapping[sample] = record
            assert set(mapping) == {str(i) for i in range(1, 12)}
            gates = defaultdict(set)
            for record in mapping.values():
                name = record['sample_name']
                if record['time_point'] == '14':
                    _, rep, gate = name.split('_')
                    assert record['sample_type'] == '14_' + gate
                    gates[rep].add(gate)
            assert dict(gates) == {'rep1': {'low', 'med', 'high'},
                                  'rep2': {'low', 'med', 'high'}}
            result['sample_design_mapping'] = mapping
            result['day14_gate_identity_complete_for_named_replicates'] = True
            result['lineage_values_opened'] = False
            result['raw_gate_weighted_clone_target_reconstructable_from_design_alone'] = False
        else:
            roles = defaultdict(set)
            pools = defaultdict(set)
            for key in counts:
                record = dict(zip(allowed, key))
                roles[(record['experiment'], record['cell_line'])].add(record['sample_type'])
                pools[record['sample_id']].add((record['experiment'], record['sample_pool'], record['sample_type']))
            assert all(len(values) == 1 for values in pools.values())
            result['experiment_line_role_identity'] = [
                {'experiment': key[0], 'cell_line': key[1], 'observed_roles': sorted(values)}
                for key, values in sorted(roles.items())]
            result['sample_pool_mapping'] = {key: list(next(iter(values)))
                                             for key, values in sorted(pools.items())}
            result['unique_cell_line_labels'] = sorted({key[1] for key in roles})
            result['no_lineage_barcode_column_in_released_header'] = True
        results.append(result)
    record = {'status': 'PASS_DESIGN_PARSER_ONLY', 'checks': results,
              'reference_sha256': hashlib.sha256(reference_path.read_bytes()).hexdigest(),
              'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'protocol_sha256': hashlib.sha256((OUT.parent / 'WATERMELON_DESIGN_AUDIT_PROTOCOL.md').read_bytes()).hexdigest(),
              'limitations': ['No biological outcome, expression, clone_size or barcode interpreted',
                              'No population weights, absolute denominator, survival or clone growth inferred',
                              'Raw future-gate target requires separate authorized lineage projection and per-replicate weights',
                              'No HTTP, model fit, provider or reserve access']}
    OUT.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(record, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
