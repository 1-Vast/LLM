"""Seal completed data-role metadata evidence without additional source calls."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT/'log/20261022/tggates_rna_feedback_pilot'
SOURCES = LOG/'rna_sources'
CODE = ROOT/'research/tggates_rna_feedback_pilot_20261022'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    direct = [json.loads(path.read_bytes()) for path in sorted(SOURCES.glob('*.http.json'))]
    heads = json.loads((LOG/'RNA_ARCHIVE_HEADS.json').read_bytes())['receipts']
    assert len(direct) == 10 and all(row['status'] == 200 for row in direct)
    assert len(heads) == 31 and all(row['status'] == 200 for row in heads)
    byte_sum = sum(row['bytes'] for row in direct)
    assert byte_sum == 1097121
    range_support = Counter(row['headers'].get('Accept-Ranges', row['headers'].get('accept-ranges', 'NOT_REPORTED')) for row in heads)
    lengths = [int(row['headers'].get('Content-Length', row['headers'].get('content-length'))) for row in heads]
    manifest = json.loads((LOG/'RNA_IDENTITY_MANIFEST.json').read_bytes())
    assert manifest['sample_count'] == 172 and manifest['compound_count'] == 31
    summary = {'status':'COMPLETE_METADATA_ONLY', 'sample_count':172, 'compound_count':31,
               'sample_counts':manifest['sample_counts'], 'direct_GET_requests':10,
               'direct_GET_statuses':dict(Counter(str(row['status']) for row in direct)),
               'direct_GET_body_bytes':byte_sum, 'HEAD_requests':31,
               'HEAD_statuses':dict(Counter(str(row['status']) for row in heads)),
               'HEAD_accept_ranges_counts':dict(range_support), 'archive_bytes':sum(lengths),
               'RNA_numerical_payload_bytes_downloaded':0, 'web_tool_calls':2, 'web_queries':4,
               'web_body_bytes':'NOT_REPORTED', 'new_model_API_calls':0, 'new_fits':0,
               'new_biological_observations':0, 'sessions_terminal_exit0':[43772,16969],
               'processed_matrix_metadata_available':True, 'processed_matrix_values_read':False,
               'source_only_processed_normalization_guarantee':False}
    with (LOG/'RNA_DATA_METADATA_SUMMARY.json').open('x', encoding='utf-8') as stream:
        json.dump(summary, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    paths = sorted(path for path in SOURCES.rglob('*') if path.is_file())
    paths += [LOG/name for name in ['RNA_METADATA_PROTOCOL.md','RNA_IDENTITY_MANIFEST.json',
              'RNA_ARCHIVE_HEADS.json','RNA_DATA_RECOMMENDATION.md','WEB_METADATA_DISCOVERY.md','RNA_DATA_METADATA_SUMMARY.json']]
    names = ['rna_metadata_sources.py','rna_metadata_followup.py','build_rna_manifest.py',
             'rna_archive_heads.py','rna_processed_metadata.py','processed_source_code_metadata.py','seal_data_metadata.py']
    paths += [CODE/name for name in names]
    seal = {'utc':datetime.now(timezone.utc).isoformat(), 'status':'DATA_ROLE_SEALED',
            'files':{path.relative_to(ROOT).as_posix():{'bytes':path.stat().st_size,'sha256':digest(path)} for path in paths},
            'RNA_payload_downloaded_or_parsed':False, 'old_phases_modified':False}
    with (LOG/'DATA_METADATA_SEAL.json').open('x',encoding='utf-8') as stream:
        json.dump(seal,stream,ensure_ascii=False,indent=2)
        stream.write('\n')
    print(json.dumps(summary,ensure_ascii=False))
    print(json.dumps({'sealed_files':len(paths),'seal_sha256':digest(LOG/'DATA_METADATA_SEAL.json')},ensure_ascii=False))


if __name__ == '__main__':
    main()
