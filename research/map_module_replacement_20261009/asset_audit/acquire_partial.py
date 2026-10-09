"""Acquire selected original torch ZIP members with bounded official HTTP ranges."""
import io, json, hashlib, re, struct, zlib, zipfile, pickle, ast
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from pathlib import Path
from html import unescape
import numpy as np
import pandas as pd
import requests
import torch
from probe_sources import RemoteZipFile, MetadataOnlyUnpickler, TensorSpec, digest

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
ASSETS = ROOT / "data/external/map_module_replacement_20261009"
MAX_BYTES = 130_000_000

def file_sha(path):
    return hashlib.file_digest(path.open("rb"),"sha256").hexdigest()

def prior_network_bytes():
    specs = ["SOURCE_RECEIPTS.json", "ISSUE_COMMENT_RECEIPTS.json"]
    total = sum(x.get("bytes",0) for name in specs for x in json.loads((OUT/name).read_text()))
    total += sum(x["bytes"] for x in json.loads((OUT/"RANGE_RECEIPTS.json").read_text()))
    p=OUT/"sources/MAPKG_CONFIRM.html"
    total += p.stat().st_size if p.exists() else 0
    # A stopped sequential run retained raw bytes but its in-memory range log
    # was not flushed. Count all retained payloads plus a conservative 1 MB
    # allowance for its metadata/header/in-flight transfers. This is an upper
    # bound, not a fabricated exact network receipt.
    retained=sum(p.stat().st_size for folder in [ASSETS/"mapkg_storages",ASSETS/"protein_storages"]
                 if folder.exists() for p in folder.iterdir() if p.is_file())
    reconstructed=total+retained+(1_000_000 if retained else 0)
    recorded=json.loads((OUT/"NETWORK_BUDGET.json").read_text())["bytes"] if (OUT/"NETWORK_BUDGET.json").exists() else 0
    return max(reconstructed,recorded)

def protein_gallery(esm):
    nodes=pd.read_csv(ROOT/"data/external/mapkg_20261009/GENE_tahoe_filtered.csv",dtype=str,keep_default_na=False)
    by_id=defaultdict(set)
    by_symbol=defaultdict(set)
    for row in nodes.to_dict("records"):
        gene,symbol=row["Gene stable ID"],row["ESM"]
        if gene and symbol:
            by_id[gene].add(symbol)
            by_symbol[symbol].add(gene)
    valid={gene:next(iter(symbols)) for gene,symbols in by_id.items()
           if len(symbols)==1 and len(by_symbol[next(iter(symbols))])==1
           and next(iter(symbols)) in esm["tensor_specs"]}
    audit=json.loads((ROOT/"outputs/knowledge_layer_validation_20261009/AUDIT.json").read_text())
    menu_targets={e["gene"] for row in audit["records"] for e in row["edges"]}
    # The original audit uses canonical evidence dictionaries; keep stable IDs.
    available_targets=sorted(g for g in menu_targets if g in valid)
    target_symbols={valid[g] for g in available_targets}
    global_pairs=sorted((symbol,gene) for gene,symbol in valid.items() if symbol not in target_symbols)
    rng=np.random.default_rng(20261009)
    sample=np.sort(rng.choice(len(global_pairs),size=1000,replace=False))
    distractors=[global_pairs[int(i)] for i in sample]
    records=[{"gene_id":g,"symbol":valid[g],"role":"menu_target"} for g in available_targets]
    records.extend({"gene_id":gene,"symbol":symbol,"role":"fixed_global_distractor"} for symbol,gene in distractors)
    records.sort(key=lambda r:r["gene_id"])
    return {"seed":20261009,"distractor_count":1000,"gallery":records,
            "global_unique_gene_ids":len(by_id),"global_valid_bijective_gene_symbol_mappings":len(valid),
            "menu_target_ids_all":sorted(menu_targets),"menu_targets_retained":available_targets,
            "menu_target_exclusions":[{"gene_id":g,"symbols":sorted(by_id.get(g,[])),
                                      "reason":"ambiguous_id_or_symbol_mapping_or_missing_ESM"} for g in sorted(menu_targets-set(available_targets))],
            "mapping_rule":"Exact stable gene ID -> exactly one ESM symbol; symbol -> exactly one stable ID; exact symbol present in released ESM lookup. Duplicate identical rows collapse; ambiguous mappings remain documented exclusions.",
            "gallery_scope":"All resolvable menu known-edge targets plus fixed 1000 global eligible distractors; target-enriched, not genome-wide."}

def drive_remote(asset_name,file_id,size,budget):
    source=f"https://drive.google.com/uc?export=download&id={file_id}"
    session=requests.Session()
    response=session.get(source,timeout=(20,35))
    response.raise_for_status()
    budget["bytes"]+=len(response.content)
    fields=dict(re.findall(r'<input[^>]+name="([^"]+)"[^>]+value="([^"]*)"',response.text))
    action=re.search(r'<form[^>]+action="([^"]+)"',response.text)
    if not action or "confirm" not in fields:raise RuntimeError("Drive confirmation unavailable")
    # The confirmation form is public download routing, not authorization material.
    (OUT/"sources"/f"{asset_name}_CONFIRM.html").write_bytes(response.content)
    remote=RemoteZipFile(source,size,budget,asset_name,session=session,target=unescape(action.group(1)),params=fields)
    return remote

def catalog(remote):
    with zipfile.ZipFile(remote) as archive:
        info=[{"name":i.filename,"size":i.file_size,"compressed_size":i.compress_size,
               "compression":i.compress_type,"crc32":f"{i.CRC:08x}","header_offset":i.header_offset}
              for i in archive.infolist()]
        # Read only checkpoint metadata; never deserialize unapproved code.
        pklname=next(i.filename for i in archive.infolist() if i.filename.endswith("/data.pkl"))
        data=archive.read(pklname)
    value=MetadataOnlyUnpickler(io.BytesIO(data)).load()
    state=value.get("model_state_dict",value)
    (OUT/"sources"/f"{remote.name}.data.pkl").write_bytes(data)
    return {"source":remote.source,"advertised_bytes":remote.size,"zip_entries":info,
            "pickle_entry":pklname,"pickle_sha256":digest(data),
            "tensor_specs":{str(k):dict(v) for k,v in state.items() if isinstance(v,TensorSpec)},
            "top_level_keys":list(value),"parsed_without_tensor_payload_or_arbitrary_globals":True}

def download_member(remote,info,folder):
    destination=folder/Path(info["name"]).name
    if destination.exists():
        data=destination.read_bytes()
        if len(data)!=info["size"] or f"{zlib.crc32(data)&0xffffffff:08x}"!=info["crc32"]:
            raise RuntimeError("Existing partial asset CRC/size mismatch")
        return destination,{"asset":remote.name,"member":info["name"],"status":"existing_crc_checked","bytes":len(data),"sha256":digest(data),"crc32":info["crc32"],"file":str(destination.relative_to(ROOT))}
    if info["compression"]!=zipfile.ZIP_STORED:raise RuntimeError("Expected uncompressed torch storage")
    remote.seek(info["header_offset"])
    header=remote.read(30)
    fields=struct.unpack("<IHHHHHIIIHH",header)
    if fields[0]!=0x04034b50:raise RuntimeError("Invalid ZIP member header")
    start=info["header_offset"]+30+fields[-2]+fields[-1]
    remote.seek(start)
    data=remote.read(info["compressed_size"])
    if len(data)!=info["size"] or f"{zlib.crc32(data)&0xffffffff:08x}"!=info["crc32"]:
        raise RuntimeError("Official range payload does not match ZIP CRC")
    destination.write_bytes(data)
    return destination,{"asset":remote.name,"source":remote.source,"member":info["name"],
           "data_start":start,"bytes":len(data),"sha256":digest(data),"crc32":info["crc32"],
           "crc_verified":True,"full_asset_sha256_verified":False,"file":str(destination.relative_to(ROOT))}

def official_projector():
    source=ROOT/"research/knowledge_layer_validation_20261009/sources/MAP-KG__model__model.py"
    tree=ast.parse(source.read_text(encoding="utf-8"))
    node=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=="ResidualProjector")
    scope={"nn":torch.nn,"torch":torch}
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),"exec"),scope)
    return scope["ResidualProjector"]

def materialize(spec,path):
    if spec["storage"]["type"]!="torch.FloatStorage":raise RuntimeError("Unexpected dtype")
    if spec["offset"]!=0:raise RuntimeError("Unexpected offset")
    arr=np.fromfile(path,dtype="<f4")
    if len(arr)!=spec["storage"]["numel"]:raise RuntimeError("Storage numel mismatch")
    tensor=torch.from_numpy(arr).reshape(spec["shape"])
    if list(tensor.stride())!=spec["stride"]:raise RuntimeError("Unsupported view stride")
    return tensor

def main():
    import probe_sources
    probe_sources.LIMIT=MAX_BYTES
    ASSETS.mkdir(parents=True,exist_ok=True)
    (ASSETS/"mapkg_storages").mkdir(exist_ok=True)
    (ASSETS/"protein_storages").mkdir(exist_ok=True)
    budget={"bytes":prior_network_bytes()}
    esm_meta=json.loads((OUT/"protein_embeddings_METADATA.json").read_text())
    gallery=protein_gallery(esm_meta)
    (OUT/"GALLERY_QUALIFICATION.json").write_text(json.dumps(gallery,indent=2),encoding="utf-8")
    print("Gallery mappings",len(gallery["gallery"]),"target exclusions",len(gallery["menu_target_exclusions"]),flush=True)
    drive=drive_remote("mapkg_encoder","18vL792x-g81SWCpzPvgUbHq3jbR45ttx",1126763160,budget)
    members=[]
    try:
        kg_meta=catalog(drive)
        (OUT/"mapkg_encoder_METADATA.json").write_text(json.dumps(kg_meta,indent=2),encoding="utf-8")
        kg_info={Path(i["name"]).name:i for i in kg_meta["zip_entries"] if "/data/" in i["name"]}
        specs={k:v for k,v in kg_meta["tensor_specs"].items() if k.startswith(("gene_projector.","smiles_projector."))}
        paths={}
        for key,spec in specs.items():
            path,receipt=download_member(drive,kg_info[spec["storage"]["key"]],ASSETS/"mapkg_storages")
            paths[key]=path
            members.append(receipt)
            print("Acquired",key,"aggregate",budget["bytes"],flush=True)
        esm_info={Path(i["name"]).name:i for i in esm_meta["zip_entries"] if "/data/" in i["name"]}
        remaining=sum(esm_info[esm_meta["tensor_specs"][row["symbol"]]["storage"]["key"]]["size"]+30
                      for row in gallery["gallery"]
                      if not (ASSETS/"protein_storages"/esm_meta["tensor_specs"][row["symbol"]]["storage"]["key"]).exists())
        if budget["bytes"]+remaining>MAX_BYTES:raise RuntimeError("Conservative aggregate budget would exceed cap")
        endpoint=requests.head(esm_meta["source"],allow_redirects=True,timeout=(20,35))
        endpoint.raise_for_status()
        worker_local=threading.local()
        def acquire_vector(row):
            spec=esm_meta["tensor_specs"][row["symbol"]]
            local_budget={"bytes":0}
            if not hasattr(worker_local,"session"):
                from urllib3.util.retry import Retry
                worker_local.session=requests.Session()
                worker_local.session.mount("https://",requests.adapters.HTTPAdapter(max_retries=Retry(total=3,connect=3,status=3,backoff_factor=.2,status_forcelist=[429,500,502,503,504])))
            remote=RemoteZipFile(esm_meta["source"],410886729,local_budget,"protein_embeddings",session=worker_local.session,target=endpoint.url)
            try:
                path,receipt=download_member(remote,esm_info[spec["storage"]["key"]],ASSETS/"protein_storages")
                return materialize(spec,path).numpy(),receipt,remote.receipts,local_budget["bytes"],None
            except Exception as exc:
                return None,None,remote.receipts,local_budget["bytes"],str(exc)
        vector_receipts=[]
        acquired={}
        errors=[]
        with ThreadPoolExecutor(max_workers=8) as pool:
            jobs={pool.submit(acquire_vector,row):i for i,row in enumerate(gallery["gallery"])}
            for future in as_completed(jobs):
                vector,receipt,ranges,size,error=future.result()
                if error:errors.append({"gallery_index":jobs[future],"error":error})
                else:
                    acquired[jobs[future]]=vector
                    members.append(receipt)
                vector_receipts.extend(ranges)
                budget["bytes"]+=size
                if len(acquired)%100==0:print("Protein vectors",len(acquired),"/",len(gallery["gallery"]),flush=True)
        if errors:
            (OUT/"PARTIAL_DOWNLOAD_ERRORS.json").write_text(json.dumps(errors,indent=2),encoding="utf-8")
            raise RuntimeError(f"{len(errors)} protein range failures; all completed members retained")
        vectors=np.array([acquired[i] for i in range(len(gallery["gallery"]))])
        projector=official_projector()
        gene=projector(5120,1024,1536).eval()
        smiles=projector(256,1024,512).eval()
        gene.load_state_dict({k.removeprefix("gene_projector."):materialize(s,paths[k]) for k,s in specs.items() if k.startswith("gene_projector.")},strict=True)
        smiles.load_state_dict({k.removeprefix("smiles_projector."):materialize(s,paths[k]) for k,s in specs.items() if k.startswith("smiles_projector.")},strict=True)
        torch.set_num_threads(4)
        with torch.inference_mode():
            projected=gene(torch.from_numpy(vectors)).numpy()
            features=np.load(ROOT/"outputs/paper_01286/released_test/FEATURES.npz")
            reconstructed=smiles(torch.from_numpy(features["molecule256"].astype(np.float32))).numpy()
            known=features["knowledge1024"]
            cache_gap=float(np.max(np.abs(reconstructed-known)))
            np.testing.assert_allclose(reconstructed,known,atol=1e-5,rtol=1e-5)
        if not np.isfinite(projected).all():raise RuntimeError("Nonfinite projected proteins")
        np.savez_compressed(ASSETS/"PROTEIN_FEATURES.npz",esm5120=vectors,protein1024=projected,
                            gene_ids=np.array([r["gene_id"] for r in gallery["gallery"]]),
                            symbols=np.array([r["symbol"] for r in gallery["gallery"]]))
        summary={"network_budget_bytes":MAX_BYTES,"network_body_bytes_upper_bound":budget["bytes"],
                 "network_receipt_note":"Includes conservative allowance for an interrupted sequential acquisition whose completed raw members were retained and CRC checked. Per-range receipts cover uninterrupted/new requests; retained-member receipts bind their original ZIP entries and bytes.",
                 "gene_projector_tensors":sum(k.startswith("gene_projector.") for k in specs),
                 "molecule_projector_tensors":sum(k.startswith("smiles_projector.") for k in specs),
                 "protein_vectors":len(vectors),"projected_shape":list(projected.shape),
                 "strict_projector_load":True,"molecule_cache_max_abs_gap":cache_gap,
                 "molecule_cache_reconstruction_passed":True,
                 "partial_member_size_and_crc_verified":True,
                 "whole_checkpoint_sha256_verified":False,
                 "whole_ESM_sha256_verified":False,
                 "provenance_limit":"Current official file-ID/revision range subsets with per-member CRC/local SHA256. Original GB-scale whole-file digests are not verified from partial ranges. Molecule projector reconstruction verifies cached representation compatibility but does not prove whole checkpoint byte identity.",
                 "scores_computed":False,"gallery_scope":gallery["gallery_scope"],
                 "protein_cache":{"file":str((ASSETS/"PROTEIN_FEATURES.npz").relative_to(ROOT)),"sha256":file_sha(ASSETS/"PROTEIN_FEATURES.npz")},
                 "member_receipts":members}
        (OUT/"PARTIAL_ASSET_RECEIPTS.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
        print(json.dumps({k:v for k,v in summary.items() if k!="member_receipts"},indent=2),flush=True)
    finally:
        receipts=drive.receipts+(vector_receipts if "vector_receipts" in locals() else [])
        (OUT/"PARTIAL_RANGE_RECEIPTS.json").write_text(json.dumps(receipts,indent=2),encoding="utf-8")
        (OUT/"NETWORK_BUDGET.json").write_text(json.dumps(budget,indent=2),encoding="utf-8")

if __name__=="__main__":main()

