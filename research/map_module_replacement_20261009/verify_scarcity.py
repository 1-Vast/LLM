"""Independent reconstruction of scarce histories, tuning, paid posteriors and CI."""
import hashlib
import importlib.util
import json
from pathlib import Path
import time

import numpy as np
from scipy.stats import t
from threadpoolctl import threadpool_limits

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT/"outputs/map_module_replacement_20261009/scarcity"
spec = importlib.util.spec_from_file_location("independent_replacement_arithmetic", HERE/"verify.py")
independent = importlib.util.module_from_spec(spec); spec.loader.exec_module(independent)
SIZES, SEEDS = (4, 8, 16), (11, 23, 47)


def verify():
    started = time.perf_counter()
    for filename in ("SCARCITY_FREEZE.json", "SCARCITY_VERIFY_FREEZE.json"):
        for name, expected in json.loads((HERE/filename).read_text())["inputs"].items():
            assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == expected, name
    arrays = dict(np.load(independent.PACKET/"training_arrays.npz"))
    records = json.loads((ROOT/"outputs/knowledge_layer_validation_20261009/AUDIT.json").read_text())["records"]
    features = dict(np.load(ROOT/"outputs/paper_01286/released_test/FEATURES.npz"))
    kernels = independent.kernels(records, features)
    factors = dict(np.load(OUT/"FACTORS.npz"))
    choices = json.loads((OUT/"MODEL_CHOICES.json").read_text())
    results = json.loads((OUT/"RESULTS.json").read_text())
    summary = json.loads((OUT/"SUMMARY.json").read_text())
    complete = np.flatnonzero((arrays["availability_A"] & arrays["availability_B"]).all(1)).tolist()
    assert len(complete) == 43 and 31 not in complete and 34 not in complete
    assert len(choices) == 387 and len(results) == 2322 and len(factors) == 387*4
    rows_by_episode = {}
    for row in results:
        rows_by_episode.setdefault(row["episode"], []).append(row)
    episodes, purchases = 0, 0
    for held in complete:
        for seed in SEEDS:
            pool = np.array([cell for cell in complete if cell != held])
            order = np.random.default_rng(np.random.SeedSequence([seed, held])).permutation(pool)
            previous = set()
            for size in SIZES:
                key = f"ref{held}__seed{seed}__n{size}"
                choice = choices[key]
                train = sorted(order[:size].tolist())
                assert choice["train"] == train and previous < set(train) and held not in train
                previous = set(train)
                assert choice["context"] == held and choice["seed"] == seed and choice["history_size"] == size
                assert choice["residual_cells"] == train
                assert choice["mean_contexts"] == choice["covariance_contexts"] == size
                p = independent.prior(arrays, train, held)
                covariance, shift, cells, rho = independent.fit(arrays, train, kernels)
                independent.equal(p, factors[key+"__prior"])
                independent.equal(shift, factors[key+"__offset"])
                independent.equal(rho, choice["rho"])
                residuals = []
                for cell in train:
                    keep = [index for index in train if index != cell]
                    prediction = independent.prior(arrays, keep, cell)
                    residuals.append(np.r_[arrays["train_B"][cell]-prediction,
                        arrays["train_A"][cell]-prediction-independent.offset(arrays, keep)])
                residuals = np.array(residuals)
                independent.equal(residuals[:, :146], factors[key+"__error_B"])
                independent.equal(residuals[:, 146:], factors[key+"__error_A"])
                losses = {arm: {eta: [] for eta in independent.ETAS} for arm in independent.ARMS}
                for fold in range(3):
                    innerheld = train[fold::3]
                    keep = [cell for position, cell in enumerate(train) if position % 3 != fold]
                    recorded = choice["inner_folds"][fold]
                    innercov, innershift, innercells, innerrho = independent.fit(arrays, keep, kernels)
                    assert len(keep) >= 2 and innerheld == recorded["held"] and keep == recorded["train"]
                    assert set(innerheld).isdisjoint(keep) and innercells == recorded["residual_cells"]
                    independent.equal(innerrho, recorded["rho"])
                    for cell in innerheld:
                        prediction = independent.prior(arrays, keep, cell)
                        bought = independent.schedule(prediction)
                        for arm in independent.ARMS:
                            for eta in independent.ETAS:
                                c = (1-eta)*innercov["empirical"]+eta*innercov[arm]
                                updated = independent.update(np.r_[prediction, prediction+innershift], c,
                                    bought, arrays["train_A"][cell, bought])[:146]
                                losses[arm][eta].append(float(np.mean((updated-arrays["train_B"][cell])**2)))
                selected_covariances = {"empirical": covariance["empirical"]}
                for arm in independent.ARMS:
                    scores = {eta: float(np.mean(values)) for eta, values in losses[arm].items()}
                    independent.equal(list(scores.values()), [choice["arms"][arm]["inner_posterior_mse"][str(eta)] for eta in independent.ETAS])
                    eta = min(independent.ETAS, key=lambda value: (scores[value], value))
                    assert eta == choice["arms"][arm]["eta"]
                    selected_covariances[arm] = (1-eta)*covariance["empirical"]+eta*covariance[arm]
                group = rows_by_episode[key]
                assert {row["arm"] for row in group} == {"no_screen", "empirical", *independent.ARMS}
                assert len(group) == 6
                bought = independent.schedule(p)
                for row in group:
                    assert row["context"] == held and row["seed"] == seed and row["history_size"] == size
                    assert row["initial_selected"] == independent.top(p)
                    if row["arm"] == "no_screen":
                        expected = p
                        assert row["purchased_A"] == [] and row["cost"] == 5 and row["eta"] is None
                    else:
                        assert row["purchased_A"] == bought and len(set(bought)) == 8 and row["cost"] == 13
                        for step, index in enumerate(bought):
                            receipt = row["history"][step]
                            assert receipt["purchased_A"] == index and receipt["cumulative_A_cost"] == step+1
                            independent.equal(receipt["observed_A"], arrays["train_A"][held, index])
                        expected = independent.update(np.r_[p, p+shift], selected_covariances[row["arm"]],
                            bought, arrays["train_A"][held, bought])[:146]
                        purchases += 8
                    independent.equal(expected, row["posterior_mean_B"])
                    assert row["selected"] == independent.top(expected)
                    assert row["history"][-1]["committed_B"] == row["selected"]
                    assert row["history"][-1]["cost_after_five_B"] == row["cost"]
                    yB = arrays["train_B"][held]
                    independent.equal(yB[row["selected"]].sum(), row["terminal_B"])
                    independent.equal(yB[independent.top(p)].sum(), row["initial_B"])
                    independent.equal(np.mean((p-yB)**2), row["initial_mse"])
                    independent.equal(np.mean((expected-yB)**2), row["posterior_mse"])
                    independent.equal(row["terminal_B"]-row["initial_B"], row["delta_vs_no_screen"])
                    incoming, outgoing = sorted(set(row["selected"])-set(independent.top(p))), sorted(set(independent.top(p))-set(row["selected"]))
                    assert row["swapped_in"] == incoming and row["swapped_out"] == outgoing
                    pairs = list(zip(sorted(incoming, key=lambda i: (-expected[i], i)), sorted(outgoing, key=lambda i: (expected[i], i))))
                    assert [(r["incoming"], r["outgoing"]) for r in row["replacement_pairs"]] == pairs
                    for replacement in row["replacement_pairs"]:
                        independent.equal(replacement["B_delta"], yB[replacement["incoming"]]-yB[replacement["outgoing"]])
                    assert row["harmful_replacements"] == sum(yB[i]-yB[j] < -1e-12 for i, j in pairs)
                episodes += 1
        print(f"Verified scarcity histories, eta choices and receipts: ref{held}", flush=True)
    for size in SIZES:
        rows = [row for row in results if row["history_size"] == size]
        outcomes = {}
        for arm in ("no_screen", "empirical", *independent.ARMS):
            group = [row for row in rows if row["arm"] == arm]
            assert len(group) == 129
            outcomes[arm] = [np.mean([row["terminal_B"] for row in group if row["context"] == cell]) for cell in complete]
            recorded = summary["history_sizes"][str(size)][arm]
            assert recorded["contexts"] == 43 and recorded["seed_episodes"] == 129
            independent.equal(np.mean(outcomes[arm]), recorded["mean_B"])
            for field in ("initial_mse", "posterior_mse", "delta_vs_no_screen"):
                independent.equal(np.mean([row[field] for row in group]), recorded[field])
            assert sum(row["cost"] for row in group) == recorded["total_cost"]
            assert sum(row["delta_vs_no_screen"] < -1e-12 for row in group) == recorded["harm_seed_episodes"]
            assert sum(row["harmful_replacements"] for row in group) == recorded["harmful_replacements"]
            assert sum(len(row["replacement_pairs"]) for row in group) == recorded["replacements"]
            if arm in independent.ARMS:
                assert {str(eta): sum(row["eta"] == eta for row in group) for eta in independent.ETAS} == recorded["eta_frequencies"]
        for control in ("empirical", "molecule", "Morgan", "permutedknowledge", "no_screen"):
            delta = np.array(outcomes["knowledge"])-np.array(outcomes[control])
            radius = t.ppf(.975, 42)*delta.std(ddof=1)/np.sqrt(43)
            recorded = summary["paired_seed_mean_context_comparisons"][str(size)][control]
            independent.equal(delta.mean(), recorded["delta_B"])
            independent.equal([delta.mean()-radius, delta.mean()+radius], recorded["paired_context_95CI"])
            independent.equal(delta.mean()/np.mean(outcomes[control]), recorded["relative_delta"])
            assert recorded["improved_contexts"] == int((delta > 1e-12).sum())
            assert recorded["harmed_contexts"] == int((delta < -1e-12).sum())
    primary = summary["paired_seed_mean_context_comparisons"]["8"]
    gate = all(primary[control]["relative_delta"] > .02 and primary[control]["paired_context_95CI"][0] > 0
               for control in ("empirical", "molecule", "Morgan"))
    assert summary["primary_history_size"] == 8 and summary["registered_development_gate"] == gate
    payload = dict(status="PASS", episodes=episodes, result_rows=len(results), paid_A_receipts=purchases,
        contexts=43, inference_units=43, seed_repetitions=3, primary_history_size=8,
        checks=["All pinned inputs/verifier code", "Nested complete histories and excluded held units",
                "All residual factors, offsets and scarce means", "Every inner fold and eta choice",
                "All shared purchases, posterior means, terminal selections, utilities and replacement harms",
                "Seed-mean context aggregation, all fifteen paired comparisons and primary gate"],
        seconds=time.perf_counter()-started, scope="Independent numerical verification; no biological or risk certification")
    with (OUT/"VERIFIED.json").open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2, allow_nan=False); stream.write("\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    with threadpool_limits(limits=1):
        verify()
