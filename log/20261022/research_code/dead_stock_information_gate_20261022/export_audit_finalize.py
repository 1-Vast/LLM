"""Source-only audit record; reads no CSV or current peer draft."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/dead_stock_information_gate/data_auditor'
OLD = ROOT / 'log/20261022/functional_dynamics_gate/skeptic'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    tree_path = OLD / 'BESTDR_CODE_TREE.body'
    primary_path = OLD / 'BESTDR_PRIMARY.body'
    tree = json.loads(tree_path.read_text(encoding='utf-8'))
    root = ET.fromstring(primary_path.read_bytes())
    paragraphs = [' '.join(''.join(element.itertext()).split()) for element in root.iter('p')]
    primary = [text for text in paragraphs if any(term in text for term in [
        'HCT116 p53-VKI cells (Lahav', 'three regions per well',
        'including the data from the previous experiment'])]
    receipts = []
    for path in sorted(OUT.glob('REQUEST_*.json')):
        receipt = json.loads(path.read_text(encoding='utf-8'))
        body = Path(receipt['body_path'])
        code = Path(receipt['decoded_path'])
        checks = {
            'receipt': str(path), 'path': receipt['path'], 'status': receipt['status'],
            'body_bytes': receipt['body_bytes'], 'decoded_bytes': receipt['decoded_bytes'],
            'body_sha256_matches': sha(body) == receipt['body_sha256'],
            'code_sha256_matches': sha(code) == receipt['decoded_sha256'],
            'blob_verified': receipt['blob_verified'],
            'prior_evidence_still_unchanged': all(sha(Path(name)) == digest
                                                   for name, digest in receipt['previous_evidence_hashes_before'].items())}
        if not all(checks[key] for key in ['body_sha256_matches', 'code_sha256_matches', 'blob_verified', 'prior_evidence_still_unchanged']):
            raise ValueError('audit_integrity_check_failed')
        receipts.append(checks)
    result = {
        'utc': datetime.now(timezone.utc).isoformat(), 'status': 'INDEPENDENT_STATIC_EXPORT_AUDIT_COMPLETE',
        'GET_count': len(receipts), 'maximum_GETs': 4, 'further_GETs_planned': False,
        'total_body_bytes': sum(item['body_bytes'] for item in receipts),
        'total_decoded_code_bytes': sum(item['decoded_bytes'] for item in receipts), 'receipt_checks': receipts,
        'tree_sha': tree['sha'], 'tree_truncated': tree['truncated'], 'tree_file_sha256': sha(tree_path),
        'HCT_cisplatin_seed_export_named_paths': [item['path'] for item in tree['tree']
                                                if re.search('hct116|cisplatin|seed|export', item['path'], re.I)],
        'primary_sha256': sha(primary_path), 'primary_exact_excerpts': primary,
        'numerical_CSV_access': False, 'numerical_count_array_access': False,
        'published_primary_numerical_narrative_exposed': True,
        'current_peer_drafts_read_before_independent': False,
        'independent_draft_sha256': sha(OUT / 'DRAFT.md'),
        'qualification': 'Operational relative-time readout forecasting is admissible; exact channel/dose-epoch/run semantics remain unverified.',
        'cross_file_reuse_warning': 'Primary explicitly says the concentration-response analysis includes data from the prior 0/12 micromolar experiment; do not treat filenames as independent runs.'}
    with (OUT / 'EVIDENCE.json').open('x', encoding='utf-8') as handle:
        json.dump(result, handle, indent=2, ensure_ascii=False)
    print(json.dumps({key: result[key] for key in ['status', 'GET_count', 'total_body_bytes',
                                                  'total_decoded_code_bytes', 'numerical_CSV_access', 'qualification']}))


if __name__ == '__main__':
    main()
