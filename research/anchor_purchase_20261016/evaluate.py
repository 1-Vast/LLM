"""Frozen qualification/headroom diagnostic; never a purchase-policy experiment."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
os.environ.setdefault("MKL_NUM_THREADS", "2")
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RAW = ROOT / "data/external/prism_19q4/raw"
META = HERE / "metadata"
OUT = HERE / "artifacts"
sys.path.insert(0, str(ROOT / "src"))
from maestro.hit_triage import CompoundIdentity, OutcomeSeal
from maestro.campaign_budget import CampaignBudget
from virtual_cell.knowledge_transfer import ANALOGUE_PARAMS

SEED = 20261016
ANCHORS = ["ACH-000219", "ACH-000681", "ACH-000019", "ACH-000552"]
CANDIDATES = ["line_mean", "chemical_neighbour", "ungated_neighbour"]
BUDGET = CampaignBudget(4, 1, 0, "hypothetical confirmation unit")


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(4 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def jsonl(path, rows):
    with Path(path).open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, allow_nan=False) + "\n")


def bundle_members(pooling, screen, line):
    pools = pooling.loc[(pooling.screen_id == screen) & (pooling.row_name == line), "pool_id"].dropna().unique()
    return sorted(set(pooling.loc[(pooling.screen_id == screen) & pooling.pool_id.isin(pools), "row_name"].astype(str)))


def prepare():
    """Metadata only: no response matrices or prediction arrays are opened."""
    if (HERE / "FREEZE.json").exists():
        raise FileExistsError("freeze exists; do not rewrite a completed design")
    META.mkdir(exist_ok=True)
    split = pd.read_csv(ROOT / "research/presage_transfer_20261016/SPLIT.csv")
    treatment = pd.read_csv(RAW / "secondary-screen-replicate-treatment-info.csv")
    treatment["core"] = treatment.broad_id.str[:13]
    treatment["replicate"] = treatment.column_name.str.extract(r"_X([123])(?:_|:)")[0]
    eligible = treatment.loc[(treatment.screen_id == "HTS002") & (treatment.dose == 2.5)
                             & (treatment.perturbation_type == "experimental_treatment")
                             & treatment.replicate.notna() & treatment.core.isin(split.core)].copy()
    rows = []
    for core, group in eligible.groupby("core", sort=True):
        for _, option in group.groupby(["broad_id", "compound_plate", "well"], sort=True):
            if set(option.replicate) != {"1", "2", "3"} or len(option) != 3:
                continue
            row = option.sort_values("replicate").iloc[0].to_dict()
            row.update({"x" + rep: option.loc[option.replicate == rep, "column_name"].iloc[0] for rep in ("1", "2", "3")})
            rows.append(row)
            break
    population = pd.DataFrame(rows).merge(split, on="core", validate="one_to_one").sort_values("core").reset_index(drop=True)
    for row in population.itertuples():
        CompoundIdentity(row.core, row.connectivity)
    for key in ("connectivity", "family_component"):
        assert population.groupby(key).fold.nunique().max() == 1
    population.to_csv(META / "population.csv", index=False)
    cells = pd.read_csv(RAW / "secondary-screen-cell-line-info.csv")
    cells = cells.loc[cells.depmap_id.notna() & cells.passed_str_profiling.astype(str).str.lower().eq("true")]
    cells = cells.loc[~cells.row_name.isin(ANCHORS)].sort_values("row_name")
    assert not cells.row_name.duplicated().any()
    cells.to_csv(META / "contexts.csv", index=False)
    pooling = pd.read_csv(RAW / "secondary-screen-pooling-info.csv")
    bundles = [{"screen": screen, "anchor": anchor,
                "all_rows": bundle_members(pooling, screen, anchor)}
               for screen in sorted(pooling.screen_id.unique()) for anchor in ANCHORS]
    write(META / "bundles.json", bundles)
    sizes = pooling.groupby(["screen_id", "pool_id"]).row_name.nunique()
    audit = {
        "qualification": "BLOCKED_INDEPENDENT_ENDPOINT", "historical_replay_A": "NOT_EXECUTED",
        "hypothetical_deployment_B": "offset and information-oracle cost diagnostics only; no actual saving",
        "population": {"campaigns": len(population), "contexts": len(cells),
                       "connectivity_groups": population.connectivity.nunique(),
                       "family_connectivity_components": population.family_component.nunique(),
                       "fold_counts": population.fold.value_counts().sort_index().to_dict(),
                       "eligible_treatment_metadata_cores": eligible.core.nunique(),
                       "excluded_incomplete_metadata_triplets": sorted(set(eligible.core) - set(population.core)),
                       "rule": "HTS002; exact 2.5uM; experimental; canonical complete metadata X1/X2/X3; prior split census",
                       "ascertainment": "historically selected PRISM secondary compounds, not unbiased primary population",
                       "availability_filter": False, "identity": "full Broad batch -> core -> existing connectivity/family component; DepMap contexts",
                       "excluded_anchor_contexts": ANCHORS},
        "lineage": {"platform": "PRISM pooled barcoded viability", "dose_uM": 2.5, "duration_hours": None,
                    "duration_note": "HTS002 column IDs do not encode duration; no per-treatment duration authenticated; do not borrow MTS010 120H encoding",
                    "readout": "ComBat-corrected log2 viability relative to DMSO",
                    "anchor_or_reference": "X1", "terminal": ["X2", "X3"],
                    "replicate_batch_plate_well": "metadata/population.csv; X detection plates in column IDs",
                    "culture_start_ids": None, "independent_culture_proven": False,
                    "shared_processing": ["outlier filtering", "SSMD filtering", "control barcodes per well/detection plate",
                                          "same-cell/plate DMSO", "per-treatment ComBat across pool-replicate batches"],
                    "MTS010": "technical redo, excluded; not independent confirmation",
                    "raw_signal_before_ComBat": "not cached; cannot undo shared preprocessing",
                    "missing_values": "unknown: unavailable or filtered; no all-attempt assay failure labels"},
        "acquisition": {"primary_scalar_entry": "collapsed, not authentic separately purchasable action",
                        "full_pool_inventory": "metadata/bundles.json, includes controls and failed-identity rows",
                        "pool_size_min": int(sizes.min()), "pool_size_max": int(sizes.max()),
                        "pool_size_mean": float(sizes.mean()),
                        "screen_rows": pooling.screen_id.value_counts().to_dict(),
                        "minimum_batch_controls_failures_price": "unqualified; no historical economic replay"},
        "exposure": [{"source": "PRISM19Q4 primary/collapsed secondary", "status": "previously exposed development",
                      "studies": ["knowledge_reality_20261013", "selective_hit_triage_20261013", "presage_transfer_20261016", "historical repeat audits"]},
                     {"source": "secondary replicate-level X1/X2/X3", "status": "same historically exposed release; first diagnostic read after current freeze; not fresh confirmation"},
                     {"source": "CTRP historical", "status": "previously exposed; raw archive not cached; not reacquired"},
                     {"source": "GDSC2 fitted", "status": "cache directory empty; no retrieval"},
                     {"source": "GCP", "status": "different histone endpoint, exposed; not substituted"},
                     {"source": "PRISM24Q2", "status": "sealed, not opened"}],
        "legal_information": {"predecision": "identity, chemical/target/MoA metadata, existing folds, training responses only",
                              "reference_diagnostic": "full X1 explicitly nondeployable positive reference",
                              "terminal": "outer query X2/X3 unavailable to model/selector; released after nomination lock"},
        "missing_requirement": "authenticated independent culture-start terminal viability measurements with separate processing/controls, compound IDs and all-attempt bundle/control/replicate costs",
    }
    write(HERE / "DATA_AUDIT.json", audit)
    files = [HERE / n for n in ("PROTOCOL.md", "NOVELTY.md", "DATA_AUDIT.json", "evaluate.py", "verify.py", "test_science.py")]
    files += sorted(META.glob("*"))
    files += [RAW / n for n in ("secondary-screen-replicate-treatment-info.csv", "secondary-screen-cell-line-info.csv",
                               "secondary-screen-pooling-info.csv", "secondary-screen-logfold-change.csv",
                               "primary-screen-readme.txt", "secondary-screen-readme.txt")]
    files += [ROOT / n for n in ("research/presage_transfer_20261016/SPLIT.csv", "src/virtual_cell/knowledge_transfer.py",
                               "src/maestro/hit_triage.py", "src/maestro/campaign_budget.py")]
    write(HERE / "FREEZE.json", {"stage": "development; qualification failed before policy fitting",
                                "created_utc": pd.Timestamp.now(tz="UTC").isoformat(),
                                "inputs": {p.relative_to(ROOT).as_posix(): digest(p) for p in files}})
    print(json.dumps(audit["population"], indent=2))


def verify_freeze():
    freeze = json.loads((HERE / "FREEZE.json").read_text())
    for name, expected in freeze["inputs"].items():
        if digest(ROOT / name) != expected:
            raise ValueError("freeze_mismatch:" + name)


def ranks(scores, k):
    return np.argsort(np.where(np.isfinite(scores), scores, np.inf), axis=1, kind="stable")[:, :k]


def terminal(x2, x3):
    known = np.isfinite(x2) & np.isfinite(x3)
    hit = known & ((x2 + x3) / 2 <= -1) & (x2 < 0) & (x3 < 0)
    return known, hit


def utility(scores, known, hit, k=4):
    choice = ranks(scores, k)
    return np.take_along_axis(hit, choice, axis=1).sum(1), (~np.take_along_axis(known, choice, axis=1)).sum(1)


def features(population):
    from rdkit import Chem, RDLogger
    from rdkit.Chem import rdFingerprintGenerator
    RDLogger.DisableLog("rdApp.*")
    gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    fp = []
    tokens = []
    for row in population.itertuples():
        mol = Chem.MolFromSmiles(str(row.smiles).split(",")[0].strip())
        if mol is None:
            raise ValueError("invalid_metadata_smiles:" + row.core)
        fp.append(gen.GetFingerprintAsNumPy(mol))
        tokens.append({prefix + token.strip() for prefix, value in (("target:", row.target), ("moa:", row.moa))
                       if pd.notna(value) for token in str(value).split(",") if token.strip()})
    vocab = sorted(set().union(*tokens))
    bits = np.array([[t in row for t in vocab] for row in tokens], dtype=float)
    result = []
    for matrix in (np.array(fp, dtype=float), bits):
        intersection = matrix @ matrix.T
        result.append(intersection / np.maximum(matrix.sum(1)[:, None] + matrix.sum(1) - intersection, 1e-12))
    return result


def mean_finite(y):
    valid = np.isfinite(y)
    return np.nansum(y, axis=0) / np.maximum(valid.sum(0), 1)


def predict(y, similarities, train, query):
    """All fitting/donor access is explicitly indexed by train."""
    mean = mean_finite(y[train])
    output = {"line_mean": np.broadcast_to(mean, (len(query), y.shape[1])).copy()}
    neighbours = []
    for similarity, key in zip(similarities, ("chem", "know")):
        k, power, floor = ANALOGUE_PARAMS[key]
        local = similarity[np.ix_(query, train)]
        order = np.argsort(-local, axis=1, kind="stable")[:, :min(k, len(train))]
        weight = np.take_along_axis(local, order, axis=1)
        weight = np.where(weight > floor, weight ** power, 0)
        donor = y[train][order]
        den = np.einsum("nk,nkl->nl", weight, np.isfinite(donor))
        num = np.einsum("nk,nkl->nl", weight, np.nan_to_num(donor))
        neighbours.append(np.where(den > 0, num / np.maximum(den, 1e-12), mean))
    output["chemical_neighbour"] = neighbours[0]
    output["ungated_neighbour"] = (neighbours[0] + neighbours[1]) / 2
    return output


def interval(values, clusters):
    groups, inverse = np.unique(clusters, return_inverse=True)
    sums = np.bincount(inverse, weights=values)
    sizes = np.bincount(inverse)
    rng = np.random.default_rng(SEED)
    draws = rng.integers(len(groups), size=(2000, len(groups)))
    estimates = sums[draws].sum(1) / sizes[draws].sum(1)
    return [float(v) for v in np.quantile(estimates, [.025, .975])]


def correlation_rows(a, b):
    finite = np.isfinite(a) & np.isfinite(b)
    count = np.maximum(finite.sum(1), 1)
    aa = np.where(finite, a, 0)
    bb = np.where(finite, b, 0)
    aa = np.where(finite, aa - aa.sum(1)[:, None] / count[:, None], 0)
    bb = np.where(finite, bb - bb.sum(1)[:, None] / count[:, None], 0)
    den = np.linalg.norm(aa, axis=1) * np.linalg.norm(bb, axis=1)
    return np.divide((aa * bb).sum(1), den, out=np.zeros(len(a)), where=den > 0)


def run():
    wall, cpu = time.perf_counter(), time.process_time()
    verify_freeze()
    OUT.mkdir(exist_ok=True)
    pop = pd.read_csv(META / "population.csv")
    cells = pd.read_csv(META / "contexts.csv").row_name.to_numpy(str)
    # First response read: after freeze verification. No primary/pathway outcomes.
    selected_columns = pop[["x1", "x2", "x3"]].to_numpy().ravel().tolist()
    response = pd.read_csv(RAW / "secondary-screen-logfold-change.csv", usecols=lambda c: c.startswith("Unnamed") or c == "" or c in selected_columns, index_col=0)
    repeats = [response.reindex(index=cells, columns=pop["x" + str(r)]).T.to_numpy(float) for r in (1, 2, 3)]
    # Scalar anchor is separate from all terminal contexts, and not used to fit.
    anchor = response.reindex(index=[ANCHORS[0]], columns=pop.x1).to_numpy(float).ravel()
    x1, x2, x3 = repeats
    known, hit = terminal(x2, x3)
    count = np.isfinite(x2).astype(int) + np.isfinite(x3)
    y = np.divide(np.nan_to_num(x2) + np.nan_to_num(x3), count,
                  out=np.full_like(x2, np.nan), where=count > 0)
    fold = pop.fold.to_numpy()
    clusters = pop.family_component.to_numpy(str)
    with threadpool_limits(limits=2):
        similarity = features(pop)
        predictions = {name: np.zeros_like(y) for name in CANDIDATES}
        strong = np.zeros_like(y)
        probabilities = np.zeros_like(y)
        fitting = []
        for outer in range(5):
            query = np.flatnonzero(fold == outer)
            train = np.flatnonzero(fold != outer)
            valid = np.flatnonzero(fold == (outer + 1) % 5)
            inner = np.flatnonzero((fold != outer) & (fold != (outer + 1) % 5))
            assert not set(clusters[train]) & set(clusters[query])
            inner_predictions = predict(y, similarity, inner, valid)
            scores = [int(utility(inner_predictions[n], known[valid], hit[valid])[0].sum()) for n in CANDIDATES]
            winner = CANDIDATES[int(np.argmax(scores))]
            fitted = predict(y, similarity, train, query)
            for name in CANDIDATES:
                predictions[name][query] = fitted[name]
            strong[query] = fitted[winner]
            probabilities[query] = hit[train].sum(0) / np.maximum(known[train].sum(0), 1)
            # Mutation test: hidden query outcomes cannot affect any fitted score.
            altered = y.copy()
            altered[query] = 123456
            checked = predict(altered, similarity, train, query)
            assert all(np.array_equal(fitted[name], checked[name]) for name in CANDIDATES)
            fitting.append({"outer": outer, "inner_validation": (outer + 1) % 5,
                            "candidate_inner_hits": dict(zip(CANDIDATES, scores)), "selected": winner,
                            "train_cores": pop.core.iloc[train].tolist(), "query_cores": pop.core.iloc[query].tolist(),
                            "heldout_mutation_invariant": True})
    rng = np.random.default_rng(SEED)
    perm = np.arange(len(pop))
    for _, group in pop.groupby(["fold", "compound_plate"], sort=True):
        ids = group.index.to_numpy()
        perm[ids] = rng.permutation(ids)
    offset = np.nan_to_num(anchor)
    shuffled_offset = np.nan_to_num(anchor[perm])
    assert np.array_equal(ranks(strong, 4), ranks(strong + offset[:, None], 4))
    assert np.array_equal(ranks(strong, 4), ranks(strong + shuffled_offset[:, None], 4))
    # Lock every diagnostic choice before accessing selected terminal outcomes.
    arms = {**predictions, "strong_selected": strong, "repeat_X1_reference": x1,
            "shuffled_X1_reference": x1[perm]}
    choices = []
    for name, score in arms.items():
        for i, row in pop.iterrows():
            choices.append({"arm": name, "core": row.core, "fold": int(row.fold), "group": row.family_component,
                            "anchor_cost": 0., "confirmation_count": 4, "modeled_spend": 4.,
                            "priced_comparable": name not in ("repeat_X1_reference", "shuffled_X1_reference"),
                            "nominations": cells[ranks(score[i:i+1], 4)[0]].tolist()})
    for ratio in (.25, 1., 2.):
        k = math.floor(4 - ratio)
        spent = BUDGET.require_feasible(k, 0, other_cost=ratio)
        for i, row in pop.iterrows():
            choices.append({"arm": f"offset_only_cost_{ratio:g}", "core": row.core, "fold": int(row.fold),
                            "group": row.family_component, "anchor_cost": ratio,
                            "confirmation_count": k, "modeled_spend": spent, "unspent": 4 - spent,
                            "priced_comparable": True, "anchor_context": ANCHORS[0],
                            "anchor_observed": bool(np.isfinite(anchor[i])),
                            "nominations": cells[ranks(strong[i:i+1] + offset[i], k)[0]].tolist()})
    jsonl(OUT / "choices.jsonl", choices)
    locked = (OUT / "choices.jsonl").read_bytes()
    canonical_digest = hashlib.sha256(locked.replace(b"\r\n", b"\n")).hexdigest()
    seal = OutcomeSeal({"protocol": hashlib.sha256((HERE / "PROTOCOL.md").read_bytes().replace(b"\r\n", b"\n")).hexdigest()}, canonical_digest)
    token = seal.release({"protocol": (HERE / "PROTOCOL.md").read_bytes()}, locked)
    records = ({"core": pop.core.iloc[i], "context": cell,
                "x2": float(x2[i, j]) if np.isfinite(x2[i, j]) else None,
                "x3": float(x3[i, j]) if np.isfinite(x3[i, j]) else None}
               for i in range(len(pop)) for j, cell in enumerate(cells))
    jsonl(OUT / "terminal_records.jsonl", records)
    np.savez_compressed(OUT / "scores.npz", cores=pop.core.to_numpy(str), contexts=cells,
                        strong=strong, x1=x1, anchor=anchor, permutation=perm, probabilities=probabilities)
    write(OUT / "fit_provenance.json", fitting)
    base_hits, base_unknown = utility(strong, known, hit)
    metrics = {}
    per_campaign = pop[["core", "connectivity", "family_component", "fold"]].copy()
    for name, score in arms.items():
        hits, unknown = utility(score, known, hit)
        per_campaign[name + "_hits"] = hits
        per_campaign[name + "_unknown"] = unknown
        difference = hits - base_hits
        metrics[name] = {"known_hits": int(hits.sum()), "unknown_nominations": int(unknown.sum()),
                         "hit_bounds": [int(hits.sum()), int((hits + unknown).sum())],
                         "mean_hits_per_campaign": float(hits.mean()),
                         "difference_vs_strong_per_campaign": float(difference.mean()),
                         "paired_group_bootstrap_95": interval(difference, clusters),
                         "difference_missing_bounds_per_campaign": [float((hits - base_hits - base_unknown).mean()), float((hits + unknown - base_hits).mean())],
                         "raw_mean_profile_pearson": float(correlation_rows(score, y).mean())}
    for ratio in (.25, 1., 2.):
        k = math.floor(4 - ratio)
        h, u = utility(strong, known, hit, k)
        name = f"offset_only_cost_{ratio:g}"
        per_campaign[name + "_hits"], per_campaign[name + "_unknown"] = h, u
        metrics[name] = {"known_hits": int(h.sum()), "unknown_nominations": int(u.sum()),
                         "hit_bounds": [int(h.sum()), int((h + u).sum())],
                         "difference_vs_strong_per_campaign": float((h - base_hits).mean()),
                         "paired_group_bootstrap_95": interval(h - base_hits, clusters),
                         "confirmation_count": k, "anchor_cost": ratio,
                         "modeled_total_spend": float(len(pop) * (k + ratio)), "unspent": float(len(pop) * (4 - k - ratio))}
    per_campaign.to_csv(OUT / "per_campaign.csv", index=False)
    oracle = {}
    total_known = hit.sum(1)
    total_unknown = (~known).sum(1)
    for k in (4, 3, 2, 1, 0):
        best = np.minimum(total_known, k)
        upper = np.minimum(total_known + total_unknown, k)
        oracle[str(k)] = {"known_hit_bound": int(best.sum()), "missing_upper_bound": int(upper.sum()),
                          "gain_vs_strong_per_campaign": float((best - base_hits).mean()),
                          "paired_group_bootstrap_95": interval(best - base_hits, clusters),
                          "fraction_campaigns_known_improvement_possible": float((best > base_hits).mean())}
    gains = [4 - int(k) for k, value in oracle.items() if value["known_hit_bound"] > int(base_hits.sum())]
    brier = float(((probabilities - hit) ** 2)[known].mean())
    bins, ece = [], 0.
    for lo, hi in zip(np.arange(0, 1, .2), np.arange(.2, 1.01, .2)):
        mask = known & (probabilities >= lo) & ((probabilities < hi) if hi < .999 else (probabilities <= hi))
        n = int(mask.sum())
        if n:
            predicted, observed = float(probabilities[mask].mean()), float(hit[mask].mean())
            ece += n / known.sum() * abs(predicted - observed)
            bins.append({"lo": float(lo), "hi": float(hi), "n": n, "predicted": predicted, "observed": observed})
    repeat_h = per_campaign.repeat_X1_reference_hits.to_numpy()
    shuffle_h = per_campaign.shuffled_X1_reference_hits.to_numpy()
    result = {"status": "BLOCKED_INDEPENDENT_ENDPOINT", "confirmation_level": "DEVELOPMENT_ONLY_TECHNICAL_REPEAT",
              "VALUE": "UNESTABLISHED_INDEPENDENT_ENDPOINT", "POLICY": "NOT_EVALUATED_QUALIFICATION_GATE",
              "population": {"campaigns": len(pop), "contexts": len(cells), "groups": len(set(clusters)),
                             "terminal_known_pairs": int(known.sum()), "terminal_unknown_pairs": int((~known).sum()),
                             "terminal_known_hits": int(hit.sum())},
              "arms": metrics, "fitting": [{k: v for k, v in row.items() if k not in ("train_cores", "query_cores")} for row in fitting],
              "repeat_signal": {"repeat_vs_shuffle_hits_per_campaign": float((repeat_h - shuffle_h).mean()),
                                "paired_group_bootstrap_95": interval(repeat_h - shuffle_h, clusters),
                                "x2_vs_x3_mean_profile_pearson": float(correlation_rows(x2, x3).mean()),
                                "shuffle_fraction_moved": float((perm != np.arange(len(pop))).mean()),
                                "qualification": "shared preprocessing; empirical positive reference, not independent or a ceiling"},
              "calibration": {"model": "training-only context hit prevalence", "Brier_known_only": brier,
                              "ECE_5_fixed_bins_known_only": float(ece), "bins": bins,
                              "limitation": "all scores other than prevalence are LFC; no conditional-model calibration certificate; unknowns excluded only for this descriptive metric"},
              "headroom_oracle": oracle, "max_integer_anchor_cost_with_positive_known_oracle_gain": max(gains) if gains else None,
              "minimum_useful_gain": .10, "practical_gain_test": "NOT_TESTABLE_WITH_UNQUALIFIED_ENDPOINT",
              "offset_rank_invariant": True, "seal_release_token": token,
              "not_executed": ["authentic priced bundle replay", "independent terminal validation", "conditional residual transfer",
                               "fixed/random/information anchor models", "learned triage", "selective purchase policy", "LLM", "pathway expansion"],
              "operational_wall_seconds": time.perf_counter() - wall, "operational_cpu_seconds": time.process_time() - cpu}
    write(HERE / "RESULTS.json", result)
    retrieval = json.loads((HERE / "source_review/RETRIEVAL.json").read_text())
    write(HERE / "COSTS.json", {"paid_API_calls": 0, "purchased_experiments": 0, "GPU": False,
                               "additional_public_success_payload_bytes": sum(v.get("bytes", 0) for v in retrieval.values()),
                               "public_failed_requests": sum("error" in v for v in retrieval.values()),
                               "retrieval_request_wall_seconds_sum_not_elapsed": sum(v["wall_seconds"] for v in retrieval.values()),
                               "retrieval_limit_bytes": 300_000_000, "cpu_limit_seconds": 7200,
                               "evaluation_cpu_seconds": result["operational_cpu_seconds"], "evaluation_wall_seconds": result["operational_wall_seconds"],
                               "operational_limit_note": "evaluation process measured; metadata/literature inspection and test overhead separately recorded in VERIFICATION.json, earlier interactive CPU not instrumented",
                               "experimental_model": {"type": "hypothetical B only", "campaign_budget": 4,
                                                      "confirmation": "one assumed unit inclusive of two readouts/controls, unknown attempts still charged",
                                                      "anchor_ratios": [.25, 1, 2], "turnaround": "0 assumed; no binding deadline",
                                                      "real_bundle_prices": None, "actual_laboratory_saving": None,
                                                      "technical_full_profile_reference": "unpriced; never a budget-matched purchasable arm"}})
    print(json.dumps({"status": result["status"], "population": result["population"], "arms": metrics, "headroom": oracle}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare-freeze", action="store_true")
    args = parser.parse_args()
    if args.prepare_freeze:
        prepare()
    else:
        run()
