"""E-WM2: are the in-context world model's reading forecasts better than the current world model's?

File summary
- Path: research/incontext_world/e_wm2.py
- Purpose: run and analyse spec.json's E-WM2 on the 20 protocol-v2.1 development tasks.
- Core points:
  - Every task is built by `protocol_v2.tasks_v21.load`. Forecasters see only the public view (the
    fold's training tables). The real executor reads the held-out compound, exactly as the
    protocol-v2.1 runner does, and supplies each item's observed label and the prompt shifts.
  - Items: episode x design-planned target x history. H1 and H2 histories use only prompts
    whose real reading was non-eliminating (profile_unresolved or no_detectable_response). An
    eliminating reading ends a real episode, so a planner is never in such a state, and the
    reference world has no likelihood for it. A QC-failed prompt conditions nothing and is not
    used as a history.
  - Arms share hyperparameters: the reference world's (s, k, e) are fitted once per task, and the
    prompt- and transfer-only ablations take their (kappa, tau) from the automatic fit's
    likelihood tables. `incontext_permuted` uses the automatic fit with a partner compound's shifts.
  - Scores use the true hypothesis's branch only: negative log-likelihood of the observed label,
    the Brier score, and the forecast and observed wrong elimination.
- Interfaces: `run_task`, `analyse`, `robustness` (post hoc); CLI
  `python -m research.incontext_world.e_wm2 run [--workers N] | analyse | robustness`
- Depends on: world.py, research/protocol_v2 (tasks_v21, contracts, runner), research/belief_planning
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/incontext_world_20260927/e_wm2"
SEED = 20260927
DRAWS = 10_000
H2_PAIRS = 6
ARMS = ("pooled", "class", "reference", "incontext", "incontext_prompt", "incontext_transfer", "incontext_permuted")
TASKS = tuple((d, t, f) for d, t in (("sciplex3", "B"), ("l1000", "LT"), ("sciplex3", "A"), ("l1000", "T"))
              for f in (0, 1, 2, 3, 4))
"""The registered folds are 0-4. The first run used 1-5 (spec.json's wording): its fold-5 records are empty and
fold 0 was run afterwards with the same code; both are kept."""


def _stable(*parts) -> int:
    import hashlib
    return int(hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()[:8], 16)


def _pooled(world, key, h1, h2):
    from maestro.acquisition import OutcomeBranch, OutcomeForecast
    from research.belief_planning import world as W
    entry = world.keys[key]
    qc = entry["qc_fail"]
    branches = []
    for own, match_own, match_other in ((h1, W.MATCH_H1, W.MATCH_H2), (h2, W.MATCH_H2, W.MATCH_H1)):
        dist = {lab: float((1 - qc) * p) for lab, p in zip((match_own, match_other, W.UNRESOLVED, W.ABSENT), entry["pooled"])}
        dist[W.QC_FAILED] = float(qc)
        branches.append(OutcomeBranch(own, dist, 0))
    return OutcomeForecast("pooled", tuple(branches), basis="pooled")


def _score(forecast, truth, h1, observed):
    from research.belief_planning import world as W
    probs = forecast.branch_for(truth).probabilities
    wrong_label = W.MATCH_H2 if truth == h1 else W.MATCH_H1
    p = float(probs.get(observed, 0.0))
    brier = sum((float(probs.get(lab, 0.0)) - (lab == observed)) ** 2 for lab in W.LABELS)
    return -np.log(max(p, 1e-12)), brier, float(probs.get(wrong_label, 0.0))


def run_task(task) -> dict:
    from threadpoolctl import threadpool_limits

    from research.belief_planning import arms as BA
    from research.belief_planning import tasks as T
    from research.belief_planning import world as W
    from research.protocol_v2 import contracts as K
    from research.protocol_v2 import runner as RN
    from research.protocol_v2 import tasks_v21 as TV

    from . import world as IW

    dataset, tier, fold = task
    started = time.time()
    E, C = K.T.E, K.T.C
    with threadpool_limits(limits=1):
        data, real_ctx, setting, design = TV.load(dataset, tier, fold)
        comp = data.compounds.drop_duplicates("compound").set_index("compound")
        heldout = set(comp.index[comp.fold == fold])
        episodes = TV.episode_list(real_ctx, fold)
        training = TV.training_compounds(real_ctx, fold)
        view = K.public_view(real_ctx, heldout, training_compounds=training, design=design)
        problems = K.public_view_problems(view, heldout)
        unit_of = T.units(dataset)[T.UNIT[dataset]].astype(str).to_dict()
        reference = BA.world_for(view, "on", "true")
        klass = BA.world_for(view, "masked", "true")
        fp, pos = view.extra["fingerprints"]
        public = view.data.compounds.drop_duplicates("compound").set_index("compound")
        unit_col = "component" if "component" in public.columns else "skeleton"
        groups = {c: g for c, g in public[unit_col].items() if isinstance(g, str)}
        common = dict(fingerprints=fp, positions=pos, vc="on", feedback="true",
                      hyperparameters=reference.hyperparameters, groups=groups)
        fit_started = time.time()
        auto = IW.InContextWorld(view.ft, view.params, training, source="auto", **common)
        fit_seconds = time.time() - fit_started
        worlds = {"incontext": auto}
        for name, src in (("incontext_prompt", "prompt"), ("incontext_transfer", "transfer")):
            w = IW.InContextWorld(view.ft, view.params, training, source=src, incontext=IW.restrict(auto.incontext, src),
                                  **common)
            w._geometry, w._transitions = auto._geometry, auto._transitions
            worlds[name] = w
        # the permutation control: a seeded derangement of the fold's episode compounds
        compounds = sorted({e[0] for e in episodes})
        rng = np.random.default_rng([SEED, fold, _stable(dataset, tier)])
        order = rng.permutation(len(compounds))
        partner = {compounds[order[i]]: compounds[order[(i + 1) % len(order)]] for i in range(len(order))} \
            if len(compounds) > 1 else {}

        shift_cache = {}

        def shift(compound, key):
            if (compound, key) not in shift_cache:
                row = real_ctx.data.index.get(key, {}).get(compound)
                ok = row is not None and C.qc_passed(real_ctx.data, row)
                shift_cache[(compound, key)] = real_ctx.data.shift[row].astype(np.float64) if ok else None
            return shift_cache[(compound, key)]

        rows = []
        for compound, truth, decoy, h1, h2 in episodes:
            available = view.data.availability[compound]
            local = RN.local_setting(setting, available)
            keys = [tuple(k) for k in local.keys]
            label = {k: W.label_of(E.execute(real_ctx, compound, k, h1, h2)["outcome"]) for k in keys}
            prompts = [k for k in keys if label[k] in (W.UNRESOLVED, W.ABSENT) and shift(compound, k) is not None]
            for target in keys:
                others = [p for p in prompts if p != target]
                histories = [()] + [(p,) for p in others]
                pairs = [(a, b) for a in others for b in others if a != b]
                if pairs:
                    pick = np.random.default_rng([SEED, _stable(compound, decoy, C.action_id(target))])
                    chosen = pick.choice(len(pairs), size=min(H2_PAIRS, len(pairs)), replace=False)
                    histories += [pairs[i] for i in sorted(chosen)]
                for hs in histories:
                    history = tuple((p, label[p]) for p in hs)
                    own = {p: shift(compound, p) for p in hs}
                    swapped = {p: shift(partner.get(compound, compound), p) for p in hs}
                    forecasts = {
                        "pooled": _pooled(reference, target, h1, h2),
                        "class": klass.forecast(target, h1, h2, compound, ()),
                        "reference": reference.forecast(target, h1, h2, compound, history),
                        "incontext": auto.forecast(target, h1, h2, compound, history, profiles=own),
                        "incontext_prompt": worlds["incontext_prompt"].forecast(target, h1, h2, compound, history,
                                                                                profiles=own),
                        "incontext_transfer": worlds["incontext_transfer"].forecast(target, h1, h2, compound, history,
                                                                                    profiles=own),
                        "incontext_permuted": auto.forecast(target, h1, h2, compound, history, profiles=swapped),
                    }
                    wrong_label = W.MATCH_H2 if truth == h1 else W.MATCH_H1
                    row = {"dataset": dataset, "tier": tier, "fold": fold, "compound": compound,
                           "unit": unit_of.get(compound, compound), "truth": truth, "decoy": decoy,
                           "target": C.action_id(target), "history": "+".join(C.action_id(p) for p in hs),
                           "hsize": len(hs), "history_labels": "+".join(label[p] for p in hs),
                           "observed": label[target], "wrong": label[target] == wrong_label,
                           "partner_prompts": sum(swapped[p] is not None for p in hs)}
                    for arm, forecast in forecasts.items():
                        if forecast.refusal:
                            row[f"nll_{arm}"] = row[f"brier_{arm}"] = row[f"pw_{arm}"] = np.nan
                            continue
                        nll, brier, pw = _score(forecast, truth, h1, label[target])
                        row[f"nll_{arm}"], row[f"brier_{arm}"], row[f"pw_{arm}"] = nll, brier, pw
                    rows.append(row)
    frame = pd.DataFrame(rows)
    hp = {k: v for k, v in auto.incontext.items()}
    return {"task": list(task), "frame": frame, "problems": problems, "episodes": len(episodes),
            "reference_hyperparameters": {k: reference.hyperparameters[k] for k in ("s", "k", "e")},
            "incontext": hp, "restricted": {n: worlds[n].incontext for n in ("incontext_prompt", "incontext_transfer")},
            "fit_seconds": fit_seconds, "seconds": time.time() - started}


def _write_task(result: dict) -> dict:
    dataset, tier, fold = result["task"]
    path = OUT / "items" / f"{dataset}_{tier}_{fold}.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    result["frame"].to_parquet(path, index=False)
    meta = {k: v for k, v in result.items() if k != "frame"}
    meta["items"] = int(len(result["frame"]))
    (OUT / "items" / f"{dataset}_{tier}_{fold}.json").write_text(json.dumps(meta, indent=1, default=str), encoding="utf-8")
    return meta


def run(workers: int = 4) -> None:
    """Run every task that has no record yet; an existing task record is never overwritten."""
    import multiprocessing as mp
    OUT.mkdir(parents=True, exist_ok=True)
    todo = [t for t in TASKS if not (OUT / "items" / f"{t[0]}_{t[1]}_{t[2]}.parquet").exists()]
    started = time.time()
    with mp.get_context("spawn").Pool(workers) as pool:
        for result in pool.imap_unordered(run_task, todo):
            meta = _write_task(result)
            print(meta["task"], meta["items"], f"{meta['seconds']:.0f}s", meta["incontext"].get("source"),
                  meta["incontext"].get("kappa"), meta["incontext"].get("tau"), "problems", len(meta["problems"]),
                  flush=True)
    print(f"total {time.time() - started:.0f}s")


# ------------------------------------------------------------------------------------ analysis
def _unit_table(frame: pd.DataFrame, columns: list) -> pd.DataFrame:
    return frame.groupby(frame.unit.astype(str))[columns].mean().sort_index()


def _interval(values: np.ndarray, index: np.ndarray) -> list:
    return np.quantile(values[index].mean(axis=1), [0.025, 0.975]).tolist()


def compare(frame: pd.DataFrame, metric: str, candidate: str, others) -> dict:
    cols = [f"{metric}_{a}" for a in ARMS]
    table = _unit_table(frame, cols).dropna()
    index = np.random.default_rng(SEED).integers(len(table), size=(DRAWS, len(table)))
    out = {"units": int(len(table)), "items": int(len(frame)),
           "arms": {a: float(table[f"{metric}_{a}"].mean()) for a in ARMS}}
    for other in others:
        diff = (table[f"{metric}_{candidate}"] - table[f"{metric}_{other}"]).to_numpy()
        out[f"{candidate}-{other}"] = {"difference": float(diff.mean()), "ci": _interval(diff, index)}
    return out


def calibration(frame: pd.DataFrame) -> dict:
    out = {}
    for arm in ARMS:
        forecast = float(frame[f"pw_{arm}"].sum())
        observed = float(frame.wrong.sum())
        out[arm] = {"observed": int(observed), "forecast": forecast,
                    "ratio": observed / forecast if forecast > 0 else None}
    return out


def analyse(out: Path = OUT) -> dict:
    frames = [pd.read_parquet(p) for p in sorted((out / "items").glob("*.parquet"))]
    metas = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((out / "items").glob("*.json"))]
    frame = pd.concat(frames, ignore_index=True)
    result = {"spec": "research/incontext_world/spec.json#E-WM2", "tasks": len(metas),
              "problems": sum(len(m["problems"]) for m in metas), "datasets": {}, "fits": {}}
    for m in metas:
        result["fits"]["_".join(map(str, m["task"]))] = {
            "reference": m["reference_hyperparameters"],
            "incontext": {k: m["incontext"].get(k) for k in ("source", "kappa", "tau", "gain", "items")},
            "restricted": m["restricted"], "items": m["items"], "seconds": round(m["seconds"])}
    others = ("reference", "class", "pooled", "incontext_permuted")
    for dataset, sub in frame.groupby("dataset"):
        entry = {}
        h0, h1, h2 = (sub[sub.hsize == n] for n in (0, 1, 2))
        entry["H0_identical"] = {
            "max_abs_nll_difference": float(np.nanmax(np.abs(h0.nll_incontext - h0.nll_reference))) if len(h0) else None}
        entry["H1"] = {"nll": compare(h1, "nll", "incontext", others),
                       "brier": compare(h1, "brier", "incontext", others),
                       "calibration": calibration(h1),
                       "ablations": {"transfer": compare(h1, "nll", "incontext_transfer", ("reference",)),
                                     "prompt": compare(h1, "nll", "incontext_prompt", ("reference",))}}
        entry["H2"] = {"nll": compare(h2, "nll", "incontext", others), "calibration": calibration(h2)} if len(h2) else None
        entry["H0"] = {"nll": compare(h0, "nll", "reference", ("class", "pooled")), "calibration": calibration(h0)}
        entry["by_task_H1_nll_difference"] = {
            f"{t}_{f}": float((g.groupby("unit").nll_incontext.mean() - g.groupby("unit").nll_reference.mean()).mean())
            for (t, f), g in h1.groupby(["tier", "fold"])}
        entry["by_prompt_label_H1"] = {
            lab: compare(g, "nll", "incontext", ("reference",)) for lab, g in h1.groupby("history_labels")}
        primary = entry["H1"]["nll"]
        permuted = entry["H1"]["nll"]["incontext-incontext_permuted"]
        gate = {
            "incontext_below_reference": primary["incontext-reference"]["ci"][1] < 0,
            "H0_identical": (entry["H0_identical"]["max_abs_nll_difference"] or 0.0) < 1e-12,
            "permuted_not_better_than_reference": None,
        }
        perm_vs_ref = compare(h1, "nll", "incontext_permuted", ("reference",))["incontext_permuted-reference"]
        entry["H1"]["permuted_vs_reference"] = perm_vs_ref
        gate["permuted_not_better_than_reference"] = perm_vs_ref["ci"][1] >= 0
        gate["pass"] = all(gate.values())
        entry["gate"] = gate
        entry["incontext_minus_permuted"] = permuted
        result["datasets"][dataset] = entry
    (out / "analysis.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    return result


def robustness(out: Path = OUT) -> dict:
    """POST HOC (written after the E-WM2 analysis was read): how far the unit-mean result depends on weighting.

    Item-weighted means with a unit-cluster bootstrap (a ratio estimator), per-tier unit means, and
    unit-mean differences by how many H1 items a unit has. Not part of the registered gate.
    """
    frame = pd.concat([pd.read_parquet(p) for p in sorted((out / "items").glob("*.parquet"))], ignore_index=True)
    rng = np.random.default_rng(SEED)

    def item_weighted(g, col):
        s = g.groupby(g.unit.astype(str))[col].agg(["sum", "size"])
        sums, counts = s["sum"].to_numpy(float), s["size"].to_numpy(float)
        index = rng.integers(len(s), size=(DRAWS, len(s)))
        boot = sums[index].sum(1) / counts[index].sum(1)
        return {"estimate": float(sums.sum() / counts.sum()), "ci": np.quantile(boot, [0.025, 0.975]).tolist(),
                "units": int(len(s)), "items": int(counts.sum())}

    def unit_mean(g, col):
        u = g.groupby(g.unit.astype(str))[col].mean().to_numpy(float)
        index = rng.integers(len(u), size=(DRAWS, len(u)))
        return {"estimate": float(u.mean()), "ci": np.quantile(u[index].mean(1), [0.025, 0.975]).tolist(),
                "units": int(len(u))}

    result = {"status": "post hoc; written after the registered analysis was read", "datasets": {}}
    for dataset, sub in frame.groupby("dataset"):
        sub = sub.assign(d=sub.nll_incontext - sub.nll_reference, dp=sub.nll_incontext_permuted - sub.nll_reference,
                         dc=sub.nll_reference - sub.nll_class)
        entry = {}
        for h in (1, 2):
            g = sub[sub.hsize == h]
            entry[f"H{h}_item_weighted"] = {"incontext-reference": item_weighted(g, "d"),
                                            "permuted-reference": item_weighted(g, "dp"),
                                            "reference-class": item_weighted(g, "dc")}
        h1 = sub[sub.hsize == 1]
        entry["H1_by_tier_unit_mean"] = {t: unit_mean(g, "d") for t, g in h1.groupby("tier")}
        entry["H1_by_tier_item_weighted"] = {t: item_weighted(g, "d") for t, g in h1.groupby("tier")}
        entry["H1_reference-class_unit_mean"] = unit_mean(h1, "dc")
        size = h1.groupby(h1.unit.astype(str)).size()
        band = pd.qcut(size, 3, labels=["few", "mid", "many"], duplicates="drop")
        h1 = h1.assign(band=h1.unit.astype(str).map(band))
        entry["H1_by_unit_item_count"] = {str(b): unit_mean(g, "d") for b, g in h1.groupby("band", observed=True)}
        result["datasets"][dataset] = entry
    (out / "robustness_posthoc.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("run", "analyse", "robustness"))
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if args.command == "robustness":
        print(json.dumps(robustness(), indent=1)[:6000])
        return
    if args.command == "run":
        run(args.workers)
    print(json.dumps(analyse(), indent=1)[:6000])


if __name__ == "__main__":
    main()
