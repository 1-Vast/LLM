"""Download selected processed resources via Windows certificate-verified curl."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from urllib.parse import quote

OUT=Path(__file__).resolve().parents[2]/'log/20261022/decrypte_feedback_pilot/molecular'
key, descriptor=sys.argv[1:3]
url='https://massive.ucsd.edu/ProteoSAFe/DownloadResultFile?file='+quote(descriptor,safe='')+'&forceDownload=true'
body=OUT/(key+'.body')
if body.exists():
    raise RuntimeError('Refuse overwrite')
record={'url':url,'descriptor':descriptor,'utc':dt.datetime.now(dt.timezone.utc).isoformat(),'scope':'processed file archived; only header decode authorized','tls':'Windows curl Schannel default verification'}
result=subprocess.run(['curl.exe','--silent','--show-error','--max-time','60','--location','--dump-header',str(OUT/(key+'.headers')),'--output',str(body),url],capture_output=True,text=True)
record.update(exit_code=result.returncode,stderr=result.stderr)
if body.exists():
    raw=body.read_bytes()
    record.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
(OUT/(key+'.receipt.json')).write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps(record,indent=2))
