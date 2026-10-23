from pathlib import Path
import hashlib
import json
import requests

OUT=Path('log/20261023/function_update_renewal/constructive')
URLS={
 'patchworld':'https://arxiv.org/html/2605.30880v1',
 'skillgrad':'https://arxiv.org/html/2605.27760v1',
 'ambimod':'https://arxiv.org/html/2609.32527v1',
 'primed':'https://arxiv.org/html/2503.20767v2',
 'pie':'https://api.biorxiv.org/details/biorxiv/2026.10.02.756297',
 'response_compound':'https://api.biorxiv.org/details/biorxiv/2026.09.28.755146',
 'tdal':'https://arxiv.org/html/2610.22122v2',
}
if __name__=='__main__':
 for key,url in URLS.items():
  try:
   r=requests.get(url,timeout=45)
   (OUT/f'{key}.body').write_bytes(r.content)
   rec={'url':url,'final_url':r.url,'status':r.status_code,'bytes':len(r.content),'sha256':hashlib.sha256(r.content).hexdigest()}
   (OUT/f'{key}.receipt.json').write_text(json.dumps(rec,indent=2))
   print(key,rec)
  except requests.RequestException as e:
   (OUT/f'{key}.failure.txt').write_text(repr(e))
   print(key,repr(e))
