"""R202-Q1 external resource hunt and qualification (metadata-only).

Reads only metadata/structure summaries produced by the hunt scripts
(tmp/extq1/*.json) and receipts; never reads response values for effects.
Writes hunt_x1.json with per-candidate gate statuses and verdicts.
"""
import hashlib
import json
import os

B = r'D:\MAESTRO'
HERE = os.path.join(B, r'research\2026-10-27-external-resource-hunt')
REC = os.path.join(HERE, 'receipts')
EXT = os.path.join(B, 'tmp', 'extq1')
PROTOCOL = os.path.join(HERE, 'PROTOCOL_X1.md')
OUT = os.path.join(HERE, 'hunt_x1.json')


def sha_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest().upper()


def load(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def q(x):
    if isinstance(x, dict):
        return {k: q(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [q(v) for v in x]
    if isinstance(x, float):
        return round(x, 6) if x == x else None
    return x


def gate_from_status(status):
    return status


def verdict_for(gates):
    statuses = []
    for g in gates.values():
        s = g['status'] if isinstance(g, dict) and 'status' in g else ('pass' if g.get('pass') else 'fail')
        statuses.append(s)
    if any(s in ('fail', 'data_unavailable', 'access_restricted', 'no_candidate') for s in statuses):
        return 'not_qualified'
    if all(s == 'pass' for s in statuses):
        return 'qualified'
    return 'qualified_with_conditions'


result = {
    'protocol': {'path_rel': 'research/2026-10-27-external-resource-hunt/PROTOCOL_X1.md',
                 'sha256': sha_file(PROTOCOL), 'version': 'PROTOCOL_X1 v1 FROZEN'},
    'script': {'path_rel': 'research/2026-10-27-external-resource-hunt/hunt_x1.py',
               'sha256': sha_file(os.path.join(HERE, 'hunt_x1.py'))},
    'response_value_use_attestation': {
        'response_values_read_for_effects': False,
        'response_columns_used': 'existence/column-name only in downloaded metadata; row/count/structure only',
        'training': False, 'effect_estimation': False, 'q_estimation': False,
    },
    'frozen_thresholds': {
        'jaaks_min_shared_cells': 10, 'jaaks_min_shared_directed_pairs': 10,
        'jaaks_min_matched_keys': 500, 'single_file_max_mb': 500,
    },
    'download_rules': {'single_file_max_mb': 500, 'metadata_only': True,
                       'no_response_effects': True, 'login_or_license_bypass': False},
    'receipts': {
        'download_manifest': 'receipts/download_manifest.json',
        'access_status': 'receipts/access_status.json',
        'search_log': 'receipts/search_log.json',
    },
}

# ---------- Candidate 1: AstraZeneca/GDSC 2024 raw well data (AACR CD-23-0388) ----------
az_scan = load(os.path.join(EXT, 'azeraw_scan.json'))
az_ent = load(os.path.join(EXT, 'azeraw_entities.json'))
az_raw = az_ent['raw']
az_shared = az_ent['shared']
az = {
    'name': 'AstraZeneca/GDSC 2024 pan-cancer combination screen raw wells (AACR Cancer Discovery CD-23-0388; GDSC007-010 + Sandpiper-01)',
    'lineage': 'AstraZeneca/GDSC combination screens; public raw well data via Figshare project 163378; same GDSC/AZ cell panel as Jaaks but different plate barcodes',
    'download': {'raw_well_zip': 'receipts/download_manifest.json#az2024_raw_well_zip',
                 'file_bytes': az_scan['zip']['bytes'], 'sha256': az_scan['zip']['sha256']},
    'structure': {
        'rows_well_level': az_scan['rows'],
        'projects': az_scan['projects'],
        'cells': az_ent['matrix_cells'],
        'drugs_mapped': az_ent['id2drug_n'],
        'barcodes': az_ent['matrix_barcodes'],
        'directed_pairs_mapped': az_ent['matrix_pairs'],
        'pair_cell_units': az_scan['pair_cell_units']['n'],
        'pair_cell_units_with_ge2_barcodes': az_scan['pair_cell_units']['units_with_ge2_barcodes'],
        'numeric_dose_columns_present': True,
        'raw_intensity_present': True,
        'exposure_time_column_present': False,
        'orthogonal_functional_columns_present': False,
        'endpoint_columns': 'INTENSITY, inhibition, HSA/HSA_excess, Bliss_additivity/Bliss_excess (viability-derived); no apoptosis/caspase/target-engagement readout',
    },
    'jaaks_overlap': {
        'shared_cells': az_shared['cells'],
        'shared_drugs': az_shared['drugs'],
        'distinct_shared_directed_pairs': az_shared['pairs'],
        'shared_cell_pair_units': az_raw['shared_with_jaaks']['pairs'],
        'shared_barcodes': az_shared['barcodes'],
        'exact_a0_matched_keys': az_raw['matched_a0_unique_keys'],
        'note': '114/125 Jaaks cells shared; 14 shared drugs; 4,510 shared cell-pair entities; exact A0 concentration matched keys only 68 (<500); plate barcodes disjoint (0 shared)',
    },
    'gates': {
        'G1_entity_and_matched_keys': {'status': 'fail',
            'cells': az_shared['cells'], 'distinct_shared_directed_pairs': az_shared['pairs'],
            'shared_cell_pair_units': az_raw['shared_with_jaaks']['pairs'],
            'matched_keys': az_raw['matched_a0_unique_keys'],
            'reason': 'cells pass (114) but distinct shared directed pairs 8 < 10 and exact A0 matched keys 68 < 500'},
        'G2_wells_disjoint_from_jaaks': {'status': 'pass',
            'shared_barcodes': az_shared['barcodes'],
            'note': '0 shared barcode values; different plates/rounds'},
        'G3_legal_exposure': {'status': 'conditional', 'numeric_dose': True,
            'exposure_time_recorded': False},
        'G4_independent_measurement_or_culture': {'status': 'fail',
            'pair_cell_units': az_scan['pair_cell_units']['n'],
            'units_with_ge2_platforms': az_scan['pair_cell_units']['units_with_ge2_barcodes'],
            'note': 'one 7x7 matrix (49 wells) per pair-cell; no repeated matrix/plate per pair-cell; no independent culture/replicate structure'},
        'G5_orthogonal_functional_readout': {'status': 'conditional',
            'note': 'viability/inhibition and derived HSA/Bliss only; no apoptosis/caspase/target-engagement/regrowth readout'},
        'G6_frozen_aggregation_delta': {'status': 'conditional',
            'note': 'raw viability and numeric dose allow pre-registered Delta, but no exposure-time field and no pre-registered aggregation exists yet'},
        'G7_non_reaggregated_lineage': {'status': 'conditional',
            'note': 'different plate barcodes from Jaaks O/V (0 overlap) and independent 2024 publication; but same GDSC/AZ cell panel and same programme family, so independence is plate/round-level, not lineage-level'},
    },
    'verdict': 'not_qualified',
    'reason_codes': ['no_independent_replicate_or_culture', 'jaaks_overlap_insufficient',
                     'no_exposure_time', 'no_orthogonal_functional_readout'],
    'what_it_can_support': 'a new, large raw 7x7 dose-matrix resource for new relations / new cell lines (754 cells; 3.9M wells); not a qualified independent replicate/functional target for Jaaks-linked A/B tests as-is',
}
az['verdict'] = verdict_for(az['gates'])

# ---------- Candidate 2: NCI-ALMANAC ----------
nci_scan = load(os.path.join(EXT, 'nci_scan.json'))
nci_ov = load(os.path.join(EXT, 'nci_overlap.json'))
nci_mk = load(os.path.join(EXT, 'nci_matched_keys.json'))
nci = {
    'name': 'NCI-ALMANAC (NCI-60 combination screen)',
    'lineage': 'NCI-60 / DTP independent screen; 2017 public data release',
    'download': {'zip': 'receipts/download_manifest.json#nci_almanac_zip',
                 'bytes': nci_scan['file']['bytes'], 'sha256': nci_scan['file']['sha256'],
                 'uncompressed_csv_bytes': nci_scan['zip_member']['uncompressed_bytes']},
    'structure': {
        'rows_well_level': nci_scan['rows'], 'combo_rows': nci_scan['combo_rows'],
        'solo_rows': nci_scan['solo_rows'], 'cells': nci_scan['cells']['n_unique'],
        'screamers': nci_scan['screamers'], 'studies': nci_scan['n_studies'],
        'plates': nci_scan['n_plates'], 'dates': nci_scan['date_range'],
        'nsc_pairs': nci_scan['nsc_pair_count'], 'unique_cell_pair_units': nci_scan['n_unique_combo_cell_pair'],
        'replicate_keys_ge2_rows_frac': nci_scan['keys']['keys_ge2_frac'],
        'replicate_keys_ge2_distinct_plates': nci_scan['keys']['keys_ge2_distinct_plates'],
        'numeric_dose_columns_present': True,
        'raw_OD_columns_present': True,
        'exposure_time_column_present': False,
        'orthogonal_functional_columns_present': False,
        'endpoint': 'PercentGrowth / PercentGrowthNoTZ / TestValue / ControlValue / TZValue; Score = expected - observed (viability-derived); no apoptosis/caspase/target engagement',
    },
    'jaaks_overlap': {
        'shared_cells': nci_ov['cells']['shared_lenient'],
        'shared_cells_a0': nci_ov['cells']['a0_cells_shared_lenient'],
        'shared_drugs': nci_ov['drugs']['matched_nsc_to_jaaks'],
        'shared_directed_pairs': nci_ov['pairs']['nci_pairs_fully_in_jaaks_drug_set'],
        'entity_cell_pair_units_ignoring_dose': nci_ov['matched_upper']['matched_cell_pair_units_ignoring_dose'],
        'exact_a0_matched_keys': nci_mk['exact_a0_matched_unique_keys'],
        'note': '13 lenient shared cells (12 A0-matched), 17 shared drugs, 186 NCI pairs fully inside Jaaks drug set; exact A0 concentration matched keys = 0',
    },
    'gates': {
        'G1_entity_and_matched_keys': {'status': 'conditional', 'cells': nci_ov['cells']['shared_lenient'],
            'matched_keys': nci_mk['exact_a0_matched_unique_keys'],
            'reason': 'cells/drugs pass but exact A0 matched keys 0 < 500'},
        'G2_wells_disjoint_from_jaaks': {'status': 'conditional',
            'note': 'NCI plate IDs (e.g. 786-0_1_T72) and Jaaks barcodes are different namespaces; no shared identifiers; cannot prove physical plate disjointness'},
        'G3_legal_exposure': {'status': 'conditional', 'numeric_dose': True,
            'exposure_time_recorded': False},
        'G4_independent_measurement_or_culture': {'status': 'fail',
            'keys_ge2_distinct_plates': nci_scan['keys']['keys_ge2_distinct_plates'],
            'keys_ge2_frac': nci_scan['keys']['keys_ge2_frac'],
            'note': 'only 6,831 / 2,866,683 keys (0.24%) have 2 rows across different plates/studies; rest single measurement'},
        'G5_orthogonal_functional_readout': {'status': 'conditional',
            'note': 'viability/OD-derived endpoint only; no orthogonal functional readout'},
        'G6_frozen_aggregation_delta': {'status': 'conditional', 'note': 'raw percent growth and numeric doses available; no pre-registered Delta aggregation'},
        'G7_non_reaggregated_lineage': {'status': 'pass',
            'note': 'NCI-60/DTP original data; independent of Jaaks raw wells; DrugComb ALMANAC is derived from this, so use raw NCI as source, not DrugComb'},
    },
    'verdict': 'not_qualified',
    'reason_codes': ['no_independent_replicate_or_culture', 'jaaks_overlap_insufficient',
                     'no_exposure_time', 'no_orthogonal_functional_readout'],
}
nci['verdict'] = verdict_for(nci['gates'])

# ---------- other candidates ----------
others = [
    {'name': 'AstraZeneca-Sanger DREAM 2015', 'status': 'not_qualified',
     'reason_codes': ['access_restricted'], 'gates': {'data_files': {'status': 'access_restricted'}},
     'details': 'public Synapse project/wiki metadata reports ~11.5k combinations, 85 cell lines, 118 drugs + monotherapy; data file entities (syn4923182, syn4925540, syn4925542, syn4925546, syn4925534) returned HTTP 403 anonymously; terms/login required; raw not downloaded.'},
    {'name': 'PanThera (2024)', 'status': 'not_qualified',
     'reason_codes': ['aggregated_only', 'no_combination_data'],
     'gates': {'data': {'status': 'fail'}},
     'details': 'Zenodo 14216168: models.zip 877 MB, data.zip 276 MB, studies.zip Optuna tuning logs; PanTheraDB 14001717 is predicted synergy triplets; no raw experimental wells.'},
    {'name': 'SAFER (2024)', 'status': 'not_qualified',
     'reason_codes': ['reaggregated_lineage', 'data_unavailable'],
     'gates': {'data': {'status': 'fail'}},
     'details': 'Zenodo 10076432: data.tar.gz 1,131,872,853 B and database.tar.gz 1,136,276,427 B (>500 MB); readme states processed O\'Neil/ALMANAC/DrugComb data; aggregated from already-audited resources.'},
    {'name': 'Dryad organoid sequential therapy (2025)', 'status': 'not_qualified',
     'reason_codes': ['jaaks_overlap_insufficient', 'access_restricted'],
     'gates': {'jaaks_overlap': {'status': 'fail'}, 'access': {'status': 'access_restricted'}},
     'details': 'Science Advances 2025 / Dryad CC0 metadata; patient-derived organoids/spheroids, sequential multidrug administration; data.zip 30,467 B + README 14,575 B but file downloads 401 (bearer token); no Jaaks cell lines; potential new direction-3 resource only under a new protocol.'},
    {'name': 'HuggingFace ABX-CT-004 sequential therapy', 'status': 'not_qualified',
     'reason_codes': ['synthetic_benchmark', 'no_cancer_combination_data'],
     'gates': {'data': {'status': 'fail'}},
     'details': 'antibiotic sequential-therapy synthetic tabular benchmark (n<1k); not experimental cancer combination data.'},
    {'name': 'Novartis DRUG-seq U2OS (HuggingFace mirror)', 'status': 'not_qualified',
     'reason_codes': ['no_combination_data', 'mono_only'],
     'gates': {'data': {'status': 'fail'}},
     'details': '49,392 mono-perturbation transcriptomic observations, 3,742 compounds, U-2 OS; no combinations/functional endpoint.'},
    {'name': 'Functional independence resources (apoptosis/caspase/target engagement/regrowth paired with combinations)', 'status': 'not_qualified',
     'reason_codes': ['no_candidate_found'], 'gates': {'search': {'status': 'fail'}},
     'details': 'bounded search did not find a public combination resource with a matched orthogonal functional readout; this is a search result, not a claim of nonexistence.'},
]
for o in others:
    o['verdict'] = 'not_qualified'

result['candidates'] = {'astrazeneca_gdsc_2024_raw': az, 'nci_almanac': nci, 'others': others}
result['overall'] = {
    'verdict': 'not_qualified',
    'qualified_candidates': [],
    'qualified_with_conditions_candidates': [],
    'best_candidate': 'AstraZeneca/GDSC 2024 raw wells (largest raw dose-matrix resource; fails G4 no independent replicate/culture and G1 matched-key threshold; only 68 exact A0 matched keys)',
    'recommendation': 'stop external hunt for the current A/B/D3/4/5 questions: public resources found are either access-restricted, already-aggregated/processed, mono-only, synthetic, or lack independent replicate/culture plus orthogonal functional readout; further web/library scouting is unlikely to change the bottleneck without new wet-lab measurement',
    'required_measurement_spec': [
        '>=2 independent replicate plates/cultures (different day/passage/flask) per (cell, directed pair) dose condition; technical wells do not count',
        'numeric doses plus explicit exposure time/assay method for every key',
        'same functional endpoint family as Jaaks DeltaEMAX source, or a pre-registered calibration/derivation; raw viability alone must not be merged with DeltaEMAX',
        '>=1 orthogonal functional readout (apoptosis/caspase, target engagement, regrowth, live imaging) paired with the same combination wells',
        '>=500 A0-concentration-matched keys with Jaaks (or an explicitly new protocol for new relations without A0 matching)',
        'independent lineage/plate chain: report source screen, plate/well IDs, and non-reaggregation from Jaaks/DrugComb/PRISM/BeatAML/Mix-seq/O\'Neil',
    ],
    'notes': [
        'Not found/unavailable is a bounded-search result, not proof of nonexistence.',
        'No 96-cell reaggregation was used as new data; DrugComb-derived tables were not treated as raw external resources.',
        'Aggregated challenge/prediction scores (PanTheraDB, SAFER processed data) were not treated as raw repeats.',
    ],
}
result['determinism'] = {'json_keys_sorted': True, 'timestamps': False}
with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
    json.dump(q(result), f, indent=1, sort_keys=True, ensure_ascii=False)
    f.write('\n')
print(json.dumps({'overall': result['overall']['verdict'],
                  'candidates': {k: v['verdict'] for k, v in result['candidates'].items() if k != 'others'},
                  'others': [(o['name'], o['status']) for o in others]}, ensure_ascii=False, indent=1))
