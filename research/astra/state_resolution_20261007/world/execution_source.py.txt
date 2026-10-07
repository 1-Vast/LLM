"""Paired native STATE response diagnosis; no treated outcomes are accepted.

Observe the native ReLU input without changing model computation. Match drug and
DMSO against identical sampled real basal tensors at two frozen set lengths.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[4]
PRIOR = ROOT / "research/astra/state_dual_core_20261007/world"
OUT = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]

def digest(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()

def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")

def run(out):
    import numpy as np
    import psutil
    import torch
    from tools.datasets.state_prospective_input import load_contract, CONTROL
    from state.tx.models.state_transition import StateTransitionPerturbationModel
    started = time.perf_counter()
    process = psutil.Process()
    cpu0 = process.cpu_times()
    out.mkdir(parents=True, exist_ok=True)
    if (out / "FREEZE.json").exists():
        raise FileExistsError("preserve frozen run; choose fresh --out")
    contract = load_contract(ROOT)
    prior_plan = json.loads((PRIOR / "metadata_freeze.json").read_text())
    with np.load(PRIOR / "basal_controls.npz") as f:
        basals = {key: f[key].copy() for key in f.files}
    samples, sample_receipts = {}, []
    for n in (32, 256):
        for plate, matrix in basals.items():
            indices = np.random.RandomState(731).choice(len(matrix), n, replace=True)
            samples[n, plate] = matrix[indices]
            sample_receipts.append({"set_length": n, "plate": plate,
                  "source_ids": [prior_plan["basal_sample_ids"][plate][i] for i in indices],
                  "unique_sampled_cells": len(set(indices.tolist())), "available_unique_cells": len(matrix),
                  "sha256": hashlib.sha256(samples[n, plate].tobytes()).hexdigest()})
    source_root = ROOT / "data/external/arc_state/source"
    source_files = {str(p.relative_to(ROOT)): digest(p) for p in sorted(source_root.rglob("*.py"))}
    source_files["research/astra/state_resolution_20261007/world/run_counterfactual.py"] = digest(Path(__file__))
    plan = {"created_utc": datetime.now(timezone.utc).isoformat(),
        "hypothesis": "A shared DMSO-decoder displacement may dominate raw predicted change; matched model-counterfactual subtraction may isolate intervention information. Set length may affect nonlinear response. Neither improvement is assumed.",
        "conditions": prior_plan["conditions"], "set_lengths": [32, 256], "seed": 731,
        "sampling": "same real source basal halves; nested replacement draws; increased set length adds repetitions, not new biological cells",
        "endpoints": ["native drug-minus-basal", "native drug-minus-predicted-DMSO"],
        "clipping_diagnostic": "passive forward-pre-hook on model.relu; capture pre-ReLU native output, do not modify input/output",
        "comparison": "identical source cells/order and native onehot perturbation except drug vs DMSO",
        "status": "exploratory, historically exposed c39, original downstream splits unchanged; no evaluation labels in inference",
        "source_files": source_files, "checkpoint_contract": contract["hashes"],
        "prior_input_hashes": {name: digest(PRIOR / name) for name in ("metadata_freeze.json", "conditions.csv", "basal_controls.npz", "contract.json")},
        "samples": sample_receipts, "model_loads_planned": 1,
        "forwards_planned": 2 * (len(prior_plan["conditions"]) + len(basals)),
        "no_head_fitting_or_outcome_access": True}
    write(out / "PROTOCOL.json", plan)
    write(out / "FREEZE.json", {"protocol_sha256": digest(out / "PROTOCOL.json"), "created_utc": datetime.now(timezone.utc).isoformat(), "inference_started": False})
    (out / "execution_source.py.txt").write_bytes(Path(__file__).read_bytes())
    write(out / "contract.json", contract)
    (out / "conditions.csv").write_bytes((PRIOR / "conditions.csv").read_bytes())
    stopped = threading.Event()
    resource = {"api_calls": 0, "api_tokens": 0, "api_cost_usd": 0.0, "downloaded_bytes": 0,
        "new_wet_measurements": 0, "local_financial_cost_usd": None, "peak_rss_bytes": process.memory_info().rss,
        "timer_scope": "after Python imports, including contract validation/sampling/freeze/model load/forwards"}
    def monitor():
        while not stopped.wait(0.05):
            resource["peak_rss_bytes"] = max(resource["peak_rss_bytes"], process.memory_info().rss)
    thread = threading.Thread(target=monitor, daemon=True)
    thread.start()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    torch.set_num_threads(2)
    torch.manual_seed(731)
    if device == "cuda":
        torch.cuda.reset_peak_memory_stats()
    trace = []
    hook = None
    try:
        start = time.perf_counter()
        model = StateTransitionPerturbationModel.load_from_checkpoint(contract["hashes"]["weights"]["path"], map_location="cpu").to(device).eval()
        resource["load_seconds"] = time.perf_counter() - start
        resource["model_loads"] = 1
        write(out / "runtime.json", {"parameter_count": sum(p.numel() for p in model.parameters()),
            "arc_state_version": importlib.metadata.version("arc-state"), "torch": torch.__version__,
            "device": device, "gpu": torch.cuda.get_device_name() if device == "cuda" else None,
            "cell_set_len": model.cell_sentence_len, "native_relu": str(model.relu), "batch_encoder": model.batch_encoder is not None})
        captured = []
        def capture(module, args):
            captured.append(args[0].detach())
        hook = model.relu.register_forward_pre_hook(capture)
        def forward(n, plate, label, condition_id):
            start = time.perf_counter()
            basal = samples[n, plate]
            onehot = torch.zeros((n, model.pert_dim), device=device)
            onehot[:, contract["mapping"][label]] = 1
            batch = {"ctrl_cell_emb": torch.tensor(basal, device=device), "pert_emb": onehot, "pert_name": [label] * n}
            captured.clear()
            prediction = model.predict_step(batch, batch_idx=0, padded=False)["preds"].detach().cpu().numpy().reshape(n, -1)
            assert len(captured) == 1, "native model.relu must be called exactly once"
            pre = captured[0].cpu().numpy().reshape(n, -1)
            assert np.array_equal(np.maximum(pre, 0), prediction)
            assert prediction.shape == basal.shape and np.isfinite(pre).all()
            trace.append({"set_length": n, "plate": plate, "label": label, "condition_id": condition_id,
                "basal_sha256": hashlib.sha256(basal.tobytes()).hexdigest(),
                "seconds": time.perf_counter() - start, "zero_fraction": float((prediction == 0).mean()),
                "pre_negative_fraction": float((pre < 0).mean()), "pre_mean": float(pre.mean()),
                "pre_rms": float(np.sqrt(np.mean(pre.astype(float) ** 2))),
                "prediction_max": float(prediction.max())})
            return prediction, pre
        prediction_means, dmso_means, basal_means, pre_deltas, clip_checks = [], [], [], [], []
        with torch.inference_mode():
            for n in (32, 256):
                controls = {plate: forward(n, plate, CONTROL, "control:" + plate) for plate in basals}
                pred_n, dmso_n, basal_n, pre_n = [], [], [], []
                for row in prior_plan["conditions"]:
                    drug, pre_drug = forward(n, row["plate"], row["label"], row["condition_id"])
                    dmso, pre_dmso = controls[row["plate"]]
                    post_diff, pre_diff = drug - dmso, pre_drug - pre_dmso
                    nonzero = pre_diff != 0
                    erased = nonzero & (post_diff == 0)
                    clip_checks.append({"condition_id": row["condition_id"], "set_length": n,
                        "pre_intervention_rms": float(np.sqrt(np.mean(pre_diff.astype(float) ** 2))),
                        "post_intervention_rms": float(np.sqrt(np.mean(post_diff.astype(float) ** 2))),
                        "nonzero_pre_values": int(nonzero.sum()), "erased_by_relu_values": int(erased.sum()),
                        "both_drug_dmso_zero_fraction": float(((drug == 0) & (dmso == 0)).mean()),
                        "mean_raw_delta_rms": float(np.sqrt(np.mean((drug.mean(0) - samples[n, row["plate"]].mean(0)) ** 2))),
                        "mean_dmso_bias_rms": float(np.sqrt(np.mean((dmso.mean(0) - samples[n, row["plate"]].mean(0)) ** 2))),
                        "mean_counterfactual_rms": float(np.sqrt(np.mean(post_diff.mean(0) ** 2)))})
                    pred_n.append(drug.mean(0)); dmso_n.append(dmso.mean(0)); basal_n.append(samples[n, row["plate"]].mean(0)); pre_n.append(pre_diff.mean(0))
                prediction_means.append(pred_n); dmso_means.append(dmso_n); basal_means.append(basal_n); pre_deltas.append(pre_n)
        pred, dmso, basal = map(np.asarray, (prediction_means, dmso_means, basal_means))
        np.savez_compressed(out / "representations.npz", condition_id=np.asarray([r["condition_id"] for r in prior_plan["conditions"]]),
            set_lengths=np.asarray([32, 256]), predicted_mean=pred, basal_mean=basal, dmso_mean=dmso,
            raw_delta=pred-basal, counterfactual_delta=pred-dmso, pre_relu_counterfactual_delta=np.asarray(pre_deltas))
        write(out / "forward_trace.json", trace)
        write(out / "clipping_diagnostics.json", clip_checks)
        diagnostics = {}
        for ni, n in enumerate((32, 256)):
            selected = [x for x in clip_checks if x["set_length"] == n]
            diagnostics[str(n)] = {"mean_raw_delta_rms": float(np.mean([x["mean_raw_delta_rms"] for x in selected])),
                "mean_dmso_bias_rms": float(np.mean([x["mean_dmso_bias_rms"] for x in selected])),
                "mean_counterfactual_rms": float(np.mean([x["mean_counterfactual_rms"] for x in selected])),
                "pre_nonzero_fraction_erased": sum(x["erased_by_relu_values"] for x in selected) / sum(x["nonzero_pre_values"] for x in selected),
                "mean_pre_intervention_rms": float(np.mean([x["pre_intervention_rms"] for x in selected])),
                "mean_post_intervention_rms": float(np.mean([x["post_intervention_rms"] for x in selected]))}
        diagnostics["interpretation_limit"] = "These are actual representation/clipping diagnostics without outcome evaluation. Erased preactivation differences do not establish useful lost biological signal. DMSO subtraction is a hypothesis, not demonstrated improvement."
        write(out / "diagnostics_summary.json", diagnostics)
        resource.update(status="completed", forwards=len(trace), predictions_sha256=digest(out / "representations.npz"),
                        sum_forward_seconds=sum(x["seconds"] for x in trace))
        assert all(digest(PRIOR / name) == value for name, value in plan["prior_input_hashes"].items())
        write(out / "identity_checks.json", {"prior_inputs_unchanged": True, "condition_ids_unique": len(set(r["condition_id"] for r in prior_plan["conditions"])) == 144,
              "real_sample_prefix_nested": all(np.array_equal(samples[32, p], samples[256, p][:32]) for p in basals),
              "native_relu_observation_verified_every_forward": True, "no_treated_outcomes_read": True,
              "raw_delta_algebra": bool(np.array_equal(pred-basal, (pred-dmso)+(dmso-basal)))})
    except Exception as exc:
        resource.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        write(out / "partial_forward_trace.json", trace)
        raise
    finally:
        if hook is not None:
            hook.remove()
        stopped.set(); thread.join()
        cpu1 = process.cpu_times()
        resource.update(elapsed_seconds=time.perf_counter() - started, cpu_seconds=cpu1.user+cpu1.system-cpu0.user-cpu0.system,
              peak_cuda_allocated_bytes=torch.cuda.max_memory_allocated() if device == "cuda" else 0,
              peak_cuda_reserved_bytes=torch.cuda.max_memory_reserved() if device == "cuda" else 0)
        write(out / "resources.json", resource)
    print(json.dumps(resource))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    run(args.out.resolve())
