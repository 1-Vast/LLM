"""One alternative primary-text route after EuropePMC fulltext HTTP500."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/next_mechanism/root/literature'
URL = 'https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_xml/PMC13528695/unicode'


def main():
    row = {'utc': datetime.now(timezone.utc).isoformat(), 'url': URL,
        'purpose': 'One alternative to failed EuropePMC route; obtain primary methods/data availability before any candidate or numerical work',
        'scope': 'public article text only; no assay/count arrays or author-result replication',
        'code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    with (OUT / 'PROFET_ALTERNATIVE_PROTOCOL.json').open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(row, handle, indent=2)
    try:
        with urlopen(Request(URL, headers={'User-Agent': 'MAESTRO-public-research/1.0'}), timeout=45) as response:
            body = response.read(5_000_001)
            row.update(status=response.status, final_url=response.url, bytes=len(body),
                       sha256=hashlib.sha256(body).hexdigest())
        with (OUT / 'profet_bioc.body').open('xb') as handle:
            handle.write(body)
        assert len(body) <= 5_000_000
        tree = ET.fromstring(body)
        passages = [' '.join(''.join(n.itertext()).split()) for n in tree.iter('passage')]
        with (OUT / 'profet_bioc.txt').open('x', encoding='utf-8', newline='\n') as handle:
            handle.write('\n\n'.join(passages))
        row.update(passages=len(passages), primary_body_available=len(passages) > 0)
    except Exception as exc:
        row.update(error_type=type(exc).__name__, error=str(exc))
    with (OUT / 'PROFET_ALTERNATIVE_RECEIPT.json').open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(row, handle, indent=2)
    print(json.dumps(row))


if __name__ == '__main__':
    main()
