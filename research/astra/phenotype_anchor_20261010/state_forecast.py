"""Stage 4: frozen STATE zero-shot forecasts for held-out lines, plus predicted-cell phase readout.

Replicates the 2026-10-07 native path: per plate, 256 full-QC DMSO cells (seeded by file and plate)
form one basal tensor; every label on that plate and DMSO are forwarded on the identical tensor
with the official ``predict_step``; the forecast is mean(predicted | label) - mean(predicted | DMSO).
Labels absent from the checkpoint one-hot map are refused by name. The phase classifier (fitted on
reference DMSO cells, ``phase_classifier.py``) reads every predicted cell.

``--basal-from`` swaps in another held-out line's basal tensors (context-permutation control);
the label set and plates stay those of the target line.
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
sys.path[:0] = [str(ROOT / "src"), str(ROOT), str(HERE)]
import analysis as A  # noqa: E402

SET = 256
WEIGHTS = ROOT / "data/external/arc_state/weights/zeroshot/state_generalization_zeroshot_X_hvg"
STAGING = json.loads((HERE / "STATE_STAGING.json").read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    with open(path, "rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def basal_tensors(name: str) -> tuple[dict, dict]:
    """256 full-QC DMSO cells per plate, from the extraction plan's recorded rows."""
    plan = json.loads((HERE / "expression" / "plans" / f"{name}.json").read_text(encoding="utf-8"))
    obs = json.loads((HERE / "obs" / f"{name}.json").read_text(encoding="utf-8"))
    pass_filter = np.load(A.CACHE / "obs" / f"{name}.npz")["pass_filter"]
    full_code = obs["categories"]["pass_filter"].index("full")
    basal = np.load(A.CACHE / "expression" / name / "basal.npz")
    rows = np.concatenate([np.asarray(g["rows"]) for g in plan["groups"] if g["basal"]])
    if len(rows) != len(basal["x"]):
        raise ValueError(f"{name}: basal rows and plan disagree")
    sets, receipts = {}, {}
    for plate in sorted(set(basal["plate"].tolist())):
        local = np.flatnonzero((basal["plate"] == plate) & (pass_filter[rows] == full_code))
        if len(local) == 0:
            continue
        seed = int(hashlib.sha256(f"basal{SET}:{name}:{plate}".encode()).hexdigest()[:8], 16)
        pick = np.random.RandomState(seed).choice(len(local), SET, replace=len(local) < SET)
        sets[plate] = np.asarray(basal["x"][local[pick]], dtype=np.float32)
        receipts[plate] = {"available_full": int(len(local)), "with_replacement": bool(len(local) < SET), "seed": seed,
                           "source_rows_sha256": hashlib.sha256(rows[local[pick]].astype(np.int64).tobytes()).hexdigest(),
                           "sha256": hashlib.sha256(sets[plate].tobytes()).hexdigest()}
    return sets, receipts


def label_plates(name: str) -> list[tuple[str, str]]:
    t = np.load(A.CACHE / "expression" / name / "treated.npz")
    return sorted(set(zip(t["label"].tolist(), t["plate"].tolist())))


def run(target: str, basal_from: str | None, out: Path):
    import torch
    from state.tx.models.state_transition import StateTransitionPerturbationModel
    from virtual_cell.state_runner import _numpy_scalar_globals

    for f in STAGING:
        if sha256(WEIGHTS / f["file"]) != f["sha256"]:
            raise SystemExit(f"STATE asset {f['file']} differs from its staging hash")
    with torch.serialization.safe_globals(list(_numpy_scalar_globals())):
        mapping = torch.load(WEIGHTS / "pert_onehot_map.pt", map_location="cpu", weights_only=True)
    clf = np.load(HERE / "phase_classifier.npz")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    torch.set_float32_matmul_precision("highest")
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    started = time.perf_counter()
    model = StateTransitionPerturbationModel.load_from_checkpoint(str(WEIGHTS / "checkpoints/final.ckpt"), map_location="cpu").to(device).eval()
    W = torch.tensor(clf["W"], device=device)
    b = torch.tensor(clf["b"], device=device)
    mu = torch.tensor(clf["mu"], device=device)
    sd = torch.tensor(clf["sd"], device=device)
    phases = [str(p) for p in clf["phases"]]
    sets, receipts = basal_tensors(basal_from or target)
    jobs, refused = [], []
    for label, plate in label_plates(target):
        if label not in mapping:
            refused.append({"label": label, "plate": plate, "reason": "LABEL_NOT_IN_CHECKPOINT"})
        elif plate not in sets:
            refused.append({"label": label, "plate": plate, "reason": "NO_SAME_PLATE_BASAL"})
        else:
            jobs.append((label, plate))
    plates = sorted({p for _, p in jobs})
    jobs = [(A.P.DMSO, p) for p in plates] + jobs
    means = np.zeros((len(jobs), 2000), np.float32)
    phase_prob = np.zeros((len(jobs), len(phases)), np.float32)
    repeat_equal = None
    with torch.inference_mode():
        for i, (label, plate) in enumerate(jobs):
            basal = torch.tensor(sets[plate], device=device)
            onehot = torch.zeros((SET, model.pert_dim), device=device)
            onehot[:, int(torch.argmax(mapping[label]))] = 1
            batch = {"ctrl_cell_emb": basal, "pert_emb": onehot, "pert_name": [label] * SET}
            pred = model.predict_step(batch, batch_idx=0, padded=False)["preds"].reshape(SET, -1)
            if repeat_equal is None:
                again = model.predict_step(batch, batch_idx=0, padded=False)["preds"].reshape(SET, -1)
                repeat_equal = bool(torch.equal(again, pred))
                if not repeat_equal:
                    raise RuntimeError("native predict_step is not repeatable on identical input")
            means[i] = pred.mean(0).float().cpu().numpy()
            logits = ((pred.float() - mu) / sd) @ W + b
            phase_prob[i] = torch.softmax(logits, dim=1).mean(0).cpu().numpy()
    dmso = {p: i for i, (lab, p) in enumerate(jobs) if lab == A.P.DMSO}
    body = [i for i, (lab, _) in enumerate(jobs) if lab != A.P.DMSO]
    paired = np.stack([means[i] - means[dmso[jobs[i][1]]] for i in body])
    dmso_phase = np.stack([phase_prob[dmso[jobs[i][1]]] for i in body])
    tag = target if basal_from is None else f"{target}__basal_{basal_from}"
    out.mkdir(parents=True, exist_ok=True)
    npz = A.CACHE / "state_forecasts" / f"{tag}.npz"
    npz.parent.mkdir(parents=True, exist_ok=True)
    np.savez(npz, label=np.array([jobs[i][0] for i in body]), plate=np.array([jobs[i][1] for i in body]),
             paired_delta=paired, predicted_mean=means[body], phase_prob=phase_prob[body], dmso_phase_prob=dmso_phase,
             phases=np.array(phases))
    receipt = {"target": target, "basal_from": basal_from or target, "forward_sets": len(jobs), "refused": refused,
               "basal": receipts, "native_predict_step_repeat_equal": repeat_equal, "device": device,
               "gpu": torch.cuda.get_device_name() if device == "cuda" else None,
               "seconds": round(time.perf_counter() - started, 1), "npz": str(npz.relative_to(ROOT)), "sha256": sha256(npz),
               "treated_rows_read": False, "checkpoint_sha256": STAGING[0]["sha256"]}
    (out / f"{tag}.json").write_text(json.dumps(receipt, indent=1), encoding="utf-8")
    print(json.dumps({k: receipt[k] for k in ("target", "basal_from", "forward_sets", "seconds")}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True)
    parser.add_argument("--basal-from", default=None)
    parser.add_argument("--out", type=Path, default=HERE / "state_forecasts")
    args = parser.parse_args()
    if not (HERE / "FREEZE.json").exists():
        raise SystemExit("STATE held-out forecasts run only after FREEZE.json exists")
    run(args.target, args.basal_from, args.out)
