"""Bounded public original/identity retrieval; preserve bodies, execute none."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261023/functional_error_renewal/root_sources'
SOURCES = {
    'cd14_identity': 'https://rest.ensembl.org/lookup/id/ENSG00000170458?content-type=application/json',
    'beataml_search': 'https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=TITLE:%22Integrative%20analysis%20of%20drug%20response%20and%20clinical%20outcome%20in%20acute%20myeloid%20leukemia%22&format=json',
}

if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    for name, url in SOURCES.items():
        target = OUT/f'{name}.receipt.json'
        if target.exists():
            raise FileExistsError(target)
        receipt = {'url': url, 'utc': datetime.now(timezone.utc).isoformat()}
        try:
            result = requests.get(url, timeout=45)
            body = result.content
            (OUT/f'{name}.body').write_bytes(body)
            receipt.update(status=result.status_code, final_url=result.url, bytes=len(body),
                           sha256=hashlib.sha256(body).hexdigest())
        except requests.RequestException as error:
            receipt.update(error=type(error).__name__)
        target.write_text(json.dumps(receipt, indent=2), encoding='utf-8')
        print(json.dumps(receipt))
