"""Independent offline reconstruction of named summaries; no producer imports."""
import hashlib
import io
import json
from pathlib import Path
import re

import pandas as pd
import pyarrow.parquet as pq


HERE = Path(__file__).resolve().parent
RELIABILITY = HERE.parent.parent / "observation_reliability"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


class RangeFile(io.RawIOBase):
    def __init__(self, size, spans):
        self.size, self.spans, self.position = size, spans, 0

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset, whence=0):
        self.position = offset if whence == 0 else self.position + offset if whence == 1 else self.size + offset
        return self.position

    def read(self, size=-1):
        size = self.size - self.position if size < 0 else size
        if size == 0:
            return b""
        for start, end, body in self.spans:
            if start <= self.position and self.position + size - 1 <= end:
                value = body[self.position-start:self.position-start+size]
                self.position += size
                return value
        raise ValueError("Attempt to read unretained source range")


def main():
    ledger = [json.loads(line) for line in (HERE / "NETWORK.jsonl").read_text().splitlines()]
    for receipt in ledger:
        body = (HERE / receipt["path"]).read_bytes()
        assert len(body) == receipt["received_body_bytes"]
        assert hashlib.sha256(body).hexdigest() == receipt["sha256"]
        assert not re.search(r"(?:Signature|Credential)=", receipt["url"], re.I)
        assert not any(re.search(r"(?:Signature|Credential)=", str(value), re.I)
                       for value in receipt.get("headers", {}).values())
    received = sum(row["received_body_bytes"] for row in ledger)
    assert received <= 25_000_000
    names = {r["name"]: r for r in ledger if r.get("http_status") in (200, 206)
             and r["status"] == "RECEIVED"}
    dataset = read(HERE / names["hf_dataset"]["path"])
    revision = "c7963cf334bec0683225d41c9586d900ca6303a2"
    assert dataset["sha"] == revision
    footer = (HERE / names["plate1_footer_metadata"]["path"]).read_bytes()
    size = 65_704_666
    spans = [(size-len(footer), size-1, footer)]
    endpoint = read(RELIABILITY / "ENDPOINT.json")
    requested = ["cell_line", "treatment"] + endpoint["symbols"]
    assert len(endpoint["symbols"]) == len(set(endpoint["symbols"])) == 39
    schema = pq.read_metadata(io.BytesIO(b"PAR1" + footer))
    assert schema.num_rows == 4443 and schema.num_row_groups == 1
    for name in requested:
        receipt = names["plate1_rg0_" + name]
        headers = {key.lower(): value for key, value in receipt["headers"].items()}
        bounds = re.fullmatch(r"bytes (\d+)-(\d+)/(\d+)", headers["content-range"])
        start, end, total = map(int, bounds.groups())
        chunk = schema.row_group(0).column(schema.schema.names.index(name))
        expected_start = min(i for i in (chunk.dictionary_page_offset, chunk.data_page_offset) if i >= 0)
        assert start == expected_start and end-start+1 == chunk.total_compressed_size and total == size
        spans.append((start, end, (HERE / receipt["path"]).read_bytes()))
    frame = pq.ParquetFile(RangeFile(size, spans)).read(columns=requested, use_threads=False).to_pandas()
    genes = read(HERE / names["static_2k_genes"]["path"])
    assert len(genes) == len(set(genes)) == 2000 and schema.schema.names[2:] == genes
    assert [genes[i] for i in endpoint["coordinates"]] == endpoint["symbols"]
    recorded = read(HERE / "COVERAGE.json")
    assert recorded["measurable_received_body_bytes"] == received
    cell_body = (HERE / names["official_cell_metadata"]["path"]).read_bytes()
    assert hashlib.sha256(cell_body).hexdigest() == "67641f5bdd3fb077978ff1fec4d0d617490674bcd42850515ae3997194c29d4d"
    cell = pd.read_parquet(io.BytesIO(cell_body))
    for entry, sid in zip(recorded["files"], ("CVCL_1715", "CVCL_1716")):
        identity = cell.loc[cell.Cell_ID_Cellosaur.eq(sid),
                            ["cell_name", "Cell_ID_Cellosaur", "Cell_ID_DepMap"]].drop_duplicates().to_dict("records")
        assert identity == [entry["cell_identity"]]
        subset = frame.loc[frame.cell_line.eq(sid)]
        assert len(subset) == entry["named_condition_rows"]
        for stat in entry["gene_statistics"]:
            gene = stat["gene"]
            assert int((subset[gene] > 0).sum()) == stat["positive_delta_conditions"]
            assert int((subset[gene] != 0).sum()) == stat["nonzero_delta_conditions"]
            top = subset.loc[subset[gene] > 0].sort_values([gene, "treatment"], ascending=[False, True])
            assert top[["treatment", gene]].head(3).rename(columns={gene: "delta"}).to_dict("records") == stat["top_positive_conditions"]
    exclusions = read(HERE / "EXPOSURES.json")
    sample_path = RELIABILITY / "literature/sources/tahoe_sample_parquet.parquet"
    assert hashlib.sha256(sample_path.read_bytes()).hexdigest() == "33167f0ce28cff8357c503cda67d1c7fea200bff6918ee1de3c4f3549175b9d3"
    sample = pd.read_parquet(sample_path)
    conditions = set(frame.treatment)
    samples = sample.loc[sample.plate.eq("plate1") & sample.drugname_drugconc.isin(conditions)]
    references = sample.loc[sample.plate.eq("plate1") & sample.drug.eq("DMSO_TF")]
    assert set(samples.drugname_drugconc) == conditions
    assert set(exclusions["excluded_pooled_sample_ids"]) == set(samples["sample"]) | set(references["sample"])
    assert len(exclusions["excluded_pooled_sample_ids"]) == 96
    assert set(exclusions["line_ids"]) == set(frame.cell_line)
    sentinel = read(RELIABILITY / "literature/UPDATED_SENTINELS.json")
    protected = {sid for r in sentinel["selected"] for sid in r["sample_counts"]}
    assert not protected & set(exclusions["excluded_pooled_sample_ids"])
    assert not set(sentinel["selected_labels"]) & conditions
    selection = read(HERE / "SELECTION.json")
    assert len(selection["selected"]) == 7 and selection["expected_hvg_payload_bytes"] == 1_792_000
    for candidate in selection["selected"]:
        matches = frame.loc[frame.cell_line.eq(candidate["cell_line_id"]) & frame.treatment.eq(candidate["label"])]
        assert len(matches) == 1
        row = matches.iloc[0]
        assert {g: float(row[g]) for g in endpoint["symbols"]} == candidate["all39_deltas"]
        official = samples.loc[samples.drugname_drugconc.eq(candidate["label"])]
        assert set(official["sample"]) == set(candidate["official_pooled_sample_ids"])
    assert recorded["actual_file_axis_certified"] is False
    assert recorded["checkpoint_output_axis_certified"] is False
    assert recorded["new_raw_paired_cell_RNA_bytes"] == 0
    verdict = {"schema": "offline_named_summary_verification_v1", "status": "PASS",
        "retained_http_responses": len(ledger), "received_body_bytes": received,
        "reconstructed_named_rows": len(frame), "reconstructed_gene_columns": 39,
        "excluded_pooled_samples": 96, "selected_calibration_conditions": 7,
        "new_network_calls": 0, "producer_imports": False,
        "actual_file_axis_certified": False, "scientific_boundary": "Observability hints; no independent decision or axis certification."}
    (HERE / "VERIFIED.json").write_text(json.dumps(verdict, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(verdict))


if __name__ == "__main__":
    main()
