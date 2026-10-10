"""Metadata-only control-cell selection for a bounded native gene-axis audit."""
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

from research.decision_value.pairwise_v3.data_availability.probe import COLS, CONTROL, archive, range_codes

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def main():
    path = HERE / "PROTOCOL.json"
    if path.exists():
        raise FileExistsError(path)
    legacy = json.loads((HERE.parent / "CONTROL_PLAN.json").read_text())
    old_groups = legacy.get("selected", legacy.get("groups"))
    excluded = {file: {int(row) for group in old_groups if group["file"] == file for row in group["rows"]}
                for file in ("c40.h5ad", "c44.h5ad")}
    jobs = [(file, col, archive(file)[0]["code_layouts"][col]) for file in excluded for col in COLS]
    arrays, receipts = {}, []
    with ThreadPoolExecutor(max_workers=4) as pool:
        for spec, result in zip(jobs, pool.map(range_codes, jobs)):
            values, receipt = result
            if values is None:
                raise RuntimeError("exact_metadata_range_unavailable")
            arrays[spec[:2]] = values
            receipts.append(receipt)
    groups, censuses = [], {}
    for file in excluded:
        meta, digest = archive(file)
        code = {col: arrays[(file, col)] for col in COLS}
        if any(hashlib.sha256(code[col].tobytes()).hexdigest() != meta["codes_sha256"][col] for col in COLS):
            raise RuntimeError("metadata_code_hash_mismatch")
        censuses[file] = meta
        names = meta["categories"]
        eligible = (code["drugname_drugconc"] == names["drugname_drugconc"].index(CONTROL)) & (code["pass_filter"] == names["pass_filter"].index("full"))
        for plate in names["plate"]:
            for sample in np.unique(code["sample"][eligible & (code["plate"] == names["plate"].index(plate))]):
                rows = [int(row) for row in np.flatnonzero(eligible & (code["plate"] == names["plate"].index(plate)) & (code["sample"] == sample)) if int(row) not in excluded[file]]
                # First eight available row identities: one fixed compact window per sample, no RNA ranking.
                groups.append(dict(file=file, cell=meta["cell_names"][0], plate=plate, sample=names["sample"][int(sample)],
                                   available_disjoint_full_control_cells=len(rows), rows=rows[:8], census_sha256=digest))
    endpoint = json.loads((HERE.parent / "ENDPOINT.json").read_text())
    protocol = dict(schema="bounded_control_only_gene_axis_v1", source_repo="arcinstitute/State-Tahoe-Filtered",
                    source_revision="fdf87abece385feea6fa5e9944ab46e173b6af50", source_files=list(excluded),
                    selected=groups, selection="Eight lowest full-QC DMSO row identities per plate/sample, after excluding all250 laternoise cells; no response values used.",
                    expression_transform="log1p(raw X)", endpoint=endpoint, minimum_nonzero_cells_per_coordinate_per_file=2,
                    matching_absolute_tolerance=1e-5, unique_matching="Exactly one rawgene vector among all sourcevar genes matches each endpointcoordinate acrossall selectedcells. Expected source symbol must match exactly, with duplicate sparse indices rejected.",
                    read_scope="Only selectedDMSO X_hvg rows, their exactrawCSR pointers/index/value spans, gene-name metadata and HDF5 indexingmetadata; no treatedcell expression decoded or requested intentionally.",
                    axis_network_body_cap_bytes=20_000_000, planned_hvg_bytes=8000*sum(len(g["rows"]) for g in groups),
                    metadata_preparation_bytes=sum(r["bytes"] for r in receipts),
                    full2000_axis_certification=False, STATE_checkpoint_axis_certification=False,
                    null_policy="Only39 individually authenticated endpointcoordinates may benamed; all1961othercoordinates remainnull. No identity inferred fromallzero values.",
                    independence="Authenticationcells are disjoint fromlaternoise cells; their culture/batch independence isunknown. This auditcertifies sourcecoordinate identityonly.",
                    original_asset_search=dict(expected_sha256="a5ab8f6b2b21b765859e55d8cdf50ad44d5b78abbc841962824d062779d7f457", recovered=False,
                        searched_roots=["D:/MAESTRO", "D:/MAESTRO_TMP"], searched_archives=["MAESTRO_biological_knowledge_20261004.zip", "maestro_drylab_solution.zip", "MAESTRO_repeat_signal_20261005.zip", "STATE_evidence_research_20261001.zip"],
                        limitation="Bounded filename/archivalGit searches; some unrelated outputs had accessdenied; not a claim ofmachinewide absence."))
    (HERE / "CENSUSES.json").write_text(json.dumps(censuses, indent=2)+"\n", encoding="utf-8")
    (HERE / "METADATA_RECEIPTS.json").write_text(json.dumps(receipts, indent=2)+"\n", encoding="utf-8")
    path.write_text(json.dumps(protocol, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(dict(groups=len(groups), cells=sum(len(g["rows"]) for g in groups), planned_hvg_bytes=protocol["planned_hvg_bytes"], metadata_bytes=protocol["metadata_preparation_bytes"])))


if __name__ == "__main__":
    main()
