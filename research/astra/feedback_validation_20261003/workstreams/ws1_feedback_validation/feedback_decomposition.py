"""WS1 step 2: decompose in-context feedback into offset, drug-in-line and pairing components.

File summary
- Path: research/astra/feedback_validation_20261003/workstreams/ws1_feedback_validation/feedback_decomposition.py
- Purpose: under the frozen budget, rounds and seeds, compare static retrieval, static transfer
  models (ridge prior as frozen; a gradient-boosted prior on the same features), offset-only,
  drug-in-line-only and full feedback, within-round feedback-shuffle controls and random; record
  every arm's purchases so independent-validation outcomes can be joined later.
- Core points:
  - The frozen TransferWorld is built once per line and never modified; variants only change
    how its joint posterior (lambda, u) is used, or which values are fed to it.
  - The campaign loop replicates agent.run_campaign's shared rounds and exploit branch exactly
    (same _top tie-break RNG consumption); parity with frozen receipts is checked in the output.
  - Shuffle controls permute what the model is told within the batch bought in one round of
    one line; hits are always scored on true labels.
- Interfaces: run the file with PYTHONPATH="src;." --library oneil|almanac --out NAME.
- Depends on: numpy, scipy, sklearn, research.certified_discovery (frozen; imported only).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np
from scipy import special

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))
from research.certified_discovery import agent  # noqa: E402
from research.certified_discovery.screens import CACHE, load_library, sha256  # noqa: E402
from research.certified_discovery.world import TransferWorld, WorldConfig  # noqa: E402

HERE = Path(__file__).resolve().parent
LIBS = {"oneil": CACHE / "oneil_v1.npz", "almanac": CACHE / "almanac_v1.npz"}
SPEC = agent.CampaignSpec(kappa=2)  # frozen confirmatory spec: 0.10 budget, 4 rounds
RANDOM_SEEDS = 20
SHUFFLE_SEEDS = 10


class Posterior:
    """The frozen world's in-context residual model with a replaceable prior and usage mode."""

    def __init__(self, world: TransferWorld, prior: np.ndarray | None = None):
        self.w = world
        self.prior = world.prior_target.copy() if prior is None else np.asarray(prior, float)
        self.Z = world.Z_target
        self.Zu = self.Z[:, 1:]
        self.A = world.A
        self.prior_drug_var = np.einsum("ij,jk,ik->i", self.Zu, self.A[1:, 1:], self.Zu)
        self.prior_var = np.einsum("ij,jk,ik->i", self.Z, self.A, self.Z) + world.s_noise
        self.Au_inv = np.linalg.inv(self.A[1:, 1:])

    def predict(self, measured, values, mode: str):
        w = self.w
        if mode == "static" or len(measured) == 0:
            return self.prior.copy(), self.prior_var.copy()
        measured = np.asarray(measured, int)
        resid = np.asarray(values, float) - self.prior[measured]
        if mode == "drug_nooffset":
            Zm = self.Zu[measured]
            cov = np.linalg.inv(self.Au_inv + Zm.T @ Zm / w.s_noise)
            eff = cov @ (Zm.T @ resid) / w.s_noise
            return self.prior + self.Zu @ eff, np.einsum("ij,jk,ik->i", self.Zu, cov, self.Zu) + w.s_noise
        Zm = self.Z[measured]
        cov = np.linalg.inv(w.A_inv + Zm.T @ Zm / w.s_noise)
        eff = cov @ (Zm.T @ resid) / w.s_noise
        if mode == "full":
            return self.prior + self.Z @ eff, np.einsum("ij,jk,ik->i", self.Z, cov, self.Z) + w.s_noise
        if mode == "offset":
            return self.prior + eff[0], cov[0, 0] + self.prior_drug_var + w.s_noise
        if mode == "drug":
            return (self.prior + self.Zu @ eff[1:],
                    w.s_line + np.einsum("ij,jk,ik->i", self.Zu, cov[1:, 1:], self.Zu) + w.s_noise)
        raise ValueError(mode)


def scorer(post: Posterior, mode: str, acquisition: str):
    thr = post.w.lib.threshold

    def score(idx, values):
        mean, var = post.predict(idx, values, mode)
        return mean if acquisition == "mean" else special.ndtr((mean - thr) / np.sqrt(var))
    return score


class Shuffled:
    """Feed the model labels (or residuals) permuted within each round's purchased batch."""

    def __init__(self, inner, prior: np.ndarray, kind: str, seed: int):
        self.inner, self.prior, self.kind = inner, prior, kind
        self.rng = np.random.default_rng([seed, 4242])
        self.fed: dict[int, float] = {}

    def __call__(self, idx, values):
        idx = np.asarray(idx, int)
        new = np.array([i for i in idx if i not in self.fed], int)
        if new.size:
            v = np.asarray(values, float)[np.searchsorted(idx, new)]
            perm = self.rng.permutation(new.size)
            if self.kind == "label":
                fed = v[perm]
            else:
                r = v - self.prior[new]
                fed = self.prior[new] + r[perm]
            self.fed.update(zip(new.tolist(), fed.tolist()))
        return self.inner(idx, np.array([self.fed[i] for i in idx.tolist()], float))


def campaign(lib, world, score, seed, spec=SPEC, diagnostics=None):
    """Replicates agent.run_campaign's shared rounds and exploit branch; returns purchases."""
    rows = world.rows
    truth = lib.y[rows]
    hits = truth > lib.threshold
    n = rows.size
    budget = int(math.ceil(spec.budget_fraction * n))
    batch = int(math.ceil(budget / spec.rounds))
    rng = np.random.default_rng(seed)
    measured = np.zeros(n, bool)
    rounds = []
    for _ in range(spec.rounds - 1):
        idx = np.flatnonzero(measured)
        k = int(min(batch, budget - measured.sum()))
        chosen = agent._top(score(idx, truth[idx]), ~measured, k, rng)
        measured[chosen] = True
        rounds.append(chosen)
    idx = np.flatnonzero(measured)
    last = int(budget - measured.sum())
    final = score(idx, truth[idx])
    pick = agent._top(final, ~measured, last, rng)
    rounds.append(pick)
    out = {"hits": int(sum(hits[r].sum() for r in rounds)), "per_round": [int(hits[r].sum()) for r in rounds],
           "purchases": [r.tolist() for r in rounds]}
    if diagnostics is not None:
        # prediction quality on the still-unmeasured candidates at the final decision
        rest = np.flatnonzero(~measured)
        for name, fn in diagnostics.items():
            mean = fn(idx, truth[idx])
            err = mean[rest] - truth[rest]
            out[f"pred_{name}_rmse"] = float(np.sqrt(np.mean(err ** 2)))
            out[f"pred_{name}_r"] = float(np.corrcoef(mean[rest], truth[rest])[0, 1])
            top = rest[np.argsort(-mean[rest], kind="stable")[:last]]
            out[f"pred_{name}_top_last_hits"] = int(hits[top].sum())
    return out


def gbm_prior(world: TransferWorld) -> np.ndarray:
    from sklearn.ensemble import HistGradientBoostingRegressor

    model = HistGradientBoostingRegressor(max_iter=200, learning_rate=0.1, random_state=0)
    model.fit(world.X_history, world.lib.y[world.history_rows])
    return model.predict(world.X_target)


def run_line(task):
    library_path, line = task
    lib = load_library(Path(library_path))
    t0 = time.perf_counter()
    world = TransferWorld(lib, line, WorldConfig())
    build = time.perf_counter() - t0
    post = Posterior(world)
    out = {"line": lib.lines[line], "line_index": line, "candidates": int(world.rows.size),
           "line_hits": int((lib.y[world.rows] > lib.threshold).sum()), "rows": world.rows.tolist(),
           "s_line": world.s_line, "s_drug": world.s_drug, "s_noise": world.s_noise,
           "world_build_seconds": round(build, 3), "arms": {}}
    arms = out["arms"]
    seed = line

    def frozen(arm_obj):
        return lambda idx, values: arm_obj.scores(idx, values)

    arms["history"] = campaign(lib, world, frozen(agent.HistoryArm(world)), seed)
    arms["oracle"] = campaign(lib, world, frozen(agent.OracleArm(world)), seed)
    arms["random"] = [campaign(lib, world, frozen(agent.RandomArm(world.rows.size, s)), s) for s in range(RANDOM_SEEDS)]
    # frozen registered arms through the frozen classes (parity anchors)
    arms["frozen_wm_static"] = campaign(lib, world, frozen(agent.WorldArm(_StaticView(world), "wm_static")), seed)
    arms["frozen_wm_full"] = campaign(lib, world, frozen(agent.WorldArm(world, "wm_full")), seed)
    arms["frozen_wm_greedy"] = campaign(lib, world, frozen(agent.WorldArm(world, "wm_greedy", acquisition="mean")), seed)
    diag = {"static": lambda i, v: post.predict(i, v, "static")[0], "full": lambda i, v: post.predict(i, v, "full")[0]}
    for mode in ("static", "offset", "drug", "drug_nooffset", "full"):
        for acq in ("mean", "phit"):
            arms[f"{mode}_{acq}"] = campaign(lib, world, scorer(post, mode, acq), seed,
                                             diagnostics=diag if (mode, acq) == ("full", "mean") else None)
    for kind, tag in (("resid", "shufres"), ("label", "shuflab")):
        for acq in ("mean", "phit"):
            arms[f"{tag}_{acq}"] = [campaign(lib, world, Shuffled(scorer(post, "full", acq), post.prior, kind, s), seed)
                                    for s in range(SHUFFLE_SEEDS)]
    t1 = time.perf_counter()
    gbm = gbm_prior(world)
    out["gbm_fit_seconds"] = round(time.perf_counter() - t1, 3)
    gpost = Posterior(world, prior=gbm)
    hpost = Posterior(world, prior=world.X_target[:, 0])
    arms["gbm_static"] = campaign(lib, world, scorer(gpost, "static", "mean"), seed)
    arms["gbm_feedback_mean"] = campaign(lib, world, scorer(gpost, "full", "mean"), seed)
    arms["history_feedback_mean"] = campaign(lib, world, scorer(hpost, "full", "mean"), seed)
    truth = lib.y[world.rows]
    out["prior_quality"] = {
        name: {"r": float(np.corrcoef(p, truth)[0, 1]), "rmse": float(np.sqrt(np.mean((p - truth) ** 2)))}
        for name, p in (("ridge", world.prior_target), ("gbm", gbm), ("history", world.X_target[:, 0]))}
    out["seconds"] = round(time.perf_counter() - t0, 2)
    return out


class _StaticView:
    def __init__(self, world):
        self._w = world

    def posterior(self, measured, values):
        return self._w.prior_target.copy(), self._w.prior_var_target.copy()

    def p_hit(self, mean, var):
        return self._w.p_hit(mean, var)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--library", choices=sorted(LIBS), default="oneil")
    parser.add_argument("--out", required=True)
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--lines", default="all")
    args = parser.parse_args(argv)
    out = HERE / "receipts" / args.out
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    lib = load_library(LIBS[args.library])
    lines = range(len(lib.lines)) if args.lines == "all" else [int(x) for x in args.lines.split(",")]
    started = time.time()
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(run_line, [(str(LIBS[args.library]), li) for li in lines]))
    out.mkdir(parents=True)
    with open(out / "lines.jsonl", "w", encoding="utf-8", newline="\n") as handle:
        for r in results:
            handle.write(json.dumps(r) + "\n")
    manifest = {"library": lib.name, "library_sha256": sha256(LIBS[args.library]),
                "exposure": "development (exposed)" if args.library == "oneil" else
                "EXPLORATORY: ALMANAC already opened 2026-10-03T17:58:48; not confirmation",
                "spec": SPEC.__dict__, "random_seeds": RANDOM_SEEDS, "shuffle_seeds": SHUFFLE_SEEDS,
                "lines": len(results), "wall_seconds": round(time.time() - started, 1),
                "started": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(started)),
                "script_sha256": sha256(Path(__file__)),
                "frozen_sources": {n: sha256(ROOT / "research/certified_discovery" / n)
                                   for n in ("world.py", "agent.py", "screens.py", "replay.py")}}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(json.dumps({"lines": len(results), "wall_seconds": manifest["wall_seconds"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
