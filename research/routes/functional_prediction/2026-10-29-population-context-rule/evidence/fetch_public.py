import sys, json, time, hashlib, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def main():
    tag, url = sys.argv[1:3]
    receipt = {'tag': tag, 'url': url, 'query': sys.argv[3] if len(sys.argv)>3 else None,
               'time_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
               'timeout_s':25, 'automatic_retries':0, 'redirect_following':False,
               'requested_model':'gpt-6.1-sol', 'requested_reasoning':'high',
               'effective_model_settings_tokens_cost':'unknown'}
    try:
        response = urllib.request.build_opener(NoRedirect()).open(
            urllib.request.Request(url, headers={'User-Agent':'MAESTRO-research-evidence/1.0'}), timeout=25)
        receipt.update(status=response.status, headers=dict(response.headers.items()), final_url=response.url)
        body = response.read(8*1024*1024+1)
        receipt['body_bytes']=len(body)
        if len(body)>8*1024*1024:
            raise RuntimeError('per-worker body ceiling exceeded')
        receipt['sha256']=hashlib.sha256(body).hexdigest()
        (ROOT/(tag+'.body')).write_bytes(body)
    except urllib.error.HTTPError as exc:
        body = exc.read(8*1024*1024+1)
        receipt.update(status=exc.code, error=str(exc), headers=dict(exc.headers.items()), body_bytes=len(body))
        (ROOT/(tag+'.body')).write_bytes(body)
    except Exception as exc:
        receipt.update(error=repr(exc), body_bytes=0)
    (ROOT/(tag+'.receipt.json')).write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print(json.dumps(receipt,indent=2))

if __name__=='__main__': main()
