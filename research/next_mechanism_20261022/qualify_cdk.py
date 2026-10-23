"""Follow one exact primary reference, without downloading assay data."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/next_mechanism/root/literature'
DOI = '10.1186/s13073-026-01690-2'


def fetch(name, url, receipts):
    row = {'name': name, 'url': url, 'utc': datetime.now(timezone.utc).isoformat()}
    try:
        with urlopen(Request(url, headers={'User-Agent': 'MAESTRO-public-research/1.0'}), timeout=45) as response:
            body = response.read(5_000_001)
            row.update(status=response.status, final_url=response.url, bytes=len(body),
                       sha256=hashlib.sha256(body).hexdigest())
        with (OUT / (name + '.body')).open('xb') as handle:
            handle.write(body)
        assert len(body) <= 5_000_000
        receipts.append(row)
        return body
    except Exception as exc:
        row.update(error_type=type(exc).__name__, error=str(exc))
        receipts.append(row)
        return None


def main():
    with (OUT / 'CDK_PROTOCOL.json').open('x', encoding='utf-8', newline='\n') as handle:
        json.dump({'utc': datetime.now(timezone.utc).isoformat(), 'before_requests': True,
            'doi': DOI, 'source': 'Exact original reference and GSE326012 attribution in now-acquired PROFET primary text',
            'question': 'Does the original CDK4/6 resistance study provide early state, functional response and independent drug/background/run joins beyond parental/resistant endpoints?',
            'scope': 'metadata and published text only; no supplement/data matrix or raw count download',
            'stop': 'No numerical expansion or task relabeling absent an authenticated independent state/function contract',
            'code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}, handle, indent=2)
    receipts = []
    body = fetch('cdk_metadata', 'https://www.ebi.ac.uk/europepmc/webservices/rest/search?' +
                 urlencode({'query': 'DOI:' + DOI, 'format': 'json', 'resultType': 'core'}), receipts)
    if body:
        records = json.loads(body)['resultList']['result']
        assert len(records) == 1 and records[0]['doi'].lower() == DOI.lower()
        pmcid = records[0].get('pmcid')
        if pmcid:
            full = fetch('cdk_bioc', 'https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_xml/' + pmcid + '/unicode', receipts)
            if full:
                passages = [p.findtext('text') or '' for p in ET.fromstring(full).iter('passage')]
                with (OUT / 'cdk_bioc.txt').open('x', encoding='utf-8', newline='\n') as handle:
                    handle.write('\n\n'.join(passages))
                receipts[-1].update(passages=len(passages), pmcid=pmcid)
    with (OUT / 'CDK_RECEIPTS.json').open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(receipts, handle, indent=2)
    print(json.dumps(receipts))


if __name__ == '__main__':
    main()
