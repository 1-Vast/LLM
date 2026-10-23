"""Anonymous author-declared repository file listing, never raw MS downloads."""
import datetime as dt
import ftplib
import json
from pathlib import Path
import sys

OUT=Path(__file__).resolve().parents[2]/'log/20261022/decrypte_feedback_pilot/molecular'
key=sys.argv[1]
path=sys.argv[2] if len(sys.argv)>2 else '/v06/MSV000093659'
record={'host':'massive-ftp.ucsd.edu','path':path,'utc':dt.datetime.now(dt.timezone.utc).isoformat(),'protocol':'anonymous FTP metadata listing; not TLS-authenticated'}
try:
    with ftplib.FTP(record['host'],timeout=35) as ftp:
        ftp.login()
        rows=[]
        ftp.retrlines('LIST '+path,rows.append)
        record['listing']=rows
except Exception as exc:
    record.update(error=type(exc).__name__,message=str(exc))
(OUT/(key+'.json')).write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps(record,indent=2))
