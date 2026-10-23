"""Gate 0: certified discoveries per 1,000 confirmation wells for A0, A1, OA-PF and ORACLE (semi-synthetic worlds
calibrated by WORLD_FIT) and for A0, A1 and A1c on real reads. Writes GATE0_RESULTS.json and GATE0_REPLAYS.csv."""
import argparse
import csv
import json
import math
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np  # noqa: E402

from common import BOOT_SEED, BUDGETS, DATA, N_BOOT, N_REPLAYS, OUT, import_certification, replay_rng  # noqa: E402
from common import require_freeze, write_json  # noqa: E402
from gate1 import Builders, load, unit_wells  # noqa: E402
from replay import Bets, Pool, run_a1c, run_arm  # noqa: E402
from worldfit import draw_effects, draw_noise  # noqa: E402

SEMI_ARMS = ("A0", "A1", "OA-PF", "ORACLE")
REAL_ARMS = ("A0", "A1")
PASS_RATIO = 1.20


class Worlds:
    def __init__(self, J, A, fit, weights):
        self.J, self.A, self.fit, self.weights = J, A, fit, weights
        self.jR = (~np.isnan(J["X"])).sum(axis=1)
        self.a_wells = unit_wells(A["wells"])
        self.aR = (~np.isnan(A["X"])).sum(axis=1)
        self.g2 = np.nonzero(A["group"] == 2)[0]
        self.bets = {a: Bets(fit[a]["noise"]["sigma"], fit[a]["noise"]["nu"], weights[f"{a}_valid"])
                     for a in ("jaaks", "az")}

    def semi(self, pool, c, r):
        """Draw a semi-synthetic world: effects from the NPMLE prior, reads from the fitted t."""
        rng = replay_rng(pool, "semi", c, r)
        if pool == "jaaks_semi":
            nz = self.fit["jaaks"]["noise"]
            pr = self.fit["jaaks"]["primary"]
            K, width = self.J["X"].shape
            mu = draw_effects(rng, self.weights["jaaks"], K)
            X = mu[:, None] + draw_noise(rng, nz["sigma"], nz["nu"], (K, width))
            X[np.arange(width)[None, :] >= self.jR[:, None]] = np.nan
            n_o = np.maximum(self.J["n_o"], 1)
            p = pr["a"] + pr["b"] * mu + pr["sigma_p"] / np.sqrt(n_o) * rng.standard_t(nz["nu"], size=K)
            p[~np.isfinite(self.J["p"])] = np.nan
            return Pool(X, p, 7.0, mu), self.bets["jaaks"]
        nz = self.fit["az"]["noise"]
        if pool == "az_prospective":
            K = self.A["X"].shape[0]
            mu = draw_effects(rng, self.weights["az"], K)
            X = mu[:, None] + draw_noise(rng, nz["sigma"], nz["nu"], (K, 3))
            p = mu + draw_noise(rng, nz["sigma"], nz["nu"], K)
            return Pool(X, p, self.a_wells, mu), self.bets["az"]
        if pool == "az_matched_semi":
            K = self.g2.size
            mu = draw_effects(rng, self.weights["az"], K)
            X = mu[:, None] + draw_noise(rng, nz["sigma"], nz["nu"], (K, 2))
            X[np.arange(2)[None, :] >= (self.aR[self.g2] - 1)[:, None]] = np.nan
            p = mu + draw_noise(rng, nz["sigma"], nz["nu"], K)
            return Pool(X, p, self.a_wells[self.g2], mu), self.bets["az"]
        raise ValueError(pool)


def tables_for(pool, bets):
    tables = {"pf": bets.pf(pool.X)}
    if pool.mu is not None:
        tables["oracle"] = bets.oracle(pool.X, pool.mu)
    return tables


def ratio_ci(num, den, rng, n_boot=N_BOOT):
    num, den = np.asarray(num, dtype=float), np.asarray(den, dtype=float)

    def ratio(a, b):
        return a / b if b > 0 else (math.inf if a > 0 else math.nan)

    point = ratio(num.mean(), den.mean())
    idx = rng.integers(0, num.size, size=(n_boot, num.size))
    nm, dm = num[idx].mean(axis=1), den[idx].mean(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        boots = np.where(dm > 0, nm / np.where(dm > 0, dm, 1.0), np.where(nm > 0, np.inf, np.nan))
    boots = boots[~np.isnan(boots)]
    lo, hi = (np.quantile(boots, [0.025, 0.975], method="lower") if boots.size else (math.nan, math.nan))
    return {"ratio": point, "lo": float(lo), "hi": float(hi)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default=str(DATA))
    parser.add_argument("--out-dir", default=str(OUT))
    parser.add_argument("--replays", type=int, default=N_REPLAYS)
    parser.add_argument("--synthetic", action="store_true", help="dry run on synthetic inputs; skips the freeze check")
    args = parser.parse_args()
    if not args.synthetic:
        require_freeze()
    data_dir, out_dir = Path(args.data_dir), Path(args.out_dir)
    t0 = time.time()
    J, A = load(data_dir)
    fit = json.loads((out_dir / "WORLD_FIT.json").read_text(encoding="utf-8"))
    weights = dict(np.load(data_dir / "WORLD_FIT.npz", allow_pickle=False))
    worlds = Worlds(J, A, fit, weights)
    builders = Builders(J, A, args.replays)
    cert = import_certification()
    rows = []
    trace = {}
    for c in BUDGETS:
        for r in range(args.replays):
            for pool_name in ("jaaks_semi", "az_prospective", "az_matched_semi"):
                pool, bets = worlds.semi(pool_name, c, r)
                tables = tables_for(pool, bets)
                budget = min(c * pool.K, int(pool.R.sum()))
                for arm in SEMI_ARMS:
                    out = run_arm(arm, pool, bets, budget, replay_rng(pool_name, "semi", c, r, arm), tables)
                    n = out.pop("_n")
                    if c == 1 and r < 3:
                        trace[f"{pool_name}|{arm}|r{r}"] = n
                    rows.append({"pool": pool_name, "c": c, "r": r, "arm": arm, **out})
                rows.append({"pool": pool_name, "c": c, "r": r, "arm": "A1c",
                             **run_a1c(pool, replay_rng(pool_name, "semi", c, r, "A1c"), cert)})
            for pool_name, pool, bets in (("jaaks_real", builders.jaaks_real(r), worlds.bets["jaaks"]),
                                          ("az_matched_real", builders.az_matched_real(r), worlds.bets["az"])):
                tables = tables_for(pool, bets)
                budget = min(c * pool.K, int(pool.R.sum()))
                for arm in REAL_ARMS:
                    out = run_arm(arm, pool, bets, budget, replay_rng(pool_name, "real", c, r, arm), tables)
                    n = out.pop("_n")
                    if c == 1 and r < 3:
                        trace[f"{pool_name}|{arm}|r{r}"] = n
                    rows.append({"pool": pool_name, "c": c, "r": r, "arm": arm, **out})
                rows.append({"pool": pool_name, "c": c, "r": r, "arm": "A1c",
                             **run_a1c(pool, replay_rng(pool_name, "real", c, r, "A1c"), cert)})
        print("budget", c, "done", round(time.time() - t0, 1), "s", flush=True)
    np.savez_compressed(data_dir / "GATE0_TRACE.npz", **trace)
    fields = sorted({k for row in rows for k in row}, key=lambda k: (k not in ("pool", "c", "r", "arm"), k))
    with (data_dir / "GATE0_REPLAYS.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    results = summarise(rows, args.replays)
    results["seconds"] = round(time.time() - t0, 1)
    write_json(out_dir / "GATE0_RESULTS.json", results)
    print(json.dumps(results["decision"], indent=1))


def summarise(rows, n_replays):
    boot = np.random.default_rng(BOOT_SEED)
    table = {}
    for row in rows:
        table.setdefault((row["pool"], row["c"], row["arm"]), []).append(row)
    summary = {}
    for (pool, c, arm), rs in sorted(table.items()):
        rs = sorted(rs, key=lambda x: x["r"])
        entry = {k: float(np.mean([x[k] for x in rs])) for k in ("D", "wells", "eff")}
        entry["eff_q025"], entry["eff_q975"] = (float(q) for q in np.quantile([x["eff"] for x in rs], [0.025, 0.975]))
        entry["replays_with_zero_D"] = int(sum(x["D"] == 0 for x in rs))
        for k in ("D1", "reads", "fdp", "false", "audit", "audit_hit_rate", "false_label_fdp", "false_truth_fdp"):
            if k in rs[0]:
                entry[k] = float(np.mean([x[k] for x in rs]))
        summary[f"{pool}|c{c}|{arm}"] = entry

    def effs(pool, c, arm):
        return [x["eff"] for x in sorted(table[(pool, c, arm)], key=lambda x: x["r"])]

    ratios = {}
    for pool in ("jaaks_semi", "az_prospective", "az_matched_semi"):
        for c in BUDGETS:
            for num, den in (("ORACLE", "A1"), ("A1", "A0"), ("OA-PF", "A1"), ("ORACLE", "OA-PF")):
                ratios[f"{pool}|c{c}|{num}/{den}"] = ratio_ci(effs(pool, c, num), effs(pool, c, den), boot)
    for pool in ("jaaks_real", "az_matched_real"):
        for c in BUDGETS:
            ratios[f"{pool}|c{c}|A1/A0"] = ratio_ci(effs(pool, c, "A1"), effs(pool, c, "A0"), boot)
    decision = {}
    for asset, pool, real, matched in (("jaaks", "jaaks_semi", "jaaks_real", "jaaks_semi"),
                                       ("az", "az_prospective", "az_matched_real", "az_matched_semi")):
        r0 = ratios[f"{pool}|c1|ORACLE/A1"]
        zero_both = sum(a["D"] == 0 and b["D"] == 0 for a, b in
                        zip(sorted(table[(pool, 1, "ORACLE")], key=lambda x: x["r"]),
                            sorted(table[(pool, 1, "A1")], key=lambda x: x["r"])))
        if zero_both > n_replays / 2:
            label = "NOT_TESTABLE"
        else:
            label = "PASS" if r0["ratio"] >= PASS_RATIO and r0["lo"] > 1.0 else "FAIL"
        sim = np.array(effs(matched, 1, "A1"))
        lo, hi = np.quantile(sim, [0.025, 0.975])
        real_eff = summary[f"{real}|c1|A1"]["eff"]
        calibrated = bool(lo <= real_eff <= hi)
        decision[asset] = {"R0_oracle_over_A1_c1": r0, "label": label + ("" if calibrated else "_SIMULATOR_MISCALIBRATED"),
                           "headroom_label": label, "calibration": {"real_A1_eff_c1": real_eff,
                                                                    "semi_matched_A1_eff_q025": float(lo),
                                                                    "semi_matched_A1_eff_q975": float(hi),
                                                                    "inside": calibrated},
                           "replays_with_zero_D_in_both_arms": int(zero_both)}
    passes = sum(decision[a]["headroom_label"] == "PASS" for a in ("jaaks", "az"))
    decision["combined"] = ("GATE0_PASS" if passes == 2 else
                            "GATE0_MIXED_PRISM_TIEBREAK_PENDING" if passes == 1 else
                            "CERTIFIED_DISCOVERY_HEADROOM_INSUFFICIENT")
    return {"summary": summary, "ratios": ratios, "decision": decision, "replays": n_replays}


if __name__ == "__main__":
    main()
