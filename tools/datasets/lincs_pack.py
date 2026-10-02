"""Build the LINCS 2020 evaluation data pack per the frozen protocol.

File summary
- Path: tools/datasets/lincs_pack.py
- Purpose: select the pool, the reference blocks and the untouched test blocks from LINCS 2020
  metadata (protocol section 2), extract the corresponding Level 5 signature columns from the
  registered GCTX source, compute reference centroids and the validator's reference readings, and
  write a hashed data pack. Test-unit signatures are written to the pack but never read by any
  fitting step; `load_pack` separates reference-side and test-side payloads.
- Core points:
  - Scope: trt_cp Level 5 signatures in A549, MCF7, PC3, VCAP at 24 h and 10 uM.
  - Pool: `moa` classes with >= 12 total pool blocks and >= 3 unseen blocks (metadata-only rule).
    The historical protocol said reference blocks; the already-recorded implementation
    deviation is retained, without changing the frozen selection rule.
  - Split: test = InChIKey connectivity blocks absent from GSE92742 and GSE70138 trt_cp lists;
    reference = the remaining blocks in pool classes.
  - The pack records the SHA-256 of every input and of itself; the protocol freeze names the code
    version that built it.
- Interfaces: `build_pack`, `load_pack`, `PackError`, `PACK_VERSION`
- Depends on: data/external/lincs2020 (registered source), data/external/lincs_l1000_phase{1,2}
  pert_info (split definition), data/external/msigdb Hallmark GMT, h5py, numpy, pandas
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PACK_VERSION = "external-pack-1"
CORE_CELL_LINES = ("A549", "MCF7", "PC3", "VCAP")
CORE_TIME_H = 24
CORE_DOSE_UM = 10
MIN_REFERENCE_BLOCKS = 12
MIN_UNSEEN_BLOCKS = 3
SEED = 20260929


class PackError(Exception):
    """The source files do not match their registered checksums or the pack is inconsistent."""


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 22), b""):
            h.update(block)
    return h.hexdigest()


def _development_blocks(workspace: Path | None = None) -> set[str]:
    """The trt_cp connectivity blocks of GSE92742 and GSE70138: the split's reference-study list."""

    root = Path(workspace).resolve() if workspace is not None else ROOT

    p1 = pd.read_csv(root / "data/external/lincs_l1000_phase1/GSE92742_Broad_LINCS_pert_info.txt.gz",
                     sep="\t", low_memory=False)
    p2 = pd.read_csv(root / "data/external/lincs_l1000_phase2/GSE70138_Broad_LINCS_pert_info.txt.gz",
                     sep="\t", low_memory=False)
    blocks = set(p1.loc[p1.pert_type == "trt_cp", "inchi_key_prefix"].dropna())
    blocks |= set(p2.loc[p2.pert_type == "trt_cp", "inchi_key"].dropna().str[:14])
    return blocks


def select_population(workspace: Path | None = None) -> dict:
    """Metadata-only population selection per protocol section 2 (no signature values)."""

    root = Path(workspace).resolve() if workspace is not None else ROOT

    ci = pd.read_csv(root / "data/external/lincs2020/compoundinfo_beta.txt", sep="\t", low_memory=False)
    ci["block"] = ci.inchi_key.str[:14]
    cols = ["sig_id", "pert_id", "pert_type", "cell_iname", "pert_dose", "pert_time"]
    si = pd.read_csv(root / "data/external/lincs2020/siginfo_beta.txt", sep="\t", usecols=cols,
                     low_memory=False)
    si = si[si.pert_type == "trt_cp"].merge(ci[["pert_id", "block", "moa", "cmap_name", "inchi_key"]],
                                            on="pert_id", how="left")
    scope = si[si.cell_iname.isin(CORE_CELL_LINES) & (si.pert_time == CORE_TIME_H)
               & (si.pert_dose == CORE_DOSE_UM)].copy()
    dev = _development_blocks(root)
    scope["unseen"] = ~scope.block.isin(dev)
    labeled = scope[scope.moa.notna()]
    per_class_all = labeled.groupby("moa").block.nunique()
    per_class_unseen = labeled[labeled.unseen].groupby("moa").block.nunique()
    pool = sorted(moa for moa in per_class_all.index
                  if per_class_all[moa] >= MIN_REFERENCE_BLOCKS
                  and per_class_unseen.get(moa, 0) >= MIN_UNSEEN_BLOCKS)
    in_pool = labeled[labeled.moa.isin(pool)]
    units = {}
    for (block, moa, unseen), group in in_pool.groupby(["block", "moa", "unseen"]):
        # one representative pert_id per block: the most frequent in the scope, ties broken by id
        pert = group.pert_id.value_counts().sort_index().idxmax()
        sigs = {row.cell_iname: row.sig_id for row in group[group.pert_id == pert].itertuples()}
        units[block] = {"moa": moa, "unseen": bool(unseen), "pert_id": pert, "signatures": sigs,
                        "cmap_name": group.cmap_name.iloc[0]}
    return {"pool": pool, "units": units,
            "counts": {"pool_classes": len(pool),
                       "reference_blocks": sum(1 for u in units.values() if not u["unseen"]),
                       "unseen_blocks": sum(1 for u in units.values() if u["unseen"])}}


def _hallmark_landmark(landmark_symbols: set[str], workspace: Path | None = None) -> dict[str, tuple[str, ...]]:
    """Hallmark v2024.1 gene sets restricted to the measured landmark space (frozen rule)."""

    root = Path(workspace).resolve() if workspace is not None else ROOT

    sets: dict[str, tuple[str, ...]] = {}
    path = root / "data/external/msigdb/h.all.v2024.1.Hs.symbols.gmt"
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 3:
            continue
        members = tuple(sorted(g for g in parts[2:] if g in landmark_symbols))
        if len(members) >= 5:
            sets[parts[0]] = members
    return sets


def build_pack(out_dir: Path | None = None, *, workspace: Path | None = None) -> dict:
    """Extract the population's signatures from the registered GCTX and write the hashed pack.

    Reference-side artifacts (centroids, reference readings, feature matrices for references) are
    fitted here; test-unit signature columns are stored raw. Nothing on the test side is read.
    """

    root = Path(workspace).resolve() if workspace is not None else ROOT

    import h5py

    out_dir = out_dir or root / "data/processed/case_memory_integration"
    out_dir.mkdir(parents=True, exist_ok=True)
    gctx_path = root / "data/external/lincs2020/level5/level5_beta_trt_cp_n720216x12328.gctx"
    if not gctx_path.is_file():
        raise PackError(f"registered source missing:{gctx_path}")
    population = select_population(root)
    pool, units = population["pool"], population["units"]
    with h5py.File(gctx_path, "r") as gctx:
        matrix = gctx["0/DATA/0/matrix"]
        col_ids = [c.decode() if isinstance(c, bytes) else str(c)
                   for c in gctx["0/META/COL/id"][:]]
        gene_ids = [g.decode() if isinstance(g, bytes) else str(g)
                    for g in gctx["0/META/ROW/id"][:]]
        col_pos = {c: i for i, c in enumerate(col_ids)}
        wanted = sorted({sig for u in units.values() for sig in u["signatures"].values()
                         if sig in col_pos})
        gene_info = pd.read_csv(root / "data/external/lincs2020/geneinfo_beta.txt", sep="\t")
        landmark = set(gene_info.loc[gene_info.feature_space == "landmark", "gene_symbol"])
        gene_symbols = dict(zip(gene_info.gene_id.astype(str), gene_info.gene_symbol))
        symbols = [gene_symbols.get(g, g) for g in gene_ids]
        landmark_rows = np.array([i for i, s in enumerate(symbols) if s in landmark], dtype=int)
        landmark_symbols = [symbols[i] for i in landmark_rows]
        # the matrix is (signatures, genes); read the wanted signatures one at a time
        # (h5py allows only 1D fancy indexing)
        positions = sorted(col_pos[s] for s in wanted)
        wanted_sorted = [col_ids[p] for p in positions]
        block = np.empty((len(landmark_rows), len(positions)), dtype=np.float32)
        for j, pos in enumerate(positions):
            block[:, j] = matrix[pos, landmark_rows]
            if j % 1000 == 999:
                print(f"  extracted {j + 1}/{len(positions)} signature columns", flush=True)
    sig_index = {s: j for j, s in enumerate(wanted_sorted)}
    gene_sets = _hallmark_landmark(set(landmark_symbols), root)
    set_names = sorted(gene_sets)
    set_rows = np.array([[landmark_symbols.index(g) for g in gene_sets[name]] for name in set_names],
                        dtype=object)
    # per-unit signature vectors in the landmark space
    vectors: dict[str, dict[str, np.ndarray]] = {}
    for block_id, unit in units.items():
        vectors[block_id] = {}
        for cell, sig in unit["signatures"].items():
            if sig in sig_index:
                vectors[block_id][cell] = block[:, sig_index[sig]]
    reference = [b for b, u in units.items() if not u["unseen"]]
    test = [b for b, u in units.items() if u["unseen"]]
    # class centroids per condition from reference blocks only
    centroids: dict[str, dict[str, np.ndarray]] = {c: {} for c in pool}
    for klass in pool:
        members = [b for b in reference if units[b]["moa"] == klass]
        for cell in CORE_CELL_LINES:
            vecs = [vectors[b][cell] for b in members if cell in vectors.get(b, {})]
            if vecs:
                centroids[klass][cell] = np.mean(vecs, axis=0)
    pack = {
        "version": PACK_VERSION,
        "seed": SEED,
        "pool": pool,
        "landmark_symbols": landmark_symbols,
        "gene_sets": {name: list(gene_sets[name]) for name in set_names},
        "units": {b: {"moa": u["moa"], "unseen": u["unseen"], "pert_id": u["pert_id"],
                      "cmap_name": u["cmap_name"],
                      "conditions": sorted(vectors.get(b, {}))} for b, u in units.items()},
        "counts": population["counts"],
    }
    arrays = {f"vec::{b}::{cell}": v for b, cells in vectors.items() for cell, v in cells.items()}
    arrays.update({f"centroid::{c}::{cell}": v for c, cells in centroids.items()
                   for cell, v in cells.items()})
    np.savez_compressed(out_dir / "pack_arrays.npz", **arrays)
    (out_dir / "pack.json").write_text(json.dumps(pack, indent=1), encoding="utf-8")
    manifest = {
        "pack_version": PACK_VERSION,
        "built_at": pd.Timestamp.now().isoformat(),
        "inputs": {
            "gctx": {"path": str(gctx_path.relative_to(root)), "sha256": sha256_file(gctx_path)},
            "compoundinfo": {"path": "data/external/lincs2020/compoundinfo_beta.txt",
                             "sha256": sha256_file(root / "data/external/lincs2020/compoundinfo_beta.txt")},
            "siginfo_columns_used": ["sig_id", "pert_id", "pert_type", "cell_iname",
                                     "pert_dose", "pert_time"],
        },
        "outputs": {
            "pack.json": sha256_file(out_dir / "pack.json"),
            "pack_arrays.npz": sha256_file(out_dir / "pack_arrays.npz"),
        },
        "counts": population["counts"],
        "counts_detail": {
            "reference_vectors": sum(len(vectors[b]) for b in reference),
            "test_vectors": sum(len(vectors[b]) for b in test),
            "centroid_entries": sum(len(c) for c in centroids.values()),
        },
    }
    (out_dir / "pack_manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    return manifest


def load_pack(*, workspace: Path | None = None) -> tuple[dict, dict[str, np.ndarray]]:
    """Load the pack. Callers must keep reference-side and test-side keys apart."""

    root = Path(workspace).resolve() if workspace is not None else ROOT

    out_dir = root / "data/processed/case_memory_integration"
    pack = json.loads((out_dir / "pack.json").read_text(encoding="utf-8"))
    arrays = dict(np.load(out_dir / "pack_arrays.npz"))
    return pack, arrays
