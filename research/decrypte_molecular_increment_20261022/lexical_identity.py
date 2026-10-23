"""Official PubChem chemical identity metadata only; no experimental responses."""
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/decrypte_molecular_increment/review/lexical_sources'


def main():
    OUT.mkdir(exist_ok=True)
    findings = []
    for canonical, internal in [('Carboplatin', 'Carboplatine'), ('Cyclophosphamide', 'Cyclophosphamid'),
                                ('Carboplatine', 'Carboplatin')]:
        url = f'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{canonical}/synonyms/JSON'
        start = datetime.now(timezone.utc).isoformat()
        request = urllib.request.Request(url, headers={'User-Agent': 'MAESTRO-research-source-qualification/1.0'})
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                body = response.read()
                status = response.status
                headers = dict(response.headers)
                final_url = response.url
        except Exception as error:
            failure = {'url': url, 'start_utc': start, 'error': str(error)}
            (OUT / f'{canonical}.failure.json').write_text(json.dumps(failure, indent=2), encoding='utf-8')
            raise
        (OUT / f'{canonical}.body.json').write_bytes(body)
        receipt = {'url': url, 'final_url': final_url, 'start_utc': start,
                   'completed_utc': datetime.now(timezone.utc).isoformat(), 'http_status': status,
                   'response_headers': headers, 'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest(),
                   'scope': 'Official PubChem compound synonyms metadata only'}
        (OUT / f'{canonical}.receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
        information = json.loads(body)['InformationList']['Information']
        matches = [{'CID': info['CID'], 'canonical_exact_present': canonical.casefold() in [s.casefold() for s in info['Synonym']],
                    'internal_exact_present': internal.casefold() in [s.casefold() for s in info['Synonym']],
                    'exact_matched_strings': [s for s in info['Synonym'] if s.casefold() in (canonical.casefold(), internal.casefold())],
                    'synonym_count': len(info['Synonym'])} for info in information]
        findings.append({'canonical': canonical, 'internal': internal, 'matches': matches,
                         'authenticated_exact_synonym': any(x['canonical_exact_present'] and x['internal_exact_present'] for x in matches),
                         'receipt': f'{canonical}.receipt.json'})
    (OUT / 'EXACT_MATCHES.json').write_text(json.dumps(findings, indent=2), encoding='utf-8')
    print(json.dumps(findings, indent=2))


if __name__ == '__main__':
    main()
