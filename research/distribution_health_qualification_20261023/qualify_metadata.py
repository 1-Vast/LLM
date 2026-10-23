"""Audit official condition IDs and counts without decoding functional response values."""
from collections import Counter
import csv
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/distribution_health_qualification'
SOURCE = ROOT / 'data/external/research_sources/20261023/distribution_health_qualification/source'
LOG_SOURCE = OUT / 'source'


def records(name, sep='\t'):
    with (SOURCE / (name + '.body')).open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle, delimiter=sep))


if __name__ == '__main__':
    rows = records('all_metadata')
    condition_cols = ('Metadata_gene_name', 'Metadata_pert_name', 'Metadata_cell_line')
    groups = {}
    for row in rows:
        key = tuple(row[c] for c in condition_cols)
        groups.setdefault(key, []).append(row)
    mapping = records('profile_id_mapping')
    mapped_pairs = [(r['Metadata_cell_line'], r['Metadata_pert_name']) for r in mapping]
    observed_pairs = {(key[2], key[1]) for key in groups}
    guide_genes = {}
    for gene, guide, line in groups:
        guide_genes.setdefault(guide, set()).add(gene)
    fields = ('n_measurements_paint', 'n_measurements_health')
    inconsistent = [key for key, group in groups.items()
                    if any(len({r[c] for r in group}) != 1 for c in fields)]
    genes = sorted({key[0] for key in groups})
    targets = records('target_mapping', ',')
    dead = [r for r in targets if r['id'] == 'vb_percent_dead']
    plate_rows = records('es2_platemap', ',')
    plate_keys = [r['well_position'] for r in plate_rows]
    image_result = json.loads((LOG_SOURCE / 'remote_image_metadata/RESULT.json').read_text(encoding='utf-8'))
    image_rows = image_result['metadata_rows']
    image_keys = [r[1] for r in image_rows]
    idr_plate_rows = [r for r in records('idr_target_metadata', ',')
                      if r['Plate'].split('__')[0] == 'SQ00014613']
    idr_wells = {}
    for row in idr_plate_rows:
        well = re.sub(r'^(\D+)(\d+)$', lambda m: m[1] + m[2].zfill(2), row['Well'])
        idr_wells.setdefault(well, []).append(row)
    empty_wells = [r['well_position'] for r in plate_rows if r['pert_name'] == 'EMPTY']
    empty_mismatches = [well for well in empty_wells
                        if well not in idr_wells or any(
                            r['Reagent Identifier'] or r['Control Type'] != 'no reagent'
                            for r in idr_wells[well])]
    reagent_mismatches = [r['well_position'] for r in plate_rows if r['pert_name'] != 'EMPTY'
                          and (r['well_position'] not in idr_wells or any(
                              x['Reagent Identifier'] != r['pert_name']
                              for x in idr_wells[r['well_position']]))]
    files = json.loads((SOURCE / 'figshare.body').read_text(encoding='utf-8'))['files']
    tree = json.loads((SOURCE / 'repo_tree.body').read_text(encoding='utf-8'))
    blobs = {r['path']: r['sha'] for r in tree['tree'] if r['type'] == 'blob'}
    paths = {
        'download_readme': '0.download-data/README.md',
        'generate_profiles': '1.generate-profiles/generate_profiles.py',
        'normalize_labels': '1.generate-profiles/scripts/nbconverted/1.normalize-labels.py',
        'process_labels': '1.generate-profiles/scripts/nbconverted/0.process-labels.py',
        'plate_map': '1.generate-profiles/data/metadata/barcode_platemap.csv',
        'author_download': '0.download-data/download.py',
        'all_metadata': '1.generate-profiles/results/all_profile_metadata.tsv',
        'profile_id_mapping': '1.generate-profiles/data/profile_id_metadata_mapping.tsv',
        'target_mapping': '1.generate-profiles/data/labels/feature_mapping_annotated.csv',
        'consensus_code': '1.generate-profiles/scripts/nbconverted/2.build-consensus-signatures.py',
        'es2_platemap': '1.generate-profiles/data/metadata/platemap/DEPENDENCIES1_ES2.csv',
        'perturbation_details': '1.generate-profiles/tables/supplementary_table_1_perturbation_details.tsv',
        'idr_target_metadata': '0.download-data/IDR/updated_idr0080-screenA-library.csv'}
    blob_checks = {}
    for name, path in paths.items():
        body = (SOURCE / (name + '.body')).read_bytes()
        blob = hashlib.sha1(f'blob {len(body)}\0'.encode() + body).hexdigest()
        blob_checks[name] = blob == blobs[path]
    result = {
        'scope': 'Metadata counts and source-byte consistency, not health truth/assay completeness',
        'metadata_rows': len(rows),
        'distinct_full_rows': len({tuple(sorted(r.items())) for r in rows}),
        'distinct_conditions': len(groups),
        'conditions_per_line': dict(Counter(k[2] for k in groups)),
        'distinct_genes_including_controls': len(genes), 'gene_names': genes,
        'distinct_guides_including_controls': len(guide_genes),
        'guide_gene_ambiguities': {g: sorted(s) for g, s in guide_genes.items() if len(s) != 1},
        'condition_internal_count_inconsistencies': len(inconsistent),
        'paint_count_distribution_over_conditions': dict(Counter(v[0]['n_measurements_paint'] for v in groups.values())),
        'health_count_distribution_over_conditions': dict(Counter(v[0]['n_measurements_health'] for v in groups.values())),
        'profile_mapping_rows': len(mapping),
        'profile_mapping_unique_id': len({r['Metadata_profile_id'] for r in mapping}) == len(mapping),
        'profile_mapping_unique_condition': len(set(mapped_pairs)) == len(mapped_pairs),
        'mapping_condition_sets_equal': set(mapped_pairs) == observed_pairs,
        'primary_target_metadata': dead,
        'remote_es2_plate_join': {
            'plate': 'SQ00014613', 'platemap_rows': len(plate_rows),
            'platemap_unique_well': len(set(plate_keys)) == len(plate_keys),
            'image_unique_well': len(set(image_keys)) == len(image_keys),
            'well_sets_equal': set(plate_keys) == set(image_keys),
            'image_plates': sorted({r[0] for r in image_rows}),
            'images_per_well_distribution': dict(Counter(r[2] for r in image_rows)),
            'total_images': sum(r[2] for r in image_rows),
            'nonmodal_image_wells': [r for r in image_rows if r[2] != 9]},
        'idr_es2_mapping': {
            'source_rows': len(idr_plate_rows),
            'acquisition_labels': sorted({r['Plate'] for r in idr_plate_rows}),
            'distinct_wells': len(idr_wells),
            'well_set_matches_platemap': set(idr_wells) == set(plate_keys),
            'rows_per_well': dict(Counter(len(v) for v in idr_wells.values())),
            'empty_well_count': len(empty_wells), 'empty_mapping_mismatches': empty_mismatches,
            'nonempty_reagent_mapping_mismatches': reagent_mismatches},
        'figshare_file_count': len(files), 'figshare_total_bytes': sum(f['size'] for f in files),
        'figshare_smallest_bytes': min(f['size'] for f in files),
        'github_tree_sha': tree['sha'], 'github_tree_truncated': tree['truncated'],
        'downloaded_bodies_match_tree_blobs': blob_checks}
    (OUT / 'METADATA_QUALIFICATION.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
