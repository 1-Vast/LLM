"""Read selected Parquet columns from exact retained ranges, without whole tables."""
import io
import json

import pyarrow.parquet as pq

from fetch import ROOT, fetch, records


REPO = "tahoebio/tahoe-de-rhaister"
REVISION = "c7963cf334bec0683225d41c9586d900ca6303a2"


class RetainedRanges(io.RawIOBase):
    def __init__(self, size, ranges):
        self.size, self.ranges, self.position = size, ranges, 0

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset, whence=0):
        self.position = offset if whence == 0 else self.position + offset if whence == 1 else self.size + offset
        return self.position

    def read(self, length=-1):
        if length < 0:
            length = self.size - self.position
        if not length:
            return b""
        for start, body in self.ranges:
            if start <= self.position and self.position + length <= start + len(body):
                result = body[self.position - start:self.position - start + length]
                self.position += length
                return result
        raise ValueError(f"Unretained range {self.position}:{self.position + length}")


def retained(name):
    receipt = [r for r in records() if r["name"] == name and r["status"] == "RECEIVED"][-1]
    return receipt, (ROOT / receipt["path"]).read_bytes()


def read_plate1(columns, *, acquire=False):
    size = 65_704_666
    url = f"https://huggingface.co/datasets/{REPO}/resolve/{REVISION}/cell_eval/plate_plate1.parquet"
    footer_receipt, footer = retained("plate1_footer_metadata")
    metadata = pq.read_metadata(io.BytesIO(b"PAR1" + footer))
    patches = [(size - len(footer), footer)]
    plans = []
    for group_index in range(metadata.num_row_groups):
        group = metadata.row_group(group_index)
        for column in columns:
            chunk = group.column(metadata.schema.names.index(column))
            start = min(offset for offset in (chunk.dictionary_page_offset, chunk.data_page_offset) if offset >= 0)
            end = start + chunk.total_compressed_size - 1
            name = f"plate1_rg{group_index}_{column}"
            cached = [r for r in records() if r["name"] == name and r["status"] == "RECEIVED"]
            if acquire and not cached:
                item, body = fetch(name, url, limit=chunk.total_compressed_size + 5000,
                                   headers={"Range": f"bytes={start}-{end}"})
            else:
                item, body = retained(name)
            assert item["status"] == "RECEIVED" and len(body) == chunk.total_compressed_size
            assert item["http_status"] == 206
            response_headers = {key.lower(): value for key, value in item["headers"].items()}
            assert response_headers.get("content-range") == f"bytes {start}-{end}/{size}"
            patches.append((start, body))
            plans.append({"column": column, "row_group": group_index, "start": start,
                          "end": end, "receipt": item["path"], "sha256": item["sha256"]})
    table = pq.ParquetFile(RetainedRanges(size, patches)).read(columns=columns, use_threads=False)
    return table, plans, metadata


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("columns", nargs="+")
    parser.add_argument("--acquire", action="store_true")
    args = parser.parse_args()
    table, plans, metadata = read_plate1(args.columns, acquire=args.acquire)
    print(json.dumps({"rows": len(table), "columns": table.column_names,
                      "range_plans": plans}, indent=2))
    if args.columns == ["cell_line", "treatment"]:
        output = table.to_pylist()
        (ROOT / "PLATE1_IDENTITIES.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
