"""Inspect retained publisher error body and obtain official PMC OA metadata."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import requests
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/hcc_link_recovery'


def fetch(name, url):
    start = datetime.now(timezone.utc).isoformat()
    r = requests.get(url, timeout=(15, 40))
    path = OUT / name
    assert not path.exists()
    path.write_bytes(r.content)
    receipt = dict(url=url, final_url=r.url, status=r.status_code,
                   utc_start=start, utc_end=datetime.now(timezone.utc).isoformat(),
                   bytes=len(r.content), sha256=hashlib.sha256(r.content).hexdigest(),
                   content_type=r.headers.get('Content-Type'))
    (OUT / (name + '.receipt.json')).write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    return r


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    old = ROOT / 'log/20261023/hcc_task_qualification/sciencedirect.html'
    raw = old.read_text(encoding='utf-8', errors='replace')
    # Require real URLs, not strings inside encoded challenge images.
    links = sorted(set(re.findall(r'https?://[^\s"<>]+', raw)))
    candidates = [x for x in links if any(s in x.lower() for s in ['els-cdn', '.xlsx', '.xls', 'mmc'])]
    (OUT / 'EXISTING_HTML_LINKS.json').write_text(json.dumps(dict(
        source=old.relative_to(ROOT).as_posix(), sha256=hashlib.sha256(old.read_bytes()).hexdigest(),
        bytes=old.stat().st_size, literal_url_count=len(links), attachment_candidates=candidates), indent=2), encoding='utf-8')
    r = fetch('pmc_oa.xml', 'https://pmc.ncbi.nlm.nih.gov/utils/oa/oa.fcgi?id=PMC12205652')
    result = dict(status=r.status_code, links=[])
    try:
        tree = ET.fromstring(r.content)
        result['links'] = [dict(x.attrib) for x in tree.iter('link')]
        result['errors'] = [dict(code=x.get('code'), text=x.text) for x in tree.iter('error')]
    except ET.ParseError as exc:
        result['parse_error'] = str(exc)
    (OUT / 'PMC_OA_LINKS.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
