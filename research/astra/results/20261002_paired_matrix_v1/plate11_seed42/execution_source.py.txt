"""Paired-baseline STATE technical comparisons; no biological efficacy claim.

The official homogeneous per-action inference loop stays intact. A process-local
hook changes only ctrl_cell_emb immediately before predict_step for planned
actions. Controls retain their original inference behavior. All actions receive
the same sampled baseline tensor, in the same order, without joining action sets.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

import anndata as ad
import numpy as np

from tools.datasets.state_prospective_input import (
    CONTROL, CONTEXT, KEY, PERT, build_requests, digest, load_contract,
    validate_requests, write_json,
)


def tensor_digest(value):
    array = value.detach().cpu().numpy() if hasattr(value, "detach") else np.asarray(value)
    return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()


def sample_baseline(baseline, count, seed):
    """Draw once, with replacement, preserving ordered source IDs for replay."""
    if isinstance(count, bool) or not isinstance(count, int) or count < 1:
        raise ValueError("positive frozen query count required")
    if not baseline.n_obs:
        raise ValueError("baseline pool is empty")
    indices = np.random.RandomState(seed).choice(baseline.n_obs, count, replace=True)
    matrix = np.asarray(baseline.obsm[KEY], dtype=np.float32)[indices].copy()
    return matrix, indices.tolist(), baseline.obs_names[indices].tolist()


def metadata_digest(batch):
    """Digest metadata without basal values; avoid changing one-hots or batch labels."""
    def plain(value):
        if hasattr(value, "detach"):
            return {"shape": list(value.shape), "dtype": str(value.dtype), "sha256": tensor_digest(value)}
        return value
    payload = {k: plain(v) for k, v in batch.items() if k != "ctrl_cell_emb"}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, allow_nan=False).encode()).hexdigest()


class PairedBasal:
    """Validate and trace one frozen homogeneous action batch per menu action."""

    def __init__(self, sampled, actions, indices, sample_ids, mapping):
        self.sampled = np.asarray(sampled, dtype=np.float32).copy()
        self.actions = tuple(actions)
        if not actions or len(set(actions)) != len(actions) or CONTROL in actions:
            raise ValueError("unique planned noncontrol actions required")
        if len(indices) != len(self.sampled) or len(sample_ids) != len(indices):
            raise ValueError("sample index count mismatch")
        if any(action not in mapping for action in actions):
            raise ValueError("unknown action")
        if self.sampled.ndim != 2 or not np.isfinite(self.sampled).all():
            raise ValueError("invalid frozen basal tensor")
        self.indices, self.sample_ids = list(indices), list(sample_ids)
        self.mapping = mapping
        self.expected_digest = tensor_digest(self.sampled)
        self.calls = []
        self.seen = set()

    def forward(self, original, model, batch, *args, **kwargs):
        import torch

        names = batch.get("pert_name")
        if not isinstance(names, (list, tuple)) or not names or len(set(names)) != 1:
            raise ValueError("homogeneous named action batch required")
        action = names[0]
        rows = len(batch["ctrl_cell_emb"])
        if len(names) != rows:
            raise ValueError("action metadata row count changed")
        before = metadata_digest(batch)
        paired = dict(batch)
        if action != CONTROL:
            if action not in self.actions or action in self.seen:
                raise ValueError("action menu changed or repeated action window")
            if rows != len(self.sampled) or tuple(batch["ctrl_cell_emb"].shape) != self.sampled.shape:
                raise ValueError("frozen query count or feature shape changed")
            onehot = batch.get("pert_emb")
            if onehot is None or onehot.ndim != 2 or len(onehot) != rows:
                raise ValueError("missing action encoding")
            expected_index = self.mapping[action]
            expected = torch.zeros_like(onehot)
            expected[:, expected_index] = 1
            if not torch.equal(onehot, expected):
                raise ValueError("action encoding differs from frozen map")
            paired["ctrl_cell_emb"] = torch.as_tensor(
                self.sampled.copy(), dtype=batch["ctrl_cell_emb"].dtype,
                device=batch["ctrl_cell_emb"].device,
            )
            self.seen.add(action)
        actual_digest = tensor_digest(paired["ctrl_cell_emb"])
        if action != CONTROL and actual_digest != self.expected_digest:
            raise ValueError("actual basal tensor differs from frozen sample")
        if metadata_digest(paired) != before:
            raise ValueError("paired replacement changed batch metadata")
        output = original(model, paired, *args, **kwargs)
        if metadata_digest(paired) != before or tensor_digest(paired["ctrl_cell_emb"]) != actual_digest:
            raise ValueError("model mutated recorded forward inputs")
        predicted = output.get("preds")
        self.calls.append({
            "action": action, "rows": rows, "paired": action != CONTROL,
            "basal_sha256": actual_digest, "metadata_sha256": before,
            "source_indices_zero_based": self.indices if action != CONTROL else None,
            "source_sample_ids": self.sample_ids if action != CONTROL else None,
            "raw_prediction_zero_count": int((predicted == 0).sum().item()) if predicted is not None else None,
            "raw_prediction_values": int(predicted.numel()) if predicted is not None else None,
        })
        return output

    def validate_complete(self):
        if self.seen != set(self.actions):
            raise ValueError("not every frozen action executed")
        paired_calls = [call for call in self.calls if call["paired"]]
        if len(paired_calls) != len(self.actions):
            raise ValueError("incomplete paired forward receipts")
        if {call["basal_sha256"] for call in paired_calls} != {self.expected_digest}:
            raise ValueError("different basals used across actions")


@contextmanager
def paired_hook(model_class, pairing):
    """Always restore the class hook; use only in an isolated comparison process."""
    original = model_class.predict_step

    def predict_step(model, batch, *args, **kwargs):
        return pairing.forward(original, model, batch, *args, **kwargs)

    model_class.predict_step = predict_step
    try:
        yield
    finally:
        model_class.predict_step = original


def worker(query_path, output, contract_path, actions, count, seed):
    import random
    import torch
    from state._cli._tx._infer import add_arguments_infer, run_tx_infer
    from state.tx.models.state_transition import StateTransitionPerturbationModel

    contract = json.loads(Path(contract_path).read_text(encoding="utf-8"))
    query_hash = digest(query_path)
    for name in ("weights", "config", "map", "dims", "axis"):
        asset = contract["hashes"][name]
        if digest(asset["path"]) != asset["sha256"]:
            raise ValueError(f"frozen model asset changed: {name}")
    query = ad.read_h5ad(query_path)
    validate_requests(query, actions, count, contract)
    baseline = query[query.obs["role"].astype(str) == "baseline_control"].copy()
    sampled, indices, sample_ids = sample_baseline(baseline, count, seed)
    pairing = PairedBasal(sampled, actions, indices, sample_ids, contract["mapping"])
    trace = {"error": None, "scope": "technical development controls, not prospective state",
             "context": CONTEXT, "plate": str(baseline.obs["plate"].iloc[0]),
             "seed": seed, "sampled_basal_sha256": pairing.expected_digest,
             "source_indices_zero_based": indices, "source_sample_ids": sample_ids,
             "model_loaded_once": "one official run_tx_infer invocation",
             "query_sha256": query_hash, "cost": "unknown"}
    parser = argparse.ArgumentParser()
    add_arguments_infer(parser)
    args = parser.parse_args([
        "--adata", str(query_path), "--output", str(output), "--model-dir", contract["model_dir"],
        "--embed-key", KEY, "--pert-col", PERT, "--celltype-col", "cell_name",
        "--batch-col", "plate", "--control-pert", CONTROL, "--seed", str(seed), "--quiet",
    ])
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    original_predict_step = StateTransitionPerturbationModel.predict_step
    try:
        with paired_hook(StateTransitionPerturbationModel, pairing):
            run_tx_infer(args)
            pairing.validate_complete()
        if digest(query_path) != query_hash:
            raise ValueError("query asset changed during inference")
    except Exception as exc:
        trace["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        trace["calls"] = pairing.calls
        trace["hook_restored"] = StateTransitionPerturbationModel.predict_step is original_predict_step
        write_json(Path(output).parent / "paired_trace.json", trace)


def run_comparison(root, baseline_path, out, actions, count=16, seed=42):
    """Build a lawful technical query and execute one isolated paired comparison."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    record = {"valid": False, "biological_state_gain": "not_tested", "physical_attempts": 0,
              "cost": "unknown", "seed": seed, "count": count, "actions": list(actions)}
    try:
        contract = load_contract(root)
        write_json(out / "contract.json", contract)
        baseline = ad.read_h5ad(baseline_path)
        query = build_requests(baseline, actions, count, contract)
        query_path, output = out / "query.h5ad", out / "prediction.h5ad"
        query.write_h5ad(query_path)
        record.update(baseline_sha256=digest(baseline_path), query_sha256=digest(query_path),
                      checkpoint_sha256=contract["hashes"]["weights"]["sha256"],
                      execution_source_sha256=digest(Path(__file__)),
                      scope="historical endpoint controls; technical pairing only")
        (out / "execution_source.py.txt").write_bytes(Path(__file__).read_bytes())
        write_json(out / "freeze.json", record)
        command = [sys.executable, "-m", "research.astra.paired_state", "worker",
                   "--query", str(query_path.resolve()), "--output", str(output.resolve()),
                   "--contract", str((out / "contract.json").resolve()),
                   "--actions-json", json.dumps(actions), "--count", str(count), "--seed", str(seed)]
        record["command"] = command
        done = subprocess.run(command, cwd=root, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=600)
        (out / "stdout.txt").write_text(done.stdout, encoding="utf-8")
        (out / "stderr.txt").write_text(done.stderr, encoding="utf-8")
        record["returncode"] = done.returncode
        if done.returncode:
            raise RuntimeError("paired worker failed; see stderr.txt")
        trace = json.loads((out / "paired_trace.json").read_text(encoding="utf-8"))
        if trace["error"] or sum(c["rows"] for c in trace["calls"]) != query.n_obs:
            raise ValueError("not all rows received executed forwards")
        paired_calls = [c for c in trace["calls"] if c["paired"]]
        if {c["action"] for c in paired_calls} != set(actions) or len(paired_calls) != len(actions):
            raise ValueError("trace action menu mismatch")
        if {c["basal_sha256"] for c in paired_calls} != {trace["sampled_basal_sha256"]}:
            raise ValueError("trace basal mismatch")
        pred = ad.read_h5ad(output)
        if not pred.obs.equals(query.obs) or list(pred.obs_names) != list(query.obs_names):
            raise ValueError("output changed query context or identities")
        matrix = np.asarray(pred.obsm[KEY])
        if matrix.shape != query.obsm[KEY].shape or not np.isfinite(matrix).all():
            raise ValueError("invalid prediction matrix")
        mask = query.obs["role"].astype(str) == "prediction_request"
        np.save(out / "request_predictions.npy", matrix[mask])
        endpoint = contract["axis"].index("0546:EGR1")
        scores = {action: float(matrix[np.asarray(query.obs[PERT].astype(str) == action), endpoint].mean())
                  for action in actions}
        record.update(valid=True, actual_forwards=len(trace["calls"]),
                      paired_basal_sha256=trace["sampled_basal_sha256"],
                      output_sha256=digest(output), endpoint="mean predicted log1p EGR1; diagnostic only",
                      endpoint_scores=scores, zero_count=int((matrix[mask] == 0).sum()),
                      prediction_values=int(matrix[mask].size))
    except Exception as exc:
        record["error"] = f"{type(exc).__name__}: {exc}"
    record["elapsed_seconds"] = time.perf_counter() - started
    write_json(out / "receipt.json", record)
    write_json(out / "manifest.json", {p.name: digest(p) for p in out.iterdir() if p.is_file()})
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["run", "worker"])
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--query", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--contract", type=Path)
    parser.add_argument("--actions-json", required=True)
    parser.add_argument("--count", type=int, default=16)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    actions = json.loads(args.actions_json)
    if args.mode == "worker":
        worker(args.query, args.output, args.contract, actions, args.count, args.seed)
        return 0
    result = run_comparison(args.root.resolve(), args.baseline, args.out, actions, args.count, args.seed)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
