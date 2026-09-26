"""Build the frozen SciPlex3 condition table for the biological-depth audit.

File summary
- Path: research/biological_depth/prepare.py
- Purpose: stream the 24 h SciPlex3 matrix once for library sizes and vehicle means, fix the gene
  universe from vehicle cells and literature anchors only, then stream again to build replicate
  pseudobulks, matched-control shifts and minibulk chunks for representation learning.
- Core points:
  - Gene selection reads vehicle cells only; no treated cell influences which genes are modelled.
  - A replicate group below the minimum cell count is excluded by name, never imputed.
  - Chunks are disjoint cell subsets of one group, so two chunks are two views of one condition.
- Run: python research/biological_depth/prepare.py --output outputs/biological_depth_20260926/prepared
- Depends on: common.py, h5py, numpy, pandas, scipy, rdkit
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
from scipy import sparse

import common

sys.path.insert(0, str(common.ROOT / "src"))

BLOCK = 20_000
CHUNK_CELLS_CONTROL = 16


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 24), b""):
            digest.update(block)
    return digest.hexdigest()


def obs_column(obs, name):
    item = obs[name]
    if isinstance(item, h5py.Group):
        categories = item["categories"].asstr()[:]
        codes = item["codes"][:]
        return np.where(codes >= 0, categories[np.clip(codes, 0, None)], None)
    return item.asstr()[:] if item.dtype.kind in "OS" else item[:]


def row_blocks(matrix, rows: int):
    indptr = matrix["indptr"][:]
    for start in range(0, rows, BLOCK):
        stop = min(start + BLOCK, rows)
        a, b = int(indptr[start]), int(indptr[stop])
        data = matrix["data"][a:b].astype(np.float64)
        indices = matrix["indices"][a:b]
        local = np.repeat(np.arange(stop - start), np.diff(indptr[start:stop + 1]))
        yield start, stop, data, indices, local


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=False)
    started = time.time()
    protocol, anchors = common.load_protocol(), common.load_anchors()
    selection = protocol["selection"]
    source = common.ROOT / protocol["source"]["h5ad"]
    digest = sha256_file(source)
    if digest != protocol["source"]["sha256"]:
        raise SystemExit(f"source_digest_mismatch:{digest}")

    # ---- metadata -------------------------------------------------------------------------
    with h5py.File(source, "r") as f:
        obs = f["obs"]
        meta = pd.DataFrame({key: obs_column(obs, key) for key in
                             ("cell_line", "perturbation", "dose_value", "time", "replicate",
                              "pathway_level_1", "pathway_level_2", "target")})
        ensembl = obs_column(f["var"], "ensembl_id").astype(str)
        n_rows, n_var = (int(v) for v in f["X"].attrs["shape"])
    lines, doses = selection["cell_lines"], [float(d) for d in selection["doses_nM"]]
    base = (meta.time == selection["time_hours"]) & meta.cell_line.isin(lines)
    control = base & (meta.perturbation == "control") & (meta.dose_value == 0)
    treated = base & (meta.perturbation != "control") & meta.dose_value.isin(doses)
    audit = {"rows": n_rows, "controls_24h": int(control.sum()), "treated_24h": int(treated.sum()),
             "controls_with_nonzero_dose": int((base & (meta.perturbation == "control") & (meta.dose_value != 0)).sum())}

    # ---- gene identity ----------------------------------------------------------------------
    # The published label table is not trusted: which label row names which column is decided
    # below by cell-identity markers (virtual_cell.identity_markers), for each candidate offset.
    from virtual_cell.identity_markers import resolve_label_offset, shift_labels

    hgnc = pd.read_csv(common.ROOT / protocol["source"]["gene_identity"], sep="\t", dtype=str,
                       usecols=["symbol", "entrez_id", "ensembl_gene_id", "status"])
    hgnc = hgnc[(hgnc.status == "Approved") & hgnc.ensembl_gene_id.notna()]
    by_ensembl = hgnc.drop_duplicates("ensembl_gene_id").set_index("ensembl_gene_id")
    offsets = (-1, 0, 1)

    def column_labels(offset):
        labels = np.array([x if x is not None else "" for x in shift_labels(list(ensembl), offset, n_var)])
        duplicated = pd.Series(labels).duplicated(keep=False).to_numpy() & (labels != "")
        human = np.array([e.startswith("ENSG") for e in labels]) & ~duplicated
        return labels, human

    candidates = {k: column_labels(k) for k in offsets}

    # ---- pass 1: library size and vehicle means under every candidate offset ------------------
    library = {k: np.zeros(n_rows) for k in offsets}
    control_sum = {k: np.zeros(n_var) for k in offsets}
    line_sum = {k: {line: np.zeros(n_var) for line in lines} for k in offsets}
    is_control = control.to_numpy()
    row_line = meta.cell_line.to_numpy()
    with h5py.File(source, "r") as f:
        for start, stop, data, indices, local in row_blocks(f["X"], n_rows):
            for k in offsets:
                keep = candidates[k][1][indices]
                library[k][start:stop] = np.bincount(local[keep], weights=data[keep], minlength=stop - start)
                rows = local[keep]
                values = np.log1p(data[keep] * 1e4 / np.maximum(library[k][start:stop][rows], 1.0))
                mask = is_control[start:stop][rows]
                control_sum[k] += np.bincount(indices[keep][mask], weights=values[mask], minlength=n_var)
                for line in lines:
                    lm = mask & (row_line[start:stop][rows] == line)
                    line_sum[k][line] += np.bincount(indices[keep][lm], weights=values[lm], minlength=n_var)
    print(f"pass 1 done {time.time() - started:.0f}s", flush=True)
    published_symbols = [by_ensembl.symbol.get(e) for e in ensembl]
    line_count = {line: max(int((is_control & (row_line == line)).sum()), 1) for line in lines}
    offset, checks, refusal = resolve_label_offset(
        {line: line_sum[0][line] / line_count[line] for line in lines}, published_symbols, offsets=offsets)
    audit["feature_label_check"] = {"chosen_offset": offset, "refusal": refusal,
                                    "first_published_label": str(ensembl[0]),
                                    "checks": [c.payload() for c in checks]}
    if refusal:
        raise SystemExit(f"{refusal}:{[c.payload() for c in checks]}")
    ensembl, human = candidates[offset]
    library, control_sum = library[offset], control_sum[offset]
    symbol = np.array([by_ensembl.symbol.get(e) if h else None for e, h in zip(ensembl, human)], dtype=object)
    control_mean = control_sum / max(int(is_control.sum()), 1)

    # ---- gene universe -----------------------------------------------------------------------
    eligible = np.flatnonzero(human & np.array([s is not None and not str(s).startswith("MT-") for s in symbol]))
    top = eligible[np.argsort(-control_mean[eligible], kind="stable")[:2000]]
    gmt = common.read_gmt(common.ROOT / protocol["source"]["gene_sets"])
    anchor_symbols = set()
    for anchor in anchors["anchors"]:
        anchor_symbols.update(anchor.get("genes", []))
        if anchor.get("gene_set"):
            anchor_symbols.update(gmt[anchor["gene_set"]])
    position_by_symbol = {s: i for i, s in enumerate(symbol) if s is not None and human[i]}
    anchor_columns = sorted(position_by_symbol[s] for s in anchor_symbols if s in position_by_symbol)
    columns = np.array(sorted(set(top.tolist()) | set(anchor_columns)))
    genes = pd.DataFrame({"ensembl": ensembl[columns], "symbol": symbol[columns],
                          "entrez": [by_ensembl.entrez_id.get(e) for e in ensembl[columns]],
                          "control_mean": control_mean[columns],
                          "in_top2000": np.isin(columns, top), "anchor_gene": np.isin(columns, anchor_columns)})
    genes.to_csv(out / "genes.csv", index=False)
    audit["genes"] = {"modelled": int(len(columns)), "top2000": 2000, "anchor_genes_found": len(anchor_columns),
                      "anchor_genes_absent_from_features": sorted(anchor_symbols - set(position_by_symbol))}
    position = np.full(n_var, -1)
    position[columns] = np.arange(len(columns))

    # ---- groups and chunks ---------------------------------------------------------------------
    rng = np.random.default_rng(20260926)
    frame = meta.loc[control | treated, ["cell_line", "perturbation", "dose_value", "replicate"]].copy()
    frame["dose_value"] = frame.dose_value.astype(float)
    keys = pd.MultiIndex.from_frame(frame)
    codes, levels = pd.factorize(keys, sort=True)
    groups = levels.to_frame(index=False)
    groups.columns = ["cell_line", "compound", "dose", "replicate"]
    groups["n_cells"] = np.bincount(codes, minlength=len(groups))
    groups["is_control"] = groups.compound == "control"
    row_group = np.full(n_rows, -1)
    row_group[frame.index.to_numpy()] = codes
    row_chunk = np.full(n_rows, -1)
    chunk_group, next_chunk = [], 0
    members = pd.Series(frame.index.to_numpy()).groupby(codes).apply(list)
    for g, rows in members.items():
        rows = np.array(rows)[rng.permutation(len(rows))]
        k = (max(1, len(rows) // CHUNK_CELLS_CONTROL) if groups.is_control[g]
             else selection["chunks_per_group"])
        for part in np.array_split(rows, k):
            if len(part):
                row_chunk[part] = next_chunk
                chunk_group.append(g)
                next_chunk += 1
    chunk_group = np.array(chunk_group)
    group_sum = np.zeros((len(groups), len(columns)))
    chunk_sum = np.zeros((next_chunk, len(columns)), dtype=np.float64)
    with h5py.File(source, "r") as f:
        for start, stop, data, indices, local in row_blocks(f["X"], n_rows):
            block_groups = row_group[start:stop]
            active = block_groups >= 0
            if not active.any():
                continue
            pos = position[indices]
            keep = (pos >= 0) & active[local]
            rows = local[keep]
            values = np.log1p(data[keep] * 1e4 / np.maximum(library[start:stop][rows], 1.0))
            dense = sparse.csr_matrix((values, (rows, pos[keep])), shape=(stop - start, len(columns)))
            active_rows = np.flatnonzero(active)
            to_group = sparse.csr_matrix((np.ones(len(active_rows)), (block_groups[active_rows], active_rows)),
                                         shape=(len(groups), stop - start))
            group_sum += (to_group @ dense).toarray()
            block_chunks = row_chunk[start:stop][active_rows]
            present = np.unique(block_chunks)
            remap = np.full(next_chunk, -1)
            remap[present] = np.arange(len(present))
            to_chunk = sparse.csr_matrix((np.ones(len(active_rows)), (remap[block_chunks], active_rows)),
                                         shape=(len(present), stop - start))
            chunk_sum[present] += (to_chunk @ dense).toarray()
    print(f"pass 2 done {time.time() - started:.0f}s", flush=True)
    group_mean = (group_sum / np.maximum(groups.n_cells.to_numpy(), 1)[:, None]).astype(np.float32)
    chunk_cells = np.bincount(row_chunk[row_chunk >= 0], minlength=next_chunk)
    chunk_mean = (chunk_sum / np.maximum(chunk_cells, 1)[:, None]).astype(np.float32)
    groups.to_csv(out / "groups.csv", index_label="group_id")
    np.savez_compressed(out / "pseudobulk.npz", group_mean=group_mean)
    np.savez_compressed(out / "chunks.npz", chunk_mean=chunk_mean, chunk_group=chunk_group, chunk_cells=chunk_cells)

    # ---- matched-control shifts per replicate ------------------------------------------------------
    control_index = {(r.cell_line, r.replicate): i for i, r in groups[groups.is_control].iterrows()}
    minimum = selection["minimum_cells_per_group"]
    records, rep_shift, excluded = [], {}, []
    for i, r in groups[~groups.is_control].iterrows():
        if r.n_cells < minimum:
            excluded.append({"group_id": int(i), "reason": "below_minimum_cells", "n_cells": int(r.n_cells)})
            continue
        c = control_index.get((r.cell_line, r.replicate))
        if c is None:
            excluded.append({"group_id": int(i), "reason": "matched_control_missing"})
            continue
        rep_shift[(r.cell_line, r.compound, r.dose, r.replicate)] = (group_mean[i] - group_mean[c], int(r.n_cells))
    conditions = sorted({k[:3] for k in rep_shift})
    shift, rep1, rep2 = [], [], []
    missing = np.full(len(columns), np.nan, dtype=np.float32)
    for line, compound, dose in conditions:
        a = rep_shift.get((line, compound, dose, "rep1"))
        b = rep_shift.get((line, compound, dose, "rep2"))
        available = [v for v in (a, b) if v is not None]
        shift.append(np.mean([v[0] for v in available], axis=0))
        rep1.append(a[0] if a is not None else missing)
        rep2.append(b[0] if b is not None else missing)
        records.append({"cell_line": line, "compound": compound, "dose": dose, "replicates": len(available),
                        "n_cells": sum(v[1] for v in available),
                        "n_cells_rep1": a[1] if a is not None else 0, "n_cells_rep2": b[1] if b is not None else 0})
    conditions_frame = pd.DataFrame(records)

    # ---- vehicle null: pseudo-groups of 8 control chunks against the rest of the controls ----------
    null = {}
    for (line, rep), c in control_index.items():
        chunk_ids = np.flatnonzero(chunk_group == c)
        order = rng.permutation(chunk_ids)
        norms, sizes = [], []
        for part in [order[i:i + 8] for i in range(0, len(order) - 7, 8)]:
            rest = np.setdiff1d(chunk_ids, part)
            inside = (chunk_mean[part] * chunk_cells[part, None]).sum(0) / chunk_cells[part].sum()
            outside = (chunk_mean[rest] * chunk_cells[rest, None]).sum(0) / chunk_cells[rest].sum()
            norms.append(float(np.linalg.norm(inside - outside)))
            sizes.append(int(chunk_cells[part].sum()))
        null.setdefault(line, {"norms": [], "sizes": []})
        null[line]["norms"] += norms
        null[line]["sizes"] += sizes
    for line, value in null.items():
        scaled = np.array(value["norms"]) * np.sqrt(np.array(value["sizes"]) / 128.0)
        value["q95_at_128_cells"] = float(np.quantile(scaled, 0.95))
        value["pseudo_groups"] = len(scaled)

    # ---- compounds: structure, skeleton, annotation, fold -------------------------------------------
    compounds = sorted(set(conditions_frame.compound))
    with h5py.File(common.ROOT / "data/raw/sciplex3/sciplex_complete_middle_subset.h5ad", "r") as f:
        o = f["obs"]
        names = o["__categories/product_name"].asstr()[:][o["product_name"][:]]
        smiles = o["__categories/SMILES"].asstr()[:][o["SMILES"][:]]
    hub = pd.read_csv(common.ROOT / "data/raw/sciplex3/repurposing_samples_20200324.txt", sep="\t", comment="!")
    manual = {"Anacardic Acid": ("CCCCCCCCCCCCCCCC1=C(C(=CC=C1)O)C(=O)O", "pubchem:CID167551")}
    structures, structure_source = common.resolve_structures(compounds, sorted(set(zip(names, smiles))), hub, manual)
    drugs = pd.read_csv(common.ROOT / protocol["source"]["targets"], sep="\t", comment="!")
    hub_rows: dict[str, list] = {}
    for _, row in drugs.iterrows():
        for key in common.name_keys(row.pert_iname):
            hub_rows.setdefault(key, []).append(row)
    annotation = meta[treated].groupby("perturbation")[["pathway_level_1", "pathway_level_2", "target"]].first()
    table = []
    for compound in compounds:
        hits = [h for key in common.name_keys(compound) for h in hub_rows.get(key, [])]
        table.append({"compound": compound, "smiles": structures.get(compound), "structure_source": structure_source.get(compound),
                      "skeleton": common.skeleton(structures[compound]) if compound in structures else None,
                      "pathway_level_1": annotation.pathway_level_1.get(compound),
                      "pathway_level_2": annotation.pathway_level_2.get(compound),
                      "target": annotation.target.get(compound),
                      "hub_targets": "|".join(sorted({g for h in hits if isinstance(h.target, str) for g in h.target.split("|")})),
                      "hub_moa": "|".join(sorted({m for h in hits if isinstance(h.moa, str) for m in h.moa.split("|")}))})
    compound_frame = pd.DataFrame(table)
    if compound_frame.smiles.isna().any():
        raise SystemExit("unresolved_structure:" + ",".join(compound_frame.compound[compound_frame.smiles.isna()]))
    folds = common.assign_folds(compound_frame[["skeleton", "pathway_level_1"]].drop_duplicates("skeleton"),
                                protocol["split"]["folds"])
    compound_frame["fold"] = compound_frame.skeleton.map(folds)
    compound_frame.to_csv(out / "compounds.csv", index=False)
    conditions_frame["fold"] = conditions_frame.compound.map(dict(zip(compound_frame.compound, compound_frame.fold)))
    conditions_frame.to_csv(out / "conditions.csv", index_label="condition_id")
    np.savez_compressed(out / "shifts.npz", shift=np.asarray(shift, dtype=np.float32),
                        rep1=np.asarray(rep1, dtype=np.float32), rep2=np.asarray(rep2, dtype=np.float32))
    universe = set(genes.symbol)
    common.write_json(out / "gene_sets.json", {name: [g for g in members if g in universe] for name, members in gmt.items()})
    common.write_json(out / "vehicle_null.json", null)
    audit.update({"conditions": len(conditions_frame), "excluded_replicate_groups": excluded,
                  "compounds": len(compound_frame), "skeleton_groups": int(compound_frame.skeleton.nunique()),
                  "fold_sizes": compound_frame.drop_duplicates("skeleton").fold.value_counts().sort_index().to_dict(),
                  "chunks": int(next_chunk), "structure_sources": compound_frame.structure_source.value_counts().to_dict()})
    common.write_json(out / "prepare_manifest.json", {"source_sha256": digest, "protocol_hashes": common.frozen_hashes(),
                                                      "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                                                      "seconds": round(time.time() - started, 1), "audit": audit})
    print(json.dumps(audit, indent=1, default=str)[:3000], flush=True)


if __name__ == "__main__":
    main()
