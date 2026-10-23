"""Official metadata for newly observed labels; no experimental values."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.request
import urllib.error

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/decrypte_molecular_increment/review/lexical_sources'
findings = []
for canonical, internal in [('Gemcitabine', 'Gemcytabine'), ('Idelalisib', 'Idealisib')]:
    url = f'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{canonical}/synonyms/JSON'
    prefix = OUT / ('additional_' + canonical)
    assert not prefix.with_suffix('.body.json').exists(), 'Do not overwrite prior response'
    started = datetime.now(timezone.utc).isoformat()
    try:
        response = urllib.request.urlopen(url, timeout=45)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        body = response.read()
        receipt = {'url': url, 'final_url': response.url, 'http_status': response.code,
                   'headers': dict(response.headers), 'started_utc': started,
                   'completed_utc': datetime.now(timezone.utc).isoformat(),
                   'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest()}
    prefix.with_suffix('.body.json').write_bytes(body)
    prefix.with_suffix('.receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    result = {'canonical': canonical, 'internal': internal, 'http_status': receipt['http_status'], 'matches': []}
    if receipt['http_status'] == 200:
        for info in json.loads(body)['InformationList']['Information']:
            names = info['Synonym']
            result['matches'].append({'CID': info['CID'], 'synonym_count': len(names),
                                      'canonical_present': any(s.casefold() == canonical.casefold() for s in names),
                                      'internal_present': any(s.casefold() == internal.casefold() for s in names),
                                      'exact_strings': [s for s in names if s.casefold() in (canonical.casefold(), internal.casefold())]})
    findings.append(result)
(OUT / 'ADDITIONAL_EXACT_MATCHES.json').write_text(json.dumps(findings, indent=2), encoding='utf-8')
print(json.dumps(findings, indent=2))
