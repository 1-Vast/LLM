"""Bounded primary-literature retrieval; no biological outcome access."""
import hashlib, json, re, time
from pathlib import Path
from urllib.request import Request, urlopen

OUT = Path('log/20261023/action_rule_search/frontier')
OUT.mkdir(parents=True, exist_ok=True)
urls = [
 ('action_search', 'https://arxiv.org/search/?query=action+calibration+world+model&searchtype=all&abstracts=show&order=-announced_date_first&size=50'),
 ('dynamics_search', 'https://arxiv.org/search/?query=test+time+dynamics+adaptation+robotics&searchtype=all&abstracts=show&order=-announced_date_first&size=50'),
]
receipts=[]
for name, url in urls:
    start=time.perf_counter()
    try:
        with urlopen(Request(url, headers={'User-Agent':'MAESTRO research contact primary-source inspection'}), timeout=45) as r:
            body=r.read(); status=r.status; final=r.url
        (OUT/(name+'.html')).write_bytes(body)
        text=re.sub('<[^>]+>', ' ', body.decode('utf-8','replace'))
        text=re.sub(r'\s+', ' ', text)
        (OUT/(name+'.txt')).write_text(text, encoding='utf-8')
        receipts.append(dict(name=name,url=url,final_url=final,status=status,bytes=len(body),sha256=hashlib.sha256(body).hexdigest(),elapsed=time.perf_counter()-start))
    except Exception as e:
        receipts.append(dict(name=name,url=url,error=repr(e),elapsed=time.perf_counter()-start))
(OUT/'SEARCH_RECEIPTS.json').write_text(json.dumps(receipts,indent=2),encoding='utf-8')
print(json.dumps(receipts,indent=2))
