"""Local-only coordinate and control-column audit. Never parse treatment values."""
import base64
import collections
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import tarfile

HERE = Path(__file__).resolve().parent
EPISODE = HERE.parent.parent
ROOT = EPISODE / 'root'
selected = json.loads((ROOT / 'selected_archives.json').read_text())
metadata = {x['accession']: x for x in json.loads((ROOT / 'sources/encode_splicing_files.json').read_text())['@graph']}
bams = {x['@id']: x for x in json.loads((ROOT / 'sources/selected_input_bams.json').read_text())['@graph']}
header_records = {x['accession']: x for x in json.loads((ROOT / 'archive_headers.json').read_text())}
safe_control = {'IJC_SAMPLE_2', 'SJC_SAMPLE_2', 'IncLevel2', 'IncFormLen', 'SkipFormLen'}
safe_identity = {'ID', 'GeneID', 'geneSymbol', 'chr', 'strand', 'exonStart_0base', 'exonEnd',
                 'upstreamES', 'upstreamEE', 'downstreamES', 'downstreamEE',
                 'longExonStart_0base', 'longExonEnd', 'shortES', 'shortEE',
                 'flankingES', 'flankingEE', '1stExonStart_0base', '1stExonEnd',
                 '2ndExonStart_0base', '2ndExonEnd', 'riExonStart_0base', 'riExonEnd'}
sets = {}
result = {'scope': 'coordinates and control columns only; no treatment values converted or printed',
          'psi_rounding_tolerance': 0.0005000001, 'archives': []}

for item in selected:
    acc = item['accession']
    path = ROOT / 'sources' / (acc + '.tar.gz')
    meta = metadata[acc]
    digest = base64.b64encode(hashlib.md5(path.read_bytes()).digest()).decode()
    origins = [bams[x] for x in meta['derived_from']]
    kd = [x for x in origins if x['dataset'] == '/experiments/' + item['experiment'] + '/']
    control = [x for x in origins if x['dataset'] == '/experiments/' + item['possible_controls'] + '/']
    record = {'accession': acc, 'target': item['target_label'], 'cell': item['cell'],
              'md5_matches_cloud': digest == meta['cloud_metadata']['md5sum_base64'],
              'file_size_matches': path.stat().st_size == meta['cloud_metadata']['file_size'],
              'assembly': meta['assembly'], 'orientation_comment': meta['submitter_comment'],
              'two_kd_two_control_origins': len(kd) == len(control) == 2 and len(origins) == 4,
              'control_dataset_exact': all(x['dataset'] == '/experiments/' + item['possible_controls'] + '/' for x in control),
              'control_bam_accessions': [x['accession'] for x in control],
              'control_bam_advertised_biological_replicates': [x['biological_replicates'] for x in control],
              'origin_biosamples': [v for x in origins for v in x['origin_batches']], 'tables': []}
    with tarfile.open(path, 'r:gz') as archive:
        record['members_match_header_audit'] = archive.getnames() == header_records[acc]['members']
        prefix = item['aliases'].split('rMATS.', 1)[1].split('.MATS_output', 1)[0]
        record['member_prefix_matches_alias'] = all(m.name == prefix or m.name.startswith(prefix + '/') for m in archive.getmembers())
        for member in archive.getmembers():
            if not member.isfile() or not member.name.endswith('.MATS.JunctionCountOnly.txt'):
                continue
            event = Path(member.name).name.split('.')[0]
            reader = csv.reader(io.TextIOWrapper(archive.extractfile(member), encoding='utf-8'), delimiter='\t')
            header = next(reader)
            # Indices are selected before any row is consumed. Forbidden fields never enter a dict.
            indexes = [(i, name) for i, name in enumerate(header) if name in safe_identity | safe_control]
            first_count = header.index('IJC_SAMPLE_1')
            key_fields = [name for name in header[:first_count] if name not in {'ID', 'geneSymbol'}]
            assert all(name in safe_identity for name in key_fields), key_fields
            counters = collections.Counter()
            identities = collections.Counter()
            genes = set()
            eligible_keys, interior_keys = set(), set()
            lengths = collections.Counter()
            max_error = 0.0
            for raw in reader:
                row = {name: raw[i] for i, name in indexes}
                counters['rows'] += 1
                key = tuple(row[name] for name in key_fields)
                identities[key] += 1
                genes.add(row['GeneID'])
                try:
                    ilen, slen = float(row['IncFormLen']), float(row['SkipFormLen'])
                    lengths[(ilen, slen)] += 1
                    valid_lengths = math.isfinite(ilen) and math.isfinite(slen) and ilen > 0 and slen > 0
                    counters['valid_positive_form_lengths'] += valid_lengths
                    vectors = [row[name].split(',') for name in ['IJC_SAMPLE_2', 'SJC_SAMPLE_2', 'IncLevel2']]
                    if [len(v) for v in vectors] != [2, 2, 2]:
                        counters['vector_length_not_two'] += 1
                        continue
                    counters['all_control_vectors_length_two'] += 1
                    ijc, sjc, psi = [[math.nan if v.lower() in {'na', 'nan', ''} else float(v)
                                      for v in vector] for vector in vectors]
                    count_valid = all(math.isfinite(v) and v >= 0 and v.is_integer() for v in ijc + sjc)
                    psi_valid = all(math.isfinite(v) and 0 <= v <= 1 for v in psi)
                    counters['finite_nonnegative_integer_control_counts'] += count_valid
                    counters['finite_control_psi_in_unit_interval'] += psi_valid
                    counters['rows_with_missing_or_nonfinite_control_psi'] += not all(math.isfinite(v) for v in psi)
                    coverage = count_valid and all(i + s >= 20 for i, s in zip(ijc, sjc))
                    counters['both_control_slots_coverage_ge20'] += coverage
                    if coverage and psi_valid and valid_lengths:
                        eligible_keys.add(key)
                        counters['eligible_rows'] += 1
                        if all(0.01 <= v <= 0.99 for v in psi):
                            interior_keys.add(key)
                            counters['eligible_rows_both_psi_interior'] += 1
                    if valid_lengths:
                        for i, s, p in zip(ijc, sjc, psi):
                            if not (math.isfinite(i) and math.isfinite(s) and i >= 0 and s >= 0):
                                continue
                            denom = i / ilen + s / slen
                            if denom > 0 and math.isfinite(p):
                                error = abs(p - (i / ilen) / denom)
                                max_error = max(max_error, error)
                                counters['psi_formula_comparable_slots'] += 1
                                counters['psi_formula_mismatch_slots'] += error > 0.0005000001
                            elif denom == 0:
                                counters['zero_denominator_slots'] += 1
                except ValueError:
                    counters['unparseable_control_or_length_rows'] += 1
            record['tables'].append({'event_type': event, 'member': member.name,
                'coordinate_key_fields': key_fields, 'unique_coordinate_gene_keys': len(identities),
                'unique_gene_ids': len(genes), 'duplicate_key_excess_rows': sum(v - 1 for v in identities.values()),
                'distinct_form_length_pairs': len(lengths), 'max_control_psi_formula_abs_error': max_error,
                'eligible_unique_keys': len(eligible_keys), 'interior_eligible_unique_keys': len(interior_keys),
                **dict(counters)})
            if event == 'SE':
                sets[(item['target_label'], item['cell'])] = (set(identities), eligible_keys, interior_keys)
    result['archives'].append(record)

result['cross_cell_coordinate_identity_counts'] = []
for target in sorted({x['target_label'] for x in selected}):
    h, k = sets[(target, 'HepG2')], sets[(target, 'K562')]
    result['cross_cell_coordinate_identity_counts'].append({'target': target,
        'SE_full_key_intersection': len(h[0] & k[0]),
        'SE_both_control_eligible_intersection': len(h[1] & k[1]),
        'SE_both_interior_eligible_intersection': len(h[2] & k[2])})
result['distinct_input_bams'] = len(bams)
result['distinct_input_origin_biosamples'] = len({v for x in bams.values() for v in x['origin_batches']})
(HERE / 'control_audit.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps({'archives': len(result['archives']), 'all_md5_match': all(x['md5_matches_cloud'] for x in result['archives']),
                  'SE_intersections': result['cross_cell_coordinate_identity_counts']}, indent=2))
