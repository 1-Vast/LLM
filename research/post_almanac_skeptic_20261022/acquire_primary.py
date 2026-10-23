from pathlib import Path
import requests,json,hashlib,datetime
out=Path('log/20261022/post_almanac_mechanism/skeptic/primary')
items=[('dgm_2025','https://arxiv.org/html/2505.22954v1'),('sica_2025','https://arxiv.org/html/2504.15228v1'),('gradient_history_2026','https://arxiv.org/html/2610.09604v1')]
for name,url in items:
    receipt={'url':url,'requested_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'primary paper only; no biological values'}
    try:
        r=requests.get(url,timeout=45); receipt.update(status=r.status_code,bytes=len(r.content),sha256=hashlib.sha256(r.content).hexdigest(),final_url=r.url)
        (out/(name+'.body')).write_bytes(r.content)
    except Exception as e:receipt['error']=repr(e)
    (out/(name+'.request.json')).write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print(name,receipt)
