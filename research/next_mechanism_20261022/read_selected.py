"""Acquire two selected primary papers, keeping bytes and section boundaries."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/next_mechanism/root/literature'
SOURCES = {'profet': 'PMC13528695', 'weak_pde': 'PMC12578354'}


def get(item):
    name, pmcid = item
    url = f'https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML'
    row = {'name': name, 'pmcid': pmcid, 'url': url, 'utc': datetime.now(timezone.utc).isoformat()}
    try:
        with urlopen(Request(url, headers={'User-Agent': 'MAESTRO-public-research/1.0'}), timeout=45) as response:
            body = response.read(5_000_001)
            row.update(status=response.status, final_url=response.url, bytes=len(body),
                       sha256=hashlib.sha256(body).hexdigest())
        with (OUT / (name + '.xml')).open('xb') as handle:
            handle.write(body)
        assert len(body) <= 5_000_000
        tree = ET.fromstring(body)
        sections = []
        for node in tree.iter():
            if node.tag in ('article-title', 'title', 'p', 'table-wrap', 'supplementary-material'):
                sections.append('[' + node.tag + '] ' + ' '.join(''.join(node.itertext()).split()))
        with (OUT / (name + '.txt')).open('x', encoding='utf-8', newline='\n') as handle:
            handle.write('\n\n'.join(sections))
        links = [{**node.attrib, 'text': ''.join(node.itertext())}
                 for node in tree.iter() if node.tag in ('ext-link', 'supplementary-material', 'media')]
        with (OUT / (name + '.links.json')).open('x', encoding='utf-8', newline='\n') as handle:
            json.dump(links, handle, indent=2)
        row.update(extracted_nodes=len(sections))
    except Exception as exc:
        row.update(error_type=type(exc).__name__, error=str(exc))
    return row


def main():
    with (OUT / 'SELECTED_PROTOCOL.json').open('x', encoding='utf-8', newline='\n') as handle:
        json.dump({'utc': datetime.now(timezone.utc).isoformat(), 'before_requests': True,
            'sources': SOURCES, 'reason': 'new time-resolved treatment state and functional-spatial observation candidates; BESTDR was already reviewed, not reacquired',
            'scope': 'published fulltext including reported results; no assay matrix decode or performance replication',
            'code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}, handle, indent=2)
    with ThreadPoolExecutor(max_workers=2) as pool:
        rows = list(pool.map(get, SOURCES.items()))
    with (OUT / 'SELECTED_RECEIPTS.json').open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(rows, handle, indent=2)
    print(json.dumps(rows))


if __name__ == '__main__':
    main()
