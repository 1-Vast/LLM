from discover import fetch
import concurrent.futures
import hashlib
import json
import requests

QUERIES = {
    'cipa_multisite': '(TITLE_ABS:"cardiomyocytes" AND TITLE_ABS:"28" AND (TITLE_ABS:"blinded" OR TITLE_ABS:"multisite" OR TITLE_ABS:"multicenter")) AND OPEN_ACCESS:Y NOT PUB_TYPE:Review',
    'cardiac_signal_data': '(TITLE_ABS:"cardiomyocytes" AND (TITLE_ABS:"Zenodo" OR TITLE_ABS:"Figshare" OR TITLE_ABS:"publicly")) AND OPEN_ACCESS:Y NOT PUB_TYPE:Review',
}
def github():
    url = 'https://api.github.com/repos/Danny-Vu/Syracuse-TAMU/git/trees/main?recursive=1'
    response = requests.get(url, timeout=90)
    with (fetch.__globals__['OUT'] / 'cardiac_ai_github_tree.body').open('xb') as f:
        f.write(response.content)
    receipt={'url':url,'status':response.status_code,'bytes':len(response.content),'sha256':hashlib.sha256(response.content).hexdigest()}
    (fetch.__globals__['OUT'] / 'cardiac_ai_github_tree.receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    return {'receipt':receipt,'tree':response.json().get('tree')}
if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        jobs=[pool.submit(fetch,item) for item in QUERIES.items()]+[pool.submit(github)]
        for job in jobs:
            print(json.dumps(job.result()))
