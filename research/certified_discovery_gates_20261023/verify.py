"""Independent recomputation of key numbers after Gates 0 and 1; writes VERIFICATION.json.

Re-derives the prepared data with the csv module (no pandas); recomputes the noise objective with adaptive quadrature
and probes its optimum; reruns the NPMLE from a random start; recomputes traced e-values with scipy.stats and e-BH
with a loop; recomputes the Gate 0 summary from the replay CSV; recomputes Gate 1b with tie-averaged expectations."""
from collections import defaultdict
import csv
import io
import json
import math
from pathlib import Path
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np  # noqa: E402
from scipy import integrate, stats  # noqa: E402

from common import (ALPHA, AZ_DESIGN, AZ_MEMBER, AZ_ZIP, DATA, JAAKS_ORIGINAL, JAAKS_VALIDATION, OUT, PF_MULTIPLES,  # noqa: E402
                    write_json)
from evalues import null_expectation_grid  # noqa: E402
from worldfit import invariant_loglik, npmle, read_loglik  # noqa: E402

CHECKS = []


def check(name, ok, detail):
    CHECKS.append({"check": name, "pass": bool(ok), "detail": detail})
    print(("PASS " if ok else "FAIL ") + name + ": " + str(detail), flush=True)


def fnum(text):
    try:
        v = float(text)
    except ValueError:
        return math.nan
    return v if math.isfinite(v) else math.nan


# ---------------------------------------------------------------- data

def jaaks_data(J):
    plates = {"o": defaultdict(lambda: [0.0, 0]), "v": defaultdict(lambda: [0.0, 0])}
    act = defaultdict(lambda: [0.0, 0, 0.0, 0])
    for tag, path in (("o", JAAKS_ORIGINAL), ("v", JAAKS_VALIDATION)):
        with open(path, encoding="utf-8", newline="") as stream:
            for row in csv.DictReader(stream):
                unit = "|".join([row["SIDM"].strip(), row["ANCHOR_ID"].strip(), repr(float(row["ANCHOR_CONC"])),
                                 row["LIBRARY_ID"].strip()])
                y = fnum(row["SYNERGY_DELTA_EMAX"])
                cell = plates[tag][(unit, row["BARCODE"].strip())]
                if not math.isnan(y):
                    cell[0] += y
                    cell[1] += 1
                if tag == "o":
                    a = act[unit]
                    av, le = fnum(row["ANCHOR_VIABILITY"]), fnum(row["LIBRARY_EMAX"])
                    if not math.isnan(av):
                        a[0] += av
                        a[1] += 1
                    if not math.isnan(le):
                        a[2] += le
                        a[3] += 1
    reads = defaultdict(list)
    for (unit, _), (s, n) in plates["v"].items():
        if n:
            reads[unit].append(s / n)
    prim = defaultdict(list)
    original_units = set()
    for (unit, _), (s, n) in plates["o"].items():
        original_units.add(unit)
        if n:
            prim[unit].append(s / n)
    pool = sorted(u for u, r in reads.items() if len(r) >= 2 and u in original_units)
    same_units = pool == list(J["unit"])
    check("Jaaks pool units re-derived with the csv module", same_units, f"{len(pool)} vs {len(J['unit'])}")
    if not same_units:
        return
    Xs = np.sort(J["X"], axis=1)
    worst = 0.0
    for i, u in enumerate(pool):
        mine = np.sort(reads[u])
        worst = max(worst, float(np.max(np.abs(mine - Xs[i, :len(mine)]))))
    p = np.array([np.mean(prim[u]) if prim[u] else np.nan for u in pool])
    p_ok = np.allclose(p, J["p"], equal_nan=True, atol=1e-12)
    inact = np.array([act[u][1] > 0 and act[u][3] > 0 and act[u][0] / act[u][1] >= 0.9 and act[u][2] / act[u][3] >= 0.9
                      for u in pool])
    check("Jaaks reads, primary means and inactive flags re-derived", worst < 1e-12 and p_ok and
          np.array_equal(inact, J["inactive"]),
          f"max read diff {worst:.1e}; primary equal {p_ok}; inactive {int(inact.sum())} vs {int(J['inactive'].sum())}")


def az_data(A):
    roles = json.loads(AZ_DESIGN.read_text(encoding="utf-8"))["role_cells"]
    exposed = set(roles["train"]) | set(roles["validation"]) | set(roles["test"])
    mats = {}
    with zipfile.ZipFile(AZ_ZIP) as archive, archive.open(AZ_MEMBER) as raw:
        reader = csv.reader(io.TextIOWrapper(raw, encoding="utf-8", newline=""))
        header = next(reader)
        ix = {k: i for i, k in enumerate(header)}
        for row in reader:
            if row[ix["MASTER_CELL_ID"]] not in exposed:
                continue
            key = (row[ix["BARCODE"]], row[ix["cmatrix"]])
            m = mats.setdefault(key, [row[ix["MASTER_CELL_ID"]], set(), 0.0, 0, 0, -math.inf, -math.inf, False])
            m[1].add((row[ix["lib1_drug_id"]].strip(), row[ix["lib2_drug_id"]].strip()))
            y = fnum(row[ix["Bliss_excess"]])
            m[4] += 1
            if not math.isnan(y):
                m[2] += y
                m[3] += 1
            h1, h2 = fnum(row[ix["lib1_yhat"]]), fnum(row[ix["lib2_yhat"]])
            if math.isnan(h1) or math.isnan(h2):
                m[7] = True
            m[5], m[6] = max(m[5], h1 if not math.isnan(h1) else -math.inf), max(m[6], h2 if not math.isnan(h2)
                                                                                 else -math.inf)
    units = defaultdict(list)
    mono = defaultdict(lambda: [-math.inf, -math.inf, False])
    for (barcode, _), (master, pairs, s, n, wells, h1, h2, nan) in mats.items():
        if len(pairs) != 1 or n < 0.8 * wells:
            continue
        a, b = sorted(next(iter(pairs)))
        name = f"{master}|{a}|{b}"
        units[name].append(s / n)
        mo = mono[name]
        mo[0], mo[1], mo[2] = max(mo[0], h1), max(mo[1], h2), mo[2] or nan
    names = sorted(units)
    same = names == list(A["unit"])
    check("AZ exposed units re-derived (reserve rows skipped first)", same, f"{len(names)} vs {len(A['unit'])}")
    if not same:
        return
    Xs = np.sort(A["X"], axis=1)
    worst = max(float(np.max(np.abs(np.sort(units[u]) - Xs[i, :len(units[u])]))) for i, u in enumerate(names))
    inact = np.array([(not mono[u][2]) and mono[u][0] <= 0.1 and mono[u][1] <= 0.1 for u in names])
    groups = np.array([3 if len(units[u]) >= 4 else 2 if len(units[u]) >= 2 else 1 for u in names])
    check("AZ reads, groups and inactive flags re-derived", worst < 1e-9 and np.array_equal(groups, A["group"]) and
          np.array_equal(inact, A["inactive"]),
          f"max read diff {worst:.1e}; inactive {int(inact.sum())} vs {int(A['inactive'].sum())}")


# ---------------------------------------------------------------- world fit

def noise_checks(name, X, noise):
    X = X[(~np.isnan(X)).sum(axis=1) >= 2]
    s, nu = noise["sigma"], noise["nu"]
    scale = noise["residual_fit"]["sigma"]
    rng = np.random.default_rng(5)
    idx = np.sort(rng.choice(X.shape[0], size=min(150, X.shape[0]), replace=False))
    exact = 0.0
    for row in X[idx]:
        x = np.sort(row[~np.isnan(row)])
        f = lambda m: float(np.exp(np.sum(stats.t.logpdf(x - m, nu, scale=s))))  # noqa: E731
        cuts = [-np.inf, *x, np.inf]
        exact += math.log(sum(integrate.quad(f, a, b, limit=500, epsabs=0, epsrel=1e-11)[0]
                              for a, b in zip(cuts[:-1], cuts[1:]) if a < b))
    approx = invariant_loglik(X[idx], s, nu, scale)
    check(f"{name} noise objective matches adaptive quadrature on 150 units", abs(approx - exact) < 1e-6 * abs(exact),
          f"{approx:.6f} vs {exact:.6f}")
    base = invariant_loglik(X, s, nu, scale)
    better = []
    for ds, dn in ((1.01, 1.0), (0.99, 1.0), (1.0, 1.05), (1.0, 0.95)):
        nu2 = min(max(nu * dn, 2.1), 100.0)
        val = invariant_loglik(X, s * ds, nu2, scale)
        if val > base + 1e-6 * abs(base):
            better.append((ds, dn, val - base))
    check(f"{name} noise fit is a local optimum (sigma +-1%, nu +-5%)", not better, f"improvements found: {better}")


def npmle_check(name, X, noise, ll_reported):
    LL = read_loglik(X, noise["sigma"], noise["nu"])
    top = LL.max(axis=1, keepdims=True)
    L = np.exp(LL - top)
    w = np.random.default_rng(9).dirichlet(np.ones(LL.shape[1]))
    for _ in range(5000):
        mix = L @ w
        w = w * (L.T @ (1.0 / mix)) / L.shape[0]
        w /= w.sum()
    ll = float(np.sum(np.log(L @ w)) + np.sum(top))
    check(f"{name} NPMLE log-likelihood reproduced from a random start", abs(ll - ll_reported) < 1e-4 * abs(ll_reported),
          f"{ll:.4f} vs reported {ll_reported:.4f}")


# ---------------------------------------------------------------- e-values and e-BH

def explicit_log_e(X, n, bets_per_unit, sigma, nu):
    """Mixture over each unit's bets of the product of t likelihood ratios over its first n reads (scipy.stats)."""
    out = np.zeros(X.shape[0])
    for u in range(X.shape[0]):
        x = X[u, :n[u]]
        if n[u] == 0:
            continue
        logs = [float(np.sum(stats.t.logpdf(x - m, nu, scale=sigma) - stats.t.logpdf(x, nu, scale=sigma)))
                for m in bets_per_unit[u]]
        top = max(logs)
        out[u] = top + math.log(sum(math.exp(v - top) for v in logs) / len(logs))
    return out


def loop_ebh(log_e, alpha=ALPHA):
    K = len(log_e)
    srt = sorted(log_e, reverse=True)
    for k in range(K, 0, -1):
        if srt[k - 1] >= math.log(K / (alpha * k)):
            return k
    return 0


def pf_bets(sigma, valid_grid):
    grid = valid_grid * sigma
    return [grid[np.searchsorted(grid, m * (1 + 1e-12), side="right") - 1] for m in PF_MULTIPLES * sigma]


def gate0_traces(fit, weights, rows):
    from gate0 import Worlds
    from gate1 import Builders, load
    J, A = load(DATA)
    worlds = Worlds(J, A, fit, weights)
    builders = Builders(J, A, 3)
    trace = dict(np.load(DATA / "GATE0_TRACE.npz", allow_pickle=False))
    recorded = {(r["pool"], r["arm"], int(r["r"])): r for r in rows if r["c"] == "1"}
    bad = []
    for key, n in sorted(trace.items()):
        pool_name, arm, rr = key.split("|")
        r = int(rr[1:])
        if pool_name in ("jaaks_real", "az_matched_real"):
            pool = builders.jaaks_real(r) if pool_name == "jaaks_real" else builders.az_matched_real(r)
            asset = "jaaks" if pool_name == "jaaks_real" else "az"
        else:
            pool, _ = worlds.semi(pool_name, 1, r)
            asset = "jaaks" if pool_name == "jaaks_semi" else "az"
        sigma, nu = fit[asset]["noise"]["sigma"], fit[asset]["noise"]["nu"]
        grid = np.linspace(0.05, 10.0, 200)[weights[f"{asset}_valid"]]
        if arm == "ORACLE":
            gs = grid * sigma
            bets = [[gs[max(np.searchsorted(gs, max(m, 0.0) * (1 + 1e-12), side="right") - 1, 0)]] for m in pool.mu]
        else:
            bets = [pf_bets(sigma, grid)] * pool.K
        ok_alloc = bool(np.all(n <= pool.R)) and int(n.sum()) == min(pool.K, int(pool.R.sum()))
        k = loop_ebh(explicit_log_e(pool.X, n, bets, sigma, nu))
        rec = recorded[(pool_name, arm, r)]
        wells = float((n * pool.wells).sum())
        if not (ok_alloc and k == int(rec["D"]) and abs(wells - float(rec["wells"])) < 1e-6):
            bad.append((key, k, rec["D"], ok_alloc))
    check("Gate 0 traced discoveries recomputed with scipy.stats and loop e-BH", not bad,
          f"{len(trace)} traces; mismatches {bad[:5]}")


def gate0_summary(rows, results):
    acc = defaultdict(list)
    for r in rows:
        acc[(r["pool"], r["c"], r["arm"])].append(float(r["eff"]))
    worst = 0.0
    for asset, pool in (("jaaks", "jaaks_semi"), ("az", "az_prospective")):
        ratio = np.mean(acc[(pool, "1", "ORACLE")]) / np.mean(acc[(pool, "1", "A1")])
        worst = max(worst, abs(ratio - results["decision"][asset]["R0_oracle_over_A1_c1"]["ratio"]))
    check("Gate 0 primary ratios recomputed from GATE0_REPLAYS.csv", worst < 1e-9, f"max abs diff {worst:.1e}")


def gate1_traces(fit, weights):
    trace = dict(np.load(DATA / "GATE1_TRACE.npz", allow_pickle=False))
    bad = []
    pools = sorted({k.split("|")[0] for k in trace})
    for name in pools:
        asset = "az" if name.startswith("AZ") else "jaaks"
        sigma, nu = fit[asset]["noise"]["sigma"], fit[asset]["noise"]["nu"]
        grid = np.linspace(0.05, 10.0, 200)[weights[f"{asset}_valid"]]
        gs = grid * sigma
        for part in ("null", "mixed"):
            X = trace[f"{name}|{part}|X"]
            for bettor, bets in (("pf", [pf_bets(sigma, grid)] * X.shape[0]),
                                 ("fixed3", [[gs[np.searchsorted(gs, 3 * sigma * (1 + 1e-12), side="right") - 1]]]
                                  * X.shape[0])):
                for nkey, lkey in (("n1", "le1"), ("n", "le")):
                    n = trace[f"{name}|{part}|{bettor}|{nkey}"]
                    le = trace[f"{name}|{part}|{bettor}|{lkey}"]
                    mine = explicit_log_e(X, n, bets, sigma, nu)
                    diff = float(np.max(np.abs(mine - le)))
                    if diff > 1e-7 or loop_ebh(mine) != loop_ebh(le):
                        bad.append((name, part, bettor, lkey, diff))
    check("Gate 1a traced e-values (PF and fixed 3 sigma) recomputed with scipy.stats", not bad,
          f"{len(pools)} pools; mismatches {bad[:5]}")


def gate1b_check(results):
    raw = dict(np.load(DATA / "DATA_JAAKS_RAW.npz", allow_pickle=False))
    NC = raw["NC"]
    vals = []
    for i in range(NC.shape[0]):
        refs = np.sort(NC[i][np.isfinite(NC[i])])
        k = refs.size
        bottom = math.ceil(0.05 * (k + 1))
        sel = (raw["well_plate"] == i) & (raw["well_loo_emax"] >= 0.9)
        for x in raw["well_intensity"][sel]:
            less = int(np.sum(refs < x))
            equal = int(np.sum(refs == x))
            prob = min(max((bottom - less) / (equal + 1), 0.0), 1.0)
            vals.append((k + 1) / bottom * prob)
    mean_exp = float(np.mean(vals)) if vals else math.nan
    rep = results["gate1b"]["L"]["mean_e"]
    check("Gate 1b Type L mean recomputed as a tie-averaged expectation", abs(mean_exp - rep) < 0.05,
          f"expected {mean_exp:.4f} vs reported (random tie-breaks) {rep:.4f}; wells {len(vals)}")
    n = results["gate1b"]["N"]
    check("Gate 1b Type N sanity check near 1", abs(n["mean_e"] - 1.0) < 4 * 4.4 / math.sqrt(max(n["wells"], 1)),
          f"mean {n['mean_e']:.4f} over {n['wells']} wells")


def composite_spot(fit):
    worst = 0.0
    from evalues import null_expectation
    for asset in ("jaaks", "az"):
        nu = fit[asset]["noise"]["nu"]
        for m in (0.05, 0.5, 2.0, 4.0, 10.0):
            for mu in (0.0, -0.3, -1.0, -5.0):
                q = null_expectation(m, mu, nu)
                worst = max(worst, abs(q - null_expectation_grid([m], mu, nu)[0]))
                if q > 1 + 1e-6:
                    worst = math.inf
    check("Composite-null spot checks by adaptive quadrature", worst < 1e-8, f"max |grid - quad| {worst:.1e}")


def main():
    fit = json.loads((OUT / "WORLD_FIT.json").read_text(encoding="utf-8"))
    weights = dict(np.load(DATA / "WORLD_FIT.npz", allow_pickle=False))
    J = dict(np.load(DATA / "DATA_JAAKS.npz", allow_pickle=False))
    A = dict(np.load(DATA / "DATA_AZ.npz", allow_pickle=False))
    jaaks_data(J)
    az_data(A)
    noise_checks("Jaaks", J["X"], fit["jaaks"]["noise"])
    noise_checks("AZ", A["X"][A["group"] >= 2], fit["az"]["noise"])
    npmle_check("Jaaks", J["X"], fit["jaaks"]["noise"], fit["jaaks"]["prior"]["loglik"])
    npmle_check("AZ", A["X"], fit["az"]["noise"], fit["az"]["prior"]["loglik"])
    composite_spot(fit)
    with (DATA / "GATE0_REPLAYS.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    gate0_traces(fit, weights, rows)
    gate0_summary(rows, json.loads((OUT / "GATE0_RESULTS.json").read_text(encoding="utf-8")))
    gate1_traces(fit, weights)
    gate1b_check(json.loads((OUT / "GATE1_RESULTS.json").read_text(encoding="utf-8")))
    write_json(OUT / "VERIFICATION.json", {"checks": CHECKS, "all_pass": all(c["pass"] for c in CHECKS)})
    print("all pass:", all(c["pass"] for c in CHECKS))


if __name__ == "__main__":
    main()
