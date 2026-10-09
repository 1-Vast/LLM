"""Acquire only original relation/text storages; no full runtime restoration or scoring."""
import json,threading
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
import requests
from acquire_partial import drive_remote,download_member
from probe_sources import RemoteZipFile,fetch_small
import probe_sources

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
ASSETS=ROOT/"data/external/map_module_replacement_20261009"
LIMIT=500_000_000

def main():
    probe_sources.LIMIT=LIMIT
    meta=json.loads((HERE/"mapkg_encoder_METADATA.json").read_text())
    specs={k:v for k,v in meta["tensor_specs"].items() if k.startswith(("text_encoder.","text_projector.","fusion_module."))}
    info={Path(i["name"]).name:i for i in meta["zip_entries"] if "/data/" in i["name"]}
    required={s["storage"]["key"] for s in specs.values()}
    payload=sum(info[k]["size"] for k in required)
    if payload>LIMIT:raise RuntimeError("Relation payload exceeds frozen acquisition cap")
    folder=ASSETS/"relation_storages"
    folder.mkdir(parents=True,exist_ok=True)
    budget={"bytes":0}
    drive=drive_remote("relation_mapkg_encoder","18vL792x-g81SWCpzPvgUbHq3jbR45ttx",1126763160,budget)
    local=threading.local()
    def acquire(key):
        if not hasattr(local,"session"):
            from urllib3.util.retry import Retry
            local.session=requests.Session()
            local.session.mount("https://",requests.adapters.HTTPAdapter(max_retries=Retry(total=3,connect=3,status=3,backoff_factor=.2,status_forcelist=[429,500,502,503,504])))
        sub_budget={"bytes":0}
        remote=RemoteZipFile(drive.source,drive.size,sub_budget,"relation_mapkg_encoder",session=local.session,target=drive.url,params=drive.params)
        try:
            _,receipt=download_member(remote,info[key],folder)
            return receipt,remote.receipts,sub_budget["bytes"],None
        except Exception as exc:return None,remote.receipts,sub_budget["bytes"],str(exc)
    members,ranges,errors=[],[],[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs={pool.submit(acquire,k):k for k in sorted(required,key=int)}
        for future in as_completed(jobs):
            receipt,rr,size,error=future.result()
            budget["bytes"]+=size
            ranges.extend(rr)
            if error:errors.append({"key":jobs[future],"error":error})
            else:members.append(receipt)
            if len(members)%25==0:print("Relation members",len(members),"/",len(required),"bytes",budget["bytes"],flush=True)
    (HERE/"RELATION_DOWNLOAD_ERRORS.json").write_text(json.dumps(errors,indent=2),encoding="utf-8")
    receipts=[]
    metadata=requests.get("https://huggingface.co/api/models/dmis-lab/biobert-v1.1",timeout=(20,35))
    metadata.raise_for_status()
    body=metadata.json()
    (HERE/"sources/BIOBERT_METADATA.json").write_bytes(metadata.content)
    revision=body["sha"]
    tokenizer=ASSETS/"biobert_tokenizer"
    tokenizer.mkdir(exist_ok=True)
    available={x["rfilename"] for x in body.get("siblings",[])}
    for name in ["config.json","vocab.txt","tokenizer_config.json","special_tokens_map.json","tokenizer.json"]:
        if name not in available:continue
        r=requests.get(f"https://huggingface.co/dmis-lab/biobert-v1.1/resolve/{revision}/{name}",timeout=(20,35))
        r.raise_for_status()
        if len(r.content)>3_000_000:raise RuntimeError("Unexpected tokenizer asset size")
        (tokenizer/name).write_bytes(r.content)
        import hashlib
        receipts.append({"source":f"https://huggingface.co/dmis-lab/biobert-v1.1/resolve/{revision}/{name}","file":str((tokenizer/name).relative_to(ROOT)),"bytes":len(r.content),"sha256":hashlib.sha256(r.content).hexdigest()})
        budget["bytes"]+=len(r.content)
    if errors:raise RuntimeError(f"Retained completed relation subsets; {len(errors)} failed members")
    report={"budget_bytes":LIMIT,"network_body_bytes":budget["bytes"],"raw_original_storage_bytes":payload,
            "selected_tensors":len(specs),"member_count":len(members),"tokenizer_revision":revision,
            "members":members,"tokenizer_assets":receipts,"ranges":ranges,
            "whole_checkpoint_sha256_verified":False,"scoring_performed":False,
            "scope":"Original fine-tuned text tower, text head and GatedFusion subset only; file-ID/range/member-CRC/local-hash integrity, no full MAP runtime or RNA."}
    (HERE/"RELATION_ASSET_RECEIPTS.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k not in ["members","ranges"]},indent=2),flush=True)

if __name__=="__main__":main()

