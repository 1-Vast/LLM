"""Frozen STATE zero-shot forecasts for MIX-Seq lines, from control cells only.

Input calibration variants (chosen on development lines before freeze):
* v0 raw: log1p(x/total * median MIX-Seq total); axis genes absent from MIX-Seq set to 0;
* v1 level: a single target sum chosen so that shared lines' mean log level equals Tahoe's;
  absent genes take the Tahoe pooled basal mean;
* v2 moment: v1, then per-gene affine map matching the pooled mean and SD of shared-line control
  cells to the same lines' Tahoe basal cells; clipped at 0.
Shared lines = MIX-Seq lines that are Tahoe lines (their control cells only; no outcome).
Per line: 256 control cells sampled with replacement (seed from line + pool); native predict_step
for every label and for DMSO on the identical tensor; paired delta = mean(label) - mean(DMSO).
The Tahoe phase classifier (phenotype_anchor_20261010) reads every predicted cell.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PA = ROOT / "research/astra/phenotype_anchor_20261010"
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
DATA = ROOT / "data/external/kinetic_horizon_20261010"
WEIGHTS = ROOT / "data/external/arc_state/weights/zeroshot/state_generalization_zeroshot_X_hvg"
TAHOE_EXPR = ROOT / "data/external/tahoe_phenotype_20261010/expression"
SET = 256
DRUGS = ("Trametinib", "Afatinib", "Everolimus", "Gemcitabine")
DOSES = (0.05, 0.5, 5.0)
DMSO = "[('DMSO_TF', 0.0, 'uM')]"


def label(drug: str, dose: float) -> str:
    return "[('" + drug + "', " + str(dose) + ", 'uM')]"


def sha256(path: Path) -> str:
    with open(path, "rb") as fh:
        return hashlib.file_digest(fh, "sha256").hexdigest()


def calibration(split: dict) -> dict:
    """Shared-line statistics from control cells of every pool (no treated cell)."""
    cells = {}
    present = None
    for unit in ("A_control", "C_control", "D_control"):
        z = np.load(DATA / "mixseq" / f"{unit}.npz", allow_pickle=True)
        for d in np.unique(z["depmap"]):
            if split["lines"][d]["tahoe_file"]:
                cells.setdefault(d, []).append(z["frac"][z["depmap"] == d])
        present = z["present"]
    shared = sorted(cells)
    mix = np.concatenate([np.concatenate(cells[d]) for d in shared])
    tah = np.concatenate([np.load(TAHOE_EXPR / split["lines"][d]["tahoe_file"] / "basal.npz")["x"].astype(np.float32) for d in shared])
    tah_p = tah[:, present]
    totals = np.concatenate([np.load(DATA / "mixseq" / f"{u}.npz", allow_pickle=True)["total"] for u in ("A_control", "C_control", "D_control")])
    target_raw = float(np.median(totals))
    grid = np.exp(np.linspace(np.log(1e3), np.log(1e6), 121))
    level = [abs(np.log1p(mix * t).mean() - tah_p.mean()) for t in grid]
    target = float(grid[int(np.argmin(level))])
    lm = np.log1p(mix * target)
    return {"present": present, "shared": shared, "target_raw": target_raw, "target_level": target,
            "tahoe_mean": tah.mean(0), "mu_mix": lm.mean(0), "sd_mix": lm.std(0) + 1e-6,
            "mu_tah": tah_p.mean(0), "sd_tah": tah_p.std(0) + 1e-6}


def project(frac: np.ndarray, cal: dict, variant: str) -> np.ndarray:
    present = cal["present"]
    out = np.zeros((len(frac), 2000), np.float32)
    if variant == "v0":
        out[:, present] = np.log1p(frac * cal["target_raw"])
        return out
    out[:] = cal["tahoe_mean"][None, :]
    x = np.log1p(frac * cal["target_level"])
    if variant == "v2":
        x = np.clip((x - cal["mu_mix"]) / cal["sd_mix"] * cal["sd_tah"] + cal["mu_tah"], 0, None)
    out[:, present] = x
    return out


def run(pool: str, variant: str) -> dict:
    import torch
    from state.tx.models.state_transition import StateTransitionPerturbationModel
    from virtual_cell.state_runner import _numpy_scalar_globals

    staging = json.loads((PA / "STATE_STAGING.json").read_text(encoding="utf-8"))
    for f in staging:
        if sha256(WEIGHTS / f["file"]) != f["sha256"]:
            raise SystemExit(f"STATE asset {f['file']} differs from its staging hash")
    split = json.loads((HERE / "MIXSEQ_SPLIT.json").read_text(encoding="utf-8"))
    cal = calibration(split)
    z = np.load(DATA / "mixseq" / f"{pool}_control.npz", allow_pickle=True)
    lines = sorted(np.unique(z["depmap"]))
    with torch.serialization.safe_globals(list(_numpy_scalar_globals())):
        mapping = torch.load(WEIGHTS / "pert_onehot_map.pt", map_location="cpu", weights_only=True)
    labels = [label(d, x) for d in DRUGS for x in DOSES]
    missing = [lab for lab in labels if lab not in mapping]
    if missing:
        raise SystemExit(f"LABEL_NOT_IN_CHECKPOINT: {missing}")
    clf = np.load(PA / "phase_classifier.npz")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    torch.set_float32_matmul_precision("highest")
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    t0 = time.perf_counter()
    model = StateTransitionPerturbationModel.load_from_checkpoint(str(WEIGHTS / "checkpoints/final.ckpt"), map_location="cpu").to(device).eval()
    W, b, mu, sd = (torch.tensor(clf[k], device=device) for k in ("W", "b", "mu", "sd"))
    jobs = [DMSO] + labels
    pmean = np.zeros((len(lines), len(jobs), 2000), np.float32)
    phase = np.zeros((len(lines), len(jobs), 3), np.float32)
    basal_mean = np.zeros((len(lines), 2000), np.float32)
    n_ctrl, receipts = [], {}
    with torch.inference_mode():
        for i, d in enumerate(lines):
            cells = project(z["frac"][z["depmap"] == d], cal, variant)
            n_ctrl.append(len(cells))
            seed = int(hashlib.sha256(f"mix{SET}:{pool}:{d}".encode()).hexdigest()[:8], 16)
            pick = np.random.RandomState(seed).choice(len(cells), SET, replace=True)
            x = torch.tensor(cells[pick], device=device)
            basal_mean[i] = cells.mean(0)
            receipts[d] = {"control_cells": int(len(cells)), "seed": seed, "sha256": hashlib.sha256(cells[pick].tobytes()).hexdigest()}
            for j, lab in enumerate(jobs):
                onehot = torch.zeros((SET, model.pert_dim), device=device)
                onehot[:, int(torch.argmax(mapping[lab]))] = 1
                batch = {"ctrl_cell_emb": x, "pert_emb": onehot, "pert_name": [lab] * SET}
                pred = model.predict_step(batch, batch_idx=0, padded=False)["preds"].reshape(SET, -1)
                pmean[i, j] = pred.mean(0).float().cpu().numpy()
                phase[i, j] = torch.softmax(((pred.float() - mu) / sd) @ W + b, dim=1).mean(0).cpu().numpy()
    paired = pmean[:, 1:] - pmean[:, :1]
    out = DATA / "mixseq_state" / f"{pool}_{variant}.npz"
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out, lines=np.array(lines), labels=np.array(labels), paired_delta=paired, predicted_mean=pmean,
                        phase_prob=phase, basal_mean=basal_mean, n_control=np.array(n_ctrl), phases=clf["phases"])
    rec = {"pool": pool, "variant": variant, "lines": len(lines), "forward_sets": len(lines) * len(jobs),
           "seconds": round(time.perf_counter() - t0, 1), "device": device, "target_raw": cal["target_raw"],
           "target_level": cal["target_level"], "shared_lines": cal["shared"], "npz_sha256": sha256(out),
           "treated_cells_read": False, "per_line": receipts}
    (HERE / "mixseq_state").mkdir(exist_ok=True)
    (HERE / "mixseq_state" / f"{pool}_{variant}.json").write_text(json.dumps(rec, indent=1), encoding="utf-8")
    return rec


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("pool", choices=["A", "C", "D"])
    ap.add_argument("variant", choices=["v0", "v1", "v2"])
    a = ap.parse_args()
    r = run(a.pool, a.variant)
    print(json.dumps({k: r[k] for k in ("pool", "variant", "lines", "forward_sets", "seconds", "target_raw", "target_level")}))
