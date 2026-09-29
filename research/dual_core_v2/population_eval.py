"""Population backend evaluation: does single-cell distribution add decision signal, and does the flow predict it?

File summary
- Path: research/dual_core_v2/population_eval.py
- Purpose: execute `protocol_population.json` on real SciPlex3 single cells.
- Core points:
  - `extract` reads the raw h5ad once and writes a compact file: per (compound, line) at 24 h and
    10 uM, the gene-space mean of up to 128 seeded treated cells, their coordinates in a 32-PC basis
    fitted on vehicle cells only, the cell counts at 10 uM and 10 nM, and the matched vehicle group
    (same line and plate when it has at least 128 cells, otherwise the line).
  - `part1` asks the decision question on observed cells: grouped by independent unit over the
    registered folds, does adding distribution features (sd ratios, responder fraction, energy
    distance) to the pseudobulk mean shift lower the log loss of the true mechanism class?
  - `part2` evaluates `virtual_cell.learned_response` on held-out units against population-preserving
    baselines (vehicle, mean shift, chemical nearest neighbour with and without its sd ratios) and a
    diagnostic oracle mean, in MMD, energy distance, mean and sd-ratio error.
  - Flow time and transport couplings are numerical constructs; nothing here reads them as time or
    lineage.
- Interfaces: `extract`, `part1`, `part2`; CLI `python -m research.dual_core_v2.population_eval extract|part1|part2`
- Depends on: h5py, sklearn, rdkit, torch, src/virtual_cell/learned_response.py, src/virtual_cell/artifacts.py
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/dual_core_v2_20260928/population"
SOURCE = ROOT / "data/raw/sciplex3/SrivatsanTrapnell2020_sciplex3.h5ad"
PREPARED = ROOT / "outputs/biological_depth_20260926/prepared"
LINES = ("A549", "K562", "MCF7")
DOSE, LOW_DOSE, TIME = 10000.0, 10.0, 24.0
CELLS, CONTROLS, PCS = 128, 512, 32
SEED = 20260928


def _column(group, name):
    import h5py
    x = group[name]
    if isinstance(x, h5py.Group):
        codes = x["codes"][:]
        return np.where(codes >= 0, x["categories"].asstr()[:][np.maximum(codes, 0)], None)
    return x.asstr()[:] if x.dtype.kind in "OS" else x[:]


def extract() -> dict:
    import h5py
    from sklearn.decomposition import PCA
    sys.path.insert(0, str(ROOT / "src"))
    from virtual_cell.artifacts import shift_labels
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / "cells.npz"
    if target.exists():
        raise FileExistsError(f"{target} exists (write-once)")
    started = time.time()
    rng = np.random.default_rng(SEED)
    compounds = pd.read_csv(PREPARED / "compounds.csv")
    compounds["compound"] = compounds.compound.astype(str).str.strip()
    known = set(compounds.compound)
    genes = pd.read_csv(PREPARED / "genes.csv")
    offset = json.loads((PREPARED / "prepare_manifest.json").read_text())["audit"]["feature_label_check"]["chosen_offset"]
    with h5py.File(SOURCE, "r") as f:
        obs = pd.DataFrame({k: _column(f["obs"], k) for k in ("cell_line", "perturbation", "dose_value", "time", "plate")})
        obs["perturbation"] = obs.perturbation.astype(str).str.strip()
        labels = np.array([s or "" for s in shift_labels(_column(f["var"], "ensembl_id"), offset, f["X"].attrs["shape"][1])])
        unique = ~pd.Series(labels).duplicated(keep=False).to_numpy()
        human = np.char.startswith(labels, "ENSG") & unique
        index = {g: i for i, g in enumerate(labels) if human[i]}
        columns = np.array([index[g] for g in genes.ensembl])
        positions = np.full(len(labels), -1)
        positions[columns] = np.arange(len(columns))
        X = f["X"]
        indptr = X["indptr"][:]

        def rows_expression(rows):
            out = np.zeros((len(rows), len(columns)), dtype=np.float32)
            for j, row in enumerate(rows):
                a, b = int(indptr[row]), int(indptr[row + 1])
                idx, counts = X["indices"][a:b], X["data"][a:b].astype(np.float64)
                library = counts[human[idx]].sum()
                keep = positions[idx] >= 0
                out[j, positions[idx[keep]]] = np.log1p(counts[keep] * 1e4 / max(library, 1.0))
            return out

        day = obs[(obs.time == TIME) & obs.cell_line.isin(LINES)]
        vehicle = day[(day.perturbation == "control") & (day.dose_value == 0)]
        groups = {}
        for (line, plate), rows in vehicle.groupby(["cell_line", "plate"]):
            if len(rows) >= CELLS:
                groups[(line, str(plate))] = np.sort(rng.choice(rows.index.to_numpy(), min(CONTROLS, len(rows)), replace=False))
        for line, rows in vehicle.groupby("cell_line"):
            groups[(line, "ALL")] = np.sort(rng.choice(rows.index.to_numpy(), min(CONTROLS, len(rows)), replace=False))
        control_expr = {k: rows_expression(v) for k, v in groups.items()}
        print(f"vehicle groups {len(groups)} read in {time.time() - started:.0f}s", flush=True)
        basis_cells = np.vstack([control_expr[(line, "ALL")] for line in LINES])
        pca = PCA(n_components=PCS, svd_solver="full", random_state=0).fit(basis_cells)
        records, cell_blocks, gene_means = [], [], []
        treated = day[(day.dose_value == DOSE) & day.perturbation.isin(known)]
        low = day[(day.dose_value == LOW_DOSE) & day.perturbation.isin(known)].groupby(["perturbation", "cell_line"]).size()
        for (drug, line), rows in treated.groupby(["perturbation", "cell_line"]):
            plate = str(rows.plate.mode().iloc[0])
            ckey = (line, plate) if (line, plate) in groups else (line, "ALL")
            pick = np.sort(rng.choice(rows.index.to_numpy(), min(CELLS, len(rows)), replace=False))
            expr = rows_expression(pick)
            gene_means.append(expr.mean(0))
            cell_blocks.append(pca.transform(expr).astype(np.float32))
            records.append({"compound": drug, "line": line, "plate": plate, "control": "|".join(ckey),
                            "cells_total": int(len(rows)), "cells_sampled": int(len(pick)),
                            "cells_low_dose": int(low.get((drug, line), 0))})
        ckeys = sorted(groups)
        np.savez_compressed(
            target, records=json.dumps(records), control_keys=json.dumps(["|".join(k) for k in ckeys]),
            gene_means=np.stack(gene_means).astype(np.float32),
            cell_offsets=np.cumsum([0] + [len(b) for b in cell_blocks]), cells=np.vstack(cell_blocks),
            control_gene_means=np.stack([control_expr[k].mean(0) for k in ckeys]).astype(np.float32),
            control_offsets=np.cumsum([0] + [len(control_expr[k]) for k in ckeys]),
            control_cells=np.vstack([pca.transform(control_expr[k]).astype(np.float32) for k in ckeys]),
            pca_mean=pca.mean_, pca_components=pca.components_, genes=genes.ensembl.to_numpy(dtype=str))
    summary = {"conditions": len(records), "vehicle_groups": len(ckeys), "seconds": time.time() - started,
               "explained_variance": float(pca.explained_variance_ratio_.sum())}
    (OUT / "extract_summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    return summary


# ------------------------------------------------------------------------------------ shared loading
def load_cells() -> dict:
    z = np.load(OUT / "cells.npz", allow_pickle=False)
    rec = pd.DataFrame(json.loads(str(z["records"])))
    ckeys = json.loads(str(z["control_keys"]))
    cells = [z["cells"][a:b] for a, b in zip(z["cell_offsets"][:-1], z["cell_offsets"][1:])]
    ctrl = {k: z["control_cells"][a:b] for k, a, b in zip(ckeys, z["control_offsets"][:-1], z["control_offsets"][1:])}
    cgm = {k: z["control_gene_means"][i] for i, k in enumerate(ckeys)}
    return {"records": rec, "cells": cells, "controls": ctrl, "control_gene_means": cgm,
            "gene_means": z["gene_means"], "pca_mean": z["pca_mean"], "pca_components": z["pca_components"],
            "genes": z["genes"]}


def _compound_table():
    sys.path[:0] = [str(ROOT), str(ROOT / "src")]
    from research.belief_planning import tasks as T
    from research.protocol_v2 import tasks_v21 as TV
    data = TV.C.load()
    comp = data.compounds.drop_duplicates("compound").set_index("compound")
    units = T.units("sciplex3")[T.UNIT["sciplex3"]].astype(str)
    return pd.DataFrame({"klass": comp.klass, "fold": comp.fold, "unit": units.reindex(comp.index),
                         "smiles": comp.get("smiles")})


def energy_distance(x, y) -> float:
    from scipy.spatial.distance import cdist
    return float(2 * cdist(x, y).mean() - cdist(x, x).mean() - cdist(y, y).mean())


def distribution_features(treated, control) -> np.ndarray:
    """log sd ratios on each PC, responder fraction along the mean-shift direction, energy distance."""
    sd = np.log(np.maximum(treated.std(0), 1e-6) / np.maximum(control.std(0), 1e-6))
    direction = treated.mean(0) - control.mean(0)
    n = np.linalg.norm(direction)
    if n > 1e-9:
        u = direction / n
        cut = np.quantile((control - control.mean(0)) @ u, 0.95)
        responder = float((((treated - control.mean(0)) @ u) > cut).mean())
    else:
        responder = 0.0
    return np.r_[sd, responder, energy_distance(treated, control)]


# ------------------------------------------------------------------------------------ part 1
def part1() -> dict:
    from sklearn.decomposition import PCA
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import balanced_accuracy_score, roc_auc_score
    from sklearn.preprocessing import StandardScaler
    d = load_cells()
    rec = d["records"]
    comp = _compound_table()
    feats = {"A": {}, "dist": {}, "abund": {}}
    for i, r in rec.iterrows():
        ctrl_cells = d["controls"][r.control]
        feats["A"][(r.compound, r.line)] = d["gene_means"][i] - d["control_gene_means"][r.control]
        feats["dist"][(r.compound, r.line)] = distribution_features(d["cells"][i], ctrl_cells)
        feats["abund"][(r.compound, r.line)] = np.array([np.log((r.cells_total + 1) / (r.cells_low_dose + 1))])
    names = sorted({c for c, _ in feats["A"]} & set(comp.index[comp.klass.notna()]))
    names = [c for c in names if all((c, line) in feats["A"] for line in LINES)]
    table = comp.loc[names]
    support = table.groupby("klass").unit.nunique()
    keep = support[support >= 3].index
    table = table[table.klass.isin(keep)]
    names = list(table.index)

    def block(kind):
        return np.stack([np.concatenate([feats[kind][(c, line)] for line in LINES]) for c in names])

    A, Dist, Ab = block("A"), block("dist"), block("abund")
    rng = np.random.default_rng(SEED)
    Dshuf = Dist.copy()
    width = Dist.shape[1] // len(LINES)
    for j in range(len(LINES)):
        Dshuf[:, j * width:(j + 1) * width] = Dist[rng.permutation(len(names)), j * width:(j + 1) * width]
    sets = {"A_pseudobulk": [A], "B_pseudobulk_plus_distribution": [A, Dist], "C_distribution_only": [Dist],
            "D_pseudobulk_plus_abundance": [A, Ab], "B_shuffled": [A, Dshuf]}
    classes = sorted(table.klass.unique())
    y = table.klass.map({k: i for i, k in enumerate(classes)}).to_numpy()
    folds = table.fold.astype(int).to_numpy()
    out = {"compounds": len(names), "units": int(table.unit.nunique()), "classes": len(classes),
           "units_per_class": support[keep].to_dict(), "sets": {}}
    probs = {}
    for name, blocks in sets.items():
        P = np.zeros((len(names), len(classes)))
        for f in range(5):
            tr, te = folds != f, folds == f
            if not te.any():
                continue
            parts_tr, parts_te = [], []
            for b in blocks:
                sc = StandardScaler().fit(b[tr])
                parts_tr.append(sc.transform(b[tr]))
                parts_te.append(sc.transform(b[te]))
            Xtr, Xte = np.hstack(parts_tr), np.hstack(parts_te)
            k = min(64, Xtr.shape[1], tr.sum() - 1)
            pca = PCA(n_components=k, random_state=0).fit(Xtr)
            model = LogisticRegression(C=1.0, class_weight="balanced", max_iter=5000)
            model.fit(pca.transform(Xtr), y[tr])
            p = np.full((te.sum(), len(classes)), 1e-9)
            p[:, model.classes_] = model.predict_proba(pca.transform(Xte))
            P[te] = p / p.sum(1, keepdims=True)
        probs[name] = P
        pred = P.argmax(1)
        try:
            auc = roc_auc_score(y, P, multi_class="ovr", average="macro")
        except ValueError:
            auc = float("nan")
        out["sets"][name] = {"log_loss": float(-np.log(np.maximum(P[np.arange(len(y)), y], 1e-12)).mean()),
                             "balanced_accuracy": float(balanced_accuracy_score(y, pred)), "macro_auroc": float(auc)}
    units = table.unit.to_numpy()
    ll = {k: -np.log(np.maximum(v[np.arange(len(y)), y], 1e-12)) for k, v in probs.items()}
    uniq = np.unique(units)
    idx = np.random.default_rng(SEED).integers(len(uniq), size=(10_000, len(uniq)))
    out["contrasts"] = {}
    for a in ("B_pseudobulk_plus_distribution", "C_distribution_only", "D_pseudobulk_plus_abundance", "B_shuffled"):
        diff = pd.Series(ll[a] - ll["A_pseudobulk"]).groupby(units).mean().reindex(uniq).to_numpy()
        out["contrasts"][f"{a} - A_pseudobulk"] = {"log_loss_difference_unit_mean": float(diff.mean()),
                                                  "ci": np.quantile(diff[idx].mean(1), [0.025, 0.975]).tolist()}
    b = out["contrasts"]["B_pseudobulk_plus_distribution - A_pseudobulk"]
    out["verdict"] = "population_signal" if b["ci"][1] < 0 else "no_population_signal_beyond_pseudobulk"
    (OUT / "part1.json").write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")
    return out


# ------------------------------------------------------------------------------------ part 2
def part2() -> dict:
    import torch
    from rdkit import Chem, RDLogger
    from rdkit.Chem import rdFingerprintGenerator
    sys.path.insert(0, str(ROOT / "src"))
    from scipy.spatial.distance import pdist
    from virtual_cell.learned_response import PopulationPair, fit_population_flow, population_mmd
    RDLogger.DisableLog("rdApp.*")
    torch.set_num_threads(2)
    d = load_cells()
    rec = d["records"]
    comp = _compound_table()
    rec = rec[rec.compound.isin(comp.index)].copy()
    rec["unit"] = rec.compound.map(comp.unit)
    rec["fold"] = rec.compound.map(comp.fold).astype(int)
    gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=128)
    fps = {}
    for c in rec.compound.unique():
        s = comp.smiles.get(c)
        mol = Chem.MolFromSmiles(s) if isinstance(s, str) and s else None
        fps[c] = gen.GetFingerprintAsNumPy(mol).astype(np.float32) if mol is not None else np.zeros(128, np.float32)
    rng = np.random.default_rng(SEED)

    def pair_of(i):
        r = rec.loc[i]
        ctrl = d["controls"][r.control]
        treated = d["cells"][i]
        cpick = ctrl[rng.choice(len(ctrl), 64, replace=False)]
        tpick = treated[rng.choice(len(treated), min(64, len(treated)), replace=False)]
        cond = np.r_[fps[r.compound], [float(r.line == line) for line in LINES]].astype(np.float32)
        return PopulationPair(cpick, tpick, cond, 1.0, str(r.unit))

    pairs = {i: pair_of(i) for i in rec.index}
    vehicle_all = np.vstack([d["controls"][f"{line}|ALL"] for line in LINES])
    dist = pdist(vehicle_all[rng.choice(len(vehicle_all), 1000, replace=False)])
    bandwidth = float(np.median(dist[dist > 0]))
    rows, histories = [], {}
    for f in range(5):
        v = (f + 1) % 5
        train_i = [i for i in rec.index if rec.fold[i] not in (f, v)]
        val_i = [i for i in rec.index if rec.fold[i] == v]
        test_i = [i for i in rec.index if rec.fold[i] == f]
        started = time.time()
        model, history = fit_population_flow([pairs[i] for i in train_i], [pairs[i] for i in val_i], bandwidth=bandwidth,
                                             seed=SEED % 1000)
        histories[f] = {"epochs": len(history), "selected_epoch": min(history, key=lambda h: h["validation_mmd"])["epoch"],
                        "seconds": time.time() - started}
        fit_i = [i for i in rec.index if rec.fold[i] != f]
        shift = {i: pairs[i].treated.mean(0) - pairs[i].control.mean(0) for i in fit_i}
        sdr = {i: np.maximum(pairs[i].treated.std(0), 1e-6) / np.maximum(pairs[i].control.std(0), 1e-6) for i in fit_i}
        for i in test_i:
            p, r = pairs[i], rec.loc[i]
            same_line = [j for j in fit_i if rec.line[j] == r.line]
            mean_shift = np.mean([shift[j] for j in same_line], axis=0)
            fq = fps[r.compound]
            sims = np.array([np.minimum(fq, fps[rec.compound[j]]).sum() / max(np.maximum(fq, fps[rec.compound[j]]).sum(), 1.0)
                             for j in same_line])
            nn = [same_line[k] for k in np.flatnonzero(np.isclose(sims, sims.max()))]
            nn_shift = np.mean([shift[j] for j in nn], axis=0)
            nn_sd = np.exp(np.mean([np.log(sdr[j]) for j in nn], axis=0))
            c0 = p.control
            preds = {"vehicle": c0, "mean_shift": c0 + mean_shift, "chemical_nn": c0 + nn_shift,
                     "shift_scale_nn": (c0 - c0.mean(0)) * nn_sd + c0.mean(0) + nn_shift,
                     "population_flow": model.predict_population(c0, p.condition, 1.0),
                     "oracle_mean": c0 + (p.treated.mean(0) - c0.mean(0))}
            obs_sd = np.log(np.maximum(p.treated.std(0), 1e-6) / np.maximum(c0.std(0), 1e-6))
            for name, yhat in preds.items():
                sd_hat = np.log(np.maximum(yhat.std(0), 1e-6) / np.maximum(c0.std(0), 1e-6))
                rows.append({"fold": f, "compound": r.compound, "line": r.line, "unit": r.unit, "model": name,
                             "mmd": population_mmd(yhat, p.treated, bandwidth),
                             "energy": energy_distance(yhat, p.treated),
                             "mean_se": float(np.square(yhat.mean(0) - p.treated.mean(0)).mean()),
                             "sd_ratio_se": float(np.square(sd_hat - obs_sd).mean())})
        print(f"fold {f}: train {len(train_i)} val {len(val_i)} test {len(test_i)} {histories[f]}", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "part2_pairs.csv", index=False)
    out = {"bandwidth": bandwidth, "pairs": int(len(df) // df.model.nunique()), "units": int(df.unit.nunique()),
           "histories": histories, "unit_means": {}, "contrasts": {}}
    for metric in ("mmd", "energy", "mean_se", "sd_ratio_se"):
        u = df.pivot_table(index=["unit"], columns="model", values=metric, aggfunc="mean")
        out["unit_means"][metric] = u.mean().to_dict()
        idx = np.random.default_rng(SEED).integers(len(u), size=(10_000, len(u)))
        for base in ("vehicle", "mean_shift", "chemical_nn", "shift_scale_nn"):
            diff = (u["population_flow"] - u[base]).to_numpy()
            out["contrasts"][f"{metric}|flow-{base}"] = {"difference": float(diff.mean()),
                                                         "ci": np.quantile(diff[idx].mean(1), [0.025, 0.975]).tolist()}
    wins = [out["contrasts"][f"mmd|flow-{b}"]["ci"][1] < 0 for b in ("vehicle", "mean_shift", "chemical_nn", "shift_scale_nn")]
    out["verdict"] = "flow_better_than_every_baseline" if all(wins) else "flow_not_better_than_every_baseline"
    (OUT / "part2.json").write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("extract", "part1", "part2"))
    args = parser.parse_args()
    print(json.dumps({"extract": extract, "part1": part1, "part2": part2}[args.command](), indent=1, default=float)[:5000])


if __name__ == "__main__":
    main()
