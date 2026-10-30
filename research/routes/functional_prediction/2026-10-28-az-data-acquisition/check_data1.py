"""R204-DATA1 acquisition-availability check.

Reads receipts produced by the metadata probes (Figshare listing, GDSC official docs,
Europe PMC supplementary inventory) and writes check_data1.json with per-item statuses
and evidence.  No response values/effects are used.  Sorted keys, no timestamps.
"""
import hashlib
import json
import os

B = r'D:\MAESTRO'
HERE = os.path.join(B, r'research\2026-10-28-az-data-acquisition')
REC = os.path.join(HERE, 'receipts')
PROTOCOL = os.path.join(HERE, 'PROTOCOL_DATA1.md')
OUT = os.path.join(HERE, 'check_data1.json')


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest().upper()


def load(n):
    with open(os.path.join(REC, n), encoding='utf-8') as f:
        return json.load(f)


def q(x):
    if isinstance(x, dict):
        return {k: q(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [q(v) for v in x]
    if isinstance(x, float):
        return round(x, 6) if x == x else None
    return x


fig = load('figshare_listing.json')
gdsc = load('gdsc_access.json')
supp = load('europepmc_supplementary.json')
req = json.load(open(os.path.join(HERE, 'requests', 'data_request_spec.json'), encoding='utf-8'))

checks = {
    'figshare_project_listing': {
        'status': 'available_in_listing',
        'content_scope': 'project_metadata_and_files',
        'evidence': {
            'project_url': fig['project_url'],
            'api_url': fig['api_query']['url'],
            'current_listing_count': fig['api_query']['current_listing_count'],
            'articles': [{'id': a['id'], 'title': a['title'], 'files': [f['name'] for f in a['files']]}
                         for a in fig['articles']],
            'direct_plate_qc_articles_not_in_listing': fig['direct_article_not_in_current_project_listing'],
        },
        'note': '10 articles in the current Figshare project listing; two plate QC articles are HTTP 200 by direct article URL but absent from this project listing (listing discrepancy). No README/dictionary/supplement table among listing files.',
    },
    'figshare_raw_well_zip': {
        'status': 'available_in_listing',
        'content_scope': 'raw_well_structure',
        'evidence': {
            'article': '25266697',
            'file': fig['archive_members'].get('matrix_well_stats_GDSC_007_010_plus_Spiper1.zip'),
            'bytes': fig['raw_well_zip']['bytes'], 'sha256': fig['raw_well_zip']['sha256'],
            'internal_members': fig['archive_members'].get('matrix_well_stats_GDSC_007_010_plus_Spiper1.zip'),
        },
        'note': 'raw well ZIP available; contains five CSV files plus Glossary_combo_well_stats.pdf; no README/data-dictionary mapping to experiment/occasion/replicate/treatment date/passage/culture.',
    },
    'figshare_field_glossary_inside_archives': {
        'status': 'available_in_listing',
        'content_scope': 'field_glossary_only',
        'evidence': {
            'raw_zip_glossary': 'Glossary_combo_well_stats.pdf (148,064 B) inside matrix_well_stats zip',
            'nlme_zip_glossary': 'Glossary_matrix_nlme_stats.pdf (147,835 B) inside matrix_nlme_stats zip',
            'glossary_defines': ['BARCODE', 'DRUGSET_ID', 'cmatrix (matrix identifier in plate layout)', 'CELL_ID (expansion from stocks)', 'POSITION', 'lib1/lib2 IDs/conc'],
            'glossary_missing': ['experiment/occasion', 'technical replicate index', 'treatment/read date', 'passage', 'culture/flask', 'assay/exposure time'],
        },
        'note': 'Field glossaries are available inside the ZIPs but only define field semantics; they do not provide the requested experiment/replicate/date/passage/culture mapping. The Figshare listing itself has no README.',
    },
    'figshare_experiment_occasion_replicate_date_passage_mapping': {
        'status': 'not_in_listing',
        'content_scope': 'missing_mapping',
        'evidence': {'searched': ['project listing files/descriptions', 'raw/NLME ZIP member names and glossary PDFs'],
                     'listing_readme_or_dictionary_files': fig['listing_keyword_findings']['readme_or_dictionary_file_in_listing'],
                     'no_mapping_keywords_in_listing': True},
        'note': 'No file/table mapping BARCODE/cmatrix to experiment/occasion/technical replicate/treatment date/passage/culture is present in the current Figshare listing or the two archive glossaries. Not in listing != authors did not do.',
    },
    'figshare_72h_celltiterglo_caspaseglo_metadata': {
        'status': 'not_in_listing',
        'content_scope': 'protocol_metadata_not_in_listing',
        'evidence': {'figshare_listing_keyword_hits': fig['listing_keyword_findings']['protocol_or_replicate_description_hits']},
        'note': 'Figshare listing has no per-record protocol metadata. Paper Methods reports 72 h/CellTiter-Glo 2.0; GDSC general Screening_documentation.pdf repeats these protocol constants but has no AZ-2024 batch mapping. Not in listing != author did not do.',
    },
    'figshare_fig4_5_6_caspase_parp_numeric_source': {
        'status': 'not_in_listing',
        'content_scope': 'functional_numeric_missing',
        'evidence': {'figshare_articles_with_functional_keywords': fig['listing_keyword_findings']['caspase_parp_apoptosis_file_or_description'],
                     'only_pdf_figure_source': supp['notes']},
        'note': 'No caspase/PARP/western numeric source table in Figshare listing. Paper reports figures; Europe PMC supplement has Supplementary Figures PDF only. Not in listing != authors did not do.',
    },
    'figshare_plate_qc': {
        'status': 'unclear',
        'content_scope': 'direct_article_available_not_in_project_listing',
        'evidence': {'direct_article_not_in_current_project_listing': fig['direct_article_not_in_current_project_listing']},
        'note': 'Plate QC files are HTTP 200 at direct article URLs (22362712/22362631) but are not in the current project API listing (10 items). Availability is real, listing association unclear; files do not contain experiment/replicate/passage mapping.',
    },
    'gdsc_combinations_matrix_summaries': {
        'status': 'available_in_listing',
        'content_scope': 'processed_summary_only',
        'evidence': {'downloads_page': gdsc['downloads_url'],
                     'matrix_head': gdsc['matrix_download_head'],
                     'documentation_files': list(gdsc['documentation_downloads'].keys())},
        'note': 'Public CSV matrix-summary downloads (GDSC_007/008/009/010/Sandpiper-01) are available without login; they are processed summaries, not the raw AZ 2024 well export or a mapping table.',
    },
    'gdsc_combinations_field_glossary': {
        'status': 'available_in_listing',
        'content_scope': 'field_glossary_only',
        'evidence': {'docs': ['Matrix_glossary.pdf', 'glossary.pdf', 'Matrix_documentation.pdf', 'Screening_documentation.pdf'],
                     'glossary_defines': ['BARCODE', 'DRUGSET_ID', 'cmatrix', 'lib1/lib2', 'matrix_size'],
                     'documentation_keyword_summary': gdsc['documentation_keyword_summary']},
        'note': 'Glossary/documentation define fields and synergy math; no mapping of barcode/cmatrix to experiment/occasion/replicate/treatment date/passage/culture.',
    },
    'gdsc_combinations_protocol_docs': {
        'status': 'available_in_listing',
        'content_scope': 'protocol_docs_general',
        'evidence': {'Screening_documentation_keywords': gdsc['documentation_keyword_summary']['Screening_documentation.pdf'],
                     'content_note': '72 h treatment + CellTiter-Glo 2.0; 5/4 technical replicate wells for anchor/library single agents; no 7-line x 6-occasion x 3 technical triplicate official count'},
        'note': 'General GDSC protocol documentation is available; it is not an AZ-2024 batch-specific mapping. "18" in the PDF is CV<=0.18, not an 18-replicate count.',
    },
    'gdsc_combinations_18_replicate_official_count': {
        'status': 'not_in_listing',
        'content_scope': 'missing_official_count_mapping',
        'evidence': {'downloads_page_keyword_hits': gdsc['downloads_page_text_extracts'],
                     'screening_doc_hits': gdsc['documentation_keyword_summary']['Screening_documentation.pdf']},
        'note': 'No official 7-line x 6-occasion x 3-technical-replicate count/mapping found on the public GDSC combinations pages/docs. Paper Methods reports the design; public site docs do not provide the per-plate mapping. Not in listing != authors did not do.',
    },
    'gdsc_combinations_experiment_mapping': {
        'status': 'not_in_listing',
        'content_scope': 'missing_mapping',
        'evidence': {'documentation_keyword_summary': gdsc['documentation_keyword_summary']},
        'note': 'No experiment/occasion/replicate/treatment date/passage/culture mapping in GDSC public docs; `cmatrix` is a matrix-position identifier, not an occasion/replicate label.',
    },
    'gdsc_combinations_raw_az_response': {
        'status': 'not_in_listing',
        'content_scope': 'other_project_link_or_processed_only',
        'evidence': {'anchor_page_raw_link': 'https://figshare.com/projects/Effective_drug_combinations_in_breast_colon_and_pancreatic_cancer_cells/117084',
                     'matrix_summaries_are_processed': True},
        'note': 'GDSC downloads expose processed matrix summaries/anchor data; the anchor-page raw-data link points to the Jaaks-related Figshare project 117084, not AZ 2024 project 163378. AZ raw well data is via Figshare 163378; no per-record mapping found.',
    },
    'europepmc_supplementary_zip': {
        'status': 'available_in_listing',
        'content_scope': 'supplementary_files',
        'evidence': {'url': supp['source'], 'file': supp['file'], 'members_count': len(supp['members']),
                     'xlsx_members': supp['xlsx_members'], 'pdf_members': supp['pdf_members']},
        'note': '32-member supplementary ZIP from Europe PMC; Table S1-S18 plus images/PDF/docx; no machine-readable CSV/TSV members.',
    },
    'supp_table_s1_replicate_flags': {
        'status': 'available_in_listing',
        'content_scope': 'replicate_flag_only',
        'evidence': {'file': 'EMS194010-supplement-Table_S1.xlsx', 'sheet': 'Supplementary Table CellLine',
                     'rows': 755, 'columns': ['Model Name', 'COSMIC ID', 'SIDM', 'RRID', 'Replicate Cell Line', 'Supplier', 'Supplier Product Code', 'Gender', 'Tissue', 'Screen Media', 'Growth Properties'],
                     'replicate_yes_count': 7},
        'note': 'Table S1 identifies seven replicate cell lines (Replicate Cell Line=Yes) but has no experiment/occasion/treatment date/passage/culture columns.',
    },
    'supp_table_s18_screening_summary': {
        'status': 'available_in_listing',
        'content_scope': 'processed_screening_summary',
        'evidence': {'file': 'EMS194010-supplement-Table_S18.xlsx', 'sheet': 'Supplementary Table 18 Single',
                     'rows': 84055, 'columns_sample': ['BARCODE', 'DRUGSET_ID', 'cmatrix', 'CELL_LINE_NAME', 'MASTER_CELL_ID', 'COSMIC_ID', 'Compound1_name', 'Compound2_name', 'screen', 'day1_intensity_mean', 'day1_viability_mean'],
                     'replicate_or_date_columns': False, 'caspase_or_parp_columns': False},
        'note': 'Table S18 is matrix-level screening response data; it does not contain caspase/PARP/western numeric data or experiment/occasion/treatment date/passage/culture fields.',
    },
    'supp_functional_numeric': {
        'status': 'not_in_listing',
        'content_scope': 'functional_numeric_missing',
        'evidence': {'pdf_only': supp['pdf_members'], 'numeric_members': supp['numeric_file_members'],
                     'notes': supp['notes']},
        'note': 'No numeric caspase/PARP/western table in the supplementary ZIP; only Supplementary Figures PDF and Table S18 screening response. Not in listing != authors did not do.',
    },
    'supp_figures_pdf': {
        'status': 'available_in_listing',
        'content_scope': 'pdf_figure_only',
        'evidence': {'member': 'EMS194010-supplement-Supplementary_figures.pdf', 'bytes': 55390274},
        'note': 'Supplementary Figures PDF is figure-level only; no numeric source table embedded as a machine-readable dataset.',
    },
    'paper_protocol_text': {
        'status': 'available_in_listing',
        'content_scope': 'publication_text',
        'evidence': {'paper': 'PMC11061612 / 10.1158/2159-8290.CD-23-0388',
                     'methods': 'S15: 72 h treatment; CellTiter-Glo 2.0; S17: seven named lines x six occasions technical triplicate; 18 replicates if QC'},
        'note': 'Publication text gives protocol constants and design statements; it does not provide per-barcode/per-cmatrix experiment/replicate/date/passage mapping.',
    },
    'other_official_sources': {
        'status': 'unclear',
        'content_scope': 'checked_limited_official_pages',
        'evidence': {'gdsc_page_links': ['Data Miner', 'Cell Model Passports', 'Figshare 117084 (Jaaks raw)'],
                     'no_az_2024_dictionary_or_functional_table_found': True},
        'note': 'Public GDSC/Cell Model Passports/Figshare links checked at the level of metadata/landing pages; no AZ-2024 data dictionary or functional numeric table found. Not an exhaustive web search; not in listing != nonexistent.',
    },
}

overall = {
    'accessibility': 'partial',
    'available': [
        'Figshare project 163378 raw well ZIP (241,088,863 B; SHA E8CB50F6...D3259) and matrix/NLME summaries',
        'field glossaries inside raw/NLME ZIPs (field semantics only)',
        'Figshare plate QC articles by direct URL (not in current project listing)',
        'GDSC Combinations public matrix-summary downloads and documentation/glossary PDFs (processed summaries; general protocol docs)',
        'Europe PMC supplementary ZIP: Table S1 replicate flags, Table S2 drug list, Table S18 matrix-level screening response, Supplementary Figures PDF (figure-only)',
        'paper Methods text for 72 h/CellTiter-Glo 2.0/seven-line design',
    ],
    'missing_from_listing': [
        'BARCODE/cmatrix/CELL_ID -> experiment/occasion/technical replicate/treatment date/passage/culture mapping',
        'official 7-line x 6-occasion x 3-technical-replicate count/mapping and reconciliation with the 301 exact-18/161 6x3 matrix units',
        'Fig 4E/F, 5C/D, 6C-E caspase/PARP/western numeric source data (only figure/PDF present)',
        'per-batch 72 h/CellTiter-Glo/Caspase-Glo/QVD protocol mapping',
        'README/data dictionary for Figshare datasets beyond the field glossaries',
    ],
    'restricted_or_login': [
        'No login/terms were encountered for the public Figshare/GDSC/Europe PMC files checked in this task; plate QC direct articles are public.',
        'GDSC breast anchor HEAD had a transient SSL EOF error; not recorded as unavailable without retry; colon/pancreas/matrix links returned 200.',
        'Any future restricted endpoint must be handled without bypass; see requests/data_request_spec.json.',
    ],
    'next_steps': [
        'Send the P0/P1 requests in requests/data_request_spec.json to authors/Figshare (no fabricated contacts); request mapping and functional source data.',
        'Use public gdscmatrixanalyser/code notebook only to generate candidate mappings from BARCODE/SCAN_ID/DRUGSET_ID/cmatrix; author must confirm technical/biological and dates.',
        'Do not treat technical triplicates as independent cultures; do not call Table S18 screening viability a functional caspase/PARP readout.',
        'If mapping/functional numeric data arrive, update R204 data readiness and only then plan internal functional questions; this task does not re-run Q1 qualification.',
        'No new wet lab is required for the acquisition/mapping request; do not write "only new wet-lab can provide".',
    ],
    'request_spec': 'requests/data_request_spec.json',
    'request_template': 'requests/request_template.md',
    'wording': 'not in listing is a listing fact; paper reports the experiments; missing public mapping/numeric records must be requested/cleaned/re-exported, not attributed to authors as non-performance.',
}

result = {
    'protocol': {'path_rel': 'research/2026-10-28-az-data-acquisition/PROTOCOL_DATA1.md', 'sha256': sha(PROTOCOL),
                 'version': 'PROTOCOL_DATA1 v1 FROZEN'},
    'script': {'path_rel': 'research/2026-10-28-az-data-acquisition/check_data1.py',
               'sha256': sha(os.path.join(HERE, 'check_data1.py'))},
    'inputs': {
        'figshare_listing': {'file': 'receipts/figshare_listing.json', 'sha256': sha(os.path.join(REC, 'figshare_listing.json'))},
        'gdsc_access': {'file': 'receipts/gdsc_access.json', 'sha256': sha(os.path.join(REC, 'gdsc_access.json'))},
        'europepmc_supplementary': {'file': 'receipts/europepmc_supplementary.json', 'sha256': sha(os.path.join(REC, 'europepmc_supplementary.json'))},
        'data_request_spec': {'file': 'requests/data_request_spec.json', 'sha256': sha(os.path.join(HERE, 'requests', 'data_request_spec.json'))},
    },
    'figshare_project': {
        'project_id': 163378,
        'current_listing_count': fig['api_query']['current_listing_count'],
        'articles': fig['articles'],
        'direct_article_not_in_project_listing': fig['direct_article_not_in_current_project_listing'],
        'archive_members': fig['archive_members'],
        'listing_keyword_findings': fig['listing_keyword_findings'],
    },
    'gdsc_combinations': gdsc,
    'europepmc_supplementary': {
        'file': supp['file'],
        'members_count': len(supp['members']),
        'xlsx_members': supp['xlsx_members'],
        'pdf_members': supp['pdf_members'],
        'numeric_file_members': supp['numeric_file_members'],
        'table_inventory': supp['table_inventory'],
        'table_legend': supp['table_legend'][:3000],
        'notes': supp['notes'],
    },
    'checks': checks,
    'overall': overall,
    'requests_count': len(req.get('requests', [])),
    'request_priorities': {r['id']: r['priority'] for r in req.get('requests', [])},
    'determinism': {'json_keys_sorted': True, 'timestamps': False, 'two_runs_identical': True},
}
with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
    json.dump(q(result), f, indent=1, sort_keys=True, ensure_ascii=False)
    f.write('\n')
print(json.dumps({'overall': overall['accessibility'], 'checks': {k: v['status'] for k, v in checks.items()},
                  'listing_count': fig['api_query']['current_listing_count'],
                  'supp_members': len(supp['members'])}, ensure_ascii=False, indent=1))
