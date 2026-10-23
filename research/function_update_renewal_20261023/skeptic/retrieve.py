import datetime, hashlib, json, pathlib, urllib.parse
import requests

ROOT = pathlib.Path('log/20261023/function_update_renewal/skeptic')
ROOT.mkdir(parents=True, exist_ok=True)
queries = {
    'online_world': '(all:"world model" AND (all:adaptation OR all:"online learning")) AND submittedDate:[202501010000 TO 202610232359]',
    'update_rule': '(all:"learned optimizer" OR all:"learning update rules" OR all:"learning to optimize") AND submittedDate:[202601010000 TO 202610232359]',
    'cell_feedback': '(all:"perturbation" AND (all:"meta-learning" OR all:"active learning" OR all:"feedback")) AND (cat:q-bio.* OR cat:cs.LG) AND submittedDate:[202501010000 TO 202610232359]',
}
receipts = []
for name, query in queries.items():
    url = 'https://export.arxiv.org/api/query?' + urllib.parse.urlencode({'search_query':query,'start':0,'max_results':25,'sortBy':'submittedDate','sortOrder':'descending'})
    try:
        r = requests.get(url, timeout=60)
        body = r.content
        (ROOT / (name+'.xml')).write_bytes(body)
        receipts.append({'name':name,'query':query,'url':url,'final_url':r.url,'status':r.status_code,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest()})
    except Exception as exc:
        receipts.append({'name':name,'url':url,'error':repr(exc)})
(ROOT/'SEARCH_RECEIPTS.json').write_text(json.dumps(receipts,indent=2),encoding='utf-8')
import xml.etree.ElementTree as ET
summaries = []
for item in receipts:
    if item.get('status') != 200: continue
    doc = ET.fromstring((ROOT/(item['name']+'.xml')).read_bytes())
    for e in doc.findall('{http://www.w3.org/2005/Atom}entry'):
        summaries.append({'query':item['name'],**{k:e.findtext('{http://www.w3.org/2005/Atom}'+k) for k in ['id','title','published','summary']}})
(ROOT/'SEARCH_SUMMARIES.json').write_text(json.dumps(summaries,indent=2),encoding='utf-8')
print(json.dumps(summaries,ensure_ascii=False,indent=2))
