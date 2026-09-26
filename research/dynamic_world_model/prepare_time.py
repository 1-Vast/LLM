"""Build the SciPlex3 condition table at both measured times, with the readouts a state needs.

File summary
- Path: research/dynamic_world_model/prepare_time.py
- Purpose: one streaming pass over the SciPlex3 matrix that yields, on the frozen 2,473-gene
  universe of the 2026-09-26 biological-depth run, replicate pseudobulk shifts for every
  24 h condition (three lines) and every 72 h condition (A549 only), vehicle pseudobulks per
  well for a well-level detection null, cell-cycle module scores, and per-well cell counts.
- Core points:
  - Gene identity is re-checked with the cell-identity markers on this pass; the run refuses by
    name unless the markers choose the same label offset as the frozen universe.
  - A shift is always taken against the vehicle of the same line, time and replicate. The 72 h
    cohort sits on its own plates, so a 24 h vs 72 h comparison of *shifts* removes the plate
    effect shared by a plate's wells; the cells at the two times are different cells.
  - Printed output is structural only (counts, exclusions, identity check). No response
    magnitude is printed before the protocol is frozen.
- Run: python research/dynamic_world_model/prepare_time.py --output outputs/dynamic_world_model_20260926/prepared
- Depends on: research/biological_depth/prepare.py (readers), virtual_cell.identity_markers, h5py, numpy, pandas, scipy
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import h5py
from scipy import sparse

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "research" / "biological_depth"))

from prepare import obs_column, row_blocks, sha256_file  # noqa: E402
from virtual_cell.identity_markers import resolve_label_offset, shift_labels  # noqa: E402

SOURCE = ROOT / "data/raw/sciplex3/SrivatsanTrapnell2020_sciplex3.h5ad"
SOURCE_SHA256 = "bde2420c"  # prefix recorded in data/README.md; the full digest is written to the manifest
FROZEN = ROOT / "outputs/biological_depth_20260926/prepared"
MINIMUM_CELLS = 20
DOSES = (10.0, 100.0, 1000.0, 10000.0)
LINES = ("A549", "K562", "MCF7")

# Tirosh et al. 2016 cell-cycle programmes (Seurat cc.genes), current HGNC symbols.
S_GENES = ("MCM5 PCNA TYMS FEN1 MCM2 MCM4 RRM1 UNG GINS2 MCM6 CDCA7 DTL PRIM1 UHRF1 CENPU HELLS RFC2 "
           "RPA2 NASP RAD51AP1 GMNN WDR76 SLBP CCNE2 UBR7 POLD3 MSH2 ATAD2 RAD51 RRM2 CDC45 CDC6 EXO1 "
           "TIPIN DSCC1 BLM CASP8AP2 USP1 CLSPN POLA1 CHAF1B BRIP1 E2F8").split()
G2M_GENES = ("HMGB2 CDK1 NUSAP1 UBE2C BIRC5 TPX2 TOP2A NDC80 CKS2 NUF2 CKS1B MKI67 TMPO CENPF TACC3 PIMREG "
             "SMC4 CCNB2 CKAP2L CKAP2 AURKB BUB1 KIF11 ANP32E TUBB4B GTSE1 KIF20B HJURP CDCA3 JPT1 CDC20 TTK "
             "CDC25C KIF2C RANGAP1 NCAPD2 DLGAP5 CDCA2 CDCA8 ECT2 KIF23 HMMR AURKA PSRC1 ANLN LBR CKAP5 "
             "CENPE CTCF NEK2 G2E3 GAS2L3 CBX5 CENPA").split()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=False)
    started = time.time()
    digest = sha256_file(SOURCE)
    if not digest.startswith(SOURCE_SHA256):
        raise SystemExit(f"source_digest_mismatch:{digest}")
    frozen_genes = pd.read_csv(FROZEN / "genes.csv")
    frozen_manifest = json.loads((FROZEN / "prepare_manifest.json").read_text(encoding="utf-8"))
    frozen_offset = frozen_manifest["audit"]["feature_label_check"]["chosen_offset"]

    with h5py.File(SOURCE, "r") as f:
        obs = f["obs"]
        meta = pd.DataFrame({key: obs_column(obs, key) for key in
                             ("cell_line", "perturbation", "dose_value", "time", "replicate", "plate", "well")})
        published = obs_column(f["var"], "ensembl_id").astype(str)
        n_rows, n_var = (int(v) for v in f["X"].attrs["shape"])
    meta["time"] = meta.time.astype(float)
    meta["dose_value"] = meta.dose_value.astype(float)

    hgnc = pd.read_csv(ROOT / "data/external/hgnc/hgnc_complete_set.txt", sep="\t", dtype=str,
                       usecols=["symbol", "ensembl_gene_id", "status"])
    hgnc = hgnc[(hgnc.status == "Approved") & hgnc.ensembl_gene_id.notna()]
    by_ensembl = hgnc.drop_duplicates("ensembl_gene_id").set_index("ensembl_gene_id").symbol

    labels = np.array([x if x is not None else "" for x in shift_labels(list(published), frozen_offset, n_var)])
    duplicated = pd.Series(labels).duplicated(keep=False).to_numpy() & (labels != "")
    human = np.array([e.startswith("ENSG") for e in labels]) & ~duplicated
    symbol = np.array([by_ensembl.get(e) if h else None for e, h in zip(labels, human)], dtype=object)

    position = np.full(n_var, -1)
    column_of = {e: i for i, e in enumerate(labels) if human[i]}
    missing_genes = [e for e in frozen_genes.ensembl if e not in column_of]
    if missing_genes:
        raise SystemExit(f"frozen_gene_absent_under_offset:{missing_genes[:5]}")
    columns = np.array([column_of[e] for e in frozen_genes.ensembl])
    position[columns] = np.arange(len(columns))
    by_symbol = {s: i for i, s in enumerate(symbol) if s is not None}
    s_cols = np.array(sorted(by_symbol[g] for g in S_GENES if g in by_symbol))
    g2m_cols = np.array(sorted(by_symbol[g] for g in G2M_GENES if g in by_symbol))
    s_member = np.zeros(n_var, bool); s_member[s_cols] = True
    g_member = np.zeros(n_var, bool); g_member[g2m_cols] = True

    in_scope = (meta.cell_line.isin(LINES) & meta.time.isin((24.0, 72.0))
                & (((meta.perturbation == "control") & (meta.dose_value == 0))
                   | ((meta.perturbation != "control") & meta.perturbation.notna() & meta.dose_value.isin(DOSES))))
    frame = meta.loc[in_scope].copy()
    frame["is_control"] = frame.perturbation == "control"
    # One group per well: a treated condition-replicate is exactly one well, a vehicle well is its own group.
    keys = pd.MultiIndex.from_frame(frame[["cell_line", "time", "perturbation", "dose_value", "replicate", "plate", "well"]])
    codes, levels = pd.factorize(keys, sort=True)
    wells = levels.to_frame(index=False)
    wells.columns = ["cell_line", "time", "compound", "dose", "replicate", "plate", "well"]
    wells["n_cells"] = np.bincount(codes, minlength=len(wells))
    wells["is_control"] = wells.compound == "control"
    row_well = np.full(n_rows, -1)
    row_well[frame.index.to_numpy()] = codes

    well_sum = np.zeros((len(wells), len(columns)))
    s_score = np.full(n_rows, np.nan)
    g_score = np.full(n_rows, np.nan)
    vehicle_line_sum = {line: np.zeros(n_var) for line in LINES}
    vehicle_line_n = {line: 0 for line in LINES}
    row_line = meta.cell_line.to_numpy()
    row_control = (meta.perturbation == "control").to_numpy() & (meta.time == 24.0).to_numpy()
    with h5py.File(SOURCE, "r") as f:
        for start, stop, data, indices, local in row_blocks(f["X"], n_rows):
            block_wells = row_well[start:stop]
            active = block_wells >= 0
            if not active.any():
                continue
            keep = human[indices]
            rows = local[keep]
            library = np.bincount(rows, weights=data[keep], minlength=stop - start)
            values = np.log1p(data[keep] * 1e4 / np.maximum(library[rows], 1.0))
            idx = indices[keep]
            # identity guard: vehicle means per line at 24 h, all columns
            vmask = row_control[start:stop][rows]
            for line in LINES:
                lm = vmask & (row_line[start:stop][rows] == line)
                vehicle_line_sum[line] += np.bincount(idx[lm], weights=values[lm], minlength=n_var)
            for line in LINES:
                vehicle_line_n[line] += int((row_control[start:stop] & (row_line[start:stop] == line)).sum())
            # cell-cycle module means per cell
            s_sum = np.bincount(rows[s_member[idx]], weights=values[s_member[idx]], minlength=stop - start)
            g_sum = np.bincount(rows[g_member[idx]], weights=values[g_member[idx]], minlength=stop - start)
            s_score[start:stop] = s_sum / max(len(s_cols), 1)
            g_score[start:stop] = g_sum / max(len(g2m_cols), 1)
            # well pseudobulks on the frozen universe
            pos = position[idx]
            sel = (pos >= 0) & active[rows]
            dense = sparse.csr_matrix((values[sel], (rows[sel], pos[sel])), shape=(stop - start, len(columns)))
            active_rows = np.flatnonzero(active)
            to_well = sparse.csr_matrix((np.ones(len(active_rows)), (block_wells[active_rows], active_rows)),
                                        shape=(len(wells), stop - start))
            well_sum += (to_well @ dense).toarray()
    print(f"pass done {time.time() - started:.0f}s", flush=True)

    # identity guard: under the corrected labels the markers must choose offset 0 among -1, 0, +1
    means = {line: vehicle_line_sum[line] / max(vehicle_line_n[line], 1) for line in LINES}
    offset, checks, refusal = resolve_label_offset(means, [by_ensembl.get(e) for e in labels], offsets=(-1, 0, 1))
    if refusal or offset != 0:
        raise SystemExit(f"identity_guard_failed:{refusal}:{[c.payload() for c in checks]}")

    well_mean = (well_sum / np.maximum(wells.n_cells.to_numpy(), 1)[:, None]).astype(np.float32)
    cells = pd.DataFrame({"well_group": row_well, "s": s_score, "g2m": g_score})
    cells = cells[cells.well_group >= 0]
    per_well = cells.groupby("well_group")[["s", "g2m"]].mean()
    wells["s_score"] = per_well.s.reindex(range(len(wells))).to_numpy()
    wells["g2m_score"] = per_well.g2m.reindex(range(len(wells))).to_numpy()
    # fraction of cells above the vehicle 90th percentile of the same line and time
    for name in ("s", "g2m"):
        wells[f"{name}_high_fraction"] = np.nan
        for (line, t), sub in wells.groupby(["cell_line", "time"]):
            vehicle_groups = sub.index[sub.is_control]
            threshold = np.quantile(cells.loc[cells.well_group.isin(vehicle_groups), name], 0.9)
            high = cells.assign(h=cells[name] > threshold).groupby("well_group").h.mean()
            wells.loc[sub.index, f"{name}_high_fraction"] = high.reindex(sub.index).to_numpy()

    # vehicle reference per (line, time, replicate): pooled over its vehicle wells
    vehicle = wells[wells.is_control]
    pooled = {}
    for key, sub in vehicle.groupby(["cell_line", "time", "replicate"]):
        weights = sub.n_cells.to_numpy()[:, None]
        pooled[key] = ((well_mean[sub.index] * weights).sum(0) / weights.sum(), int(weights.sum()), list(sub.index))
    vehicle_count = vehicle.groupby(["cell_line", "time", "plate"]).n_cells.mean()

    records, shift, rep1, rep2, excluded = [], [], [], [], []
    missing = np.full(len(columns), np.nan, dtype=np.float32)
    treated = wells[~wells.is_control]
    for (line, t, compound, dose), sub in treated.groupby(["cell_line", "time", "compound", "dose"], sort=True):
        reps = {}
        for i, r in sub.iterrows():
            if r.n_cells < MINIMUM_CELLS:
                excluded.append({"well_group": int(i), "reason": "below_minimum_cells", "n_cells": int(r.n_cells),
                                 "cell_line": line, "time": t, "compound": compound, "dose": dose})
                continue
            ref = pooled.get((line, t, r.replicate))
            if ref is None:
                excluded.append({"well_group": int(i), "reason": "matched_vehicle_missing"})
                continue
            plate_vehicle = vehicle_count.get((line, t, r.plate))
            reps[r.replicate] = (well_mean[i] - ref[0], int(r.n_cells), r.plate, r.well,
                                 float(np.log2(r.n_cells / plate_vehicle)) if plate_vehicle else np.nan,
                                 r.s_score, r.g2m_score, r.s_high_fraction, r.g2m_high_fraction)
        if not reps:
            continue
        a, b = reps.get("rep1"), reps.get("rep2")
        available = [v for v in (a, b) if v is not None]
        shift.append(np.mean([v[0] for v in available], axis=0))
        rep1.append(a[0] if a is not None else missing)
        rep2.append(b[0] if b is not None else missing)
        rec = {"cell_line": line, "time": t, "compound": compound, "dose": dose, "replicates": len(available),
               "n_cells": sum(v[1] for v in available)}
        for tag, v in (("rep1", a), ("rep2", b)):
            rec.update({f"n_cells_{tag}": v[1] if v else 0, f"plate_{tag}": v[2] if v else None,
                        f"well_{tag}": v[3] if v else None, f"log2_count_ratio_{tag}": v[4] if v else np.nan,
                        f"s_score_{tag}": v[5] if v else np.nan, f"g2m_score_{tag}": v[6] if v else np.nan,
                        f"s_high_{tag}": v[7] if v else np.nan, f"g2m_high_{tag}": v[8] if v else np.nan})
        records.append(rec)
    conditions = pd.DataFrame(records)
    compounds = pd.read_csv(FROZEN / "compounds.csv")
    fold = {c.strip(): f for c, f in zip(compounds.compound, compounds.fold)}
    conditions["fold"] = conditions.compound.map(lambda c: fold.get(str(c).strip()))
    if conditions.fold.isna().any():
        raise SystemExit("compound_without_fold:" + ",".join(sorted(set(conditions.compound[conditions.fold.isna()]))))
    conditions.to_csv(out / "conditions.csv", index_label="condition_id")
    np.savez_compressed(out / "shifts.npz", shift=np.asarray(shift, np.float32), rep1=np.asarray(rep1, np.float32),
                        rep2=np.asarray(rep2, np.float32))
    wells.to_csv(out / "wells.csv", index_label="well_group")
    np.savez_compressed(out / "well_means.npz", well_mean=well_mean)
    vehicle_refs = {f"{k[0]}|{k[1]:g}|{k[2]}": {"cells": v[1], "well_groups": v[2]} for k, v in pooled.items()}

    # consistency with the frozen 24 h preparation (same genes, same normalization, same vehicles)
    old = pd.read_csv(FROZEN / "conditions.csv")
    old_shift = np.load(FROZEN / "shifts.npz")["shift"]
    new24 = conditions[conditions.time == 24.0].reset_index()
    lookup = {(r.cell_line, r.compound, float(r.dose)): r["index"] for _, r in new24.iterrows()}
    diffs = [float(np.max(np.abs(old_shift[i] - np.asarray(shift)[lookup[(r.cell_line, r.compound, float(r.dose))]])))
             for i, r in old.iterrows() if (r.cell_line, r.compound, float(r.dose)) in lookup]
    audit = {
        "source_sha256": digest, "label_offset": frozen_offset, "identity_guard": [c.payload() for c in checks],
        "genes": int(len(columns)), "s_genes_found": int(len(s_cols)), "g2m_genes_found": int(len(g2m_cols)),
        "wells": int(len(wells)), "vehicle_wells": int(wells.is_control.sum()),
        "conditions_by_time": {f"{t:g}h|{line}": int(n) for (t, line), n in conditions.groupby(["time", "cell_line"]).size().items()},
        "compounds_at_72h": int(conditions[conditions.time == 72.0].compound.nunique()),
        "excluded_wells": excluded, "vehicle_references": vehicle_refs,
        "frozen_24h_conditions_matched": len(diffs), "frozen_24h_conditions": int(len(old)),
        "frozen_24h_max_abs_difference": max(diffs) if diffs else None,
        "seconds": round(time.time() - started, 1),
    }
    (out / "prepare_manifest.json").write_text(json.dumps({
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "audit": audit},
        indent=1, default=str), encoding="utf-8")
    printable = {k: v for k, v in audit.items() if k not in ("vehicle_references", "identity_guard")}
    print(json.dumps(printable, indent=1, default=str)[:4000], flush=True)


if __name__ == "__main__":
    main()
