"""Write a source-only admission interface, with unresolved bindings explicit."""
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

OUT = Path(__file__).parent
BASE = Path('D:/MAESTRO/data/external/conditional_interventions_20261030/egi')
projection = json.loads((OUT / 'identity_design_projection.json').read_text())

def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')

def flat(node):
    return ' '.join(''.join(node.itertext()).split())

article = ET.parse(BASE / '04_primary_fulltext.xml').getroot()
methods = {}
for sid in ['S18', 'S21', 'S23', 'S24', 'S31', 'S33']:
    sec = article.find(f'.//sec[@id="{sid}"]')
    methods[sid] = {'title': flat(sec.find('title')), 'paragraphs': [flat(p) for p in sec.findall('p')]}
code = {}
for name, cells in [('06_call_genetic_interactions.ipynb', [2, 3, 4, *range(6, 38)]), ('08_differential_analysis.ipynb', [2, 5, 7, 12, 13]), ('09_replicate_quality_control.ipynb', [2, 3, 5, 6])]:
    notebook = json.loads((BASE / name).read_text(encoding='utf-8'))
    code[name] = [{'cell': i, 'source': ''.join(notebook['cells'][i].get('source', []))} for i in cells]
save('methods_variable_projection.json', {'scope': 'Source text only; all notebook outputs excluded; growthScores values excluded', 'methods': methods, 'code_source': code})

identification = []
allowed_starts = ['Since ATRi-treated interactions reflect', 'To this end, we constructed a differential interaction matrix by subtracting', 'All three new GI maps were generated', 'We thus constructed two new dGI matrices representing']
for paragraph in article.iter('p'):
    text = flat(paragraph)
    for sentence in re.split(r'(?<=[.!?])\s+', text):
        if any(sentence.startswith(prefix) for prefix in allowed_starts):
            identification.append({'exact_source_sentence': sentence, 'supplement_xrefs_in_parent_paragraph': [{'rid': x.get('rid'), 'label': flat(x)} for x in paragraph.iter('xref') if x.get('rid', '').startswith('SD')]})
save('identification_projection.json', {'source': str(BASE / '04_primary_fulltext.xml'), 'source_sha256': next(x['sha256'] for x in projection['originals'] if x['file'] == '04_primary_fulltext.xml'), 'scope': 'Controlled object-identification sentences only; no response values/distributions', 'sentences': identification})

environment_rows = []
for native, batch, endpoint, reference, treatment, method in [
    ('dmso1_map', 'GI1', 'UT', None, 'DMSO vehicle, batch 1', 'S24.3'),
    ('atr_map', 'GI1', 'ATR', 'dmso1_map', '1.25 uM AZD6738 days 0 and 7; endpoint day 9', 'S24.3'),
    ('dmso2_map', 'GI2', 'UT', None, 'DMSO vehicle, batch 2', 'S24.4-S24.5'),
    ('etop_map', 'GI2', 'ETOP', 'dmso2_map', '500 nM etoposide day 0; washout at 24 h; repeat day 3; subsequent daily splitting without washout; endpoint day 9', 'S24.4'),
    ('keto_map', 'GI2', 'KETO', 'dmso2_map', 'RPMI without glucose days 0-9; endpoint day 9', 'S24.5'),
]:
    samples = [s for s in projection['sample_binding'] if s['batch'] == batch and s['geo_title'].endswith('_' + endpoint)]
    t0 = [s for s in projection['sample_binding'] if s['batch'] == batch and s['environment'] == 'T0']
    environment_rows.append({'native_variable': native, 'batch': batch, 'role': 'reference' if reference is None else 'environment', 'geo_arm': endpoint, 'matched_reference_variable': reference, 'count_file': samples[0]['count_file'], 'endpoint_columns': [s['count_column'] for s in samples], 'endpoint_geo_accessions': [s['geo_accession'] for s in samples], 'T0_columns': [s['count_column'] for s in t0], 'T0_geo_accessions': [s['geo_accession'] for s in t0], 'biological_replicates': [1, 2], 'T0_day': 0, 'endpoint_day': 9, 'T0_days_post_transduction': 7, 'treatment_schedule': treatment, 'source_method': method, 'code_source_cells': list(range(6, 11)), 'native_aggregation': 'Intersect passing constructs between two biological replicates; arithmetic mean normalized replicate phenotypes; AB/BA mean; query quadratic GI fit and NTC residual scaling; mean guide combinations to gene level', 'native_is_average_of_independently_fitted_replicate_GIs': False})

known = {4: ('Table S3', 'SD10', ['dmso1_map', 'atr_map']), 5: ('Table S4', 'SD12', ['dmso1_map', 'atr_map']), 6: ('Table S5', 'SD4', ['atr_map - dmso1_map']), 7: ('Table S6', 'SD11', ['dmso2_map', 'etop_map', 'keto_map']), 8: ('Table S7', 'SD9', ['dmso2_map', 'etop_map', 'keto_map']), 9: ('Table S8', 'SD3', ['dmso2_map', 'etop_map', 'keto_map']), 10: ('Table S9', 'SD5', ['etop_map - dmso2_map', 'keto_map - dmso2_map']), 11: ('Table S10', 'SD6', ['etop_map - dmso2_map', 'keto_map - dmso2_map'])}
matrices = []
for header in projection['matrix_headers']:
    mmc = int(header['member'].split('MMC')[1].split('.')[0])
    table, xref, candidates = known[mmc]
    matrices.append({'original_member': header['member'], 'original_member_sha256': header['sha256_member'], 'supplement_table': table, 'xml_xref': xref, 'exact_binding_status': 'EXACT' if mmc == 6 else 'UNRESOLVED_WITHIN_SOURCE_GROUP', 'exact_native_expression': candidates[0] if mmc == 6 else None, 'source_group_candidate_expressions': candidates, 'forbidden_resolution': 'Do not infer per-file identity by list order, timestamps, score distributions or numerical matrix matching before protocol admission', 'gene_axis_identities': 304, 'target_gene_identities': 303, 'NTC_identity': 'non-targeting', 'axis_order_equal': header['same_axis_order'], 'numerical_finiteness_or_symmetry_checked': False, 'replicate_field_present_in_axis_headers': False})
save('environment_binding.json', {'scope': 'Design/identity only; numerical access not authorized by this artifact', 'original_source': '04_primary_fulltext.xml', 'original_source_sha256': next(x['sha256'] for x in projection['originals'] if x['file'] == '04_primary_fulltext.xml'), 'controlled_identification_evidence': 'identification_projection.json', 'native_variable_environment_bindings': environment_rows, 'supplement_matrix_bindings': matrices, 'source_defined_differentials': {'atr_di_map': 'atr_map - dmso1_map', 'etop_di_map': 'etop_map - dmso2_map', 'keto_di_map': 'keto_map - dmso2_map'}, 'cross_batch_reference_comparison_is_environment': False, 'metadata_independent_cultures_per_environment': 2, 'shared_ancestry': ['GI1 Rep1/Rep2 T0 reused by matched UT and ATR arms', 'GI2 Rep1/Rep2 T0 and UT reused by matched ETOP and KETO arms'], 'missing_culture_metadata': ['No individual culture/transduction IDs beyond experiment and replicate labels', 'No proof that every treatment arm within one replicate ancestry is independent', 'No multi-timepoint post-intervention trajectory; T0 and day-9 endpoint only']})
with (OUT / 'environment_binding.tsv').open('w', newline='', encoding='utf-8') as stream:
    columns = ['original_member', 'supplement_table', 'xml_xref', 'exact_binding_status', 'exact_native_expression', 'source_group_candidate_expressions', 'gene_axis_identities', 'target_gene_identities', 'NTC_identity', 'original_member_sha256']
    writer = csv.DictWriter(stream, fieldnames=columns, delimiter='\t', extrasaction='ignore')
    writer.writeheader()
    writer.writerows([{**r, 'source_group_candidate_expressions': ' | '.join(r['source_group_candidate_expressions'])} for r in matrices])

contract = {
    'status': 'RAW_IDENTITY_DESIGN_ADMITTED; NATIVE_MATRIX_FILE_BINDING_PARTIAL; NO_NUMERICAL_ACCESS_OR_TEST_ADMISSION',
    'source_counts': [{k: c[k] for k in ['file', 'header', 'delimiter', 'unique_construct_identities', 'sorted_identity_sha256']} for c in projection['count_files']],
    'raw_structural_gene_pair_universe': {'target_gene_identities': 313, 'unordered_distinct_identity_pairs': 48828, 'is_valid_numerical_observation_count': False},
    'source_root': str(BASE),
    'source_original_manifest': 'identity_design_projection.json: originals',
    'sample_binding_file': 'sample_binding.tsv',
    'guide_identity_file': 'guide_identity.tsv',
    'guide_identity_columns': ['guide_identity', 'source_gene_label', 'analysis_gene_label', 'is_ntc', 'source_sequence'],
    'NTC_source_gene_label': 'negative',
    'NTC_guide_name_prefix': 'non-targeting_',
    'NTC_guides': projection['negative_guides'],
    'vector_orientation': {'ordered_construct_identity': 'name_a:name_b', 'a': 'first vector guide position', 'b': 'second vector guide position', 'AB_BA': 'same two guides in reverse vector positions', 'genomic_plus_minus': 'Guide name genomic strand marker; not vector orientation', 'keep_together_under_pair_split': True},
    'replication': {'method': 'S24.1: independent biological transduction and passaging in duplicate', 'independent_cultures_per_environment': 2, 'native_final_maps': 'Two normalized replicate phenotype vectors are intersected and averaged before fitting, not raw counts pooled and not replicate-GI maps averaged', 'per_rep_source_path': 'calling notebook cells 24-33; Rep1 phenotype generation commented; many writes commented; replicate_QC imports per-rep maps', 'clean_end_to_end_notebook_reproduction_verified': False, 'per_rep_derived_responses_possible_in_principle': True, 'per_rep_numeric_validity_or_reproducibility_verified': False, 'shared_controls': 'Preserve matched r and batch; ETOP and KETO share GI2 UT and T0; same pair guides/orientations and controls do not multiply biological replicate count'},
    'time': {'T0_days_post_transduction_for_GI_screens': 7, 'post_T0_endpoint_day': 9, 'post_intervention_timepoints': [0, 9], 'endpoint_is_growth_selection': True, 'continuous_time_dynamics_identified': False, 'treatment_schedules': {r['native_variable']: r['treatment_schedule'] for r in environment_rows}},
    'new_raw_endpoint_feasibility': {
        'status': 'Metadata support only; coordinator must freeze mathematical choices and access protocol before any calculation',
        'name': 'Per-replicate environmental double-vs-single differential enrichment contrast',
        'not_equivalent_to': ['published native standardized GI or native differential GI', 'death/survival/proliferation mechanism', 'continuous-time dynamics'],
        'symbolic_definition': {
            'p': 'Positive pseudocount fixed before numerical access; not chosen by auditor',
            'N': 'Exact 13 source NTC guide identities',
            'D_ab_e_r': 'log2((C_ab,e,r + p)/(C_ab,matched_UT,r + p))',
            'Q_ab_e_r': 'D_ab,e,r - mean[n in N](D_a:n,e,r) - mean[n in N](D_n:b,e,r) + mean[n,m in N](D_n:m,e,r)',
            'orientation_aggregation': '(Q_a:b + Q_b:a)/2 with fixed equal weights if both valid; missingness policy must be frozen',
            'gene_aggregation': 'Fixed identity-based average over admitted guide combinations; gene with one guide cannot be called two-guide replication',
            'T0_cancellation': 'This unscaled matched-environment count-log-ratio contrast equals the treated-minus-reference contrast of identically defined T0 log enrichments because the same r-specific T0 term cancels. It does not cancel after different culture-specific population-doubling divisors.',
            'depth_scale': 'Four contrast coefficients sum to zero, cancelling a condition-specific additive log-depth offset for exact log abundance. Pseudocount placement and count-depth effects must be specified.',
            'growth_doubling_scale': 'No per-doubling normalization in this symbolic alternative; if used, fixed original growthScores and separate C_e/C_UT to T0 terms define a different endpoint.'
        },
        'target_is_used_only_in_label': 'Held-out double-construct endpoint counts may construct the sealed response only; they must not fit query-wide baselines, features, imputation, scaling, filter tuning, pair selection or candidate decisions',
        'controls_and_singles': 'The NTC-NTC and gene-NTC constructs can define fixed labels/normalizers. If target-environment singles enter features, declare them as observed prediction-time measurements.',
        'native_label_coupling': 'Native calculateInteractions uses every paired phenotype involving each query to fit its quadratic; labels for development pairs can therefore depend on held-out pair phenotypes. Fixed published native labels may be evaluated only as a declared derived measurement object. They do not certify a strict withheld-raw-phenotype prediction.',
        'strict_alternative': 'A fixed algebraic local double-vs-single contrast requires no query-wide fit. A training-only native-style fit is possible but changes the native estimand and must be predeclared.',
        'preaccess_unresolved_choices': ['development/held-out environment(s)', 'unordered gene-pair split and complete guide/orientation grouping', 'pseudocount and its placement', 'NTC/control aggregation and any exclusion', 'count validity filters and fixed missingness policy', 'gene-guide aggregation weights', 'unscaled endpoint versus population-doubling scale', 'available prediction-time single/base-control information', 'replicate/noise/null/headroom and biological-effect/prioritization gates', 'ordinary baseline/candidate matrix and independent verification'],
        'no_claim_of_observed_valid_pairs': True
    },
    'remaining_gates': ['Original counts are opaque: adequate depth, missingness, two-replicate agreement and useful headroom unknown', 'Source panel is ATR-nominating-screen selected; not unbiased gene or environment generalization', 'Selected validation library has discovery-outcome ancestry and a changed regimen', 'Processed per-file environment binding unresolved except Table S5/MMC6', 'No condition-composition or unseen-environment resource identified', 'Coordinator and independent challenge must admit any numerical access/test']
}
save('replication_label_contract.json', contract)

receipts = [json.loads(line) for line in (OUT / 'request_receipts.jsonl').read_text().splitlines()]
used = sum(r['saved_decoded_body_bytes'] for r in receipts)
same_gaps = []
previous = {}
for r in receipts:
    if r['origin'] in previous:
        same_gaps.append(r['started_epoch'] - previous[r['origin']]['ended_epoch'])
    previous[r['origin']] = r
usage = {'role': 'K562 source and identity admission investigator', 'asof_utc': datetime.now(timezone.utc).isoformat(), 'attempt_limit': 22, 'completed_decoded_body_byte_limit': 48_000_000, 'counted_http_attempts': len(receipts), 'completed_decoded_body_bytes': used, 'known_saved_partial_decoded_bytes': sum(r['saved_decoded_body_bytes'] for r in receipts if not r['completed']), 'unknown_partial_traffic': any(r.get('partial_traffic_unknown', False) for r in receipts), 'wire_byte_total_certified': False, 'redirect_attempts': sum(r['status'] in [301,302,303,307,308] for r in receipts), 'HTTP_error_responses': [{'attempt': r['attempt'], 'status': r['status']} for r in receipts if r['status'] >= 400], 'automatic_retries': 0, 'access_bypass': False, 'same_origin_sequential': True, 'minimum_same_origin_completion_to_next_start_seconds': min(same_gaps) if same_gaps else None, 'same_origin_spacing_note': 'No repeated origin in this role: three sequential requests to three origins', 'unspent_attempts': 22-len(receipts), 'unspent_completed_decoded_body_bytes': 48_000_000-used, 'unused_allowance_reallocated': False, 'network_closed_by_coordinator': True, 'model_execution_or_fits': 0, 'downloaded_code_execution': False, 'original_count_numeric_tokens_converted': False, 'GI_numeric_cells_or_response_distributions_accessed': False, 'exposure': ['Prior admission records and original Methods/source variables read', 'All notebook outputs excluded; no author code executed', 'PDF text scanned for Table/Data caption-start lines; none found; figure images/legends not displayed', 'One numeric-masked xref identification probe accidentally displayed two qualitative gene/interaction-direction sentences from published Results. This source auditor is not an outcome-unexposed challenger.', 'Crossref JSON acquired opaque except selected identity/link fields; Elsevier API returned metadata only; standard ScienceDirect HTML returned403 and was not read or worked around'], 'read_scope': ['Original XML Methods S18,S21,S23,S24,S31,S33 and supplementary xref/file metadata', 'Original code source cells recorded in methods_variable_projection.json; growthScores keys only', 'GEO GI sample titles/characteristics/processing/relation metadata', 'Raw count first-line headers and first identity field only; library guide/gene/sequence reference columns', 'Workbook row1/columnA string identities and document properties only; no numerical score cells'], 'memory_rollout_read': False, 'shared_index_or_prior_frozen_file_edited': False}
save('usage.json', usage)
save('request_audit.json', {'receipts': receipts, 'usage': usage})

receipt_files = [p for p in OUT.iterdir() if p.is_file() and p.name not in ['processing_receipts.json']]
save('processing_receipts.json', {'created_utc': datetime.now(timezone.utc).isoformat(), 'original_source_pins': projection['originals'], 'local_artifacts': [{'path': str(p), 'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(receipt_files)], 'checks': {'both_count_identity_sets_equal': projection['count_identity_sets_equal'], 'count_library_identity_sets_equal': projection['aligned_library_identity_set_equals_counts'], 'sample_columns_present': len(projection['sample_binding']) == 14, 'eight_matrix_identity_headers_only': len(projection['matrix_headers']) == 8, 'one_exact_MMC_environment_binding': len([r for r in matrices if r['exact_binding_status'] == 'EXACT']) == 1}, 'not_numerical_admission': True})
print(json.dumps({'status': contract['status'], 'sample_binding_rows': len(projection['sample_binding']), 'exact_processed_file_bindings': len([r for r in matrices if r['exact_binding_status'] == 'EXACT']), 'http_attempts': len(receipts), 'completed_decoded_body_bytes': used, 'all_identity_checks_pass': all([projection['count_identity_sets_equal'], projection['aligned_library_identity_set_equals_counts']])}, indent=2))
