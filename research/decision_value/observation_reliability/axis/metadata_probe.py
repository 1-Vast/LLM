"""Inspect HDF5 metadata for an explicit ordered HVG annotation; no RNA reads."""
import hashlib
import json
from pathlib import Path

import h5py
import requests

from .verify import RetainedSource

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OUT = HERE / "metadata_probe"


class MetadataSource(RetainedSource):
    def __init__(self, name, size, receipts, budget):
        super().__init__(name, size, receipts)
        self.budget = budget
        self.url = f"https://huggingface.co/datasets/arcinstitute/State-Tahoe-Filtered/resolve/fdf87abece385feea6fa5e9944ab46e173b6af50/{name}"

    def bytes_at(self, start, end):
        try:
            return super().bytes_at(start, end)
        except RuntimeError:
            size = end - start + 1
            if self.budget["bytes"] + size > 900_000:
                raise RuntimeError("metadata_probe_cap_exceeded")
            with requests.get(self.url, headers={"Range": f"bytes={start}-{end}", "Accept-Encoding": "identity"},
                              params={"metadata_probe": f"{start}-{end}"}, stream=True, timeout=(15, 30)) as response:
                if response.status_code != 206 or response.headers.get("Content-Range") != f"bytes {start}-{end}/{self.size}":
                    raise RuntimeError("metadata_probe_range_mismatch")
                pieces, received = [], 0
                for piece in response.iter_content(65536):
                    received += len(piece)
                    if received > size: raise RuntimeError("metadata_probe_overrun")
                    pieces.append(piece)
            data = b"".join(pieces)
            if len(data) != size: raise RuntimeError("metadata_probe_truncated")
            path = OUT / f"{self.name}_{start}_{end}.bin"
            path.write_bytes(data)
            receipt = dict(file=self.name, start=start, end=end, bytes=size, http_status=206,
                           sha256=hashlib.sha256(data).hexdigest(), asset=path.relative_to(ROOT).as_posix(),
                           purpose="HDF5group_dataset_attribute_metadata_only")
            self.budget["bytes"] += size
            self.budget["receipts"].append(receipt)
            self.spans.append((start, end, data))
            return data


def clean(value):
    if isinstance(value, bytes): return value.decode("utf-8")
    if hasattr(value, "tolist"): return value.tolist()
    return value


def describe(group):
    result = dict(keys=list(group.keys()), attrs={name: clean(value) for name, value in group.attrs.items()})
    result["members"] = {}
    for name in group.keys():
        obj = group[name]
        record = dict(type="dataset" if isinstance(obj, h5py.Dataset) else "group", attrs={key: clean(value) for key, value in obj.attrs.items()})
        if isinstance(obj, h5py.Dataset): record.update(shape=list(obj.shape), dtype=obj.dtype.str)
        else: record["keys"] = list(obj.keys())
        result["members"][name] = record
    return result


def main():
    OUT.mkdir(exist_ok=False)
    censuses = json.loads((HERE / "CENSUSES.json").read_text())
    receipts = [json.loads(line) for line in (HERE / "NETWORK.jsonl").read_text().splitlines()]
    budget = dict(bytes=0, receipts=[])
    files = []
    for name in ("c40.h5ad", "c44.h5ad"):
        source = MetadataSource(name, censuses[name]["file_bytes"], receipts, budget)
        with h5py.File(source, "r") as h5:
            files.append(dict(file=name, root_keys=list(h5.keys()),
                              root_attrs={key: clean(value) for key, value in h5.attrs.items()},
                              var=describe(h5["var"]), uns=describe(h5["uns"]), obsm=describe(h5["obsm"])))
    url = "https://huggingface.co/api/datasets/arcinstitute/State-Tahoe-Filtered/tree/fdf87abece385feea6fa5e9944ab46e173b6af50"
    response = requests.get(url, timeout=(15, 30)); response.raise_for_status()
    data = response.content
    if budget["bytes"] + len(data) > 900_000: raise RuntimeError("metadata_probe_cap_exceeded")
    (OUT / "TREE.json").write_bytes(data)
    budget["bytes"] += len(data)
    budget["receipts"].append(dict(public_url=url, http_status=200, bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), asset=(OUT / "TREE.json").relative_to(ROOT).as_posix(), purpose="public_source_file_listing"))
    result = dict(schema="source_HVG_metadata_inventory_v1", source_revision="fdf87abece385feea6fa5e9944ab46e173b6af50", files=files,
                  source_files=[dict(path=entry["path"], size=entry.get("size")) for entry in response.json()],
                  metadata_probe_body_bytes=budget["bytes"], receipts=budget["receipts"], expression_data_read=False,
                  frozen_axis_result_unchanged=True, producer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (OUT / "RESULTS.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(dict(metadata_bytes=budget["bytes"], files=[dict(file=f["file"], var_keys=f["var"]["keys"], uns_keys=f["uns"]["keys"], obsm_keys=f["obsm"]["keys"]) for f in files])))


if __name__ == "__main__":
    main()
