"""Static evidence extraction from verified code text and existing primary metadata."""
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'log/20261022/intervention_dynamics_renewal'
OUT = BASE / 'ap1_code_io'


def main():
    manifest = json.loads((BASE/'root_scout/AP1_REPOSITORY_MANIFEST.json').read_text(encoding='utf-8'))
    entries = {e['path']: e for e in manifest['entries']}
    receipts = [json.loads(p.read_text(encoding='utf-8')) for p in sorted(OUT.glob('REQUEST_*.json'))]
    code_evidence = []
    for receipt in receipts:
        content = Path(receipt['decoded_file']).read_bytes()
        git_sha = hashlib.sha1(b'blob '+str(len(content)).encode()+b'\0'+content).hexdigest()
        text = content.decode('utf-8')
        inputs = []
        for path in re.findall(r'read\.csv\("([^"\n]+)"', text):
            relative = 'extractedData/'+path.split('/extractedData/', 1)[1]
            inputs.append(entries[relative])
        code_evidence.append({'path': receipt['path'], 'bytes': len(content), 'git_blob_sha1': git_sha,
                              'identity_verified': git_sha == receipt['expected_git_blob_sha1'],
                              'input_csv_manifest_entries': inputs,
                              'name_filter_literals': re.findall(r'Name == "([^"\n]+)"', text),
                              'executed': False})
    primary_path = BASE/'skeptic/AP1_MEMORY_PRIMARY.body'
    primary_bytes = primary_path.read_bytes()
    primary = ET.fromstring(primary_bytes)
    methods = {s.get('id'): {'title': s.findtext('title'), 'text': ''.join(s.itertext())}
               for s in primary.findall('.//sec') if s.get('id') in ['Sec13', 'Sec14', 'Sec15', 'Sec16', 'Sec19', 'Sec20', 'Sec30']}
    candidate_paths = [
        'extractedData/incucyte/tram/1541/VID1541_repA.csv',
        'extractedData/incucyte/tram/1541/VID1541_repB.csv',
        'extractedData/incucyte/jnkin8/VID2536.csv',
        'extractedData/dexmemFISH/rep4/20230830_075959_359_WellB1_ChannelDAPI_DMout,CY3,A594,CY5,CY7_Seq0001-1_3ddmso_1.csv',
        'extractedData/dexmemFISH/rep4/20230830_075959_359_WellC2_ChannelDAPI_DMout,CY3,A594,CY5,CY7_Seq0005-2_3ddex.csv',
        'extractedData/dexmemFISH/rep4/probes.txt']
    evidence = {
        'status': 'VERIFIED_CODE_IO_ONLY_NO_STATE_FUNCTION_JOIN_AUTHENTICATED',
        'repository': manifest['full_name'], 'tree_sha': manifest['tree_sha'], 'truncated': manifest['truncated'],
        'requests': receipts, 'request_count': len(receipts), 'body_bytes_total': sum(r['bytes'] for r in receipts),
        'all_blob_identities_verified': len(receipts) == 3 and all(e['identity_verified'] for e in code_evidence),
        'code': code_evidence, 'primary_sha256': hashlib.sha256(primary_bytes).hexdigest(), 'primary_methods': methods,
        'functional_schema_expected': {
            'input_column_consumed': 'Name', 'colony_definition_in_code': 'number of CSV rows for each Name within each input file',
            'derived_columns': ['colony', 'exp'], 'time_column_used': False, 'well_or_colony_id_deduplication': False,
            'raw_unit_not_yet_verified': 'One row per final independent colony is assumed by counting code, not proven from the unopened CSV.'},
        'functional_repeat_handling': {
            'tram': {'inputs': ['VID2180', 'VID2181', 'VID1516', 'VID2536', 'VID2112', 'VID1541_repA', 'VID1541_repB'],
                     'filter': ['hi1', 'lo1', 'lohi1'], 'independence': 'File labels are not proof of independent runs;1541A/B especially need design confirmation.'},
            'jnk': {'included': ['VID1516', 'VID2536', 'VID2112'], 'comment_only_not_included': 'exp2925',
                    'observed_zero_inserted': {'exp': 'exp2536', 'Name': 'hi2', 'colony': 0,
                                               'reason_verbatim': 'did not have any colonies for hi2 (all cells died = no resistant colony formation)'}}},
        'state_schema_expected': {
            'required_downstream': ['cy3', 'a594', 'cy5', 'cy7', 'cell.Blob.Blob.metrics...Area'],
            'optional_numeric_conversion_list': ['cell.Blob.Blob.metrics...Perimeter', 'cell.Blob.Blob.metrics...Centroid...y', 'cell.Blob.Blob.metrics...Centroid...x'],
            'derived_labels': {'file_identifier': 'last filename hyphen-delimited suffix before.csv', 'file_id': 'bind_rows positional list ordinal'},
            'normalizations': ['cy3,a594,cy5 divided by cy7', 'cell area multiplied by0.0467 then channel counts divided by area'],
            'gene_channel_mapping': 'not defined by audited function', 'condition_or_time_mapping': 'not parsed by audited function',
            'independent_run_mapping': 'not defined; caller inputdirectory is not invoked in this file',
            'missing_handling': 'as.numeric coercion; na.omit for raw melted and area-normalized plots; no explicit denominator-finiteness check',
            'outliers': 'outlier.shape=NA hides plotted outlier points, does not delete their underlying rows'},
        'actual_join_operations_between_state_and_function': [],
        'candidate_next_objects_not_fetched': [entries[p] for p in candidate_paths],
        'published_code_exposure': ['exp2536/hi2 observed zero and death explanation', 'fixed area calibration0.0467',
                                    'included and commented-out file/run labels; no rendered statistical outputs read'],
        'limits': ['No CSV or spreadsheet headers/values verified.', 'No R/Rmd code executed.',
                   'No colony-to-state run/condition key or same-cell trajectory authenticated.']}
    with (OUT/'STATIC_EVIDENCE.json').open('x', encoding='utf-8') as handle:
        json.dump(evidence, handle, indent=2)
    print(json.dumps({k: evidence[k] for k in ['status', 'request_count', 'body_bytes_total', 'all_blob_identities_verified']}))


if __name__ == '__main__':
    main()
