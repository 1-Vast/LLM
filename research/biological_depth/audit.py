"""Score out-of-fold predictions with the pre-registered biological-depth battery.

File summary
- Path: research/biological_depth/audit.py
- Purpose: compute B1-B8 and the ten anchors identically on observed shifts and on every arm's
  out-of-fold predictions, then apply the frozen verdict rules.
- Core points:
  - Centering always uses the systematic arm's out-of-fold reference, so it never contains the
    scored compound.
  - Anchors count against a model only when they hold in the observed data.
  - Every interval is a compound-cluster bootstrap.
- Run: python research/biological_depth/audit.py --prepared <dir> --cv <dir> --output <dir>
- Depends on: common.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

import common

LINES = ("A549", "K562", "MCF7")
TOP = 10000.0
ANNOTATED = {"latent_jepa_moa", "latent_jepa_moa_shuffled"}


def pearson(a: np.ndarray, b: np.ndarray) -> float:
    a, b = a - a.mean(), b - b.mean()
    denominator = np.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / denominator) if denominator > 1e-12 else 0.0


class Audit:
    def __init__(self, prepared: Path, cv: Path):
        self.conditions = pd.read_csv(prepared / "conditions.csv", index_col="condition_id")
        self.compounds = pd.read_csv(prepared / "compounds.csv").set_index("compound")
        self.genes = pd.read_csv(prepared / "genes.csv")
        shifts = np.load(prepared / "shifts.npz")
        self.y, self.rep1, self.rep2 = shifts["shift"], shifts["rep1"], shifts["rep2"]
        self.gene_sets = json.loads((prepared / "gene_sets.json").read_text())
        self.null = json.loads((prepared / "vehicle_null.json").read_text())
        self.symbol_index = {s: i for i, s in enumerate(self.genes.symbol)}
        self.pred, self.spread = {}, {}
        n, g = self.y.shape
        for fold in range(5):
            part = np.load(cv / f"fold{fold}.npz")
            test = part["test"]
            for key in part.files:
                if key.endswith("__prediction"):
                    arm = key.split("__")[0]
                    self.pred.setdefault(arm, np.full((n, g), np.nan, dtype=np.float32))[test] = part[key]
                elif key.endswith("__spread"):
                    arm = key.split("__")[0]
                    self.spread.setdefault(arm, np.full(n, np.nan, dtype=np.float32))[test] = part[key]
        missing = {arm: int(np.isnan(v).all(1).sum()) for arm, v in self.pred.items()}
        if any(missing.values()):
            raise SystemExit(f"incomplete_out_of_fold_predictions:{missing}")
        self.m = self.pred["systematic"]
        c = self.conditions
        self.key = {(r.cell_line, r.compound, float(r.dose)): i for i, r in c.iterrows()}
        # The release spells some compounds with trailing whitespace ("Prednisone "); anchors name
        # them without it. Identity is folded wherever a declared name meets the data.
        self.data_name = {n.strip(): n for n in c.compound.unique()}
        threshold = np.array([self.null[l]["q95_at_128_cells"] for l in c.cell_line]) * np.sqrt(128.0 / c.n_cells.to_numpy())
        self.threshold = threshold
        self.norm = np.linalg.norm(self.y, axis=1)
        self.responsive = self.norm > threshold
        self.rng = np.random.default_rng(20260926)

    # ------------------------------------------------------------------ B1 / B2
    def b1(self, arm: str, rows: np.ndarray, scramble: bool = False) -> dict[str, float]:
        per_compound: dict[str, list[float]] = {}
        rng = np.random.default_rng(7)
        for i in rows:
            p = self.pred[arm][i] - self.m[i]
            if scramble:
                p = p[rng.permutation(p.size)]
            per_compound.setdefault(self.conditions.compound[i], []).append(pearson(p, self.y[i] - self.m[i]))
        return {k: float(np.mean(v)) for k, v in per_compound.items()}

    def ceiling(self, rows: np.ndarray) -> dict[str, float]:
        per_compound: dict[str, list[float]] = {}
        for i in rows:
            if np.isnan(self.rep1[i]).any() or np.isnan(self.rep2[i]).any():
                continue
            per_compound.setdefault(self.conditions.compound[i], []).append(
                pearson(self.rep1[i] - self.m[i], self.rep2[i] - self.m[i]))
        return {k: float(np.mean(v)) for k, v in per_compound.items()}

    def mse_skill(self, arm: str, rows: np.ndarray, scramble: bool = False) -> dict[str, float]:
        per_compound: dict[str, list[float]] = {}
        rng = np.random.default_rng(7)
        for i in rows:
            p = self.pred[arm][i]
            if scramble:
                centered = p - self.m[i]
                p = self.m[i] + centered[rng.permutation(centered.size)]
            denominator = float(np.square(self.y[i]).mean())
            skill = 1.0 - float(np.square(p - self.y[i]).mean()) / denominator if denominator > 0 else 0.0
            per_compound.setdefault(self.conditions.compound[i], []).append(skill)
        return {k: float(np.mean(v)) for k, v in per_compound.items()}

    # ------------------------------------------------------------------ B3
    def top_profiles(self, matrix: np.ndarray) -> dict[str, np.ndarray]:
        out = {}
        for compound in self.compounds.index:
            rows = [self.key.get((line, compound, TOP)) for line in LINES]
            if all(r is not None for r in rows):
                out[compound] = np.concatenate([matrix[r] - self.m[r] for r in rows])
        return out

    def b3(self) -> dict:
        observed = self.top_profiles(self.y)
        cls = self.compounds.pathway_level_2
        skeleton_counts = self.compounds.reset_index().drop_duplicates("skeleton").pathway_level_2.value_counts()
        responsive_top = {c for c in observed
                          if any(self.responsive[self.key[(l, c, TOP)]] for l in LINES)}
        fold = self.compounds.fold
        scored = [c for c in sorted(observed) if c in responsive_top and skeleton_counts.get(cls[c], 0) >= 2
                  and any(cls[r] == cls[c] and fold[r] != fold[c] for r in observed)]

        def retrieve(profiles: dict[str, np.ndarray]) -> dict[str, float]:
            hits = {}
            for c in scored:
                refs = [r for r in observed if fold[r] != fold[c]]
                q = profiles[c]
                best, best_sim = None, -np.inf
                for r in refs:
                    denominator = np.linalg.norm(q) * np.linalg.norm(observed[r])
                    sim = float(q @ observed[r] / denominator) if denominator > 0 else -np.inf
                    if sim > best_sim:
                        best, best_sim = r, sim
                hits[c] = float(best is not None and cls[best] == cls[c])
            return hits

        from models import morgan, tanimoto  # noqa: E402

        fps = morgan(self.compounds.smiles.tolist(), 2048)
        index = {c: i for i, c in enumerate(self.compounds.index)}
        chem_hits, chance = {}, {}
        for c in scored:
            refs = [r for r in observed if fold[r] != fold[c]]
            sims = tanimoto(fps[[index[c]]], fps[[index[r] for r in refs]])[0]
            chem_hits[c] = float(cls[refs[int(np.argmax(sims))]] == cls[c])
            chance[c] = float(np.mean([cls[r] == cls[c] for r in refs]))
        result = {"scored_compounds": len(scored), "classes": int(cls[scored].nunique()),
                  "observed_ceiling": common.cluster_bootstrap(retrieve(observed)),
                  "chemistry_nearest_neighbour": common.cluster_bootstrap(chem_hits),
                  "chance": common.cluster_bootstrap(chance), "arms": {}}
        for arm in self.pred:
            if arm in ANNOTATED or arm in ("zero", "systematic"):
                continue
            result["arms"][arm] = common.cluster_bootstrap(retrieve(self.top_profiles(self.pred[arm])))
        return result

    # ------------------------------------------------------------------ B4 / B5
    def b4(self, arm: str) -> dict:
        out = {}
        for line in LINES:
            rows = [self.key[(line, c, TOP)] for c in self.compounds.index if (line, c, TOP) in self.key]
            p = np.linalg.norm(self.pred[arm][rows], axis=1)
            o = self.norm[rows]
            out[line] = float(stats.spearmanr(p, o).statistic) if np.ptp(p) > 1e-9 else 0.0
        return out

    def b5(self, arm: str, interaction: bool) -> dict:
        corr, correct, majority_pool = {}, {}, []
        for c in self.compounds.index:
            rows = [self.key.get((l, c, TOP)) for l in LINES]
            if any(r is None for r in rows) or not any(self.responsive[r] for r in rows):
                continue
            p = np.stack([self.pred[arm][r] - (self.m[r] if interaction else 0) for r in rows])
            o = np.stack([self.y[r] - (self.m[r] if interaction else 0) for r in rows])
            corr[c] = pearson((p - p.mean(0)).ravel(), (o - o.mean(0)).ravel())
            observed_top = int(np.argmax(np.linalg.norm(np.stack([self.y[r] for r in rows]), axis=1)))
            predicted_norms = np.linalg.norm(np.stack([self.pred[arm][r] for r in rows]), axis=1)
            correct[c] = float(np.ptp(predicted_norms) > 1e-9 and int(np.argmax(predicted_norms)) == observed_top)
            majority_pool.append(observed_top)
        majority = np.bincount(majority_pool, minlength=3).max() / max(len(majority_pool), 1)
        return {"correlation": common.cluster_bootstrap(corr), "top_line_accuracy": common.cluster_bootstrap(correct),
                "majority_line_rate": float(majority)}

    # ------------------------------------------------------------------ B6 anchors
    def _set_indices(self, anchor: dict) -> list[int]:
        members = anchor.get("genes") or self.gene_sets.get(anchor.get("gene_set", ""), [])
        return [self.symbol_index[g] for g in members if g in self.symbol_index]

    def _gene_score(self, vector: np.ndarray, idx: list[int], draws: int = 2000) -> tuple[float, float, float]:
        score = float(vector[idx].mean())
        pool = np.setdiff1d(np.arange(vector.size), idx)
        rng = np.random.default_rng(len(idx) * 7919)
        null = np.array([vector[rng.choice(pool, size=len(idx), replace=False)].mean() for _ in range(draws)])
        return score, float(np.quantile(null, 0.05)), float(np.quantile(null, 0.95))

    def anchors(self, matrix: np.ndarray, spec: dict) -> dict:
        results = {}
        norms = np.linalg.norm(matrix, axis=1)
        for anchor in spec["anchors"]:
            kind, compounds = anchor["kind"], anchor["primary_compounds"]
            if isinstance(compounds, list):
                unknown = [c for c in compounds if c.strip() not in self.data_name]
                if unknown:
                    raise SystemExit(f"anchor_compound_not_in_data:{anchor['id']}:{unknown}")
                compounds = [self.data_name[c.strip()] for c in compounds]
            detail: dict = {}
            if kind in ("gene_set_direction", "gene_set_context"):
                idx = self._set_indices(anchor)
                detail["genes_used"] = len(idx)
                dose = float(anchor["dose_nM"])
                for c in compounds:
                    for line in anchor["cell_lines"]:
                        r = self.key.get((line, c, dose))
                        if r is None:
                            continue
                        detail[f"{c}|{line}"] = self._gene_score(matrix[r] - self.m[r], idx)
                if anchor["id"] == "A3_estrogen_receptor_mcf7":
                    ok = [all(k in detail for k in (f"{c}|MCF7", f"{c}|A549", f"{c}|K562")) and
                          detail[f"{c}|MCF7"][0] < detail[f"{c}|MCF7"][1] and
                          detail[f"{c}|MCF7"][0] < min(detail[f"{c}|A549"][0], detail[f"{c}|K562"][0]) for c in compounds]
                    passed = sum(ok) >= 1
                elif anchor["id"] == "A7_p53_context":
                    c = compounds[0]
                    passed = all(k in detail for k in (f"{c}|A549", f"{c}|MCF7", f"{c}|K562")) and \
                        detail[f"{c}|A549"][0] > detail[f"{c}|K562"][0] and detail[f"{c}|MCF7"][0] > detail[f"{c}|K562"][0]
                else:
                    up = anchor["expected"] == "up"
                    per_compound = []
                    for c in compounds:
                        hits = [(v[0] > v[2]) if up else (v[0] < v[1]) for k, v in detail.items()
                                if isinstance(v, tuple) and k.startswith(c + "|")]
                        per_compound.append(sum(hits))
                    rule = {"A1_hsp90_hsf1": (2, 2), "A2_glucocorticoid_gr": (1, 1), "A4_mek_mpas": (1, 1),
                            "A5_phd_hypoxia": (2, 1), "A6_bet_hexim1": (2, 1)}[anchor["id"]]
                    passed = sum(h >= rule[0] for h in per_compound) >= rule[1]
                    detail["lines_passing_per_compound"] = dict(zip(compounds, per_compound))
            elif kind == "magnitude_context":
                ratio = {}
                for line in LINES:
                    per_compound = {}
                    for c in self.compounds.index:
                        rows = [self.key[(line, c, d)] for d in (10.0, 100.0, 1000.0, TOP) if (line, c, d) in self.key]
                        if rows:
                            per_compound[c] = float(norms[rows].mean())
                    median = float(np.median(list(per_compound.values())))
                    for c in compounds:
                        # An arm predicting no change has no scale to compare against; it fails.
                        ratio[f"{c}|{line}"] = per_compound.get(c, np.nan) / median if median > 0 else np.nan
                wins = [ratio[f"{c}|K562"] > max(ratio[f"{c}|A549"], ratio[f"{c}|MCF7"]) for c in compounds]
                detail["relative_norm"] = ratio
                passed = sum(wins) >= 2
            elif kind == "magnitude_class":
                hdac = [c for c in self.compounds.index if self.compounds.pathway_level_2[c] == "Histone deacetylation"
                        and "HDAC" in str(self.compounds.target[c])]
                checks = {}
                for line in LINES:
                    avg = {}
                    for c in self.compounds.index:
                        rows = [self.key[(line, c, d)] for d in (10.0, 100.0, 1000.0, TOP) if (line, c, d) in self.key]
                        if rows:
                            avg[c] = float(norms[rows].mean())
                    inside = [v for c, v in avg.items() if c in hdac]
                    outside = [v for c, v in avg.items() if c not in hdac]
                    checks[line] = (float(np.median(inside)), float(np.median(outside)))
                detail["median_hdac_vs_others"] = checks
                detail["hdac_compounds"] = len(hdac)
                passed = all(a > b for a, b in checks.values())
            elif kind == "magnitude_negative":
                below = {}
                for c in compounds:
                    for line in LINES:
                        r = self.key.get((line, c, TOP))
                        if r is not None:
                            below[f"{c}|{line}"] = (float(norms[r]), float(self.threshold[r]))
                detail["norm_vs_threshold"] = below
                passed = sum(v[0] < v[1] for v in below.values()) >= 5
            else:
                raise SystemExit(f"unknown_anchor_kind:{kind}")
            results[anchor["id"]] = {"passed": bool(passed), "detail": detail}
        return results

    # ------------------------------------------------------------------ B7
    def b7(self, arm: str, rows: np.ndarray) -> dict:
        if arm not in self.spread:
            return {}
        spread = self.spread[arm]
        error = np.sqrt(np.square(self.pred[arm] - self.y).mean(1))
        centered = np.array([1.0 - pearson(self.pred[arm][i] - self.m[i], self.y[i] - self.m[i]) for i in range(len(self.y))])
        relative = spread / np.maximum(np.linalg.norm(self.pred[arm] - self.m, axis=1), 1e-9)
        groups = self.conditions.compound.to_numpy()

        def boot(x, e):
            compounds = np.unique(groups[rows])
            value = float(stats.spearmanr(x[rows], e[rows]).statistic)
            draws = []
            rng = np.random.default_rng(11)
            by = {c: rows[groups[rows] == c] for c in compounds}
            for _ in range(500):
                pick = np.concatenate([by[c] for c in rng.choice(compounds, size=len(compounds))])
                draws.append(stats.spearmanr(x[pick], e[pick]).statistic)
            return {"spearman": value, "ci95": [float(np.nanquantile(draws, 0.025)), float(np.nanquantile(draws, 0.975))]}

        confident = rows[spread[rows] <= np.median(spread[rows])]
        return {"registered_spread_vs_rmse": boot(spread, error),
                "scale_free_relative_spread_vs_centered_error": boot(relative, centered),
                "b1_confident_half": common.cluster_bootstrap(self.b1(arm, confident)),
                "b1_all": common.cluster_bootstrap(self.b1(arm, rows))}

    # ------------------------------------------------------------------ B8
    def b8(self) -> dict:
        path = common.ROOT / "data/raw/prism/secondary-screen-dose-response-curve-parameters.csv"
        prism = pd.read_csv(path, usecols=["name", "depmap_id", "auc"])
        ids = {"ACH-000681": "A549", "ACH-000019": "MCF7"}
        prism = prism[prism.depmap_id.isin(ids) & prism.auc.notna() & prism.name.notna()]
        keyed = {}
        for name, dep, auc in zip(prism.name, prism.depmap_id, prism.auc):
            for k in common.name_keys(name):
                keyed.setdefault((k, ids[dep]), []).append(auc)
        pairs = []
        for c in self.compounds.index:
            for line in ("A549", "MCF7"):
                values = [v for k in common.name_keys(c) for v in keyed.get((k, line), [])]
                r = self.key.get((line, c, TOP))
                if values and r is not None:
                    pairs.append((c, line, r, float(np.mean(values))))
        if not pairs:
            return {"matched": 0}
        rows = np.array([p[2] for p in pairs])
        auc = np.array([p[3] for p in pairs])
        out = {"matched_compound_lines": len(pairs), "matched_compounds": len({p[0] for p in pairs}),
               "observed": float(stats.spearmanr(self.norm[rows], -auc).statistic), "arms": {}}
        for arm, matrix in self.pred.items():
            p = np.linalg.norm(matrix[rows], axis=1)
            out["arms"][arm] = float(stats.spearmanr(p, -auc).statistic) if np.ptp(p) > 1e-9 else 0.0
        return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--cv", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    protocol, spec = common.load_protocol(), common.load_anchors()
    a = Audit(args.prepared, args.cv)
    everything = np.arange(len(a.y))
    responsive = np.flatnonzero(a.responsive)
    arms = [arm for arm in a.pred]
    report = {"protocol_hashes": common.frozen_hashes(),
              "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "population": {"conditions": int(len(a.y)), "responsive": int(len(responsive)),
                             "responsive_by_line": {l: int(a.responsive[(a.conditions.cell_line == l).to_numpy()].sum())
                                                    for l in LINES},
                             "responsive_by_dose": {str(d): int(a.responsive[(a.conditions.dose == d).to_numpy()].sum())
                                                    for d in (10.0, 100.0, 1000.0, TOP)}},
              "B1": {}, "B2": {}, "B4": {}, "B5": {}, "B5_interaction": {}, "B6": {}, "B7": {}}
    ceiling_responsive = a.ceiling(responsive)
    report["ceiling"] = {"responsive": common.cluster_bootstrap(ceiling_responsive),
                         "all": common.cluster_bootstrap(a.ceiling(everything))}
    b1_responsive = {}
    for arm in arms:
        b1_responsive[arm] = a.b1(arm, responsive)
        report["B1"][arm] = {"responsive": common.cluster_bootstrap(b1_responsive[arm]),
                             "all": common.cluster_bootstrap(a.b1(arm, everything))}
        report["B2"][arm] = {"b1_scrambled_responsive": common.cluster_bootstrap(a.b1(arm, responsive, scramble=True)),
                             "mse_skill_responsive": common.cluster_bootstrap(a.mse_skill(arm, responsive)),
                             "mse_skill_scrambled_responsive": common.cluster_bootstrap(a.mse_skill(arm, responsive, scramble=True))}
        report["B4"][arm] = a.b4(arm)
        report["B5"][arm] = a.b5(arm, interaction=False)
        report["B5_interaction"][arm] = a.b5(arm, interaction=True)
        report["B7"][arm] = a.b7(arm, responsive)
        print("scored", arm, flush=True)
    report["B3"] = a.b3()
    observed_anchors = a.anchors(a.y, spec)
    report["B6"]["observed"] = observed_anchors
    held = [k for k, v in observed_anchors.items() if v["passed"]]
    for arm in arms:
        result = a.anchors(a.pred[arm], spec)
        report["B6"][arm] = {"reproduced": sorted(k for k in held if result[k]["passed"]),
                             "passed_but_absent_in_data": sorted(k for k, v in result.items() if v["passed"] and k not in held),
                             "detail": result}
    report["B8"] = a.b8()
    report["primary"] = {
        "P1_jepa_minus_knn": common.paired_bootstrap(b1_responsive["latent_jepa"], b1_responsive["knn_chem"]),
        "P2_jepa_minus_pca": common.paired_bootstrap(b1_responsive["latent_jepa"], b1_responsive["latent_pca"]),
        "P3_anchors": {"latent_jepa": len(report["B6"]["latent_jepa"]["reproduced"]),
                       "mlp_existing": len(report["B6"]["mlp_existing"]["reproduced"]), "held_in_data": len(held)}}
    verdicts = {"data_carries_biology": {"held": held, "passed": len(held) >= 7}}
    ceiling_mean = report["ceiling"]["responsive"]["mean"]
    for arm in arms:
        if arm in ("zero",):
            continue
        b1 = report["B1"][arm]["responsive"]
        diff = common.paired_bootstrap(b1_responsive[arm], b1_responsive["knn_chem"])
        b7 = report["B7"].get(arm, {}).get("registered_spread_vs_rmse")
        v = {"specific_signal": b1["ci95"][0] is not None and b1["ci95"][0] > 0,
             "beyond_retrieval": arm != "knn_chem" and diff["ci95"][0] is not None and diff["ci95"][0] > 0,
             "near_ceiling": b1["mean"] is not None and b1["mean"] >= 0.5 * ceiling_mean,
             "anchor_depth": len(report["B6"][arm]["reproduced"]) >= 0.5 * max(len(held), 1),
             "knows_what_it_does_not_know": bool(b7) and b7["ci95"][0] > 0}
        v["sufficient_for_advisory_ranking"] = v["specific_signal"] and v["anchor_depth"] and v["knows_what_it_does_not_know"]
        verdicts[arm] = v
    report["verdicts"] = verdicts
    common.write_json(args.output / "audit.json", report)
    print(json.dumps({"population": report["population"], "primary": report["primary"],
                      "verdicts": verdicts}, indent=1, default=str), flush=True)


if __name__ == "__main__":
    main()
