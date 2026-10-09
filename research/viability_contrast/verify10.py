"""Raw-source, arithmetic and purchase replay verification of the repair pilot."""
import json

import numpy as np
import pandas as pd
from scipy.optimize import brentq
from scipy.stats import binom

from . import prepare, run6, run8, run9, run10


def upper(wrong, n, delta):
    if n == 0 or wrong == n:
        return 1.
    return float(brentq(lambda p: binom.cdf(wrong, n, p) - delta, 0., 1.))


def evaluate(e, threshold):
    if threshold is None:
        return {"decided": False, "wrong": False, "measurements": 0, "qc": 0}
    for step, (score, _) in enumerate(e["trajectory"]):
        if abs(score) >= threshold:
            return {"decided": True, "wrong": (score > 0) != (e["truth_sign"] > 0),
                    "measurements": step + 1, "qc": e["qc_prefix"][step]}
    return {"decided": False, "wrong": False, "measurements": len(e["trajectory"]),
            "qc": e["qc_prefix"][-1] if e["trajectory"] else 0}


def density(values, means, scales, tau):
    """Independent dense-covariance evaluation of the clipped working score."""
    if not len(values):
        return 0.
    residual = np.clip((values - means) / scales, -3., 3.) * scales
    covariance = np.diag(scales ** 2) + tau * np.ones((len(values), len(values)))
    return float(len(values) * np.log(2 * np.pi) + np.linalg.slogdet(covariance)[1]
                 + residual @ np.linalg.solve(covariance, residual))


def main():
    run10.freeze_check()
    out = run10.OUT
    orders_receipt = json.loads((out / "orders.json").read_text())
    trajectories = json.loads((out / "trajectories.json").read_text())
    calibration = json.loads((out / "calibration.json").read_text())
    summary = json.loads((out / "summary.json").read_text())
    pack = prepare.load_pack()
    classes, idx = pack["menu"]["classes"], pack["index"]
    ci = {c: k for k, c in enumerate(classes)}
    labels = np.array([ci.get(pack["meta"].loc[c, "moa_main"], -1) for c in pack["compounds"]])
    pool = np.array([pack["line_index"][l] for l in pack["menu"]["pool_lines"] if l in pack["line_index"]])
    train = orders_receipt["train"]
    positions = np.array([idx[c] for c in train])
    by_class = [[idx[c] for c in train if labels[idx[c]] == k] for k in range(len(classes))]
    fw = run6.FoldWorld(pack["auc"], by_class, positions, pool, run9.KEY, pack["meta"]["unit"].to_numpy())
    prior = run10.residual_prior(fw, pack["auc"], positions, labels, pool)
    tau, tau_pool = run8.estimate_tau2(pack["auc"], positions, labels, fw.med,
        fw.scale, fw.valid, fw.med_p, fw.scale_p, pool, len(classes))
    score_count = source_count = episode_count = 0
    for phase, field in (("training", "train"), ("calibration", "calibration"), ("evaluation", "evaluation")):
        for arm, episodes in trajectories[phase].items():
            assert [e["compound"] for e in episodes] == orders_receipt[field]
            for e in episodes:
                episode_count += 1
                purchased = e["purchase_positions"]
                assert len(purchased) == len(set(purchased)) == len(e["trajectory"])
                assert len(purchased) in (0, 16)
                source = pack["auc"][idx[e["compound"]], pool]
                expected_values = [float(source[p]) if np.isfinite(source[p]) else None for p in purchased]
                assert e["purchase_values"] == expected_values
                assert e["purchase_lines"] == [pack["lines"][pool[p]] for p in purchased]
                assert e["qc_prefix"] == np.cumsum([v is None for v in expected_values]).tolist()
                source_count += len(purchased)
                if not purchased:
                    assert e["pair"] is None
                    continue
                first, second = e["pair"]
                assert first < second
                assert e["truth_sign"] == (1 if labels[idx[e["compound"]]] == first else -1)
                pair = run6.class_pair_templates(fw.med, fw.scale, fw.valid,
                          fw.med_p, fw.scale_p, pool, first, second)
                for step, (score, charged) in enumerate(e["trajectory"]):
                    assert charged == step + 1
                    finite = np.array([p for p in purchased[:charged] if np.isfinite(source[p])], dtype=int)
                    d1 = density(source[finite], pair[0][0][finite], pair[0][1][finite], tau[first])
                    d2 = density(source[finite], pair[1][0][finite], pair[1][1][finite], tau[second])
                    np.testing.assert_allclose(score, .5 * (d2 - d1), atol=1e-9)
                    score_count += 1
    for a in run10.ARMS:
        for endpoint in ("marginal", "conditional"):
            table = calibration["tables"][a][endpoint]
            order = orders_receipt["orders"][a][endpoint]
            assert [r["threshold"] for r in table] == order[:len(table)]
            passing = []
            for row in table:
                results = [evaluate(e, row["threshold"]) for e in trajectories["calibration"][a]]
                d, w = sum(r["decided"] for r in results), sum(r["wrong"] for r in results)
                n = len(results) if endpoint == "marginal" else d
                bound = upper(w, n, .05 / 8)
                np.testing.assert_allclose(row["ucb"], bound, atol=1e-10)
                assert (row["n"], row["decided"], row["wrong"]) == (len(results), d, w)
                assert row["certified"] == (bound <= .05)
                if row["certified"]:
                    passing.append(row)
                else:
                    assert row is table[-1]
            best = max(passing, key=lambda r: (r["decided"], -r["threshold"])) if passing else None
            assert calibration["selected"][a][endpoint] == (best["threshold"] if best else None)
            evaluation = [evaluate(e, calibration["selected"][a][endpoint]) for e in trajectories["evaluation"][a]]
            arm = summary["arms"][f"{a}__{endpoint}"]
            assert arm["decided"] == sum(r["decided"] for r in evaluation)
            assert arm["wrong"] == sum(r["wrong"] for r in evaluation)
            assert arm["charged"] == sum(r["measurements"] for r in evaluation)
            assert arm["qc"] == sum(r["qc"] for r in evaluation)
    expected_rows = [{"arm": a, "endpoint": endpoint, "compound": e["compound"],
                      "unit": e["unit"], "supported": e["pair"] is not None,
                      **evaluate(e, threshold)}
                     for a in run10.ARMS for endpoint, threshold in calibration["selected"][a].items()
                     for e in trajectories["evaluation"][a]]
    pd.testing.assert_frame_equal(pd.DataFrame(expected_rows), pd.read_csv(out / "episodes.csv"))
    # Reexecute every purchase for a fixed outcome-blind subset, not just scores.
    subset = orders_receipt["evaluation"][:3]
    rivals = {int(k): v for k, v in orders_receipt["rivals"].items()}
    replay = run10.make_episodes(subset, pack, labels, pool, fw, prior, tau, tau_pool, rivals)
    for a in run10.ARMS:
        for actual, saved in zip(replay[a], trajectories["evaluation"][a][:3]):
            assert actual["purchase_positions"] == saved["purchase_positions"]
            assert actual["purchase_values"] == saved["purchase_values"]
            np.testing.assert_allclose(actual["trajectory"], saved["trajectory"], atol=1e-10)
    forecasts = pd.read_csv(out / "forecasts.csv")
    forecast_replay = pd.DataFrame(run10.forecast_check(subset, pack, labels, pool, fw, prior))
    pd.testing.assert_frame_equal(forecast_replay.reset_index(drop=True),
        forecasts[forecasts.compound.isin(subset)].reset_index(drop=True), check_exact=False)
    for a, group in forecasts.groupby("arm"):
        for metric in ("mse", "nll"):
            np.testing.assert_allclose(group[metric].mean(), summary["forecast_means"][a][metric])
    run10.freeze_check()
    receipt = {"passed": True, "episodes_source_checked": episode_count,
        "purchased_source_values_checked": source_count, "dense_covariance_score_checks": score_count,
        "acquisition_replay_episodes": len(subset) * len(run10.ARMS),
        "scope": "All recorded source values and scores checked; raw acquisition reexecuted on first3evaluation units only. Not an independent scientific outcome.",
        "outputs": {p.name: run9.digest(p) for p in out.iterdir() if p.is_file()}}
    print(json.dumps(receipt, indent=2))
    path = prepare.ROOT / "log/20261008/VIABILITY_CONTRAST_V10_VERIFY.json"
    if not path.exists():
        path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
