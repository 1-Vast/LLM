"""Offline methods/manifest extraction; never reads outcome-table files."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/intervention_dynamics_renewal/functional_scout'


def load(name):
    return json.loads((OUT/name).read_bytes())


def main():
    receipts = [json.loads(p.read_text(encoding='utf-8')) for p in sorted(OUT.glob('REQUEST_*.json'))]
    article = ET.fromstring((OUT/'RESPONSE_03_melanoma_sequence_fulltext.bin').read_bytes())
    methods = {s.get('id'): {'title': s.findtext('title'), 'text': ''.join(s.itertext())}
               for s in article.findall('.//sec') if s.get('id') in ['Sec3', 'Sec7', 'Sec8', 'Sec9']}
    manifest = load('RESPONSE_04_melanoma_zenodo_manifest.bin')
    files = [{k: f.get(k) for k in ['key', 'size', 'checksum', 'links']} for f in manifest['files']]
    next_object = next(f for f in files if f['key'] == 'Suppl Data 03.xlsx')
    evidence = {
        'status': 'CONDITIONAL_SMALL_DATA_AUDIT_LEAD_NOT_QUALIFIED',
        'request_count': len(receipts), 'body_bytes_total': sum(r['bytes'] for r in receipts),
        'within_budget': len(receipts) <= 6 and all(r['bytes'] <= 3_000_000 for r in receipts),
        'requests': receipts, 'primary_article': {
            'title': 'Systematic interrogation of drug sensitivities in melanoma reveals potent synergistic and antagonistic drug combinations with translational potential.',
            'doi': '10.1038/s43856-026-01583-w', 'pmcid': 'PMC13338063', 'publication_date': '2026-04-30'},
        'methods_verbatim': methods,
        'repository': {'doi': manifest['metadata']['doi'], 'date': manifest['metadata']['publication_date'],
                       'description': manifest['metadata']['description'], 'files': files},
        'minimum_next_object': next_object,
        'authenticated_design': {
            'cell_line': 'WM1366', 'first_action': 'cladribine, abemaciclib, or DMSO',
            'second_action': 'wash twice at24h, then fresh medium with the next treatment',
            'observed_orders': ['cladribine -> abemaciclib', 'abemaciclib -> cladribine'],
            'cladribine_dose_uM': 0.2, 'abemaciclib_dose': 'NOT_AUTHENTICATED_FROM_TEXT',
            'imaging': 'baseline, then every3h through48h; Cytotox Green and total cell counts',
            'functional_endpoint': 'relative cell death: Cytotox-positive cells / total cells',
            'molecular_state_assay': 'DNA content and gammaH2Ax flow cytometry',
            'flow_independent_experiments': 'three, conducted on different days',
            'imaging_replicates': 'Figure4B explicitly three technical replicates per treatment; methods mention biological replicates without the figure-specific run count',
            'screen_replicates_not_sequence_replicates': 'three MeWo full-screen experiments do not establish three WM1366 sequence runs'},
        'joins': {
            'known': ['paper Figure4B -> SupplementaryData3 -> Zenodo Suppl Data03.xlsx',
                      'cell line + treatment order + nominal time define a published condition'],
            'not_yet_verified': ['xlsx column names, per-well identifiers and time coverage',
                                 'biological run IDs and availability of all independent runs',
                                 'exact abemaciclib dose and all treatment durations in graphical Figure4A',
                                 'flow measurement time relative to switch and terminal imaging',
                                 'flow-to-imaging condition/batch correspondence and numerical flow-state availability']},
        'permitted_narrow_task': 'Conditional on an authenticated condition-level early state and action history, predict later population death fraction under a fixed sequence; physical-cell identity is not required for a matched-condition mean task.',
        'not_authorized_here': ['outcome workbook opening', 'large-data download', 'numeric performance experiment'],
        'secondary_metadata_only': {'title': 'Simultaneous targeting of KRAS and CDK4 synergistically induces durable growth arrest in pancreatic cancer cells.',
                                    'doi': '10.1038/s41419-025-08362-w', 'pmcid': 'PMC12847887',
                                    'status': 'abstract lead only; no full text, manifest or state/function/run join audited'},
        'exposure': 'Read discovery abstracts, primary methods, relevant published results prose and Figure4 caption including published statistical summaries; no source outcome table or new outcome array opened.',
        'search_limit': 'Two successful metadata searches inspect only their returned first16/20 records; one focused search returned503 without retry. Not a comprehensive absence claim.'}
    with (OUT/'EVIDENCE.json').open('x', encoding='utf-8') as handle:
        json.dump(evidence, handle, indent=2, ensure_ascii=False)
    print(json.dumps({k: evidence[k] for k in ['status', 'request_count', 'body_bytes_total', 'within_budget', 'minimum_next_object']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
