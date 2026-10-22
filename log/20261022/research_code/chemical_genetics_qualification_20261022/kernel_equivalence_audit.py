"""Verify the proposed Gaussian gene writeback's exact kernel normal form."""
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/chemical_genetics_qualification/mechanism_review"
target = OUT / "KERNEL_AUDIT_RESULT.json"
if target.exists():
    raise FileExistsError(target)
rng = np.random.default_rng(20261022)
features = rng.normal(size=(7, 9))
factor = rng.normal(size=(7, 7))
covariance = factor @ factor.T + np.eye(7)
dependent = features.copy()
dependent[:, 3:6] = dependent[:, :3]
lowrank = factor[:, :2] @ factor[:, :2].T
cases = {
    "full_rank": (features, covariance),
    "dependent_drug_features": (dependent, covariance),
    "zero_features": (np.zeros_like(features), covariance),
    "rank_deficient_covariance": (features, lowrank),
}
prior = rng.normal(size=7)
observations = rng.normal(size=5)
queries = np.array([0, 2, 4, 6, 8])
rows = []
for name, (s, c) in cases.items():
    sq = s[:, queries]
    k = s.T @ c @ s
    for noise in (0.01, 0.1, 1.0):
        residual = observations - sq.T @ prior
        alpha = np.linalg.solve(k[np.ix_(queries, queries)] + noise * np.eye(5), residual)
        gene_prediction = s.T @ (prior + c @ sq @ alpha)
        kernel_prediction = s.T @ prior + k[:, queries] @ alpha
        batch_error = float(np.max(np.abs(gene_prediction - kernel_prediction)))
        sequential_errors = []
        for order in (range(5), reversed(range(5))):
            mean, cov = prior.copy(), c.copy()
            for j in order:
                x = sq[:, j]
                cx = cov @ x
                gain = cx / (noise + x @ cx)
                mean = mean + gain * (observations[j] - x @ mean)
                cov = cov - np.outer(gain, cx)
            sequential_errors.append(float(np.max(np.abs(s.T @ mean - kernel_prediction))))
        rows.append({"case": name, "noise_variance": noise,
                     "batch_max_abs_error": batch_error,
                     "sequential_max_abs_errors": sequential_errors})

noise = 0.1
wrong_k = features.T @ features
right_k = features.T @ covariance @ features
sq = features[:, queries]
residual = observations - sq.T @ prior
wrong = wrong_k[:, queries] @ np.linalg.solve(
    wrong_k[np.ix_(queries, queries)] + noise * np.eye(5), residual)
right = right_k[:, queries] @ np.linalg.solve(
    right_k[np.ix_(queries, queries)] + noise * np.eye(5), residual)
negative_error = float(np.max(np.abs(right - wrong)))
passed = all(r["batch_max_abs_error"] < 1e-9 and
             max(r["sequential_max_abs_errors"]) < 1e-9 for r in rows) and negative_error > 1e-3
result = {"scope": "SYNTHETIC_ALGEBRA_ONLY", "seed": 20261022,
          "cases": rows, "negative_control_max_abs_error": negative_error,
          "passed": passed, "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          "protocol_sha256": hashlib.sha256((OUT / "KERNEL_AUDIT_PROTOCOL.md").read_bytes()).hexdigest(),
          "source_response_values_used": False}
target.write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps({"passed": passed, "cases": len(rows),
                  "max_batch_error": max(r["batch_max_abs_error"] for r in rows),
                  "max_sequential_error": max(max(r["sequential_max_abs_errors"]) for r in rows),
                  "negative_control_error": negative_error}))
raise SystemExit(0 if passed else 1)
