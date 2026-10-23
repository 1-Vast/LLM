"""Exact DOI metadata, conditionally exact PMC Methods source, local text snippets."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys
import requests

ROOT = Path('D:/MAESTRO')
OUT = ROOT / 'log/20261022/generative_repair_renewal/source'
DOI = '10.1038/s41586-026-11001-9'

def request(label, url, cap, params=None):
    assert not (OUT / (label+'.receipt.json')).exists(), 'Do not repeat requests'
    receipt = dict(url=url, params=params, started_utc=datetime.now(timezone.utc).isoformat(),
                   cap=cap, automatic_redirects=False)
    body = bytearray()
    try:
        with requests.get(url, params=params, stream=True, timeout=45, allow_redirects=False) as response:
            receipt.update(status=response.status_code, final_url=response.url, headers=dict(response.headers))
            for chunk in response.iter_content(16384):
                if len(body) + len(chunk) > cap:
                    receipt['body_capped'] = True
                    break
                body.extend(chunk)
    except requests.RequestException as exc:
        receipt['error'] = repr(exc)
    (OUT / (label+'.body')).write_bytes(body)
    receipt.update(bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
    (OUT / (label+'.receipt.json')).write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps(receipt, indent=2))

def local():
    sources = [ROOT / 'tmp/ptv1_src/si.txt', ROOT / 'tmp/ptv1_src/art.txt',
               ROOT / 'research/dual_core_innovation_validation_20261021/SOURCE_MANIFEST.json',
               ROOT / 'data/external/ptv1_proteintalks_20261021/repo/README.md']
    lines = sources[0].read_text(encoding='utf-8', errors='replace').splitlines()
    intervals = [('S1_labels_and_S2_metadata', 14, 56), ('S7_PTNC_and_S8_PTPC', 133, 176),
                 ('specific_dose_response_normalization', 600, 615)]
    result = dict(sources=[dict(path=str(path.relative_to(ROOT)), bytes=path.stat().st_size,
                                sha256=hashlib.sha256(path.read_bytes()).hexdigest()) for path in sources],
                  excerpts=[dict(label=label, start_line=start, end_line=end,
                                 text='\n'.join(lines[start-1:end])) for label,start,end in intervals])
    (OUT / 'LOCAL_EXCERPTS.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(dict(local_sources=len(sources), excerpts=len(intervals))))

if __name__ == '__main__':
    if sys.argv[1] == 'local':
        local()
    elif sys.argv[1] == 'metadata':
        request('epmc_metadata', 'https://www.ebi.ac.uk/europepmc/webservices/rest/search', 1000000,
                dict(query='DOI:'+DOI, format='json', resultType='core'))
    else:
        record = json.loads((OUT / 'epmc_metadata.body').read_text(encoding='utf-8'))
        matches = [item for item in record['resultList']['result'] if item.get('doi','').lower() == DOI]
        assert len(matches) == 1
        item = matches[0]
        assert item.get('pmcid') and item.get('inPMC') == 'Y', 'No authenticated available PMC full text'
        request('epmc_fulltext', 'https://www.ebi.ac.uk/europepmc/webservices/rest/'+item['pmcid']+'/fullTextXML', 5000000)
