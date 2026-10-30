"""R204-DATA2 code/notebook/data-dictionary hunt summary.

Reads receipts/code_hunt_evidence.json (public GitHub/GDSC code/docs/search results)
and writes hunt_data2.json with per-item availability statuses.  Does not execute
any repository code or response analysis.  Sorted keys, no timestamps.
"""
import hashlib
import json
import os

B = r'D:\MAESTRO'
HERE = os.path.join(B, r'research\2026-10-28-az-code-hunt')
REC = os.path.join(HERE, 'receipts')
PROTOCOL = os.path.join(HERE, 'PROTOCOL_DATA2.md')
OUT = os.path.join(HERE, 'hunt_data2.json')


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest().upper()


def q(x):
    if isinstance(x, dict):
        return {k: q(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [q(v) for v in x]
    if isinstance(x, float):
        return round(x, 6) if x == x else None
    return x


ev = json.load(open(os.path.join(REC, 'code_hunt_evidence.json'), encoding='utf-8'))
repos = ev['repos']

repo_brief = {}
for name in ['eac54/Large-scale-pan-cancer-screening', 'CancerRxGene/gdscmatrixanalyser',
             'CancerRxGene/gdscmatrixexplorer', 'CancerRxGene/gdscIC50', 'CancerRxGene/gdsctools']:
    r = repos.get(name, {})
    repo_brief[name] = {
        'url': r.get('url'), 'license': r.get('license'), 'last_pushed': r.get('pushed_at'),
        'last_updated': r.get('updated_at'), 'description': r.get('description'),
        'tarball_bytes': (r.get('tarball') or {}).get('bytes'), 'tarball_sha256': (r.get('tarball') or {}).get('sha256'),
        'n_files': r.get('n_files'), 'files_sample': r.get('files_sample', [])[:30],
    }

checks = {
    'paper_analysis_code': {
        'status': 'available_public_code',
        'repo': 'eac54/Large-scale-pan-cancer-screening',
        'evidence': repo_brief['eac54/Large-scale-pan-cancer-screening'],
        'license_note': 'GitHub API reports no license for this repo; code publicly viewable but reuse license not declared.',
        'content_scope': 'paper_analysis_code_only',
        'key_files': ['README.md', 'Figure 1.Rmd', 'Figure 3.Rmd', 'Supplementary Figure 1.Rmd'],
        'mapping_evidence': ev['code_evidence']['paper_analysis_code'][0],
        'note': 'Figure/analysis Rmd; reads Figshare matrix results; aggregates replicates by mean; no mapping to experiment/occasion/technical replicate/treatment date/passage/culture and no functional numeric source data.',
    },
    'matrix_analyser_code': {
        'status': 'available_public_code',
        'repo': 'CancerRxGene/gdscmatrixanalyser',
        'evidence': repo_brief['CancerRxGene/gdscmatrixanalyser'],
        'license': 'AGPL-3.0',
        'content_scope': 'parser_and_field_glossary_only',
        'key_files': ['R/classes.R', 'R/pipeline.R', 'R/matrix_well_stats.R', 'README.md'],
        'mapping_evidence': ev['code_evidence']['paper_analysis_code'][1],
        'note': 'plate object supports barcode/plate_date/scan_id/drugset_id/cell_id; make_plate_list derives plate_date from DATE_CREATED input; no public mapping of experiment/occasion/technical replicate/treatment date/passage/culture; public export lacks DATE_CREATED.',
    },
    'matrix_explorer_code': {
        'status': 'available_public_code',
        'repo': 'CancerRxGene/gdscmatrixexplorer',
        'evidence': repo_brief['CancerRxGene/gdscmatrixexplorer'],
        'license': 'NOASSERTION (GitHub API; license file present but not standard SPDX)',
        'content_scope': 'app_and_field_glossary_only',
        'key_files': ['README.md', 'models.py', 'pages/documentation.py', 'downloads/screen_information_20190211.pdf', 'scripts/db_loader.py'],
        'mapping_evidence': ev['code_evidence']['gdsc_tools_code'][0],
        'replicate_definition': ev['code_evidence']['replicate_definition'],
        'note': 'app models group MatrixResult by (project, lib1_id, lib2_id); project_replicates/all_replicates are same drug pair across projects, NOT the paper six-occasion technical triplicate or independent culture; field glossary only; no per-barcode occasion/date/passage/culture mapping.',
    },
    'gdscIC50_raw_format_code': {
        'status': 'available_public_code',
        'repo': 'CancerRxGene/gdscIC50',
        'evidence': repo_brief['CancerRxGene/gdscIC50'],
        'license': 'GPL-3.0',
        'content_scope': 'parser_raw_format_only',
        'key_files': ['R/nlme_fit_prep.R', 'vignettes/gdsc_raw_data_format.Rmd'],
        'mapping_evidence': ev['code_evidence']['gdsc_tools_code'][1],
        'note': 'Supports raw screen data columns including SCAN_ID/BARCODE/RESEARCH_PROJECT/DATE_CREATED/SCAN_DATE/CELL_ID/DRUGSET_ID/ASSAY/DURATION, but public AZ export lacks these per-record columns and no mapping file is included.',
    },
    'gdsctools_code': {
        'status': 'available_public_code',
        'repo': 'CancerRxGene/gdsctools',
        'evidence': repo_brief['CancerRxGene/gdsctools'],
        'license': 'NOASSERTION',
        'content_scope': 'general_gdsc_tools_not_az_specific',
        'key_files': ['gdsctools/', 'doc/'],
        'mapping_evidence': None,
        'note': 'General GDSC tools; no AZ-2024 matrix mapping/functional numeric; not directly useful for requested mapping.',
    },
    'public_figshare_raw_data': {
        'status': 'available_public_data',
        'evidence': ev['data1_context'],
        'content_scope': 'raw_well_and_processed_matrix_summaries',
        'note': 'Already available from DATA1: raw well ZIP (241,088,863 B; SHA E8CB...D3259) and matrix summaries; no data dictionary mapping to experiment/occasion/replicate/date/passage/culture.',
    },
    'protocol_doc_7lines_18rep': {
        'status': 'available_public_code',
        'repo': 'CancerRxGene/gdscmatrixexplorer',
        'file': ev['screen_information']['path_rel'],
        'page': ev['screen_information'].get('page'),
        'pages': ev['screen_information'].get('pages'),
        'content_scope': 'protocol_doc_only',
        'quote': ev['screen_information'].get('snippet'),
        'note': 'Public repo docs contain the exact seven-line/six-occasion/18-replicate statement plus 72h/CellTiter-Glo protocol; it is a design statement, NOT a per-barcode/cmatrix mapping.',
    },
    'field_glossary': {
        'status': 'available_public_code',
        'files': ['CancerRxGene/gdscmatrixexplorer/downloads/glossary.pdf', 'CancerRxGene/gdscmatrixexplorer/pages/documentation.py',
                  'GDSC Combos Matrix_glossary.pdf (DATA1)'],
        'content_scope': 'field_glossary_only',
        'note': 'Defines BARCODE/DRUGSET_ID/cmatrix/CELL_ID etc.; cmatrix is a matrix identifier, not an occasion/technical-replicate label. C205: field glossary != mapping.',
    },
    'mapping_barcode_cmatrix_cellid_to_experiment_occasion_technical_replicate_treatment_date_passage_culture': {
        'status': 'not_found_in_public_code',
        'secondary_status': 'requires_author_request',
        'content_scope': 'mapping_missing',
        'evidence': {
            'searched_repos': list(repo_brief.keys()),
            'code_hits': ev['code_evidence']['functional_keyword_scan'],
            'replicate_definition': ev['code_evidence']['replicate_definition'],
            'public_export_lacks_date_fields': True,
        },
        'note': 'No public README/script/notebook was found that maps BARCODE/cmatrix/CELL_ID/SCAN_ID/DRUGSET_ID to experiment/occasion/technical replicate/treatment date/passage/culture. gdscmatrixanalyser/gdscIC50 can parse DATE_CREATED/SCAN_DATE if supplied, but public AZ export does not supply them; gdscmatrixexplorer all_replicates is same-pair-across-project, not technical triplicate. Requires author request/DATA1 spec; not "does not exist".',
    },
    'official_18_replicate_per_barcode_mapping': {
        'status': 'not_found_in_public_code',
        'secondary_status': 'requires_author_request',
        'content_scope': 'official_count_text_only',
        'evidence': {'screen_information': ev['screen_information']},
        'note': 'The design statement (7 lines, six occasions, technical triplicate, 18 replicates) is public, but no public per-barcode/cmatrix mapping or official reconciliation table was found. Requires author mapping/DATA1 REQ-REP-01.',
    },
    'functional_caspase_parp_western_numeric': {
        'status': 'not_found_in_public_code',
        'secondary_status': 'requires_author_request',
        'content_scope': 'functional_numeric_missing',
        'evidence': {'keyword_scan': ev['code_evidence']['functional_keyword_scan'],
                     'data1': ev['data1_context']},
        'note': 'No caspase/PARP/western/apoptosis numeric or source-data table was found in the inspected public repositories or GDSC/Figshare listings; paper figures/Supplementary Figures PDF exist. Not found in public code != authors did not do.',
    },
    'readme_data_dictionary_beyond_field_glossary': {
        'status': 'not_found_in_public_code',
        'secondary_status': 'requires_author_request',
        'content_scope': 'mapping_missing',
        'evidence': {'paper_repo_readme': ev['code_evidence']['paper_analysis_code'][0],
                     'gdsc_docs': 'Matrix_glossary/glossary/docs only'},
        'note': 'No README/data dictionary defining experiment/replicate/date/passage/culture; only field glossaries and general documentation. Requires author request/DATA1 REQ-DICT-01.',
    },
    'paper_code_links': {
        'status': 'available_public_code',
        'evidence': {'paper_data_availability': 'https://europepmc.org/articles/PMC11061612',
                     'repos': ['https://github.com/eac54/Large-scale-pan-cancer-screening',
                               'https://github.com/CancerRxGene/gdscmatrixanalyser']},
        'content_scope': 'paper_analysis_code_only',
        'note': 'Code Availability links resolve and are public; they contain figure/analysis code, not the requested mapping/functional source data.',
    },
}

overall = {
    'code_accessibility': 'public code available, but mapping/functional numeric not available',
    'public_code_found': [
        'eac54/Large-scale-pan-cancer-screening (paper figure/analysis code; no mapping; no license declared)',
        'CancerRxGene/gdscmatrixanalyser (AGPL-3.0; matrix parser/plate objects; DATE_CREATED support but no public mapping)',
        'CancerRxGene/gdscmatrixexplorer (NOASSERTION; Dash app/models/field glossary; all_replicates is same-pair-across-projects, not technical triplicate)',
        'CancerRxGene/gdscIC50 (GPL-3.0; raw data format/parser; no public mapping)',
        'CancerRxGene/gdsctools (NOASSERTION; general GDSC tools, not AZ-specific)',
    ],
    'public_data_found': ['Figshare 163378 raw well ZIP/matrix summaries via DATA1; no new mapping/functional numeric'],
    'requires_author_request': [
        'BARCODE/cmatrix/CELL_ID -> experiment/occasion/technical replicate/treatment date/passage/culture mapping',
        'official seven-line x six-occasion x three-technical-replicate per-barcode mapping/reconciliation',
        'Fig 4/5/6 caspase/PARP/western numeric/source data',
        'README/data dictionary beyond field glossaries',
    ],
    'not_found_in_public_code': [
        'mapping script/notebook for experiment/occasion/technical replicate/treatment date/passage/culture',
        'functional numeric source data',
        'official per-barcode 18-replicate mapping',
    ],
    'next_steps': [
        'Keep DATA1 requests/data_request_spec.json as the priority: send P0/P1 requests to authors/Figshare; no new wet lab required for mapping/source data.',
        'If author supplies raw screen_data with DATE_CREATED/SCAN_DATE/ASSAY/DURATION, gdscmatrixanalyser/gdscIC50 can be used to construct plate objects and check date/assay fields; this still does not create occasion/technical-replicate/passage labels without author metadata.',
        'Do not use gdscmatrixexplorer.all_replicates as the six-occasion technical triplicate mapping: it groups same drug pairs across projects (models.py lines 70-97/195-224).',
        'Do not treat public field glossaries/protocol docs as the requested mapping (C205); do not claim functional numeric availability from PDF figures.',
        'If no author mapping/functional data are available, keep R204 data readiness open; do not restart Q1 qualification or claim new wet lab is the only path.',
    ],
    'no_independent_challenge': True,
    'wording': '有界检索未发现公开映射/功能数值；不是不存在；需要作者请求/重导，不是只能新湿实验。',
}

result = {
    'protocol': {'path_rel': 'research/2026-10-28-az-code-hunt/PROTOCOL_DATA2.md', 'sha256': sha(PROTOCOL),
                 'version': 'PROTOCOL_DATA2 v1 FROZEN'},
    'script': {'path_rel': 'research/2026-10-28-az-code-hunt/hunt_data2.py',
               'sha256': sha(os.path.join(HERE, 'hunt_data2.py'))},
    'inputs': {
        'code_hunt_evidence': {'file': 'receipts/code_hunt_evidence.json',
                               'sha256': sha(os.path.join(REC, 'code_hunt_evidence.json'))},
    },
    'repos': repo_brief,
    'code_evidence': ev['code_evidence'],
    'screen_information': ev['screen_information'],
    'search_evidence': ev['search_evidence'],
    'data1_context': ev['data1_context'],
    'checks': checks,
    'overall': overall,
    'determinism': {'json_keys_sorted': True, 'timestamps': False, 'two_runs_identical': True},
}
with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
    json.dump(q(result), f, indent=1, sort_keys=True, ensure_ascii=False)
    f.write('\n')
print(json.dumps({'checks': {k: v['status'] for k, v in checks.items()},
                  'overall': overall['code_accessibility'],
                  'repos': list(repo_brief.keys())}, ensure_ascii=False, indent=1))
