"""Fail-closed research wrapper for STATE; prediction requests are not observations.

The registered axis has unnamed coordinates. Existing X_hvg fixtures are usable
for software tests; raw RNA cannot be certified until that axis is recovered.
No outcome file is accepted by the builder or prediction worker.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

import anndata as ad
import numpy as np
import pandas as pd

MODEL = "state_generalization_zeroshot_X_hvg"
CONTROL = "[('DMSO_TF', 0.0, 'uM')]"
CONTEXT = "NCI-H596"
KEY = "X_hvg"
PERT = "drugname_drugconc"


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def load_contract(root):
    import torch
    from src.virtual_cell.state_runner import _numpy_scalar_globals

    root = Path(root)
    registry_path = root / "data/virtual_cell/registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    model = registry["models"][MODEL]
    dataset = registry["datasets"]["tahoe_c39"]
    model_dir = root / model["directory"]
    files = {
        "weights": (model_dir / "checkpoints/final.ckpt", model["checkpoint_sha256"]),
        "map": (model_dir / "pert_onehot_map.pt", model["pert_onehot_map_sha256"]),
        "dims": (model_dir / "var_dims.pkl", model["var_dims_sha256"]),
        "axis": (root / dataset["feature_names"], dataset["feature_names_sha256"]),
        "dataset": (root / dataset["path"], dataset["sha256"]),
    }
    hashes = {}
    for key, (path, expected) in files.items():
        actual = digest(path)
        if actual != expected:
            raise ValueError(f"registered {key} hash mismatch")
        hashes[key] = {"path": str(path.resolve()), "sha256": actual, "bytes": path.stat().st_size}
    for key, path in {"config": model_dir / "config.yaml", "registry": registry_path}.items():
        hashes[key] = {"path": str(path.resolve()), "sha256": digest(path), "bytes": path.stat().st_size}
    names = json.loads(files["axis"][0].read_text(encoding="utf-8"))["names"]
    with torch.serialization.safe_globals(list(_numpy_scalar_globals())):
        mapping = torch.load(files["map"][0], map_location="cpu", weights_only=True)
    for label, vector in mapping.items():
        if vector.shape != (1138,) or not torch.isfinite(vector).all() or not torch.all((vector == 0) | (vector == 1)) or vector.sum() != 1:
            raise ValueError(f"invalid onehot vector: {label}")
    return {
        "model_dir": str(model_dir.resolve()), "hashes": hashes,
        "axis": [f"{i:04d}:{name if name is not None else '__UNRESOLVED__'}" for i, name in enumerate(names)],
        "unresolved_coordinates": [i for i, name in enumerate(names) if name is None],
        "mapping": {str(k): int(v.argmax()) for k, v in mapping.items()},
        "context": CONTEXT, "control": CONTROL, "feature_count": 2000,
        "new_rna_preprocessing_certified": False,
        "training_exposure": "unknown; evaluator holdout does not establish checkpoint holdout",
        "local_calibration_exposure": registry.get("scale_calibrations", []),
    }


def validate_baseline(baseline, contract):
    if not baseline.n_obs:
        raise ValueError("missing baseline controls")
    if list(baseline.uns.get("state_feature_axis", [])) != contract["axis"]:
        raise ValueError("feature order or identity mismatch")
    values = np.asarray(baseline.obsm[KEY])
    if values.shape != (baseline.n_obs, contract["feature_count"]) or not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("invalid log1p baseline matrix")
    for column, expected in ((PERT, CONTROL), ("cell_name", CONTEXT), ("role", "baseline_control")):
        if column not in baseline.obs or not (baseline.obs[column].astype(str) == expected).all():
            raise ValueError(f"invalid baseline {column}")
    if "plate" not in baseline.obs or baseline.obs["plate"].isna().any() or baseline.obs["plate"].astype(str).nunique() != 1:
        raise ValueError("one explicit matched baseline pool required; cross-batch pooling forbidden")
    if not baseline.obs_names.is_unique:
        raise ValueError("duplicate baseline sample IDs")


def build_requests(baseline, actions, count, contract, placeholder=0.0):
    validate_baseline(baseline, contract)
    if not actions or len(set(actions)) != len(actions) or CONTROL in actions:
        raise ValueError("unique noncontrol action menu required")
    if any(action not in contract["mapping"] for action in actions):
        raise ValueError("unknown perturbation; control fallback forbidden")
    if not isinstance(count, int) or count <= 0:
        raise ValueError("positive predeclared query count required")
    rows = [dict(cell_name=CONTEXT, plate=str(baseline.obs["plate"].iloc[0]),
                 role="prediction_request", **{PERT: action})
            for action in actions for _ in range(count)]
    obs = pd.DataFrame(rows, index=[f"prediction_request:{i}" for i in range(len(rows))])
    query = ad.AnnData(obs=pd.concat([baseline.obs[[PERT, "cell_name", "plate", "role"]], obs]))
    query.obsm[KEY] = np.concatenate([np.asarray(baseline.obsm[KEY], dtype=np.float32),
                                    np.full((len(rows), contract["feature_count"]), placeholder, dtype=np.float32)])
    query.uns["state_feature_axis"] = np.asarray(contract["axis"])
    query.uns["purpose"] = "technical_fixture_not_biological_evidence"
    validate_requests(query, actions, count, contract)
    return query


def validate_requests(query, actions, count, contract):
    if not query.obs_names.is_unique:
        raise ValueError("duplicate request IDs")
    if list(query.uns.get("state_feature_axis", [])) != contract["axis"]:
        raise ValueError("feature order or identity mismatch")
    roles = set(query.obs["role"].astype(str))
    if "baseline_control" not in roles:
        raise ValueError("missing baseline controls")
    if roles != {"baseline_control", "prediction_request"}:
        raise ValueError("observed outcomes cannot enter prediction requests")
    controls = query.obs["role"].astype(str) == "baseline_control"
    validate_baseline(query[controls].copy(), contract)
    requests = query.obs[~controls]
    if not (requests["cell_name"].astype(str) == CONTEXT).all():
        raise ValueError("wrong query context")
    if not (requests["plate"].astype(str) == str(query.obs.loc[controls, "plate"].iloc[0])).all():
        raise ValueError("missing matched baseline; global control fallback forbidden")
    if any(action not in contract["mapping"] for action in requests[PERT].astype(str)):
        raise ValueError("unknown perturbation; control fallback forbidden")
    expected = {action: count for action in actions}
    if requests[PERT].astype(str).value_counts().to_dict() != expected:
        raise ValueError("query menu/count changed from frozen plan")
    if np.asarray(query.obsm[KEY]).shape != (query.n_obs, contract["feature_count"]):
        raise ValueError("invalid query matrix shape")


def preprocess_new_rna(counts, gene_names, contract):
    # Failing before any normalization avoids silently filling 31 unknown genes.
    if contract["unresolved_coordinates"] or not contract["new_rna_preprocessing_certified"]:
        raise ValueError("new RNA preprocessing uncertified: unresolved feature identity / normalization provenance")
    raise ValueError("new RNA requires an independently reviewed preprocessing contract")


def predict(query_path, out, contract, actions, count, seed=42, checkpoint=None, forbidden_outcome=None):
    """A subprocess error or unexecuted forward can never produce valid=True."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    query = ad.read_h5ad(query_path)
    record = {"valid": False, "valid_experiment": False, "purpose": "technical_fixture",
              "model": MODEL, "query_sha256": digest(query_path), "cost": "unknown"}
    started = time.perf_counter()
    try:
        validate_requests(query, actions, count, contract)
        output = out / "prediction.h5ad"
        command = [sys.executable, "-m", "tools.datasets.state_prospective_input", "worker",
                   "--adata", str(Path(query_path).resolve()), "--output", str(output.resolve()),
                   "--model-dir", contract["model_dir"], "--embed-key", KEY, "--pert-col", PERT,
                   "--celltype-col", "cell_name", "--batch-col", "plate", "--control-pert", CONTROL,
                   "--seed", str(seed), "--quiet"]
        if checkpoint is not None:
            command += ["--checkpoint", str(checkpoint)]
        if forbidden_outcome is not None:
            command += ["--forbid-outcome-file", str(Path(forbidden_outcome).resolve())]
        record["command"] = command
        done = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
        (out / "stdout.txt").write_text(done.stdout, encoding="utf-8")
        (out / "stderr.txt").write_text(done.stderr, encoding="utf-8")
        record["returncode"] = done.returncode
        if done.returncode:
            raise RuntimeError("STATE subprocess failed; see stderr.txt")
        trace = json.loads((out / "forward_trace.json").read_text(encoding="utf-8"))
        record["trace"] = trace
        if trace["error"] or sum(call["rows"] for call in trace["calls"]) != query.n_obs:
            raise ValueError("not every row has an executed STATE forward")
        pred = ad.read_h5ad(output)
        if list(pred.obs_names) != list(query.obs_names) or not pred.obs.equals(query.obs):
            raise ValueError("prediction changed request identities")
        matrix = np.asarray(pred.obsm[KEY])
        if matrix.shape != query.obsm[KEY].shape or not np.isfinite(matrix).all():
            raise ValueError("invalid prediction shape or nonfinite output")
        request_mask = query.obs["role"].astype(str) == "prediction_request"
        np.save(out / "request_predictions.npy", matrix[request_mask])
        record.update(valid=True, output_sha256=digest(output), prediction_sha256=digest(out / "request_predictions.npy"),
                      query_rows=int(request_mask.sum()), forward_calls=len(trace["calls"]))
    except Exception as exc:
        record["error"] = f"{type(exc).__name__}: {exc}"
    record["elapsed_seconds"] = time.perf_counter() - started
    write_json(out / "receipt.json", record)
    return record


def install_outcome_guard(path, trace):
    """Fail if a Python file-open attempts to read the held-out sentinel."""
    protected = Path(path).resolve()

    def audit(event, args):
        if event == "open" and isinstance(args[0], (str, bytes)):
            opened = Path(args[0].decode() if isinstance(args[0], bytes) else args[0]).resolve()
            if opened == protected:
                trace["outcome_access_attempts"].append(str(opened))
                raise PermissionError("future outcome access forbidden in prediction process")

    sys.addaudithook(audit)


def worker(argv):
    guard_parser = argparse.ArgumentParser(add_help=False)
    guard_parser.add_argument("--forbid-outcome-file")
    guard_args, remaining = guard_parser.parse_known_args(argv)
    trace = {"calls": [], "error": None, "outcome_access_attempts": []}
    if guard_args.forbid_outcome_file:
        install_outcome_guard(guard_args.forbid_outcome_file, trace)
    import random
    import torch
    from state._cli._tx._infer import add_arguments_infer, run_tx_infer
    from state.tx.models.state_transition import StateTransitionPerturbationModel

    parser = argparse.ArgumentParser()
    add_arguments_infer(parser)
    args = parser.parse_args(remaining)
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.cuda.manual_seed_all(args.seed)
    trace.update(torch=torch.__version__, cuda=torch.cuda.is_available(), outcome_guard=bool(guard_args.forbid_outcome_file))
    original = StateTransitionPerturbationModel.predict_step

    def traced(self, batch, *positional, **keywords):
        result = original(self, batch, *positional, **keywords)
        trace["calls"].append({"keys": sorted(batch), "rows": len(batch["ctrl_cell_emb"]),
                               "action": batch["pert_name"][0], "device": str(next(self.parameters()).device),
                               "basal_sha256": hashlib.sha256(batch["ctrl_cell_emb"].detach().cpu().numpy().tobytes()).hexdigest()})
        return result

    StateTransitionPerturbationModel.predict_step = traced
    try:
        run_tx_infer(args)
    except Exception as exc:
        trace["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        StateTransitionPerturbationModel.predict_step = original
        write_json(Path(args.output).parent / "forward_trace.json", trace)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "worker":
        worker(sys.argv[2:])
    else:
        raise SystemExit("Use the research certification driver or the worker subcommand.")
