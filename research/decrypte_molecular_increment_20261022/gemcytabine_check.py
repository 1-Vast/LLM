"""Bounded official metadata followups for an unresolved label."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.request
import urllib.error

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/decrypte_molecular_increment/review/lexical_sources'
report = []
for name, url in [('CHEBI175901', 'https://www.ebi.ac.uk/chebi/backend/api/public/compound/175901/'),
                  ('PubChem_Gemcytabine', 'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/Gemcytabine/synonyms/JSON')]:
    prefix = OUT / name
    assert not prefix.with_suffix('.body.json').exists()
    start = datetime.now(timezone.utc).isoformat()
    try:
        response = urllib.request.urlopen(url, timeout=45)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        body = response.read()
        receipt = {'url': url, 'final_url': response.url, 'http_status': response.code,
                   'headers': dict(response.headers), 'started_utc': start,
                   'completed_utc': datetime.now(timezone.utc).isoformat(), 'bytes': len(body),
                   'sha256': hashlib.sha256(body).hexdigest()}
    prefix.with_suffix('.body.json').write_bytes(body)
    prefix.with_suffix('.receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    result = {'source': name, 'http_status': receipt['http_status']}
    if receipt['http_status'] == 200:
        data = json.loads(body)
        if name.startswith('CHEBI'):
            names = [entry['name'] for values in data['names'].values() for entry in values]
            result.update(accession=data['chebi_accession'], main_name=data['name'],
                          gemcytabine_exact_present=any(s.casefold() == 'gemcytabine' for s in names),
                          names=names)
        else:
            result['information'] = data.get('InformationList', {}).get('Information', [])
    report.append(result)
(OUT / 'GEMCYTABINE_FOLLOWUP.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))
