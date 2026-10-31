"""Fetch public BioGRID gene/hit column chunks and retain only temporal-train rows.

The source parquet is 1.09 GB.  This script uses HTTP Range requests for the
two required columns (about 251 MB compressed), never touches LaTest, and
does not score validation/test rows.  Scalar metadata was fetched separately.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import pathlib
import time
import urllib.request

import numpy as np
import pyarrow.parquet as pq

AUDIT = pathlib.Path(__file__).resolve().parent
ROOT = pathlib.Path("D:/MAESTRO/data/external/virtual_cell_four_directions_20261030/assaybench")
URL = "https://huggingface.co/datasets/Genentech/assaybench/resolve/fa2ed4195d2eea1e5ed570d1a67c21e47650962d/biogrid/train-00000-of-00001.parquet"
SIZE = 1092438556
CAP = 265_000_000


def log(entry):
    with (AUDIT / "requests.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")


def fetch_range(start: int, end: int, label: str) -> bytes:
    """Fetch one exact byte range, with local raw retention and strict checks."""
    path = ROOT / "chunks" / label
    if path.exists():
        return path.read_bytes()
    cap_used = sum(p.stat().st_size for p in (ROOT / "chunks").glob("*.bin")) if (ROOT / "chunks").exists() else 0
    if cap_used + end - start + 1 > CAP:
        raise RuntimeError(f"source cap would be exceeded: {cap_used}+{end-start+1}>{CAP}")
    request = urllib.request.Request(URL, headers={"Range": f"bytes={start}-{end}", "User-Agent": "MAESTRO-source-audit/1.0"})
    last = None
    for attempt in range(5):
        entry = {"url": URL, "range": f"bytes={start}-{end}", "file": f"chunks/{label}", "attempt": attempt + 1}
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                body = response.read(end - start + 2)
                entry.update(status=response.status, content_range=response.headers.get("Content-Range"), bytes_received=len(body))
            if response.status != 206 or entry["content_range"] != f"bytes {start}-{end}/{SIZE}" or len(body) != end - start + 1:
                raise RuntimeError(f"unexpected range response: {entry}")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
            entry.update(outcome="saved", saved_bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
            log(entry)
            print(json.dumps(entry))
            return body
        except Exception as error:
            last = error
            entry.update(outcome="error", error=repr(error), bytes_received=0)
            log(entry)
            time.sleep(1 + attempt)
    raise last


class SegmentedReader(io.RawIOBase):
    """Read a sparse parquet file made from exact retained ranges."""

    def __init__(self, segments: list[tuple[int, bytes]]):
        self.segments = sorted(segments)
        self.pos = 0

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, offset, whence=0):
        self.pos = offset if whence == 0 else self.pos + offset if whence == 1 else SIZE + offset
        return self.pos

    def read(self, size=-1):
        end = SIZE if size is None or size < 0 else min(SIZE, self.pos + size)
        if end == self.pos:
            return b""
        # Arrow reads within one chunk; allowing adjacent segments makes footer/header reads robust.
        cursor = self.pos
        pieces = []
        while cursor < end:
            match = next(((start, body) for start, body in self.segments if start <= cursor < start + len(body)), None)
            if match is None:
                raise RuntimeError(f"uncached parquet read {cursor}:{end}")
            start, body = match
            take = min(end, start + len(body)) - cursor
            pieces.append(body[cursor - start:cursor - start + take])
            cursor += take
        self.pos = end
        return b"".join(pieces)


def load_footer() -> tuple[list[tuple[int, bytes]], dict]:
    footer_path = ROOT / "ranges/1092361555-1092438555.bin"
    header_path = ROOT / "ranges/4-1380.bin"
    if not footer_path.exists():
        footer = fetch_range(SIZE - 76993 - 8, SIZE - 1, "footer.bin")
        footer_start = SIZE - len(footer)
    else:
        footer = footer_path.read_bytes()
        footer_start = SIZE - len(footer)
    header = header_path.read_bytes() if header_path.exists() else fetch_range(4, 1380, "header.bin")
    metadata = pq.read_metadata(io.BytesIO(b"PAR1" + footer))
    return [(0, b"PAR1" + header), (footer_start, footer)], metadata.to_dict()


if __name__ == "__main__":
    ROOT.joinpath("chunks").mkdir(parents=True, exist_ok=True)
    segments, footer_dict = load_footer()
    metadata = pq.ParquetFile(SegmentedReader(segments), pre_buffer=False).metadata
    # The scalar census supplies temporal labels for every row; no validation/test outcomes are emitted.
    scalar_csv = AUDIT / "metadata_census_source.csv"
    with scalar_csv.open(newline="", encoding="utf-8") as handle:
        scalar = list(csv.DictReader(handle))
    if len(scalar) != metadata.num_rows:
        raise RuntimeError(f"scalar rows {len(scalar)} != parquet rows {metadata.num_rows}")
    train_indices = {i for i, row in enumerate(scalar) if row.get("yearfold0") == "train"}
    if len(train_indices) != 1349:
        raise RuntimeError(f"expected 1349 temporal train rows, got {len(train_indices)}")
    gene_names = "relevance_genes.list.element"
    hit_names = "hit.list.element"
    # Download both physical columns for each row group. A group may contain val/test rows;
    # those are discarded immediately after decoding by the scalar yearfold mask.
    ranges = []
    offset = 0
    train_groups = []
    for rg_index in range(metadata.num_row_groups):
        rg = metadata.row_group(rg_index)
        if not any(i in train_indices for i in range(offset, offset + rg.num_rows)):
            offset += rg.num_rows
            continue
        train_groups.append(rg_index)
        for column_name in (gene_names, hit_names):
            column = next(rg.column(i) for i in range(rg.num_columns) if rg.column(i).path_in_schema == column_name)
            start = min(x for x in (column.dictionary_page_offset, column.data_page_offset) if x is not None and x >= 0)
            end = start + column.total_compressed_size - 1
            label = f"rg{rg_index:02d}_{'genes' if column_name == gene_names else 'hit'}.bin"
            body = fetch_range(start, end, label)
            segments.append((start, body))
            ranges.append({"row_group": rg_index, "column": column_name, "start": start, "end": end, "bytes": len(body), "file": f"chunks/{label}"})
        offset += rg.num_rows
    (AUDIT / "train_column_ranges.json").write_text(json.dumps(ranges, indent=2), encoding="utf-8")
    reader = SegmentedReader(segments)
    parquet = pq.ParquetFile(reader, pre_buffer=False)
    rows = []
    global_index = 0
    for rg_index in range(parquet.num_row_groups):
        n_group_rows = parquet.metadata.row_group(rg_index).num_rows
        if rg_index not in train_groups:
            global_index += n_group_rows
            continue
        table = parquet.read_row_group(rg_index, columns=["relevance_genes", "hit"], use_threads=False)
        local_train_indices = [i for i in range(n_group_rows) if global_index + i in train_indices]
        table = table.take(local_train_indices)
        genes_col = table.column("relevance_genes").to_pylist()
        hits_col = table.column("hit").to_pylist()
        for local_index, (genes, hits) in enumerate(zip(genes_col, hits_col)):
            index = global_index + local_train_indices[local_index]
            if len(genes) != len(hits):
                raise RuntimeError(f"gene/hit length mismatch at row {index}: {len(genes)} vs {len(hits)}")
            if index in train_indices:
                base = scalar[index]
                rows.append({
                    "row_index": index,
                    "dataset_name": base["dataset_name"],
                    "author": base["author"],
                    "source_id": base["source_id"],
                    "cell_line": base["cell_line"],
                    "cell_type": base["cell_type"],
                    "phenotype": base["phenotype"],
                    "screen_rationale": base["screen_rationale"],
                    "screen_type": base["screen_type"],
                    "library_type": base["library_type"],
                    "duration": base["duration"],
                    "condition_name": base["condition_name"],
                    "condition_dosage": base["condition_dosage"],
                    "condition_clause": base["condition_clause"],
                    "screen_category": base["screen_category"],
                    "cleaned_phenotype": base["cleaned_phenotype"],
                    "yearfold0": base["yearfold0"],
                    "genes": genes,
                    "hit_indices": [i for i, hit in enumerate(hits) if hit],
                    "hit_count": int(sum(bool(hit) for hit in hits)),
                })
        global_index += n_group_rows
    if len(rows) != 1349:
        raise RuntimeError(f"saved train rows {len(rows)} != 1349")
    universe = sorted({gene for row in rows for gene in row["genes"]})
    gene_index = {gene: i for i, gene in enumerate(universe)}
    measured_indices, hit_indices = [], []
    measured_indptr, hit_indptr = [0], [0]
    for row in rows:
        mapped = [gene_index[gene] for gene in row["genes"]]
        measured_indices.extend(mapped)
        hit_indices.extend(mapped[i] for i in row["hit_indices"])
        measured_indptr.append(len(measured_indices))
        hit_indptr.append(len(hit_indices))
    out = ROOT / "biogrid_temporal_train_gene_hits_csr.npz"
    np.savez_compressed(out, genes=np.asarray(universe), dataset_names=np.asarray([row["dataset_name"] for row in rows]), measured_indices=np.asarray(measured_indices, dtype=np.int32), measured_indptr=np.asarray(measured_indptr, dtype=np.int64), hit_indices=np.asarray(hit_indices, dtype=np.int32), hit_indptr=np.asarray(hit_indptr, dtype=np.int64), shape=np.asarray([len(rows), len(universe)], dtype=np.int64))
    compact_rows = [{k: v for k, v in row.items() if k not in ("genes", "hit_indices")} | {"gene_count": len(row["genes"])} for row in rows]
    with (ROOT / "biogrid_temporal_train_metadata.json").open("w", encoding="utf-8") as handle:
        json.dump(compact_rows, handle, indent=2, ensure_ascii=False)
    (AUDIT / "train_gene_hits_manifest.json").write_text(json.dumps({"source_url": URL, "revision": "fa2ed4195d2eea1e5ed570d1a67c21e47650962d", "rows": len(rows), "array_columns": ["relevance_genes", "hit"], "temporal_train_rows": len(rows), "validation_test_rows_discarded": metadata.num_rows - len(rows), "column_range_bytes": sum(x["bytes"] for x in ranges), "output": str(out)}, indent=2), encoding="utf-8")
    print(json.dumps({"rows": len(rows), "column_range_bytes": sum(x["bytes"] for x in ranges), "output": str(out)}))
