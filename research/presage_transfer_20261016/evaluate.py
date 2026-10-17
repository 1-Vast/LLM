"""Run the frozen, exposed-data P0 gate. No downloads or provider calls."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "4")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "4")
os.environ.setdefault("MKL_NUM_THREADS", "4")
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))
from virtual_cell.knowledge_transfer import ANALOGUE_PARAMS

RAW = ROOT / "data/external/prism_19q4/raw"
CENSUS = ROOT / "research/knowledge_reality_20261013/compounds.csv"
GMT = HERE / "source_review/Reactome_2022.gmt"
SEED, DIM = 20261016, 64
OUT = HERE / "artifacts"


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(4 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def input_paths():
    return [CENSUS, GMT, RAW / "primary-screen-replicate-collapsed-treatment-info.csv",
            RAW / "primary-screen-cell-line-info.csv",
            RAW / "primary-screen-replicate-collapsed-logfold-change.csv",
            ROOT / "src/virtual_cell/knowledge_transfer.py",
            HERE / "PROTOCOL.md", Path(__file__)]


def normalise(x):
    return x / np.maximum(np.linalg.norm(x, axis=1, keepdims=True), 1e-12)


def tokens(values):
    return sorted({t.strip() for v in values.dropna() for t in str(v).split(",") if t.strip()})


def prepare_metadata():
    """No outcome file is opened by this function."""
    census = pd.read_csv(CENSUS, dtype={"unit": str})
    info = pd.read_csv(RAW / "primary-screen-replicate-collapsed-treatment-info.csv")
    info["core"] = info.broad_id.str[:13]
    assert not info.column_name.duplicated().any()
    assert set(census.core) <= set(info.core)
    meta = info.sort_values("column_name").groupby("core")
    cores = census.core.to_numpy(str)
    targets = [tokens(meta.get_group(c).target) for c in cores]
    moas = [tokens(meta.get_group(c).moa) for c in cores]
    genes = sorted({g for row in targets for g in row})
    gi = {g: i for i, g in enumerate(genes)}
    pathways = [line.rstrip("\n").split("\t") for line in GMT.read_text().splitlines()]
    membership = np.zeros((len(genes), len(pathways)), np.float64)
    for j, row in enumerate(pathways):
        for g in set(row[2:]):
            if g in gi:
                membership[gi[g], j] = 1
    rng = np.random.default_rng(SEED)
    embedding = normalise(normalise(membership) @ rng.normal(size=(len(pathways), DIM)))
    have = membership.sum(1) > 0
    random = normalise(rng.normal(size=(len(genes), DIM))) * have[:, None]
    degree = np.zeros(len(genes), int)
    for row in targets:
        for g in row:
            degree[gi[g]] += 1
    strata = np.column_stack([have.astype(int), np.digitize(degree, [2, 5, 20]),
                             np.digitize(membership.sum(1), [2, 5, 20, 100])])
    # Connected components of existing families and compound connectivity units.
    parent = {f: f for f in census.family}
    def root(f):
        while parent[f] != f:
            parent[f] = parent[parent[f]]
            f = parent[f]
        return f
    for _, group in census.groupby("unit"):
        fs = sorted(set(group.family))
        for f in fs[1:]:
            a, b = sorted([root(fs[0]), root(f)])
            parent[b] = a
    clusters = np.array([root(f) for f in census.family])
    original = dict(zip(census.family, census.fold))
    folds = np.array([original[c] for c in clusters], int)
    for u in set(census.unit):
        assert len(set(folds[census.unit.to_numpy() == u])) == 1
    vocab = sorted({m for row in moas for m in row})
    mi = {m: i for i, m in enumerate(vocab)}
    moa = np.zeros((len(cores), len(vocab)))
    for i, row in enumerate(moas):
        for m in row:
            moa[i, mi[m]] = 1
    moa_features = normalise(moa) @ rng.normal(size=(len(vocab), DIM)) / np.sqrt(DIM)
    from rdkit import Chem, RDLogger
    from rdkit.Chem import rdFingerprintGenerator
    RDLogger.DisableLog("rdApp.*")
    fp = np.zeros((len(cores), 2048), np.float64)
    scaffolds = []
    from rdkit.Chem.Scaffolds import MurckoScaffold
    gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    for i, core in enumerate(cores):
        smiles = meta.get_group(core).smiles.dropna().iloc[0]
        mol = Chem.MolFromSmiles(str(smiles).split(",")[0].strip())
        if mol is None:
            raise ValueError(f"unparsable_census_structure:{core}")
        fp[i] = gen.GetFingerprintAsNumPy(mol)
        scaffolds.append(MurckoScaffold.MurckoScaffoldSmiles(mol=mol))
    chemistry = normalise(fp) @ rng.normal(size=(2048, DIM)) / np.sqrt(DIM)
    kinds = []
    for row in moas:
        text = " ".join(row).lower()
        inh = any(s in text for s in ("inhibitor", "antagonist", "blocker"))
        act = any(s in text for s in ("agonist", "activator", "opener")) and "antagonist" not in text
        kinds.append(3 if inh and act else 2 if "degrad" in text else 1 if act else 0 if inh else 4)
    # Target overlap tokens support the ungated neighbour comparator, not a biological prior.
    target_matrix = np.zeros((len(cores), len(genes)))
    for i, row in enumerate(targets):
        for g in row:
            target_matrix[i, gi[g]] = 1
    return dict(census=census, cores=cores, info=info, genes=genes, gi=gi, targets=targets,
                moas=moas, embedding=embedding, random=random, have=have, strata=strata,
                folds=folds, clusters=clusters, fp=fp, chemistry=chemistry, moa=moa_features,
                tokens=np.column_stack([target_matrix, moa]), scaffolds=np.array(scaffolds),
                kinds=kinds, pathways=len(pathways))


def drug_embedding(m, emb):
    result = np.zeros((len(m["cores"]), DIM))
    for i, row in enumerate(m["targets"]):
        covered = [m["gi"][g] for g in row if m["have"][m["gi"][g]]]
        if covered:
            result[i] = np.roll(emb[covered].mean(0), 11 * m["kinds"][i])
    return result


def permute_rows(embedding, strata, seed):
    rng = np.random.default_rng(seed)
    perm = np.arange(len(embedding))
    for key in sorted(set(map(tuple, strata))):
        group = np.flatnonzero(np.all(strata == key, axis=1))
        perm[group] = rng.permutation(group)
    return embedding[perm], perm


def ridge_predict(x, y, train, query, alpha):
    center, scale = x[train].mean(0), x[train].std(0)
    scale = np.where(scale > 1e-8, scale, 1)
    a, b = (x[train] - center) / scale, (x[query] - center) / scale
    mean = np.nanmean(y[train], axis=0)
    if not np.isfinite(mean).all():
        raise ValueError("line_has_no_training_measurement")
    residual = np.nan_to_num(y[train] - mean)
    beta = np.linalg.solve(a.T @ a + alpha * np.eye(x.shape[1]), a.T @ residual)
    return b @ beta + mean


def fit_predict(x, y, train, query, folds, outer):
    validation = (outer + 1) % 5
    inner = train[folds[train] != validation]
    valid = train[folds[train] == validation]
    losses = []
    for alpha in (1, 10, 100):
        p = ridge_predict(x, y, inner, valid, alpha)
        losses.append(float(np.nanmean((p - y[valid]) ** 2)))
    alpha = (1, 10, 100)[int(np.argmin(losses))]
    return ridge_predict(x, y, train, query, alpha), alpha


def neighbour(features, y, train, query, params):
    a, b = features[query], features[train]
    intersection = a @ b.T
    similarity = intersection / np.maximum(a.sum(1)[:, None] + b.sum(1) - intersection, 1e-12)
    k, power, floor = params
    order = np.argsort(-similarity, axis=1, kind="stable")[:, :k]
    weights = np.take_along_axis(similarity, order, axis=1)
    weights = np.where(weights > floor, weights ** power, 0)
    yy = y[train][order]
    den = np.einsum("nk,nkl->nl", weights, np.isfinite(yy))
    num = np.einsum("nk,nkl->nl", weights, np.nan_to_num(yy))
    mean = np.nanmean(y[train], axis=0)
    return np.where(den > 0, num / np.maximum(den, 1e-12), mean)


def scores(prediction, y):
    finite = np.isfinite(y)
    count = finite.sum(1)
    a = np.where(finite, prediction, 0)
    b = np.nan_to_num(y)
    a -= (a.sum(1) / np.maximum(count, 1))[:, None] * finite
    b -= (b.sum(1) / np.maximum(count, 1))[:, None] * finite
    correlation = (a * b).sum(1) / np.maximum(np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1), 1e-12)
    mse = np.where(count > 0, np.nansum((prediction - y) ** 2, axis=1) / np.maximum(count, 1), 0)
    return correlation, mse


def ranking(prediction, y, k):
    chosen = np.argsort(prediction, axis=1, kind="stable")[:, :k]
    selected = np.take_along_axis(y, chosen, axis=1)
    hits = np.isfinite(y) & (y <= -1)
    found = np.sum(np.isfinite(selected) & (selected <= -1), axis=1)
    return {"hits": int(found.sum()), "slots": int(len(y) * k),
            "yield": float(found.sum() / (len(y) * k)),
            "missing_selected": int((~np.isfinite(selected)).sum()),
            "false_exclusion_fraction": float(1 - found.sum() / max(hits.sum(), 1))}


def interval(difference, clusters):
    keys, index = np.unique(clusters, return_inverse=True)
    sums = np.bincount(index, weights=difference)
    counts = np.bincount(index)
    rng = np.random.default_rng(SEED)
    values = []
    for _ in range(2000):
        draw = rng.integers(len(keys), size=len(keys))
        values.append(sums[draw].sum() / counts[draw].sum())
    return [float(x) for x in np.quantile(values, [.025, .975])]


def verify_freeze():
    freeze = json.loads((HERE / "FREEZE.json").read_text())
    for name, expected in freeze["inputs"].items():
        if digest(ROOT / name) != expected:
            raise ValueError(f"freeze_mismatch:{name}")


def run():
    verify_freeze()
    started, cpu = time.perf_counter(), time.process_time()
    m = prepare_metadata()
    # The first outcome read in this study occurs only after freeze verification.
    raw = pd.read_csv(RAW / "primary-screen-replicate-collapsed-logfold-change.csv", index_col=0)
    line_meta = pd.read_csv(RAW / "primary-screen-cell-line-info.csv")
    lines = line_meta.loc[line_meta.depmap_id.notna(), "row_name"].astype(str).to_numpy()
    assert set(lines) <= set(raw.index)
    mapping = m["info"].set_index("column_name").core
    assert set(raw.columns) <= set(mapping.index)
    response = raw.reindex(lines).T.groupby(mapping.reindex(raw.columns).to_numpy()).mean()
    y = response.reindex(m["cores"]).to_numpy(float)
    base = np.column_stack([m["chemistry"], m["moa"]])
    prior = drug_embedding(m, m["embedding"])
    features = {"chemistry": m["chemistry"], "mechanism_class": m["moa"],
                "chemistry_moa": base, "matched_random_target": np.column_stack([base, drug_embedding(m, m["random"])]),
                "pathway": np.column_stack([base, prior]), "pathway_only": prior}
    movement = []
    for seed in range(20):
        emb, perm = permute_rows(m["embedding"], m["strata"], SEED + 100 + seed)
        movement.append(float(np.mean(perm[m["have"]] != np.flatnonzero(m["have"]))))
        features[f"permuted_{seed:02}"] = np.column_stack([base, drug_embedding(m, emb)])
    predictions = {name: np.zeros_like(y) for name in [*features, "chemical_neighbour", "ungated_neighbour", "fixed_fusion", "ungated_residual", "line_mean"]}
    tuning = {}
    overlap = []
    with threadpool_limits(limits=4):
        for outer in range(5):
            train, query = np.flatnonzero(m["folds"] != outer), np.flatnonzero(m["folds"] == outer)
            assert not set(m["clusters"][train]) & set(m["clusters"][query])
            tuning[str(outer)] = {}
            for name, x in features.items():
                p, alpha = fit_predict(x, y, train, query, m["folds"], outer)
                predictions[name][query] = p
                tuning[str(outer)][name] = alpha
            chem = neighbour(m["fp"], y, train, query, ANALOGUE_PARAMS["chem"])
            know = neighbour(m["tokens"], y, train, query, ANALOGUE_PARAMS["know"])
            predictions["chemical_neighbour"][query] = chem
            predictions["ungated_neighbour"][query] = (chem + know) / 2
            predictions["fixed_fusion"][query] = (predictions["pathway"][query] + predictions["chemistry_moa"][query]) / 2
            base_train = ridge_predict(base, y, train, train, tuning[str(outer)]["chemistry_moa"])
            residual_y = y.copy()
            residual_y[train] -= base_train
            residual = ridge_predict(prior, residual_y, train, query, 100)
            predictions["ungated_residual"][query] = predictions["chemistry_moa"][query] + residual
            predictions["line_mean"][query] = np.nanmean(y[train], axis=0)
            target_train = {g for i in train for g in m["targets"][i]}
            moa_train = {g for i in train for g in m["moas"][i]}
            scaffold_train = set(m["scaffolds"][train]) - {""}
            overlap.append({"fold": outer, "n": len(query),
                            "known_target": sum(bool(set(m["targets"][i]) & target_train) for i in query),
                            "known_moa": sum(bool(set(m["moas"][i]) & moa_train) for i in query),
                            "known_nonempty_scaffold": sum(m["scaffolds"][i] in scaffold_train for i in query)})
            print(f"completed fold {outer}: {len(query)} compounds", flush=True)
    OUT.mkdir(exist_ok=True)
    result, per_entity = {}, {}
    for name, p in predictions.items():
        r, mse = scores(p, y)
        per_entity[name] = r
        result[name] = {"mean_pearson": float(r.mean()), "mean_mse": float(mse.mean()),
                        "ranking": {str(k): ranking(p, y, k) for k in (1, 3, 5, 10)}}
    baselines = ["chemistry", "mechanism_class", "chemistry_moa", "matched_random_target",
                 "chemical_neighbour", "ungated_neighbour", "line_mean"]
    contrasts = {}
    for name in baselines:
        d = per_entity["pathway"] - per_entity[name]
        contrasts[name] = {"gain": float(d.mean()), "ci95": interval(d, m["clusters"])}
    real = result["pathway"]["mean_pearson"]
    null = [result[f"permuted_{i:02}"]["mean_pearson"] for i in range(20)]
    pvalue = (1 + sum(v >= real for v in null)) / 21
    passed = all(c["gain"] >= .01 and c["ci95"][0] > 0 for c in contrasts.values()) and pvalue <= 1 / 21
    source_manifest = {str(p.relative_to(ROOT)).replace("\\", "/"): {"sha256": digest(p), "bytes": p.stat().st_size} for p in input_paths()}
    write(HERE / "SOURCE_MANIFEST.json", source_manifest)
    split = pd.DataFrame({"core": m["cores"], "connectivity": m["census"].unit,
                          "family_component": m["clusters"], "fold": m["folds"]})
    split.to_csv(HERE / "SPLIT.csv", index=False)
    pd.DataFrame({"core": m["cores"], **per_entity}).to_csv(OUT / "per_compound.csv", index=False)
    np.savez_compressed(OUT / "predictions.npz", cores=m["cores"], lines=lines,
                        **{k: v.astype(np.float32) for k, v in predictions.items()})
    output = {"stage": "P0_EXPOSED_DEVELOPMENT", "verdict": "PASS" if passed else "NO_GO",
              "counts": {"compounds": len(y), "lines": len(lines), "family_components": len(set(m["clusters"])),
                         "genes": len(m["genes"]), "covered_genes": int(m["have"].sum()), "pathways": m["pathways"],
                         "covered_drugs": int(np.count_nonzero(np.linalg.norm(prior, axis=1))),
                         "missing_response_fraction": float((~np.isfinite(y)).mean())},
              "arms": result, "contrasts": contrasts, "correspondence_null": {"mean": float(np.mean(null)),
              "max": float(max(null)), "p": pvalue, "covered_gene_movement": movement},
              "tuning": tuning, "split_overlap": overlap,
              "costs": {"wall_seconds": time.perf_counter() - started, "cpu_seconds": time.process_time() - cpu,
                        "provider_calls": 0, "purchased_assays": 0, "paid_usd": 0,
                        "nomination_slots_are_scenarios": True},
              "not_run": ["P1_anchor_adaptation", "P2_joint_acquisition_revision", "LLM_structural_proposer", "P3_memory", "sealed_confirmation"],
              "artifact_sha256": {p.name: digest(p) for p in [HERE / "SPLIT.csv", OUT / "per_compound.csv", OUT / "predictions.npz"]}}
    write(HERE / "RESULTS.json", output)
    print(json.dumps({"verdict": output["verdict"], "counts": output["counts"], "contrasts": contrasts, "null_p": pvalue}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", action="store_true")
    args = parser.parse_args()
    if args.freeze:
        target = HERE / "FREEZE.json"
        if target.exists():
            raise ValueError("freeze_already_exists")
        write(target, {"stage": "exposed_development", "inputs": {str(p.relative_to(ROOT)).replace("\\", "/"): digest(p) for p in input_paths()}})
        print("Frozen; no response values read.")
    else:
        run()
