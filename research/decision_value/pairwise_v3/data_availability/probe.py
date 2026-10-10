"""Read public source metadata only; never request an expression-matrix byte."""
import hashlib
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import requests


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
REVISION = "fdf87abece385feea6fa5e9944ab46e173b6af50"
REPO = "arcinstitute/State-Tahoe-Filtered"
COLS = ("drugname_drugconc", "plate", "sample", "pass_filter")
CONTROL = "[('DMSO_TF', 0.0, 'uM')]"


def archive(name):
    data = subprocess.check_output(["git", "show", "91b0c10:research/astra/zeroshot_context_20261007/census/" + name + ".json"], cwd=ROOT)
    return json.loads(data), hashlib.sha256(data).hexdigest()


def range_codes(spec):
    name, column, layout = spec
    start = layout["offset"]
    end = start + layout["storage_bytes"] - 1
    url = f"https://huggingface.co/datasets/{REPO}/resolve/{REVISION}/{name}"
    with requests.get(url, headers={"Range": f"bytes={start}-{end}", "Accept-Encoding": "identity"},
                      params={"download": "true", "metadata_span": f"{start}-{end}"}, stream=True, timeout=(20, 40)) as response:
        receipt = dict(file=name, column=column, public_url=url, byte_start=start, byte_end=end,
                       http_status=response.status_code, content_range=response.headers.get("Content-Range"))
        if response.status_code != 206 or not response.headers.get("Content-Range", "").startswith(f"bytes {start}-{end}/"):
            return None, {**receipt, "status": "range_unavailable", "bytes": 0}
        blocks, size = [], 0
        for block in response.iter_content(65536):
            size += len(block)
            if size > layout["storage_bytes"]:
                raise RuntimeError("metadata_range_exceeds_declared_span")
            blocks.append(block)
        data = b"".join(blocks)
    if len(data) != layout["storage_bytes"]:
        raise RuntimeError("metadata_range_length_mismatch")
    receipt.update(status="metadata_read", bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
    return np.frombuffer(data, dtype=layout["dtype"]), receipt


def main():
    output = HERE / "AVAILABILITY.json"
    if output.exists():
        raise FileExistsError(output)
    source = json.loads((HERE.parent / "p0/SOURCE_RECEIPTS.json").read_text())
    raw = json.loads((ROOT / "outputs/decision_value/pairwise_v3_p0/RAW_CHANNELS.json").read_text())
    complete = {row["context"] for row in raw["per_context"]}
    census = [(name, *archive(name)) for index, name in enumerate(source["packet_training_file_order"]) if index in complete]
    census.sort(key=lambda row: row[1]["n_cells"])
    picked = census[:3]
    jobs = [(name, col, meta["code_layouts"][col]) for name, meta, _ in picked for col in COLS]
    readings = {}
    receipts = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [(spec, pool.submit(range_codes, spec)) for spec in jobs]
        for spec, future in futures:
            try:
                codes, receipt = future.result()
                receipts.append(receipt)
                if codes is not None:
                    readings[spec[:2]] = codes
            except Exception as exc:
                receipts.append(dict(file=spec[0], column=spec[1], status="blocked", error_type=type(exc).__name__))
    bindings = json.loads((ROOT / "research/astra/boundary_acquisition_20261007/packet2/PACKET_MANIFEST.json").read_text())["wells"]
    summaries = []
    for name, meta, digest in picked:
        cols = {col: readings.get((name, col)) for col in COLS}
        item = dict(file=name, cell_name=meta["cell_names"][0], archive_census_sha256=digest,
                    full_h5ad_bytes=meta["file_bytes"], metadata_bytes=sum(meta["code_layouts"][col]["storage_bytes"] for col in COLS),
                    expression_layout=meta["layouts"]["obsm/X_hvg"])
        if all(values is not None for values in cols.values()):
            verified = {col: hashlib.sha256(cols[col].tobytes()).hexdigest() == meta["codes_sha256"][col] for col in COLS}
            item["archived_code_hash_matches"] = verified
            groups = []
            labels, plates, samples = [meta["categories"][col] for col in ("drugname_drugconc", "plate", "sample")]
            full = cols["pass_filter"] == meta["categories"]["pass_filter"].index("full")
            for label, plate_names in bindings.items():
                for plate in plate_names:
                    mask = (cols["drugname_drugconc"] == labels.index(label)) & (cols["plate"] == plates.index(plate)) & full
                    rows = np.flatnonzero(mask)
                    groups.append(dict(label=label, plate=plate, full_cells=int(mask.sum()),
                                       sample_counts={samples[int(s)]: int(n) for s, n in zip(*np.unique(cols["sample"][mask], return_counts=True))},
                                       first_full_row=int(rows[0]) if len(rows) else None))
            controls = []
            for plate in plates:
                mask = (cols["drugname_drugconc"] == labels.index(CONTROL)) & (cols["plate"] == plates.index(plate)) & full
                controls.append(dict(plate=plate, full_cells=int(mask.sum()),
                                     sample_counts={samples[int(s)]: int(n) for s, n in zip(*np.unique(cols["sample"][mask], return_counts=True))}))
            item.update(candidate_groups=groups, control_groups=controls,
                        expression_bytes_for_128_cells_per_candidate_group=8000 * sum(min(128, g["full_cells"]) for g in groups),
                        expression_bytes_for_512_cells_per_control=8000 * sum(min(512, g["full_cells"]) for g in controls))
        summaries.append(item)
    result = dict(schema="metadata_only_source_availability_v1", revision=REVISION, source_repo=REPO,
                  file_selection="Three smallest previously exposed, complete-menu training files; metadata size only, not outcome value.",
                  files=summaries, receipts=receipts, metadata_body_bytes=sum(r.get("bytes", 0) for r in receipts),
                  expression_bytes_requested=0, target_outcomes_read=False, production_changed=False,
                  caution="Sample identities do not certify independent cultures; phenotype or RNA-response values are not inspected.")
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("metadata_body_bytes", "expression_bytes_requested", "target_outcomes_read")}))


if __name__ == "__main__":
    main()
