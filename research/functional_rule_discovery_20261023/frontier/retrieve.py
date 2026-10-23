"""Four-request bounded primary search; no biological dataset access."""
import hashlib,json,re,time
from pathlib import Path
from urllib.request import Request,urlopen
out=Path('log/20261023/functional_rule_discovery/frontier')
out.mkdir(parents=True,exist_ok=True)
queries=[('update_search','https://arxiv.org/search/?query=learned+optimizer+functional+feedback+world+model&searchtype=all&abstracts=show&order=-announced_date_first&size=50'),('meta_search','https://arxiv.org/search/?query=meta+learning+test+time+adaptation+residual+posterior&searchtype=all&abstracts=show&order=-announced_date_first&size=50')]
receipts=[]
for name,url in queries:
    t=time.perf_counter()
    try:
        with urlopen(Request(url,headers={'User-Agent':'MAESTRO primary source research'}),timeout=45) as r:
            body=r.read(); status=r.status; final=r.url
        (out/(name+'.html')).write_bytes(body)
        receipts.append(dict(name=name,url=url,final_url=final,status=status,bytes=len(body),sha256=hashlib.sha256(body).hexdigest(),seconds=time.perf_counter()-t))
        print(name)
        for b in re.split(r'<li class="arxiv-result">',body.decode('utf-8','replace'))[1:26]:
            title=re.search(r'<p class="title[^>]*>(.*?)</p>',b,re.S)
            ident=re.search(r'https://arxiv.org/abs/([\d.]+)',b)
            print(ident.group(1) if ident else '?',re.sub('<[^>]+>',' ',title.group(1)).strip() if title else '?')
    except Exception as e:
        receipts.append(dict(name=name,url=url,error=repr(e),seconds=time.perf_counter()-t))
(out/'SEARCH_RECEIPTS.json').write_text(json.dumps(receipts,indent=2),encoding='utf-8')
