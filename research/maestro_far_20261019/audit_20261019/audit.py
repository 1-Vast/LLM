"""Read-only reproduction of the exposed FAR arena; writes only this directory.

Run with the maestro Python. Never invokes a predecessor stage writer or opens
PRISM 24Q2. Synthetic interventions diagnose dependency, not biological effects.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import pickle
import sys
from pathlib import Path

if "--original-env" not in sys.argv:
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("MKL_NUM_THREADS", "1")
import numpy as np
import pandas as pd
from rdkit import Chem
from threadpoolctl import threadpool_info

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
sys.path.insert(0, str(STUDY))
import far_core as fc
import far_data
import far_run as fr


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot():
    return {p.name: digest(p) for p in STUDY.iterdir() if p.is_file()}


def saved_statistics():
    """Independent family-sum implementation, matching the frozen RNG schedule."""
    out = {}
    for stage in ("search", "select", "test", "vault"):
        with np.load(STUDY / f"records_{stage}.npz") as z:
            folds = sorted({int(k.split("|")[0]) for k in z.files})
            families = {f: np.unique(z[f"{f}|fam"], return_inverse=True) for f in folds}
            weights = {f: np.zeros((4000, len(families[f][0]))) for f in folds}
            rng = np.random.default_rng(fr.SEED)
            for b in range(4000):
                for f in folds:
                    uf = families[f][0]
                    picked, counts = np.unique(rng.choice(uf, len(uf)), return_counts=True)
                    weights[f][b, np.searchsorted(uf, picked)] = counts
            for metric in ("U", "hits"):
                saved = json.loads((STUDY / f"CONTRASTS_{stage}_{metric}.json").read_text())
                suffix = "|hits" if metric == "hits" else ""
                err = 0.0
                values = {}
                for name, expected in saved["contrasts"].items():
                    a, b = name.split("-")
                    a, b = a.replace(".", "|"), b.replace(".", "|")
                    obs, boot = 0.0, np.zeros(4000)
                    for f in folds:
                        delta = z[f"{f}|{a}{suffix}"] - z[f"{f}|{b}{suffix}"]
                        obs += delta.sum() / len(folds)
                        sums = np.bincount(families[f][1], weights=delta)
                        boot += weights[f] @ sums / len(folds)
                    actual = [float(obs), *np.percentile(boot, [2.5, 97.5, 5]).tolist()]
                    target = [expected["diff"], *expected["ci95"], expected["lcb95_one_sided"]]
                    err = max(err, float(np.max(np.abs(np.array(actual) - target))))
                    values[name] = dict(diff=actual[0], ci95=actual[1:3], lcb95_one_sided=actual[3])
                out[f"{stage}_{metric}"] = dict(n_contrasts=len(values), max_abs_error=err, values=values)
    return out


def metadata_audit(D):
    ti = pd.read_csv(far_data.RAW / "primary-screen-replicate-collapsed-treatment-info.csv")
    ti = ti[ti.column_name.str.endswith("::HTS")].copy()
    ti["cmp"] = ti.broad_id.str[:13]
    ti = ti.drop_duplicates("cmp")
    with np.load(far_data.L1 / "derived/blockq_phase1.npz", allow_pickle=True) as q:
        keys = q["pert_ids"].astype(str)
    ids = set(ti.cmp)
    exact = ids & set(keys)
    token = ids & {s for row in keys for s in row.split("|")}
    joined = ti[ti.smiles.fillna("").str.contains(",", regex=False)]
    distinct_structures, bad_first = [], []
    for row in joined.itertuples():
        structures = set()
        for s in row.smiles.split(","):
            mol = Chem.MolFromSmiles(s.strip())
            if mol is not None:
                structures.add(Chem.MolToSmiles(mol))
        if len(structures) > 1:
            distinct_structures.append(row.cmp)
        if Chem.MolFromSmiles(row.smiles.split(", ")[0]) is None:
            bad_first.append(row.cmp)
    labels = ti.set_index("name").moa
    all_labels = {}
    for name, fold in zip(D["drug"], D["fold"]):
        if name not in labels.index:
            continue
        value = labels.loc[name]
        if not isinstance(value, str):
            continue
        for lab in value.split(","):
            all_labels.setdefault(lab.strip(), set()).add(int(fold))
    crossing = {k: sorted(v) for k, v in all_labels.items() if k and len(v) > 1}
    return dict(dev_drugs=len(D["drug"]), families=len(set(D["family"])),
                folds=np.bincount(D["fold"]).tolist(), lines=len(D["lines"]),
                exact_broad_matches=len(exact), token_broad_matches=len(token),
                matches_missed_by_joined_ids=sorted(token - exact),
                comma_smiles_rows=len(joined), comma_rows_with_multiple_structures=distinct_structures,
                comma_rows_with_unparseable_first=bad_first, all_moa_labels_crossing_folds=crossing)


def synthetic_dependencies():
    rng = np.random.default_rng(123)
    n = 150
    T = rng.uniform(0.01, 0.4, (n, n))
    T = (T + T.T) / 2
    np.fill_diagonal(T, 1)
    D = dict(T=T, X=rng.normal(size=(n, 3, 12)), Y=rng.normal(size=(n, 8)),
             fold=np.repeat(np.arange(5), 30))
    changes = {}
    for stage, fold, poison_fold in (("search", 0, 2), ("test", 3, 4)):
        c = fc.Campaign(D, fold, fc.REFS[stage][fold])
        poison = dict(D, Y=D["Y"].copy())
        mask = D["fold"] == poison_fold
        poison["Y"][mask] += rng.normal(0, 10, (mask.sum(), 8))
        p = fc.Campaign(poison, fold, fc.REFS[stage][fold])
        changes[f"{stage}_base_change_when_fold_{poison_fold}_outcomes_changed"] = float(np.max(np.abs(c.base - p.base)))
    # Primary deterministic acquisition must not consult candidate L1000 values.
    c = fc.Campaign(D, 3, fc.REFS["test"][3])
    altered = dict(D, X=D["X"].copy())
    altered["X"][D["fold"] == 3] *= -1
    p = fc.Campaign(altered, 3, fc.REFS["test"][3])
    changes["preassay_feature_change_when_query_l1000_changed"] = float(np.max(np.abs(fc.value_features(c, 0) - fc.value_features(p, 0))))
    return changes


def replay(D):
    model = json.loads((STUDY / "MODEL.json").read_text())
    try:
        with (STUDY / "VALUE_MODEL.pkl").open("rb") as handle:
            vm = pickle.load(handle)
        model_error = None
    except ModuleNotFoundError as exc:
        vm, model_error = None, str(exc)
    beta = np.array(model["coef"])
    fmodel = lambda c, j: 1 / (1 + np.exp(-(fc.false_prog_features(c, j) @ beta + model["intercept"])))
    vmodel = lambda c, j: np.clip(vm.predict(fc.value_features(c, j)), 0, None)
    result = {}
    for stage in ("select", "test"):
        saved = np.load(STUDY / f"records_{stage}.npz")
        rng = np.random.default_rng(fr.SEED)
        tables = []
        famids = {v: i for i, v in enumerate(np.unique(D["family"]))}
        for fold, refs in fc.REFS[stage].items():
            c = fc.Campaign(D, fold, refs)
            c.famid = np.array([famids[f] for f in D["family"][c.q]])
            tables.append(fr.pairs(c, rng))
            costs, errors, levels = {}, {}, {}
            runs = [(p, "gate") for p in fr.POLICIES] + [(p, r) for p in ("exploit", "far") for r in fr.REPAIRS if r != "gate"]
            for policy, repair in runs:
                if policy == "far2" and vm is None:
                    continue
                u, hits, fraction = fc.run_policy(c, policy, repair, model["tau"], vmodel if policy == "far2" else fmodel, fr.SEED + fold)
                key = f"{fold}|{policy}|{repair}"
                errors[f"{policy}.{repair}"] = max(float(np.max(np.abs(u - saved[key]))), float(np.max(np.abs(hits - saved[key + "|hits"]))))
                levels[f"{policy}.{repair}"] = dict(replayed=float(u.sum()), saved=float(saved[key].sum()), difference=float(u.sum() - saved[key].sum()))
                costs[f"{policy}.{repair}"] = dict(mean_measured_compounds=fraction * len(c.q), pool_fraction=fraction)
            sizes = np.bincount(c.slice)
            result[f"{stage}_{fold}"] = dict(query=len(c.q), reference=len(c.r), lines=len(c.lines),
                slice_sizes=sizes.tolist(), min_possible_4_slice_cost=int(np.sort(sizes)[:4].sum()),
                max_possible_4_slice_cost=int(np.sort(sizes)[-4:].sum()),
                max_record_error=max(errors.values()), record_errors=errors, costs=costs,
                utility_levels=levels, far2_replay_error=model_error)
            print(stage, fold, "replayed", "max error", max(errors.values()), flush=True)
        X, y, fam = zip(*tables)
        X, y, fam = np.vstack(X), np.concatenate(y), np.concatenate(fam)
        atlas = json.loads((STUDY / f"ATLAS_{stage}.json").read_text())
        auc_error = 0.0
        for k, name in enumerate(("domain_distance", "neighbour_dispersion", "model_disagreement")):
            actual = fr.boot_auc(X[:, k], y, fam)
            expected = atlas["signatures"][name]
            auc_error = max(auc_error, float(np.max(np.abs(np.array(actual) - [expected["auroc"], expected["lcb90"], expected["ucb90"]]))))
        result[f"{stage}_atlas_max_error"] = auc_error
    return result


def main():
    before = snapshot()
    frozen = json.loads((STUDY / "FREEZE.json").read_text())["hashes"]
    out = dict(environment=dict(python=sys.executable, versions={p: importlib.metadata.version(p) for p in ("numpy", "pandas", "scipy", "scikit-learn", "rdkit")}, threadpools=threadpool_info()),
               frozen_hash_matches={p: fr.sha(STUDY / p) == h for p, h in frozen.items()})
    print("Recomputing all saved contrasts", flush=True)
    out["statistics"] = saved_statistics()
    out["synthetic_dependencies"] = synthetic_dependencies()
    print("Loading dev arena only", flush=True)
    D = far_data.load("dev")
    out["metadata"] = metadata_audit(D)
    out["replay"] = replay(D)
    out["predecessor_files_unchanged"] = before == snapshot()
    out["predecessor_sha256"] = before
    out["scope"] = "Exposed development data only; select/test replay; saved search/vault statistics only. No model retraining or new outcome tier."
    out["input_sha256"] = {str(p.relative_to(far_data.EXT)): digest(p) for p in (
        far_data.RAW / "primary-screen-replicate-collapsed-treatment-info.csv",
        far_data.RAW / "primary-screen-replicate-collapsed-logfold-change.csv",
        far_data.L1 / "derived/blockq_phase1.npz")}
    out["checks"] = dict(frozen_hashes=all(out["frozen_hash_matches"].values()),
        originals_unchanged=out["predecessor_files_unchanged"],
        all_saved_statistics_match=max(v["max_abs_error"] for v in out["statistics"].values()) < 1e-9,
        all_replayed_records_match=all((v["max_record_error"] if isinstance(v, dict) else v) < 1e-9 for v in out["replay"].values()))
    name = "RESULTS_original_env.json" if "--original-env" in sys.argv else "RESULTS.json"
    (HERE / name).write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out["checks"]), flush=True)


if __name__ == "__main__":
    main()
