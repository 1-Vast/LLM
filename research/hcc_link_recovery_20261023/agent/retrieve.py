import datetime
import hashlib
import json
from pathlib import Path
import urllib.request
import urllib.error

OUT = Path('log/20261023/hcc_link_recovery/agent')
SOURCES = [
    ('crossref', 'https://api.crossref.org/works/10.1016/j.jhepr.2025.101426'),
    ('elsevier_article', 'https://api.elsevier.com/content/article/pii/S258955592500103X?httpAccept=text/xml'),
    ('ncbi_oa', 'https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=PMC12205652'),
    ('epmc_core', 'https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:PMC12205652&format=json&resultType=core'),
]

for name, url in SOURCES:
    start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    request = urllib.request.Request(url, headers={'User-Agent': 'MAESTRO-source-qualification/1.0'})
    error = None
    try:
        response = urllib.request.urlopen(request, timeout=45)
    except urllib.error.HTTPError as exc:
        response = exc
        error = str(exc)
    except Exception as exc:
        receipt = {'url': url, 'start': start, 'end': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'error': repr(exc)}
        (OUT / (name + '.receipt.json')).write_text(json.dumps(receipt, indent=2), encoding='utf-8')
        print(name, 'transport error', repr(exc), flush=True)
        continue
    body = response.read()
    (OUT / (name + '.body')).write_bytes(body)
    receipt = {'url': url, 'final_url': response.geturl(), 'start': start, 'end': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status': response.status, 'headers': dict(response.headers), 'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest(), 'error': error}
    (OUT / (name + '.receipt.json')).write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(name, receipt['status'], len(body), flush=True)
