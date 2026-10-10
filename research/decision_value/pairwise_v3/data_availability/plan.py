"""Prepare exact control-only byte ranges from metadata; do not fetch RNA."""
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

from .probe import COLS, CONTROL, HERE, REPO, REVISION, ROOT, archive, range_codes


def main():
    destination = HERE / "SOURCE_RECOVERY_PLAN.json"
    if destination.exists():
        raise FileExistsError(destination)
    availability = json.loads((HERE / "AVAILABILITY.json").read_text())
    files = [row["file"] for row in availability["files"][:2]]
    jobs = [(file, col, archive(file)[0]["code_layouts"][col]) for file in files for col in COLS]
    values, receipts = {}, []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [(spec, pool.submit(range_codes, spec)) for spec in jobs]
        for spec, future in futures:
            codes, receipt = future.result()
            if codes is None:
                raise RuntimeError("exact_metadata_ranges_unavailable")
            values[spec[:2]] = codes
            receipts.append(receipt)
    selections = []
    for file in files:
        meta, digest = archive(file)
        assert all(hashlib.sha256(values[(file, col)].tobytes()).hexdigest() == meta["codes_sha256"][col] for col in COLS)
        code = {col: values[(file, col)] for col in COLS}
        names = meta["categories"]
        eligible = (code["drugname_drugconc"] == names["drugname_drugconc"].index(CONTROL)) & (code["pass_filter"] == names["pass_filter"].index("full"))
        for plate in ("plate6", "plate14"):
            for sample in sorted({names["sample"][int(value)] for value in code["sample"][eligible & (code["plate"] == names["plate"].index(plate))]}):
                rows = np.flatnonzero(eligible & (code["plate"] == names["plate"].index(plate)) & (code["sample"] == names["sample"].index(sample)))
                # Preserve the historical control-role hash: >=.5 denotes reference, never basal.
                ref = [int(row) for row in rows if int(hashlib.sha256(f"control-role:{file}:{int(row)}".encode()).hexdigest()[:12], 16) >= 16 ** 12 / 2]
                selected = sorted(ref, key=lambda row: hashlib.sha256(f"control-noise-pilot-20261009:{file}:{row}".encode()).hexdigest())[:32]
                offset = meta["layouts"]["obsm/X_hvg"]["offset"]
                selections.append(dict(file=file, cell_name=meta["cell_names"][0], plate=plate, sample=sample,
                                       full_cells=int(len(rows)), reference_cells=len(ref), selected_cells=len(selected),
                                       source_census_sha256=digest, rows=sorted(selected),
                                       exact_x_hvg_ranges=[dict(start=offset + row * 8000, end=offset + (row + 1) * 8000 - 1, bytes=8000) for row in sorted(selected)]))
    source_bytes = sum(receipt["bytes"] for receipt in receipts)
    planned_rna = 8000 * sum(row["selected_cells"] for row in selections)
    plan = dict(schema="control_only_source_recovery_plan_v1", source_repo=REPO, revision=REVISION,
                source_url_template=f"https://huggingface.co/datasets/{REPO}/resolve/{REVISION}/{{file}}",
                selection="First two smallest complete-menu exposed training files; plates6/14 cover92/146 original A/B bindings. Up to32 full-QC historical-reference cells per sample, selected by a fixed metadata-only hash.",
                selected=selections, metadata_receipts=receipts, preparation_metadata_bytes=source_bytes,
                initial_metadata_bytes=availability["metadata_body_bytes"], total_actual_metadata_bytes=source_bytes + availability["metadata_body_bytes"],
                planned_control_rna_bytes=planned_rna, maximum_aggregate_bytes=10_000_000,
                planned_actual_plus_control_bytes=source_bytes + availability["metadata_body_bytes"] + planned_rna,
                expression_bytes_requested=0, treated_response_bytes_requested=0, new_state_inference_calls=0,
                status="BLOCKED/GENE_AXIS_AUTHENTICATION", endpoint_mapping="Historical protocol declares39 coordinate indices; the original1969named/31null full-axis identity asset and its gene-by-gene verification receipt are absent.",
                prerequisite="Recover the original feature-identity JSON matching a5ab8f6b2b21b765859e55d8cdf50ad44d5b78abbc841962824d062779d7f457 and verify source revision. Alternatively preregister a control-only X-to-X_hvg identity verification before reading RNA, with byte bounds; never infer names from coordinate position.",
                next_study="After axis authentication, freeze producer, selections and protocol. Estimate scalar-cell endpoint variance s2 and s2/32. Compare with diagonal-only weighted39gene variance sum(w_g^2*s_g^2)/32 to isolate covariance; retain the legacy mean-of2000gene-variances proxy as a separate diagnostic because its endpoint and scale differ. Report sample/plate association only; no independent culture, biological variance fraction, decision benefit, viability or apoptosis claim.",
                producer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    destination.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: plan[k] for k in ("status", "total_actual_metadata_bytes", "planned_control_rna_bytes", "planned_actual_plus_control_bytes")}))


if __name__ == "__main__":
    main()
