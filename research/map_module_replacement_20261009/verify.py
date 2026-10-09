"""Independent residual arithmetic, inner selection and paid replay checks."""
import hashlib
import json
import time
from pathlib import Path

import numpy as np
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import rdMolDescriptors
from scipy.stats import t
from threadpoolctl import threadpool_limits

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "outputs/map_module_replacement_20261009/response"
PACKET = ROOT / "research/astra/boundary_acquisition_20261007/packet2"
ARMS = ("molecule", "knowledge", "Morgan", "permutedknowledge")
ETAS = (0., .25, .5, 1.)


def equal(actual, expected):
    np.testing.assert_allclose(actual, expected, atol=1e-12, rtol=1e-10)


def top(mean):
    return sorted(range(len(mean)), key=lambda i: (-mean[i], i))[:5]


def prior(a, train, cell):
    available = a["availability_B"][train]
    weights = np.where(available, a["precision_B"][train], 0.)
    mean = np.sum(weights * np.where(available, a["train_B"][train], 0.), axis=0) / weights.sum(0)
    support = a["state_available_B"][train]
    centre = np.where(support, a["state_B"][train], 0.).sum(0) / support.sum(0)
    deviation = np.where(a["state_available_B"][cell], a["state_B"][cell] - centre, 0.)
    return mean + .5 * deviation


def offset(a, train):
    valid = (a["availability_A"] & a["availability_B"])[train]
    return np.where(valid, a["train_A"][train] - a["train_B"][train], 0.).sum(0) / valid.sum(0)


def kernels(records, features):
    groups = {}
    for index, record in enumerate(records):
        groups.setdefault((record["cid"], record["smiles"]), []).append(index)
    identities = sorted(groups)
    order = np.random.default_rng(20261009).permutation(len(identities))
    shuffled = np.empty_like(features["knowledge1024"])
    for target, source in zip(identities, order):
        shuffled[groups[target]] = features["knowledge1024"][groups[identities[source]][0]]
    fingerprints = []
    RDLogger.DisableLog("rdApp.warning")
    for row in records:
        bits = np.zeros(2048)
        fp = rdMolDescriptors.GetMorganFingerprintAsBitVect(Chem.MolFromSmiles(row["smiles"]), 2, nBits=2048)
        DataStructs.ConvertToNumpyArray(fp, bits)
        fingerprints.append(bits)
    result = {}
    for arm, values in zip(ARMS, [features["molecule256"], features["knowledge1024"], np.array(fingerprints), shuffled]):
        values = np.asarray(values, dtype=float)
        values = values / np.linalg.norm(values, axis=1)[:, None]
        matrix = np.zeros((len(records), len(records)))
        for i, left in enumerate(records):
            for j, right in enumerate(records):
                if (left["dose"], left["unit"]) == (right["dose"], right["unit"]):
                    matrix[i, j] = np.dot(values[i], values[j])
        np.fill_diagonal(matrix, 1.)
        assert np.linalg.eigvalsh(matrix).min() > -1e-5
        result[arm] = matrix
    return result


def fit(a, train, candidate_kernels):
    cells = [i for i in train if (a["availability_A"][i] & a["availability_B"][i]).all()]
    residuals = []
    for cell in cells:
        keep = [i for i in train if i != cell]
        mean = prior(a, keep, cell)
        residuals.append(np.r_[a["train_B"][cell] - mean, a["train_A"][cell] - mean - offset(a, keep)])
    residuals = np.array(residuals)
    raw = residuals.T @ residuals / len(cells)
    sd = np.sqrt(np.diag(raw))
    standardized = np.divide(residuals, sd, out=np.zeros_like(residuals), where=sd > 0)
    n = a["train_B"].shape[1]
    rho = np.clip((standardized[:, :n] * standardized[:, n:]).mean(), -1., 1.)
    covariances = {"empirical": raw}
    for arm, matrix in candidate_kernels.items():
        blocks = np.kron(np.array([[1., rho], [rho, 1.]]), matrix)
        covariances[arm] = blocks * np.outer(sd, sd)
    for arm, matrix in covariances.items():
        covariances[arm] = .5 * (matrix + np.diag(np.diag(matrix))) + np.eye(len(matrix)) * 1e-12
    return covariances, offset(a, train), cells, float(rho)


def schedule(mean):
    rank = sorted(range(len(mean)), key=lambda i: (-mean[i], i))
    midpoint = (mean[rank[4]] + mean[rank[5]]) / 2
    return sorted(range(len(mean)), key=lambda i: (abs(mean[i] - midpoint), i))[:8]


def update(mean, covariance, indices, values):
    coordinates = len(mean) // 2 + np.array(indices)
    cross = covariance[:, coordinates]
    marginal = covariance[np.ix_(coordinates, coordinates)]
    return mean + cross @ np.linalg.solve(marginal, np.array(values) - mean[coordinates])


def verify():
    started = time.perf_counter()
    for filename in ("FREEZE.json", "VERIFY_FREEZE.json"):
        freeze = json.loads((HERE / filename).read_text())
        for name, expected in freeze["inputs"].items():
            assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
    a = dict(np.load(PACKET / "training_arrays.npz"))
    public = dict(np.load(PACKET / "public_prior.npz"))
    private = dict(np.load(PACKET / "evaluator_private.npz"))
    records = json.loads((ROOT / "outputs/knowledge_layer_validation_20261009/AUDIT.json").read_text())["records"]
    features = dict(np.load(ROOT / "outputs/paper_01286/released_test/FEATURES.npz"))
    candidate_kernels = kernels(records, features)
    models = dict(np.load(OUT / "MODELS.npz"))
    predictions = dict(np.load(OUT / "PREDICTIONS.npz"))
    choices = json.loads((OUT / "MODEL_CHOICES.json").read_text())
    results = json.loads((OUT / "RESULTS.json").read_text())
    for scope, choice in choices.items():
        train = choice["train"]
        covariance, shift, cells, rho = fit(a, train, candidate_kernels)
        assert cells == choice["residual_cells"]
        equal(rho, choice["rho"])
        equal(shift, models[scope + "__offset"])
        equal(covariance["empirical"], models[scope + "__empirical"])
        if scope.startswith("ref"):
            cell = int(scope[3:])
            assert cell not in train
            equal(prior(a, train, cell), predictions[scope])
        scores = {arm: {eta: [] for eta in ETAS} for arm in ARMS}
        for fold in range(3):
            keep = [i for i in train if i % 3 != fold]
            inner_covariance, inner_offset, inner_cells, _ = fit(a, keep, candidate_kernels)
            recorded = choice["inner_folds"][fold]
            assert keep == recorded["train"] and inner_cells == recorded["residual_cells"]
            for cell in recorded["held"]:
                assert cell not in keep and cell % 3 == fold
                p = prior(a, keep, cell)
                bought = schedule(p)
                for arm in ARMS:
                    for eta in ETAS:
                        c = (1 - eta) * inner_covariance["empirical"] + eta * inner_covariance[arm]
                        m = update(np.r_[p, p + inner_offset], c, bought, a["train_A"][cell, bought])[:len(p)]
                        scores[arm][eta].append(np.mean((m - a["train_B"][cell]) ** 2))
        for arm in ARMS:
            loss = {eta: float(np.mean(values)) for eta, values in scores[arm].items()}
            equal(list(loss.values()), [choice["arms"][arm]["inner_posterior_mse"][str(eta)] for eta in ETAS])
            eta = min(ETAS, key=lambda value: (loss[value], value))
            assert eta == choice["arms"][arm]["eta"]
            equal((1 - eta) * covariance["empirical"] + eta * covariance[arm], models[scope + "__" + arm])
        print("Independent fits and tuning:", scope, flush=True)
    for row in results:
        context = row["context"]
        p = predictions[context]
        scope = context if context.startswith("ref") else "targets"
        if context.startswith("ref"):
            cell = int(context[3:]); y_a, y_b = a["train_A"][cell], a["train_B"][cell]
        else:
            equal(p, public[context + "__M2"])
            y_a, y_b = private[context + "__A"], private[context + "__B"]
        assert row["initial_selected"] == top(p)
        if row["policy"] == "no_screen":
            expected = p
            assert row["purchased_A"] == [] and row["cost"] == 5
        else:
            indices = row["purchased_A"]
            assert len(indices) == len(set(indices)) == 8 and row["cost"] == 13
            if row["policy"] == "shared":
                assert indices == schedule(p)
            history = row["history"]
            for step, index in enumerate(indices):
                assert history[step]["purchased_A"] == index
                assert history[step]["cumulative_A_cost"] == step + 1
                equal(history[step]["observed_A"], y_a[index])
            covariance = models[scope + "__" + row["arm"]]
            shift = models[scope + "__offset"]
            expected = update(np.r_[p, p + shift], covariance, indices, y_a[indices])[:len(p)]
        equal(expected, row["posterior_mean_B"])
        assert top(expected) == row["selected"]
        equal(y_b[row["selected"]].sum(), row["terminal_B"])
        equal(np.mean((expected - y_b) ** 2), row["posterior_mse"])
        equal(row["terminal_B"] - y_b[top(p)].sum(), row["delta_vs_no_screen"])
    summary = json.loads((OUT / "SUMMARY.json").read_text())
    for scope in ("reference", "exposed_targets"):
        rows = [r for r in results if r["scope"] == scope]
        knowledge = {r["context"]: r["terminal_B"] for r in rows if r["policy"] == "shared" and r["arm"] == "knowledge"}
        for control in ("empirical", *ARMS):
            if control == "knowledge":
                continue
            base = [r for r in rows if r["policy"] == "shared" and r["arm"] == control]
            delta = np.array([knowledge[r["context"]] - r["terminal_B"] for r in base])
            radius = t.ppf(.975, len(delta) - 1) * delta.std(ddof=1) / np.sqrt(len(delta))
            recorded = summary["paired_shared_comparisons"][scope][control]
            equal(delta.mean(), recorded["delta_B"])
            equal([delta.mean() - radius, delta.mean() + radius], recorded["paired_context_95CI"])
    payload = dict(status="PASS", model_scopes=len(choices), results=len(results),
                   paid_observations=sum(len(r["purchased_A"]) for r in results),
                   checks=["Frozen input and verifier hashes", "Independent full-dimensional kernels and dose masks",
                           "All outer and inner residuals, variances, offsets and eta choices",
                           "All paid observation identities, costs and batch posteriors",
                           "All committed top-five choices, RNA utility and MSE", "Paired-context interval arithmetic"],
                   seconds=time.perf_counter() - started,
                   limits="Development arithmetic only; graph/pretraining exposure and shared RNA endpoints preclude independent biological, functional or LLM benefit certification.")
    with (OUT / "VERIFIED.json").open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2); stream.write("\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    with threadpool_limits(limits=1):
        verify()
