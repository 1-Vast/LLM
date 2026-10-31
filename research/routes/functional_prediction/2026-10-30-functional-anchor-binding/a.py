"""Retrospective source-only projected-Ridge countertest; no held-out access."""
import os
for option in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[option] = "4"
import hashlib
import json
from pathlib import Path
import sys
import time
import numpy as np
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[3]
PARENT = ROOT.parent / "2026-10-30-conditional-intervention-admission"
SOURCE = PROJECT / "data/processed/conditional_interventions_20261030/cgi/stage1_corrected"
OUT = PROJECT / "data/processed/functional_anchor_binding_20261030/a"
METHODS = ["frequency", "chemical_ridge100", "knowledge_ridge100", "joint_ridge1",
           "joint_ridge10", "joint_ridge100", "joint_rbf1", "joint_teacher32"]

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def write(path, obj):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)

def ridge(a, b, alpha):
    mean, sd = a.mean(0), a.std(0)
    sd[sd == 0] = 1
    a, b = (a - mean) / sd, (b - mean) / sd
    return np.linalg.solve(a @ a.T + alpha * np.eye(len(a)), a @ b.T).T + 1 / len(a)

def operators(x, k, folds):
    result = {}
    for fold in np.unique(folds):
        train, query = np.flatnonzero(folds != fold), np.flatnonzero(folds == fold)
        joint = np.concatenate([x, k], axis=1)
        weights = [None, ridge(x[train], x[query], 100), ridge(k[train], k[query], 100)]
        weights += [ridge(joint[train], joint[query], alpha) for alpha in (1, 10, 100)]
        a, b = joint[train], joint[query]
        sd = a.std(0)
        gamma = 1 / max(1, np.count_nonzero(sd))
        sd[sd == 0] = 1
        mean = a.mean(0)
        a, b = (a - mean) / sd, (b - mean) / sd
        def rbf(left, right):
            distance = left.__pow__(2).sum(1)[:, None] + right.__pow__(2).sum(1)[None, :] - 2 * left @ right.T
            return np.exp(-gamma * np.maximum(distance, 0))
        kernel, cross = rbf(a, a), rbf(b, a)
        colmean, grand = kernel.mean(0), kernel.mean()
        centered = kernel - colmean[None, :] - colmean[:, None] + grand
        cross = cross - cross.mean(1)[:, None] - colmean[None, :] + grand
        weights.append(np.linalg.solve(centered + np.eye(len(a)), cross.T).T + 1 / len(a))
        assert all(np.allclose(w.sum(1), 1, atol=1e-8) for w in weights[1:])
        result[int(fold)] = (train, query, weights)
    return result

def teacher(y):
    centered = y - y.mean(0)
    eigen, vectors = np.linalg.eigh(centered @ centered.T)
    order = np.argsort(-eigen, kind="stable")
    eigen, vectors = eigen[order], vectors[:, order]
    tolerance = 1e-10 * max(1., float(eigen[0]))
    positive = int(np.count_nonzero(eigen > tolerance))
    if positive > 32 and eigen[31] - eigen[32] <= tolerance:
        raise RuntimeError("TIED_RANK_BOUNDARY")
    rank = min(32, positive)
    return vectors[:, :rank], {"rank": rank, "positive_modes": positive,
        "largest_eigenvalue": float(eigen[0]), "tolerance": tolerance,
        "boundary_gap": float(eigen[31] - eigen[32]) if positive > 32 else None}

def evaluate(truth, weights):
    top = np.full((8, len(truth), 20), -1, dtype=np.int32)
    scores = np.full(top.shape, np.nan)
    diagnostics = {}
    for fold, (train, query, matrices) in weights.items():
        count = truth[train].sum(0)
        eligible = np.flatnonzero((count >= 1) & (count * 10 <= len(train)))
        if len(eligible) < 20:
            raise RuntimeError("INSUFFICIENT_ELIGIBLE_GENES")
        u, diagnostics[str(fold)] = teacher(truth[train].astype(float))
        projected = 1 / len(train) + ((matrices[5] - 1 / len(train)) @ u) @ u.T
        y = truth[np.ix_(train, eligible)].astype(float)
        for method, matrix in enumerate(matrices + [projected]):
            if method == 0:
                predicted = np.broadcast_to(count[eligible] / len(train), (len(query), len(eligible)))
            else:
                predicted = np.clip(matrix @ y, 0, 1)
            assert np.isfinite(predicted).all()
            selected = np.argsort(-predicted, axis=1, kind="stable")[:, :20]
            top[method, query] = eligible[selected]
            scores[method, query] = np.take_along_axis(predicted, selected, axis=1)
        diagnostics[str(fold)]["eligible_genes"] = len(eligible)
    assert (top >= 0).all()
    return top, scores, diagnostics

def recovered(truth, indices):
    return truth[np.arange(len(truth))[None, :, None], indices].sum(2, dtype=np.int64)

def save_ranks(path, aligned, aligned_scores, nulls, null_scores, maps):
    temp = path.with_suffix(".tmp.npz")
    np.savez_compressed(temp, methods=np.array(METHODS), aligned_indices=aligned,
        aligned_scores=aligned_scores, null_indices=np.asarray(nulls),
        null_scores=np.asarray(null_scores), null_assignments=maps)
    temp.replace(path)

def synthetic():
    rng = np.random.default_rng(31)
    a, b, y = rng.normal(size=(40, 8)), rng.normal(size=(5, 8)), rng.normal(size=(40, 55))
    w = ridge(a, b, 100)
    u, _ = teacher(y)
    yc = y - y.mean(0)
    _, _, vt = np.linalg.svd(yc, full_matrices=False)
    expected = y.mean(0) + (w @ yc) @ vt[:32].T @ vt[:32]
    actual = (1 / len(a) + ((w - 1 / len(a)) @ u) @ u.T) @ y
    assert np.allclose(actual, expected, atol=1e-10)
    count = np.array([7, 7, 3, 7], dtype=np.int64)
    assert np.array_equal(np.argsort(-(count / 161), kind="stable"), [0, 1, 3, 2])
    print(json.dumps({"synthetic_projection_max_error": float(np.max(np.abs(actual - expected))),
                      "exact_count_tie_test": "PASS"}))

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    assert not (OUT / "run.json").exists(), "No replay or overwrite"
    started, cpu = time.perf_counter(), time.process_time()
    receipt = {"status": "running", "threads": 4, "completed_nulls": 0,
        "python": sys.executable, "numpy": np.__version__, "failure": None,
        "settings": {"threads": 4, "null_seed": 20261030, "bootstrap_seed": 20261031,
            "n_null": 49, "n_bootstrap": 2000, "teacher_rank": 32},
        "access": "Corrected exposed development arrays only; no63 held-out CGI or S2 values"}
    write(OUT / "run.json", receipt)
    try:
        freeze = json.loads((ROOT / "a_execution_freeze.json").read_text())
        for path, expected in freeze["sha256"].items():
            assert sha(path) == expected, f"Hash changed: {path}"
        receipt["freeze"] = freeze
        data = dict(np.load(SOURCE / "labels.npz", allow_pickle=False))
        compounds, truth, folds = data["compounds"], data["calls"], data["folds"]
        assert truth.shape == (231, 18415)
        chem = np.load(PARENT / "chemical_features.npz", allow_pickle=False)
        lookup = {c: i for i, c in enumerate(chem["compounds"])}
        x = chem["fingerprints"][[lookup[c] for c in compounds]].astype(float)
        pharmacology = np.load(ROOT / "pharmacology_features.npz", allow_pickle=False)
        assert np.array_equal(pharmacology["compounds"], compounds)
        k = pharmacology["features"].astype(float)
        data["annotation_available"] = k[:, -1].astype(bool)
        np.savez_compressed(OUT / "labels.npz", **data)
        mappings_archive = np.load(SOURCE / "permutation_assignments.npz", allow_pickle=False)
        mappings = mappings_archive[mappings_archive.files[0]]
        assert mappings.shape == (49, 231)
        np.savez_compressed(OUT / "permutation_assignments.npz", assignments=mappings)
        with threadpool_limits(limits=4):
            weights = operators(x, k, folds)
            aligned, aligned_scores, diagnostic = evaluate(truth, weights)
            nulls, null_scores, null_totals, null_diagnostics = [], [], [], []
            for number, mapping in enumerate(mappings, 1):
                permuted = truth[mapping]
                indices, scores, detail = evaluate(permuted, weights)
                nulls.append(indices); null_scores.append(scores); null_diagnostics.append(detail)
                total = recovered(permuted, indices).sum(1)
                null_totals.append(int(total[7] - total[:7].max()))
                save_ranks(OUT / "ranks.partial.npz", aligned, aligned_scores, nulls, null_scores, mappings)
                receipt["completed_nulls"] = number
                write(OUT / "run.json", receipt)
        hits = recovered(truth, aligned)
        totals = hits.sum(1)
        direct = int(np.argmax(totals[:7]))
        difference = hits[7] - hits[direct]
        gain_total = int(totals[7] - totals[direct])
        p = (1 + np.count_nonzero(np.array(null_totals) >= gain_total)) / 50
        groups = data["groups"]
        names = np.unique(groups)
        group_sum = np.array([difference[groups == g].sum() for g in names])
        group_n = np.array([np.count_nonzero(groups == g) for g in names])
        rng = np.random.default_rng(20261031)
        draws = rng.integers(0, len(names), size=(2000, len(names)))
        interval = np.quantile(group_sum[draws].sum(1) / (20 * group_n[draws].sum(1)), [.025, .975]).tolist()
        eligible_denominator = np.zeros(len(truth), dtype=np.int64)
        for train, query, _ in weights.values():
            count = truth[train].sum(0)
            eligible = (count >= 1) & (count * 10 <= len(train))
            eligible_denominator[query] = truth[np.ix_(query, np.flatnonzero(eligible))].sum(1)
        recall = np.divide(hits, eligible_denominator[None, :], out=np.zeros(hits.shape), where=eligible_denominator[None, :] > 0)
        summary = {"methods": METHODS, "precision": (hits / 20).tolist(), "recall": recall.tolist(),
            "mean_precision": dict(zip(METHODS, (totals / (20 * len(truth))).tolist())),
            "mean_recall": dict(zip(METHODS, recall.mean(1).tolist())), "recovered_totals": totals.tolist(),
            "candidate_method": METHODS[7], "best_direct_method": METHODS[direct],
            "selected_gain": gain_total / (20 * len(truth)), "selected_integer_gain": gain_total,
            "null_gains": (np.array(null_totals) / (20 * len(truth))).tolist(),
            "null_integer_gains": null_totals, "permutation_p": p,
            "oracle": (np.minimum(20, eligible_denominator) / 20).tolist(),
            "mean_oracle": float((np.minimum(20, eligible_denominator) / 20).mean()),
            "eligible_gene_counts": {f: d["eligible_genes"] for f, d in diagnostic.items()},
            "distinct_mappings": len(np.unique(mappings, axis=0)),
            "movable_compounds": int(np.any(mappings != np.arange(len(truth)), axis=0).sum()),
            "annotated_mean_precision": dict(zip(METHODS, (hits[:, data["annotation_available"]] / 20).mean(1).tolist()))}
        write(OUT / "summary.json", summary)
        write(OUT / "decision.json", {"status": "NO_HELD_OUT_RELEASE", "information_gate_pass": bool(gain_total > 0 and p <= .05),
            "held_out_release": False, "robust_benefit_established": False,
            "paired_scaffold_interval95": interval, "conditional_interval_above_zero": bool(interval[0] > 0)})
        save_ranks(OUT / "ranks.npz", aligned, aligned_scores, nulls, null_scores, mappings)
        write(OUT / "teacher_diagnostics.json", {"aligned": diagnostic, "nulls": null_diagnostics})
        receipt.update(status="complete", shapes={"calls": list(truth.shape), "ranks": list(aligned.shape)})
    except Exception as exc:
        receipt.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
        write(OUT / "decision.json", {"status": "NO_HELD_OUT_RELEASE", "information_gate_pass": False,
            "held_out_release": False, "robust_benefit_established": False,
            "conditional_interval_above_zero": False, "failure": receipt["failure"]})
        raise
    finally:
        receipt.update(wall_seconds=time.perf_counter() - started, cpu_seconds=time.process_time() - cpu)
        write(OUT / "run.json", receipt)

if __name__ == "__main__":
    if "--synthetic" in sys.argv:
        synthetic()
    else:
        main()
