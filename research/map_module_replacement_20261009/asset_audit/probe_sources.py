"""Bounded official MAP asset/source feasibility probe; no full checkpoint restore."""
import io, json, hashlib, pickle, re, struct, time, zipfile
from concurrent.futures import ThreadPoolExecutor
from html import unescape
from pathlib import Path
import requests
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
SOURCES = OUT / "sources"
REV = "629ebdc1617eaf89825185a1512d772eccc3dc7e"
SE_REV = "5a9a80f44f7ce32ce57059933ef0d735d7c10ce5"
LIMIT = 100_000_000
SOURCES.mkdir(parents=True, exist_ok=True)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def fetch_small(spec):
    name, url = spec
    destination = SOURCES / name
    if destination.exists():
        data = destination.read_bytes()
        return {"file": str(destination.relative_to(OUT)), "url": url, "status": "existing", "bytes": len(data), "sha256": digest(data)}
    response = requests.get(url, stream=True, timeout=(20, 35))
    response.raise_for_status()
    chunks, size = [], 0
    for chunk in response.iter_content(65536):
        size += len(chunk)
        if size > 10_000_000:
            response.close()
            raise RuntimeError("Small-source cap exceeded")
        chunks.append(chunk)
    data = b"".join(chunks)
    destination.write_bytes(data)
    return {"file": str(destination.relative_to(OUT)), "url": url, "http_status": response.status_code, "bytes": len(data), "sha256": digest(data)}

class RemoteZipFile(io.RawIOBase):
    def __init__(self, source, size, budget, name, session=None, target=None, params=None):
        self.source = source
        self.url = target or source
        self.params = params
        self.name = name
        self.size = size
        self.position = 0
        self.budget = budget
        self.session = session or requests.Session()
        self.receipts = []
    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.position
    def seek(self, offset, whence=0):
        self.position = offset if whence == 0 else self.position + offset if whence == 1 else self.size + offset
        if self.position < 0: raise ValueError("Negative seek")
        return self.position
    def read(self, n=-1):
        if n < 0: n = self.size - self.position
        n = min(n, self.size - self.position)
        if n <= 0: return b""
        start, end = self.position, self.position + n - 1
        if self.budget["bytes"] + n > LIMIT: raise RuntimeError("100 MB aggregate network budget exceeded")
        response = self.session.get(self.url, params=self.params, headers={"Range": f"bytes={start}-{end}", "Accept-Encoding": "identity"}, stream=True, timeout=(30, 50))
        cr = response.headers.get("Content-Range", "")
        if response.status_code != 206 or cr != f"bytes {start}-{end}/{self.size}":
            response.close()
            raise RuntimeError(f"Server does not honor exact ranges: HTTP{response.status_code}, Content-Range={cr!r}")
        chunks, count = [], 0
        for chunk in response.iter_content(1024 * 1024):
            count += len(chunk)
            if count > n:
                response.close()
                raise RuntimeError("Range payload exceeds request")
            chunks.append(chunk)
        data = b"".join(chunks)
        if len(data) != n: raise RuntimeError("Truncated range")
        self.budget["bytes"] += n
        self.receipts.append({"asset": self.name, "source": self.source, "start": start, "end": end, "bytes": n, "sha256": digest(data), "http_status": response.status_code})
        self.position += n
        return data

class TensorSpec(dict):
    pass

def tensor_spec(storage, offset, size, stride, requires_grad=False, hooks=None, metadata=None):
    return TensorSpec(storage=storage, offset=offset, shape=list(size), stride=list(stride), requires_grad=requires_grad)

class MetadataOnlyUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if (module, name) == ("collections", "OrderedDict"):
            from collections import OrderedDict
            return OrderedDict
        if module == "torch" and name.endswith("Storage"):
            return "torch." + name
        if module == "torch._utils" and name in {"_rebuild_tensor_v2", "_rebuild_tensor"}:
            return tensor_spec
        if module == "torch._utils" and name == "_rebuild_parameter":
            return lambda data, requires_grad, hooks: data
        if (module, name) == ("numpy", "dtype"): return np.dtype
        if (module, name) == ("_codecs", "encode"):
            import codecs
            return codecs.encode
        if module in {"numpy.core.multiarray", "numpy._core.multiarray"} and name == "scalar": return np._core.multiarray.scalar
        raise pickle.UnpicklingError(f"Unapproved metadata global: {module}.{name}")
    def persistent_load(self, value):
        if not isinstance(value, tuple) or value[0] != "storage": raise pickle.UnpicklingError("Unknown persistent object")
        return {"type": value[1], "key": str(value[2]), "location": value[3], "numel": value[4]}

def probe_archive(remote):
    with zipfile.ZipFile(remote) as archive:
        info = [{"name": i.filename, "size": i.file_size, "compressed_size": i.compress_size, "compression": i.compress_type, "crc32": f"{i.CRC:08x}", "header_offset": i.header_offset} for i in archive.infolist()]
        pkl_name = next(i.filename for i in archive.infolist() if i.filename.endswith("/data.pkl"))
        payload = archive.read(pkl_name)
        (SOURCES / f"{remote.name}.data.pkl").write_bytes(payload)
        value = MetadataOnlyUnpickler(io.BytesIO(payload)).load()
        state = value.get("model_state_dict", value) if isinstance(value, dict) else value
        specs = {str(k): dict(v) for k, v in state.items() if isinstance(v, TensorSpec)}
        result = {"source": remote.source, "advertised_bytes": remote.size, "zip_entries": info, "pickle_entry": pkl_name, "pickle_bytes": len(payload), "pickle_sha256": digest(payload), "tensor_specs": specs, "top_level_keys": [str(k) for k in value.keys()] if isinstance(value, dict) else [], "parsed_without_tensor_payload_or_arbitrary_globals": True}
        (OUT / f"{remote.name}_METADATA.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result

def main():
    receipts_path = OUT / "SOURCE_RECEIPTS.json"
    specs = [
        ("DRIVE_FOLDER.html", "https://drive.google.com/drive/folders/1cV0ZTk92PguKS2nyii6dLV0IfqoSDHsQ"),
        ("GITHUB_ISSUES.json", "https://api.github.com/repos/MAGIC-AI4Med/MAP/issues?state=all&per_page=100"),
        ("SE_TREE.json", f"https://huggingface.co/api/models/arcinstitute/SE-600M/tree/{SE_REV}?recursive=true&limit=100"),
        ("MAP_TREE_CURRENT.json", f"https://api.github.com/repos/MAGIC-AI4Med/MAP/git/trees/{REV}?recursive=1"),
    ]
    for path in ["MAP/demo.py", "MAP/train.py", "MAP/data/ds_multi_cell_lora_se.py", "preprocess/E_hvg_multi_celllines.py", "MAP/model/gene_decoders.py", "MAP/model/transformer_encoder.py", "MAP/model/se.py", "preprocess/G2_extract_se_inputs_sharded_indexed.py"]:
        specs.append((path.replace("/", "__"), f"https://raw.githubusercontent.com/MAGIC-AI4Med/MAP/{REV}/{path}"))
    receipts = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [(spec, pool.submit(fetch_small, spec)) for spec in specs]
        for spec, future in futures:
            try: receipts.append(future.result())
            except Exception as exc: receipts.append({"url": spec[1], "file": spec[0], "status":"blocked", "error": f"{type(exc).__name__}: {exc}"})
    receipts_path.write_text(json.dumps(receipts, indent=2), encoding="utf-8")
    budget = {"bytes": sum(x.get("bytes", 0) for x in receipts)}
    results, range_receipts = {}, []
    hf_source = f"https://huggingface.co/arcinstitute/SE-600M/resolve/{SE_REV}/protein_embeddings.pt"
    esm = RemoteZipFile(hf_source, 410886729, budget, "protein_embeddings")
    try: results["protein_embeddings"] = probe_archive(esm)
    except Exception as exc: results["protein_embeddings"] = {"status":"blocked", "error":f"{type(exc).__name__}: {exc}"}
    range_receipts.extend(esm.receipts)
    drive_source = "https://drive.google.com/uc?export=download&id=18vL792x-g81SWCpzPvgUbHq3jbR45ttx"
    session = requests.Session()
    drive = None
    try:
        response = session.get(drive_source, timeout=(20,35))
        html = response.text
        fields = dict(re.findall(r'<input[^>]+name="([^"]+)"[^>]+value="([^"]*)"', html))
        action = re.search(r'<form[^>]+action="([^"]+)"', html)
        if not action or "confirm" not in fields: raise RuntimeError(f"Drive confirmation unavailable: HTTP{response.status_code}")
        budget["bytes"] += len(response.content)
        (SOURCES/"MAPKG_CONFIRM.html").write_bytes(response.content)
        drive = RemoteZipFile(drive_source, 1126763160, budget, "mapkg_encoder", session=session, target=unescape(action.group(1)), params=fields)
        results["mapkg_encoder"] = probe_archive(drive)
    except Exception as exc: results["mapkg_encoder"] = {"status":"blocked", "error":f"{type(exc).__name__}: {exc}"}
    if drive: range_receipts.extend(drive.receipts)
    (OUT/"RANGE_RECEIPTS.json").write_text(json.dumps(range_receipts,indent=2),encoding="utf-8")
    summary = {"download_budget_bytes":LIMIT,"network_body_bytes":budget["bytes"],"asset_probe_status":{k:{"status":"metadata_parsed" if "tensor_specs" in v else v.get("status"),"tensor_count":len(v.get("tensor_specs",{})), "error":v.get("error")} for k,v in results.items()}}
    (OUT/"PROBE_SUMMARY.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2), flush=True)

if __name__ == "__main__": main()

