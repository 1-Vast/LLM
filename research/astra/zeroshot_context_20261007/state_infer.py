"""Stage 3: frozen STATE zero-shot forecasts on real same-plate control cells.

For every context and plate, 256 full-QC DMSO cells from the hash-assigned 'basal'
half are sampled once (seeded by file and plate) and reused for every condition on
that plate and for the paired DMSO forward. The forecast for a (drug-dose, plate)
group is the mean predicted cell minus the mean predicted DMSO cell on the
identical basal tensor. Labels absent from the checkpoint's one-hot map are refused,
never mapped by the CLI's control fallback. No treated row is read by this stage.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import sys
import threading
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT), str(HERE)]
from remote import CACHE  # noqa: E402

CONTROL = "[('DMSO_TF', 0.0, 'uM')]"
SET = 256


def digest(path) -> str:
    with open(path, "rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def basal_sets(file: str) -> tuple[dict, dict, list]:
    plan = json.loads((CACHE / "extract" / "plans" / f"{file}.plan.json").read_text(encoding="utf-8"))
    rows = np.load(CACHE / "extract" / file / "rows.npy", mmap_mode="r")
    slots = np.load(CACHE / "extract" / file / "slots.npz")
    start = dict(zip(slots["group"].tolist(), slots["start"].tolist()))
    sets, receipts = {}, {}
    for g in plan["groups"]:
        if not g["control"]:
            continue
        local = [i for i, (role, full) in enumerate(zip(g["control_role"], g["full"])) if role == "basal" and full]
        seed = int(hashlib.sha256(f"basal{SET}:{file}:{g['plate']}".encode()).hexdigest()[:8], 16)
        rng = np.random.RandomState(seed)
        pick = rng.choice(len(local), SET, replace=len(local) < SET)
        index = [start[g["group"]] + local[i] for i in pick]
        sets[g["plate"]] = np.asarray(rows[index], dtype=np.float32)
        receipts[g["plate"]] = {"available_basal_full": len(local), "with_replacement": bool(len(local) < SET),
                                "source_rows": [int(g["rows"][local[i]]) for i in pick], "seed": seed,
                                "sha256": hashlib.sha256(sets[g["plate"]].tobytes()).hexdigest()}
    return sets, receipts, plan["groups"]


def run(files: list[str], out: Path, batch_sets: int = 16):
    import psutil
    import torch
    from tools.datasets.state_prospective_input import load_contract
    from state.tx.models.state_transition import StateTransitionPerturbationModel
    out.mkdir(parents=True, exist_ok=True)
    contract = load_contract(ROOT)
    mapping = contract["mapping"]
    process = psutil.Process()
    resource = {"peak_rss_bytes": process.memory_info().rss, "api_calls": 0, "downloaded_bytes": 0}
    stop = threading.Event()

    def monitor():
        while not stop.wait(0.2):
            resource["peak_rss_bytes"] = max(resource["peak_rss_bytes"], process.memory_info().rss)
    threading.Thread(target=monitor, daemon=True).start()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    torch.set_num_threads(4)
    # Full float32: TF32 kernels changed per-cell outputs by up to 0.07 between batch shapes.
    torch.set_float32_matmul_precision("highest")
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    if device == "cuda":
        torch.cuda.reset_peak_memory_stats()
    t0 = time.perf_counter()
    model = StateTransitionPerturbationModel.load_from_checkpoint(contract["hashes"]["weights"]["path"], map_location="cpu").to(device).eval()
    resource["load_seconds"] = time.perf_counter() - t0
    runtime = {"parameter_count": sum(p.numel() for p in model.parameters()), "cell_set_len": model.cell_sentence_len,
               "pert_dim": model.pert_dim, "input_dim": model.input_dim, "relu": str(model.relu),
               "arc_state": importlib.metadata.version("arc-state"), "torch": torch.__version__, "device": device,
               "gpu": torch.cuda.get_device_name() if device == "cuda" else None,
               "checkpoint": contract["hashes"]["weights"], "pert_map": contract["hashes"]["map"], "config": contract["hashes"]["config"]}
    (out / "runtime.json").write_text(json.dumps(runtime, indent=1), encoding="utf-8")
    for file in files:
        checked = False  # the batched/native agreement check runs on every context's first batch
        target = CACHE / "state_forecasts" / f"{file}.npz"
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            continue
        started = time.perf_counter()
        sets, receipts, groups = basal_sets(file)
        jobs, refused = [], []
        for g in groups:
            if g["control"]:
                continue
            if g["label"] not in mapping:
                refused.append({"group": g["group"], "label": g["label"], "reason": "label_not_in_checkpoint_onehot_map"})
                continue
            if g["plate"] not in sets:
                refused.append({"group": g["group"], "label": g["label"], "reason": "no_same_plate_basal_controls"})
                continue
            jobs.append((g["group"], g["label"], g["plate"]))
        plates = sorted(sets)
        jobs = [(-1 - i, CONTROL, p) for i, p in enumerate(plates)] + jobs
        means = np.zeros((len(jobs), 2000), dtype=np.float32)
        zero_fraction = np.zeros(len(jobs), dtype=np.float32)
        with torch.inference_mode():
            for b in range(0, len(jobs), batch_sets):
                chunk = jobs[b:b + batch_sets]
                basal = torch.tensor(np.concatenate([sets[p] for _, _, p in chunk]), device=device)
                onehot = torch.zeros((len(chunk) * SET, model.pert_dim), device=device)
                for i, (_, label, _) in enumerate(chunk):
                    onehot[i * SET:(i + 1) * SET, mapping[label]] = 1
                batch = {"ctrl_cell_emb": basal, "pert_emb": onehot, "pert_name": [x[1] for x in chunk for _ in range(SET)]}
                if batch_sets == 1:
                    # Native path: exactly the official predict_step on one 256-cell set.
                    pred = model.predict_step(batch, batch_idx=0, padded=False)["preds"].reshape(1, SET, -1)
                    if not checked:
                        again = model.predict_step(batch, batch_idx=0, padded=False)["preds"].reshape(1, SET, -1)
                        same = bool(torch.equal(again, pred))
                        (out / f"repeat_check_{file}.json").write_text(json.dumps({"native_predict_step_exact_repeat_equal": same,
                            "file": file, "matmul_precision": torch.get_float32_matmul_precision()}, indent=1), encoding="utf-8")
                        if not same:
                            raise RuntimeError("native predict_step is not repeatable on identical input")
                        checked = True
                if not checked:
                    single = {"ctrl_cell_emb": basal[:SET], "pert_emb": onehot[:SET], "pert_name": batch["pert_name"][:SET]}
                    reference = model.predict_step(single, batch_idx=0, padded=False)["preds"].reshape(SET, -1)
                    element = float((reference - pred[0]).abs().max())
                    difference = float((reference.mean(0) - pred[0].mean(0)).abs().max())
                    (out / f"batching_check_{file}.json").write_text(json.dumps({"max_abs_cell_mean_batched_vs_predict_step_single": difference,
                        "max_abs_element_batched_vs_predict_step_single": element, "tolerance_on_cell_mean": 1e-4,
                        "passed": difference < 1e-4, "file": file, "matmul_precision": torch.get_float32_matmul_precision(),
                        "cudnn_tf32": torch.backends.cudnn.allow_tf32}, indent=1), encoding="utf-8")
                    if difference >= 1e-4:
                        raise RuntimeError("batched forward differs from native predict_step on the cell mean")
                    checked = True
                means[b:b + len(chunk)] = pred.mean(1).float().cpu().numpy()
                zero_fraction[b:b + len(chunk)] = (pred == 0).float().mean((1, 2)).cpu().numpy()
        dmso = {p: means[i] for i, p in enumerate(plates)}
        body = slice(len(plates), len(jobs))
        group_ids = np.array([j[0] for j in jobs[body]], dtype=np.int64)
        plate_of = [j[2] for j in jobs[body]]
        paired = means[body] - np.stack([dmso[p] for p in plate_of]) if len(plate_of) else np.zeros((0, 2000), np.float32)
        np.savez(target, group=group_ids, label=np.array([j[1] for j in jobs[body]]), plate=np.array(plate_of),
                 predicted_mean=means[body], paired_delta=paired.astype(np.float32), zero_fraction=zero_fraction[body],
                 dmso_plates=np.array(plates), dmso_predicted_mean=np.stack([dmso[p] for p in plates]),
                 basal_mean_by_plate=np.stack([sets[p].mean(0) for p in plates]))
        (out / f"{file}.receipt.json").write_text(json.dumps({"file": file, "forwards_sets": len(jobs), "refused": refused,
            "basal": receipts, "seconds": round(time.perf_counter() - started, 3), "npz": str(target.relative_to(CACHE)), "sha256": digest(target),
            "treated_rows_read": False}, indent=1), encoding="utf-8")
        print(json.dumps({"file": file, "sets": len(jobs), "refused": len(refused), "seconds": round(time.perf_counter() - started, 2)}), flush=True)
    stop.set()
    resource.update(elapsed_seconds=time.perf_counter() - t0,
                    peak_cuda_allocated_bytes=torch.cuda.max_memory_allocated() if device == "cuda" else 0)
    (out / f"resources_{int(time.time())}.json").write_text(json.dumps(resource, indent=1), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--files", nargs="+", required=True)
    parser.add_argument("--out", type=Path, default=HERE / "state_forecasts")
    parser.add_argument("--batch-sets", type=int, default=1, help="1 = native predict_step per set (canonical); >1 = batched forward with a cell-mean agreement check")
    args = parser.parse_args()
    run(args.files, args.out, args.batch_sets)
