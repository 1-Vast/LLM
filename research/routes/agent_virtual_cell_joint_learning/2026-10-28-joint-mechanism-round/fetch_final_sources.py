"""PASS6 source accesses 4-7; inspect bytes only, never run downloaded code."""
from pathlib import Path, PurePosixPath
import concurrent.futures
import hashlib
import io
import json
import stat
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parent / "sources/final_refresh"
jobs = [
    ("organoid_release1.zip", "https://zenodo.org/api/records/14890340/files/yakavetsiv/ml-mf_chemo-1.0.zip/content"),
    ("switched_realization_1103.1343v2.html", "https://arxiv.org/html/1103.1343v2"),
    ("psr_bases_1612.09076v1.html", "https://arxiv.org/html/1612.09076v1"),
    ("predictive_skill_2604.07016v1.html", "https://arxiv.org/html/2604.07016v1"),
]
def fetch(job):
    filename,url=job
    receipt={"date":"2026-10-28","url":url,"file":filename,"automatic_retry":False}
    path=ROOT/filename
    if path.exists():
        return dict(receipt,error="artifact exists; no replay")
    try:
        request=urllib.request.Request(url,headers={"User-Agent":"MAESTRO bounded primary-source reading"})
        with urllib.request.urlopen(request,timeout=25) as response:
            body=response.read(8_000_001)
            assert len(body)<=8_000_000
            receipt.update(status=response.status,final_url=response.url,content_type=response.headers.get("Content-Type"),bytes=len(body),sha256=hashlib.sha256(body).hexdigest())
        path.write_bytes(body)
        if filename.endswith(".zip"):
            archive=zipfile.ZipFile(io.BytesIO(body))
            listing=[]
            destination=ROOT/"organoid_release1"
            for member in archive.infolist():
                name=PurePosixPath(member.filename)
                assert not name.is_absolute() and ".." not in name.parts
                assert not stat.S_ISLNK(member.external_attr>>16)
                if member.is_dir():
                    continue
                assert member.file_size<=2_000_000
                payload=archive.read(member)
                target=destination.joinpath(*name.parts)
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(payload)
                listing.append({"member":member.filename,"bytes":len(payload),"sha256":hashlib.sha256(payload).hexdigest()})
            (ROOT/"organoid_release1_members.json").write_text(json.dumps(listing,indent=2),encoding="utf-8")
    except Exception as error:
        receipt["error"]=f"{type(error).__name__}: {error}"
    return receipt
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    receipts=list(pool.map(fetch,jobs))
(ROOT/"primary_receipts.json").write_text(json.dumps(receipts,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(receipts,ensure_ascii=False))
