"""Read public BioGRID parquet footer and scalar metadata, never outcome arrays."""
import hashlib
import io
import json
import pathlib
import struct
import urllib.request
from datetime import datetime, timezone

import pyarrow.parquet as pq

AUDIT = pathlib.Path(__file__).resolve().parent
ROOT = pathlib.Path("D:/MAESTRO/data/external/virtual_cell_four_directions_20261030/assaybench")
URL = "https://huggingface.co/datasets/Genentech/assaybench/resolve/fa2ed4195d2eea1e5ed570d1a67c21e47650962d/biogrid/train-00000-of-00001.parquet"
SIZE = 1092438556


def fetch_range(start, end):
    name = f"ranges/{start}-{end}.bin"
    path = ROOT / name
    if path.exists():
        return path.read_bytes()
    request = urllib.request.Request(URL, headers={"Range": f"bytes={start}-{end}", "User-Agent": "MAESTRO-source-audit/1.0"})
    for attempt in range(3):
        entry = dict(time_utc=datetime.now(timezone.utc).isoformat(), url=URL, range=f"bytes={start}-{end}", file=name)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                body = response.read(end - start + 2)
                entry.update(status=response.status, content_range=response.headers.get("Content-Range"), bytes_received=len(body))
            break
        except Exception as error:
            entry.update(outcome="error", error=repr(error), bytes_received=0)
            with (AUDIT / "requests.jsonl").open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry) + "\n")
            if attempt == 2:
                raise
    if entry["status"] != 206 or entry["content_range"] != f"bytes {start}-{end}/{SIZE}" or len(body) != end - start + 1:
        entry["outcome"] = "range_failed_not_saved"
        with (AUDIT / "requests.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\n")
        raise RuntimeError(entry)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    entry.update(outcome="saved", saved_bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
    with (AUDIT / "requests.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")
    print(json.dumps(entry))
    return body


class CachedRanges(io.RawIOBase):
    def __init__(self, segments):
        super().__init__()
        self.segments = segments
        self.pos = 0

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, offset, whence=0):
        self.pos = offset + (self.pos if whence == 1 else SIZE if whence == 2 else 0)
        return self.pos

    def read(self, size=-1):
        end = SIZE if size < 0 else min(SIZE, self.pos + size)
        for start, body in self.segments:
            if start <= self.pos and end <= start + len(body):
                result = body[self.pos - start:end - start]
                self.pos = end
                return result
        raise RuntimeError(f"Attempted uncached read {self.pos}:{end}; outcome arrays are not allowed")


if __name__ == "__main__":
    footer_start = SIZE - 65536
    footer = fetch_range(footer_start, SIZE - 1)
    metadata_size = struct.unpack("<I", footer[-8:-4])[0]
    if metadata_size + 8 > len(footer):
        footer_start = SIZE - metadata_size - 8
        footer = fetch_range(footer_start, SIZE - 1)
    metadata = pq.read_metadata(io.BytesIO(b"PAR1" + footer))
    summary = metadata.to_dict()
    (AUDIT / "parquet_footer.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("row_groups", metadata.num_row_groups, "rows", metadata.num_rows, "metadata_bytes", metadata_size)
    segments = [(footer_start, footer)]
    scalar_names = [metadata.schema.column(i).name for i in range(metadata.num_columns) if metadata.schema.column(i).name != "element"]
    for group in range(metadata.num_row_groups):
        ranges = []
        rg = metadata.row_group(group)
        for index in range(metadata.num_columns):
            column = rg.column(index)
            if column.path_in_schema in scalar_names:
                start = min(value for value in [column.dictionary_page_offset, column.data_page_offset] if value is not None and value >= 0)
                end = start + column.total_compressed_size - 1
                if ranges and start <= ranges[-1][1] + 1:
                    ranges[-1][1] = end
                else:
                    ranges.append([start, end])
        for start, end in ranges:
            if end - start > 3_000_000:
                raise RuntimeError("Unexpectedly large scalar metadata range")
            segments.append((start, fetch_range(start, end)))
    table = pq.ParquetFile(CachedRanges(segments), pre_buffer=False).read(columns=scalar_names, use_threads=False)
    pq.write_table(table, ROOT / "biogrid_metadata_only.parquet")
    table.to_pandas().to_csv(AUDIT / "metadata_census_source.csv", index=False)
    print("saved scalar-only metadata", table.num_rows, table.column_names)
