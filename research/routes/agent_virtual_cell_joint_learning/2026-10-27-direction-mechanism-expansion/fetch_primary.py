"""Read public bibliographic endpoints and retain receipts; no datasets or models."""
from pathlib import Path
import datetime
import hashlib
import json
import urllib.parse
import urllib.request

root = Path(__file__).parent / 'primary'
root.mkdir(exist_ok=True)
dois = ['10.3390/genes17070816', '10.1038/s41467-026-72903-w',
        '10.1186/s13321-026-01242-1']
receipts = []
for doi in dois:
    tag = doi.replace('/', '_')
    query = urllib.parse.urlencode({'query': 'DOI:'+doi, 'format':'json', 'resultType':'core'})
    url = 'https://www.ebi.ac.uk/europepmc/webservices/rest/search?'+query
    try:
        with urllib.request.urlopen(url, timeout=25) as response:
            raw = response.read()
        (root/(tag+'.json')).write_bytes(raw)
        results = json.loads(raw)['resultList']['result']
        print(doi, [(r.get('pmcid'), r.get('title')) for r in results])
        receipts.append({'doi':doi, 'url':url, 'bytes':len(raw), 'sha256':hashlib.sha256(raw).hexdigest()})
        for item in results[:1]:
            pmcid = item.get('pmcid')
            if not pmcid:
                continue
            url_xml = 'https://www.ebi.ac.uk/europepmc/webservices/rest/'+pmcid+'/fullTextXML'
            try:
                with urllib.request.urlopen(url_xml, timeout=25) as response:
                    xml = response.read()
                if b'<article' not in xml[:5000]:
                    raise ValueError('No JATS article marker')
                (root/(pmcid+'.xml')).write_bytes(xml)
                receipts.append({'doi':doi, 'url':url_xml, 'bytes':len(xml), 'sha256':hashlib.sha256(xml).hexdigest()})
                print(pmcid,'JATS stored',len(xml))
            except Exception as exc:
                receipts.append({'doi':doi,'url':url_xml,'failure':str(exc)})
                print(pmcid,type(exc).__name__)
    except Exception as exc:
        receipts.append({'doi':doi,'url':url,'failure':str(exc)})
        print(doi,type(exc).__name__)
(root/'receipts.json').write_text(json.dumps({'date_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'requests':receipts},ensure_ascii=False,indent=2),encoding='utf-8')
