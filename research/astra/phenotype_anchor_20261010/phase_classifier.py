"""Cell-level phase readout: softmax regression X_hvg -> obs phase, fitted on reference DMSO cells.

Validation: (a) 30-line fit scored on the other 10 qualified reference lines' DMSO cells; (b) the
final fit scored on stored raw treated cells (domain shift). The final classifier uses all
qualified reference lines. No held-out file is read.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import analysis as A  # noqa: E402

PHASES = ("G1", "S", "G2M")


def cells(files):
    X, y, X_t, y_t = [], [], [], []
    for f in files:
        receipt = json.loads((HERE / "obs" / f"{f}.json").read_text(encoding="utf-8"))
        names = receipt["categories"]["phase"]
        remap = np.array([PHASES.index(n) for n in names])
        b = np.load(A.CACHE / "expression" / f / "basal.npz")
        X.append(b["x"])
        y.append(remap[b["phase"]])
        t = np.load(A.CACHE / "expression" / f / "treated.npz")
        plan = json.loads((HERE / "expression" / "plans" / f"{f}.json").read_text(encoding="utf-8"))
        phase = np.load(A.CACHE / "obs" / f"{f}.npz")["phase"]
        treated_groups = [g for g in plan["groups"] if not g["basal"]]
        rows = np.concatenate([np.asarray(g["rows"][:4]) for g in treated_groups])
        X_t.append(t["raw"].astype(np.float32))
        y_t.append(remap[phase[rows]])
    return np.concatenate(X), np.concatenate(y), np.concatenate(X_t), np.concatenate(y_t)


def fit(X, y, l2=1e-4, epochs=300, seed=20261010):
    torch.manual_seed(seed)
    mu, sd = X.mean(0), X.std(0) + 1e-3
    Xt = torch.tensor((X - mu) / sd)
    yt = torch.tensor(y)
    W = torch.zeros((X.shape[1], len(PHASES)), requires_grad=True)
    b = torch.zeros(len(PHASES), requires_grad=True)
    opt = torch.optim.LBFGS([W, b], lr=1, max_iter=epochs, line_search_fn="strong_wolfe")

    def closure():
        opt.zero_grad()
        loss = torch.nn.functional.cross_entropy(Xt @ W + b, yt) + l2 * (W ** 2).sum()
        loss.backward()
        return loss
    opt.step(closure)
    return {"W": W.detach().numpy(), "b": b.detach().numpy(), "mu": mu.astype(np.float32), "sd": sd.astype(np.float32)}


def accuracy(model, X, y):
    logits = ((X - model["mu"]) / model["sd"]) @ model["W"] + model["b"]
    pred = logits.argmax(1)
    prob = np.exp(logits - logits.max(1, keepdims=True))
    prob /= prob.sum(1, keepdims=True)
    return {"accuracy": float((pred == y).mean()), "n": int(len(y)),
            "observed_fraction": [float((y == k).mean()) for k in range(3)],
            "mean_predicted_probability": prob.mean(0).astype(float).tolist()}


def main():
    files, _ = A.qualified_reference()
    order = sorted(files, key=lambda f: hashlib.sha256(f.encode()).hexdigest())
    test_files, train_files = order[:10], order[10:]
    X, y, _, _ = cells(train_files)
    Xv, yv, Xvt, yvt = cells(test_files)
    split = fit(X, y)
    report = {"validation_lines": test_files, "dmso_heldout_lines": accuracy(split, Xv, yv),
              "treated_heldout_lines": accuracy(split, Xvt, yvt)}
    Xa, ya, Xta, yta = cells(files)
    final = fit(Xa, ya)
    report["final_train_dmso"] = accuracy(final, Xa, ya)
    report["final_on_treated_cells"] = accuracy(final, Xta, yta)
    np.savez(HERE / "phase_classifier.npz", phases=np.array(PHASES), **final)
    report["sha256"] = hashlib.sha256((HERE / "phase_classifier.npz").read_bytes()).hexdigest()
    (HERE / "PHASE_CLASSIFIER.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
