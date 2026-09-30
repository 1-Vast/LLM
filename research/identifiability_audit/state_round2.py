"""Verify inherited STATE queries and repeat inference seeds without fitting a model."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import anndata as ad
import numpy as np

from research.identifiability_audit import round2 as R, state_sensitivity as S


def run(out: Path):
    target = out / "state"
    target.mkdir(exist_ok=True)
    if any(target.iterdir()):
        raise FileExistsError("STATE output directory already contains artifacts")
    inherited = R.R1 / "state_recheck"
    baseline = ad.read_h5ad(inherited / "queries/baseline.h5ad")
    control = baseline.obs[S.PERT_COLUMN].astype(str).to_numpy() == S.CONTROL
    old_vector = np.load(inherited / "predictions/baseline.npy")
    verified = []
    records = []
    queries = sorted((inherited / "queries").glob("*.h5ad"))
    for query in queries:
        name = query.stem
        if name == "target_rows_deleted":
            continue
        a = ad.read_h5ad(query)
        mask = a.obs[S.PERT_COLUMN].astype(str).to_numpy() == S.CONTROL
        assert baseline.obs.loc[control].astype(str).reset_index(drop=True).equals(
            a.obs.loc[mask].astype(str).reset_index(drop=True))
        assert np.array_equal(baseline.obsm[S.EMBED_KEY][control], a.obsm[S.EMBED_KEY][mask])
        assert set(a.obs[S.PERT_COLUMN].astype(str)) == {S.CONTROL, S.TARGET}
        vector = np.load(inherited / "predictions" / (name + ".npy"))
        prediction = ad.read_h5ad(inherited / "predictions" / (name + ".h5ad"))
        predicted = prediction.obsm[S.EMBED_KEY]
        labels = prediction.obs[S.PERT_COLUMN].astype(str).to_numpy()
        derived = predicted[labels == S.TARGET].mean(axis=0) - predicted[labels == S.CONTROL].mean(axis=0)
        assert np.allclose(derived, vector, rtol=0, atol=1e-7)
        verified.append({"arm": name, "origin": "inherited_execution_independently_verified",
                         "query_sha256": R.file_hash(query),
                         "prediction_sha256": R.file_hash(inherited / "predictions" / (name + ".h5ad")),
                         "vector_sha256": R.file_hash(inherited / "predictions" / (name + ".npy")),
                         "identical_to_baseline": bool(np.array_equal(vector, old_vector)),
                         "target_rows": int((~mask).sum()),
                         "relative_l2": float(np.linalg.norm(vector - old_vector) / np.linalg.norm(old_vector)),
                         "cosine": float(vector @ old_vector / (np.linalg.norm(vector) * np.linalg.norm(old_vector)))})
    for seed in (42, 77, 123):
        S.SEED = seed  # runtime only; source and checkpoint remain unchanged
        dest = target / ("seed_" + str(seed))
        dest.mkdir()
        for name in ("baseline", "expression_permuted_s303", "expression_replaced_s333"):
            result = S.run_arm(name, inherited / "queries" / (name + ".h5ad"), dest, Path(sys.executable))
            result["inference_seed"] = seed
            records.append(result)
            print("STATE", seed, name, result.get("served"), flush=True)
        current = [r for r in records if r["inference_seed"] == seed]
        base = current[0]
        for r in current:
            r["identical_within_inference_seed"] = bool(r.get("served") and base.get("served") and
                                                        r["vector_sha256"] == base["vector_sha256"])
    deleted = inherited / "queries/target_rows_deleted.h5ad"
    dest = target / "deletion.subset.json"
    command = [sys.executable, str(S.RUNNER), "subset", "--input", str(deleted), "--summary", str(dest),
               "--perturbation", S.TARGET, "--control", S.CONTROL, "--perturbation-column", S.PERT_COLUMN,
               "--embed-key", S.EMBED_KEY, "--celltype-column", S.CELLTYPE_COLUMN,
               "--batch-column", S.BATCH_COLUMN, "--context-column", S.CELLTYPE_COLUMN, "--context", S.CONTEXT,
               "--subset-output", str(target / "deletion.subset.h5ad")]
    done = subprocess.run(command, capture_output=True, text=True, check=False)
    refusal = json.loads(dest.read_text())
    if done.returncode == 0 or refusal.get("valid"):
        raise AssertionError("absent_target_unexpectedly_supported")
    checkpoint = {p.relative_to(R.ROOT).as_posix(): R.file_hash(p) for p in S.MODEL_DIR.rglob("*") if p.is_file()}
    R.save(target / "state_summary.json", {
        "inherited_verified": verified, "new_inference": records,
        "target_deleted": {"status": "unsupported_query", "class": "interface_refusal",
                           "returncode": done.returncode, "query_sha256": R.file_hash(deleted),
                           "command": command, "errors": refusal.get("errors")},
        "checkpoint_hashes": checkpoint, "context": S.CONTEXT, "target": S.TARGET, "controls": S.CONTROL,
        "action_ranking": {"identified": False, "reason": "Registered STATE context is absent from both tasks; "
                           "no selector consumes its prediction. No counterfactual rank is invented."},
        "exposure": "Registered Tahoe c39 development condition; Tahoe checkpoint exposure declared in Round 1. "
                    "This interface audit does not establish unmeasured compound, dose, time or independent generalization.",
        "environment": {"python": sys.version, "interpreter": sys.executable},
        "command": [sys.executable, *sys.argv]})


if __name__ == "__main__":
    run(Path(sys.argv[1]) if len(sys.argv) > 1 else R.OUT)
