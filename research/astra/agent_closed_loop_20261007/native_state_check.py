"""Reproduce native STATE forecasts for the frozen development cases, without treated inputs."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRIOR = HERE.parent / "zeroshot_context_20261007"
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(PRIOR)]


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    destination = HERE / "native_state_check.json"
    arrays_path = HERE / "native_state_check.npz"
    if destination.exists() or arrays_path.exists():
        raise FileExistsError("Native reproduction outputs already exist")
    protocol = json.loads((HERE / "PROTOCOL.json").read_text())
    freeze = json.loads((HERE / "PROTOCOL_FREEZE.json").read_text())
    assert digest(HERE / "PROTOCOL.json") == freeze["protocol_sha256"]
    import torch
    from state.tx.models.state_transition import StateTransitionPerturbationModel
    from tools.datasets.state_prospective_input import load_contract
    from state_infer import basal_sets, CACHE, CONTROL, SET

    started = time.perf_counter()
    contract = load_contract(ROOT)
    assert contract["hashes"]["weights"]["sha256"] == protocol["checkpoint"]["sha256"]
    assert digest(protocol["checkpoint"]["path"]) == protocol["checkpoint"]["sha256"]
    torch.set_num_threads(4)
    torch.set_float32_matmul_precision("highest")
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda":
        torch.cuda.reset_peak_memory_stats()
    model = StateTransitionPerturbationModel.load_from_checkpoint(
        protocol["checkpoint"]["path"], map_location="cpu").to(device).eval()
    context_data, controls, rows, values = {}, {}, [], []

    def forward(basal, label):
        onehot = torch.zeros((SET, model.pert_dim), device=device)
        onehot[:, contract["mapping"][label]] = 1
        batch = {"ctrl_cell_emb": torch.tensor(basal, device=device), "pert_emb": onehot,
                 "pert_name": [label] * SET}
        return model.predict_step(batch, batch_idx=0, padded=False)["preds"].mean(0).cpu().numpy()

    with torch.inference_mode():
        for case in protocol["cases"]:
            file = case["file"]
            if file not in context_data:
                sets, input_receipts, _ = basal_sets(file)
                forecast_path = CACHE / "state_forecasts" / f"{file}.npz"
                forecast_receipt = json.loads((PRIOR / "state_forecasts" / f"{file}.receipt.json").read_text())
                assert digest(forecast_path) == forecast_receipt["sha256"]
                context_data[file] = (sets, input_receipts, np.load(forecast_path))
            sets, inputs, cached = context_data[file]
            for plate in (case["first_plate"], case["independent_plate"]):
                key = (file, plate)
                if key not in controls:
                    controls[key] = forward(sets[plate], CONTROL)
                prediction = forward(sets[plate], case["label"]) - controls[key]
                index = np.flatnonzero((cached["label"] == case["label"]) & (cached["plate"] == plate))
                assert len(index) == 1
                error = float(np.max(np.abs(prediction - cached["paired_delta"][index[0]])))
                if error > 1e-5:
                    raise AssertionError(f"Native forecast disagreement: {file}/{plate}/{error}")
                rows.append({"context": case["context"], "label": case["label"], "plate": plate,
                             "basal_input_sha256": inputs[plate]["sha256"], "basal_cells": SET,
                             "max_abs_difference_from_cached": error})
                values.append(prediction)
    np.savez(arrays_path, paired_delta=np.stack(values))
    receipt = {"status": "PASS", "checkpoint": protocol["checkpoint"], "cases": rows,
               "native_drug_forwards": len(rows), "native_control_forwards": len(controls),
               "treated_rows_used_as_inputs": False, "device": device,
               "peak_cuda_bytes": torch.cuda.max_memory_allocated() if device == "cuda" else 0,
               "elapsed_seconds": time.perf_counter() - started,
               "arrays_sha256": digest(arrays_path),
               "claim": "Real checkpoint reproduction on previously exposed development contexts; not independent biological validation"}
    with destination.open("x", encoding="utf-8") as stream:
        json.dump(receipt, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"status": receipt["status"], "drug_forwards": len(rows),
                      "control_forwards": len(controls), "seconds": receipt["elapsed_seconds"],
                      "max_abs_difference": max(r["max_abs_difference_from_cached"] for r in rows)}))


if __name__ == "__main__":
    main()
