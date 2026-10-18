"""Run the fixed-seed attribution study: per-line decisions of every arm at every layer.

File summary
- Path: research/seed_attribution_20261017/run.py
- Purpose: produce the per-line records (hits, unknown nominations, nominated sets) that `analyse.py`
  turns into RESULTS.json. Nothing is tuned here. The arms, layers, variants and seeds are those of
  PROTOCOL.md; FREEZE.json hashes this file, `analyse.py`, `nulls.py`, NULLS.json and PROTOCOL.md.
- Data and access: the PRISM 19Q4 future strata (67 future-line + 180 future-lineage lines) were opened
  by `program_revision_20261017` (its ACCESS.json). They are EXPOSED data: this is attribution on exposed
  data, not confirmation. The first read of this study is written to ACCESS.json (write-once).
- Contract: every arm uses `corrected.CorrectedDomain` (one aggregation, reference and threshold from
  `contract`). The frozen implementation is run only as a parity check and must reproduce the frozen
  RESULTS.json means; otherwise the study stops (PARITY_FAILED).
- Layers:
  - ``policy``: exploit-first feedback campaign (28 wells per line, batches 5+5+4) on the I2 fold, the
    layer of the frozen headline contrast (primary);
  - ``I1``, ``I2``: single-shot top-10 nominations from the committed prediction.
- Arms (names are fixed in PROTOCOL.md): A_S; B_seed; D_shared_only; C0_additive; C1_global_ridge;
  C1x_global_ridge_cross; C2_per_drug_ridge; C3_pooled_gbm; E00..E19 (NULLS.json).
- Variants (component layers only): variance decomposition of B/D/C1/C3 and availability weighting.
- Cost: wells and rounds are recorded per line; compute seconds per arm.
- Interfaces: ``python run.py [--smoke]``. ``--smoke`` uses 12 lines and 2 nulls, writes under tmp/ and
  never touches write-once files.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import corrected as C  # noqa: E402
import contract  # noqa: E402
import engine  # noqa: E402
import policy  # noqa: E402
from revise import SEED_LIBRARY  # noqa: E402
from vc import Program, ProgramLibrary  # noqa: E402

ROOT = HERE.parents[1]
RECORDS = HERE / "records"
SMOKE_DIR = ROOT / "tmp" / "seed_attribution_20261017"
FROZEN = HERE.parent / "program_revision_20261017"
POLICY = "exploit_first_feedback"
VARIANT_ARMS = ("B_seed", "D_shared_only", "C1_global_ridge", "C3_pooled_gbm")


def seed_library(shared_only: bool = False) -> ProgramLibrary:
    return ProgramLibrary([Program(s, g, "seed") for s, g in SEED_LIBRARY], shared_only=shared_only)


def build_arms(nulls: list) -> dict:
    scopes = sorted({s for s, _ in SEED_LIBRARY})
    genes = sorted({g.split(":")[1] for _, g in SEED_LIBRARY})
    pairs = [(s, g.split(":")[1]) for s, g in SEED_LIBRARY]
    cross = [(s, g) for s in scopes for g in genes]
    arms = {"A_S": None, "B_seed": seed_library(), "D_shared_only": seed_library(True),
            "C0_additive": C.AdditiveRidge(scopes, genes), "C1_global_ridge": C.GlobalInteractionRidge(pairs),
            "C1x_global_ridge_cross": C.GlobalInteractionRidge(cross), "C2_per_drug_ridge": C.PerDrugGateRidge(genes),
            "C3_pooled_gbm": C.PooledGBM(scopes, genes)}
    for n in nulls:
        arms[f"E{n['index']:02d}"] = ProgramLibrary([Program(p["scope"], p["state"], "null") for p in n["programs"]])
    return arms


class AvailPredictor(C.CorrectedPredictor):
    """Nomination score = crossing probability x the drug's training-line availability (sensitivity only)."""

    def __init__(self, *args, weight, **kwargs):
        super().__init__(*args, **kwargs)
        self.weight = weight

    def score(self, j, readouts):
        sc, mean, var, st = super().score(j, readouts)
        return sc * self.weight, mean, var, st


class World:
    def __init__(self, smoke: bool):
        self.dom = C.CorrectedDomain(open_future=True)
        dom = self.dom
        L = dom.lines
        split = L.line_split.to_numpy()
        self.train = np.flatnonzero(dom.src_line)
        T = np.flatnonzero((split == "future_line") | (split == "future_lineage"))
        if smoke:
            T = T[:: max(1, len(T) // 12)][:12]
        self.T = T
        self.strata = split[T]
        self.cluster = L.primary_tissue.to_numpy()[T]
        self.probes = engine.fixed_probe_design(dom, 8)
        frozen_probes = json.loads((FROZEN / "LIBRARIES.json").read_text(encoding="utf-8"))["_bench"]["probes"]
        if self.probes != frozen_probes:
            raise SystemExit("DESIGN_MISMATCH: the frozen probe design does not reproduce")
        self.fold = {"I1": C.SafeContextFold(dom, self.train, T, "I1", []),
                     "I2": C.SafeContextFold(dom, self.train, T, "I2", self.probes)}
        self.drows = self.fold["I2"].drows
        self.thr = dom.thr[self.drows]
        self.frozen_thr = dom.frozen_thr[self.drows]
        src = np.flatnonzero(dom.src_line)
        self.avail = dom.known[np.ix_(self.drows, src)].mean(1)
        self.cache = {}

    # ---------------------------------------------------------------- layers
    def score_noms(self, nom):
        h, u = engine.score_nominations(self.dom, nom, self.drows, self.T)
        return h, u

    def component(self, layer, corrector, mean_from="lib", var_from="crossfit", weight=None, thr=None):
        fold = self.fold[layer]
        mean, var, score = C.decide(fold, corrector, self.thr if thr is None else thr, mean_from, var_from, self.cache)
        if weight is not None:
            score = score * weight[:, None]
        nom = engine.nominate(score, self.dom.tie_drug[fold.drows])
        h, u = self.score_noms(nom)
        d = self.drows[nom]                      # (K, lines) global drug rows
        c = self.T[None, :]
        status = np.where(self.dom.hit[d, c], 1, np.where(self.dom.known[d, c], 0, -1))
        return {"hits": h.tolist(), "unknown": u.tolist(), "nominated": nom.T.tolist(), "status": status.T.tolist()}

    def oos_variance(self, corrector, layer="I2"):
        if corrector is None or not getattr(corrector, "programs", None):
            return None
        key = (C.corrector_key(corrector), id(self.fold[layer]))
        if key not in self.cache:
            self.cache[key] = C.crossfit_variance(self.fold[layer], corrector)
        return self.cache[key]

    def campaign(self, corrector, layer="I2", var="crossfit", weight=None, thr=None, record_sets=False):
        fold = self.fold[layer]
        oos = self.oos_variance(corrector, layer) if var == "crossfit" else None
        kwargs = dict(oos_var=oos, thr=self.thr if thr is None else thr)
        pred = (AvailPredictor(fold, corrector, weight=weight, **kwargs) if weight is not None
                else C.CorrectedPredictor(fold, corrector, **kwargs))
        rows = {"hits": [], "unknown": [], "wells": [], "rounds": [], "confirmed": []}
        sets, stats = [], []
        pos = {int(d): i for i, d in enumerate(self.drows)}
        for j in range(len(self.T)):
            r = policy.run_campaign(pred, j, policy.POLICIES[POLICY], fixed_probes=self.probes if layer == "I2" else ())
            rows["hits"].append(r["hits"])
            rows["unknown"].append(r["unknown"])
            rows["wells"].append(r["wells"])
            rows["rounds"].append(r["rounds"])
            rows["confirmed"].append(r["confirmed"])
            if record_sets:
                conf = [t for t in r["trace"] if t["action"] == "confirm"]
                sets.append([pos[self.dom.drug_index[t["drug"]]] for t in conf])
                stats.append([1 if t["hit"] else 0 if t["known"] else -1 for t in conf])
        if record_sets:
            rows["confirmed_drugs"], rows["status"] = sets, stats
        return rows


def parity(world: World) -> dict:
    """Frozen mode (frozen thresholds, in-sample library variance) must reproduce the frozen RESULTS means."""

    frozen = json.loads((FROZEN / "RESULTS.json").read_text(encoding="utf-8"))
    dom = world.dom
    out, ok = {}, True
    seed = seed_library()
    for layer in ("I1", "I2"):
        for arm, lib, key in (("A_S", None, f"strong|{layer}"), ("B_seed", seed, f"seed_fixed|{layer}")):
            r = world.component(layer, lib, "lib", "frozen", thr=world.frozen_thr)
            ref = frozen["B_table_hits_unknown_per_line"][key]["all"]
            got = [float(np.mean(r["hits"])), float(np.mean(r["unknown"]))]
            out[f"{arm}|{layer}"] = {"got": got, "frozen": ref}
            ok &= bool(np.allclose(got, ref, atol=1e-9))
    for arm, lib, key in (("A_S", None, "strong|exploit_first_feedback"), ("B_seed", seed, "seed_fixed|exploit_first_feedback")):
        r = world.campaign(lib, "I2", var="base", thr=world.frozen_thr)
        ref = frozen["C_policies"][key]
        got = float(np.mean(r["hits"]))
        out[f"{arm}|policy"] = {"got": got, "frozen": ref["hits_per_line"], "unknown_got": float(np.mean(r["unknown"])), "unknown_frozen": ref["unknown"]}
        ok &= bool(np.isclose(got, ref["hits_per_line"], atol=1e-9)) and bool(np.isclose(np.mean(r["unknown"]), ref["unknown"], atol=1e-9))
    out["all_match"] = ok
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--skip-parity", action="store_true")
    args = ap.parse_args()
    t0 = time.time()
    import seal
    if not args.smoke:
        seal.check()
        seal.record_access()
    nulls = json.loads((HERE / "NULLS.json").read_text(encoding="utf-8"))["nulls"]
    if args.smoke:
        nulls = nulls[:2]
    out_path = (SMOKE_DIR / "units_smoke.json") if args.smoke else (RECORDS / "units.json")
    if out_path.exists() and not args.smoke:
        raise SystemExit(f"{out_path.name} exists; the run is write-once")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    world = World(args.smoke)
    dom = world.dom
    print("world", len(world.T), "lines", len(set(world.cluster)), "clusters", round(time.time() - t0, 1), flush=True)

    units = {"_meta": {"lines": [str(dom.lines.depmap_id[c]) for c in world.T], "stratum": world.strata.tolist(),
                       "cluster": world.cluster.tolist(), "n_train_lines": int(len(world.train)), "probes": world.probes,
                       "undefined_reference_drugs": int(np.isnan(world.thr).sum()), "smoke": bool(args.smoke),
                       "drug_cores": [str(dom.drugs.core[d]) for d in world.drows],
                       "structure_group": [str(dom.drugs.structure_group[d]) for d in world.drows],
                       "gates": {g: world.dom.lf["panel"][world.T, list(dom.lf["panel_genes"]).index(g)].tolist()
                                 for g in sorted({gg.split(":")[1] for _, gg in SEED_LIBRARY})},
                       "source_any_gate_prevalence": float((dom.lf["panel"][world.train][:, [list(dom.lf["panel_genes"]).index(g) for g in sorted({gg.split(":")[1] for _, gg in SEED_LIBRARY})]].sum(1) > 0).mean()),
                       "source_gate_prevalence": {g: float(dom.lf["panel"][world.train, list(dom.lf["panel_genes"]).index(g)].mean())
                                                  for g in sorted({gg.split(":")[1] for _, gg in SEED_LIBRARY})}},
             "parity": None, "arms": {}, "variants": {}, "seconds": {}}
    if not args.skip_parity:
        units["parity"] = parity(world)
        print("parity", units["parity"]["all_match"], round(time.time() - t0, 1), flush=True)
        if not units["parity"]["all_match"]:
            print(json.dumps(units["parity"], indent=1))
            raise SystemExit("PARITY_FAILED: the frozen implementation did not reproduce the frozen results")

    arms = build_arms(nulls)
    record_sets = {"A_S", "B_seed"}
    for name, corr in arms.items():
        t1 = time.time()
        rec = {"I1": world.component("I1", corr), "I2": world.component("I2", corr),
               "policy": world.campaign(corr, "I2", record_sets=name in record_sets)}
        units["arms"][name] = rec
        units["seconds"][name] = round(time.time() - t1, 2)
        print(name, {k: round(float(np.mean(v["hits"])), 3) for k, v in rec.items()}, units["seconds"][name], flush=True)

    # secondary layer: the exploit-first campaign on the I1 fold (no unused probe design)
    for name in ("A_S", "B_seed"):
        units["arms"][name]["policy_I1fold"] = world.campaign(arms[name], "I1")

    # variance decomposition (component layers) and availability weighting
    for name in VARIANT_ARMS:
        corr = arms[name]
        for layer in ("I1", "I2"):
            units["variants"][f"{name}|{layer}|mean_only"] = world.component(layer, corr, "lib", "base")
            units["variants"][f"{name}|{layer}|variance_only_oos"] = world.component(layer, corr, "base", "crossfit")
            units["variants"][f"{name}|{layer}|full_frozen_variance"] = world.component(layer, corr, "lib", "frozen")
            if name == "B_seed":
                units["variants"][f"{name}|{layer}|variance_only_in_sample"] = world.component(layer, corr, "base", "frozen")
    for layer in ("I1", "I2"):
        for name in ("A_S", "B_seed"):
            units["variants"][f"{name}|{layer}|availability_weighted"] = world.component(layer, arms[name], weight=world.avail)
    for name in ("A_S", "B_seed"):
        units["variants"][f"{name}|policy|availability_weighted"] = world.campaign(arms[name], "I2", weight=world.avail)
    units["seconds"]["total"] = round(time.time() - t0, 1)
    out_path.write_text(json.dumps(units, indent=None, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")
    print("written", out_path, units["seconds"]["total"], "s", flush=True)


if __name__ == "__main__":
    main()
