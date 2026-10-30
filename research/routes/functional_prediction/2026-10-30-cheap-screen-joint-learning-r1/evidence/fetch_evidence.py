"""Bounded source acquisition only; never decode assay outcomes."""
import datetime, hashlib, json, pathlib, subprocess, sys
from urllib.parse import urlencode

BASE = pathlib.Path(__file__).parent
ledger = BASE / 'requests.json'
rows = json.loads(ledger.read_text()) if ledger.exists() else []
name, url = sys.argv[1:3]
if len(rows) >= 24:
    raise SystemExit('request budget exhausted')
out = BASE / (name + '.body')
if out.exists():
    raise SystemExit('preserve existing body')
start = datetime.datetime.now(datetime.timezone.utc).isoformat()
cmd = ['curl.exe', '--silent', '--show-error', '--max-time', '25', '--retry', '0',
       '--max-filesize', '10000000', '--dump-header', str(BASE / (name+'.headers')),
       '--output', str(out), '--write-out', '%{http_code}\n%{size_download}\n%{url_effective}', url]
p = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
body = out.read_bytes() if out.exists() else b''
row = dict(name=name, url=url, started_utc=start, exit_code=p.returncode,
           transfer=p.stdout, error=p.stderr, received_saved_bytes=len(body),
           sha256=hashlib.sha256(body).hexdigest(), automatic_retries=0,
           automatic_redirects=False, deadline_seconds=25)
rows.append(row)
ledger.write_text(json.dumps(rows,indent=2),encoding='utf-8')
print(json.dumps(row))
