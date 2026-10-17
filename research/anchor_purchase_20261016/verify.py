"""Independently reconstruct hit utility from locked choices and raw records."""
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import time

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main():
    started, cpu = time.perf_counter(), time.process_time()
    freeze = json.loads((HERE / "FREEZE.json").read_text())
    for path, expected in freeze["inputs"].items():
        assert sha(ROOT / path) == expected, path
    results = json.loads((HERE / "RESULTS.json").read_text())
    pop = pd.read_csv(HERE / "metadata/population.csv").set_index("core")
    contexts = set(pd.read_csv(HERE / "metadata/contexts.csv").row_name)
    excluded = {"ACH-000219", "ACH-000681", "ACH-000019", "ACH-000552"}
    assert not contexts & excluded
    assert pop.groupby("connectivity").fold.nunique().max() == 1
    assert pop.groupby("family_component").fold.nunique().max() == 1
    for fit in json.loads((HERE / "artifacts/fit_provenance.json").read_text()):
        train, test = pop.loc[fit["train_cores"]], pop.loc[fit["query_cores"]]
        for key in ("connectivity", "family_component"):
            assert not set(train[key]) & set(test[key])
        assert not set(test.fold) & set(train.fold)
        assert fit["heldout_mutation_invariant"]
    # Independent standard-library criterion, no evaluator or aggregate import.
    outcomes = {}
    total_hits = Counter()
    total_unknown = Counter()
    for line in (HERE / "artifacts/terminal_records.jsonl").open(encoding="utf-8"):
        row = json.loads(line)
        key = (row["core"], row["context"])
        assert key not in outcomes
        a, b = row["x2"], row["x3"]
        if a is None or b is None:
            status = "unknown"
            total_unknown[row["core"]] += 1
        elif a < 0 and b < 0 and a + b <= -2:
            status = "hit"
            total_hits[row["core"]] += 1
        else:
            status = "inactive"
        outcomes[key] = status
    assert len(outcomes) == len(pop) * len(contexts)
    totals = defaultdict(Counter)
    campaign = {}
    base_by_core = {}
    choices = [json.loads(line) for line in (HERE / "artifacts/choices.jsonl").open(encoding="utf-8")]
    for row in choices:
        core, name, nominations = row["core"], row["arm"], row["nominations"]
        assert len(nominations) == len(set(nominations)) == row["confirmation_count"]
        assert set(nominations) <= contexts and not set(nominations) & excluded
        assert row["confirmation_count"] + row["anchor_cost"] <= 4
        assert row["modeled_spend"] == row["confirmation_count"] + row["anchor_cost"]
        counts = Counter(outcomes[(core, cell)] for cell in nominations)
        totals[name].update(counts)
        totals[name]["campaigns"] += 1
        campaign[(core, name)] = counts
        if name == "strong_selected":
            base_by_core[core] = nominations
    for name, counts in totals.items():
        assert counts["campaigns"] == len(pop), name
        assert counts["hit"] == results["arms"][name]["known_hits"], name
        assert counts["unknown"] == results["arms"][name]["unknown_nominations"], name
    for row in choices:
        if row["arm"].startswith("offset_only"):
            assert row["nominations"] == base_by_core[row["core"]][:row["confirmation_count"]]
    for k in (4, 3, 2, 1, 0):
        assert sum(min(total_hits[c], k) for c in pop.index) == results["headroom_oracle"][str(k)]["known_hit_bound"]
        assert sum(min(total_hits[c] + total_unknown[c], k) for c in pop.index) == results["headroom_oracle"][str(k)]["missing_upper_bound"]
    # Bootstrap implemented independently from saved per-campaign records.
    keys = sorted(set(pop.family_component))
    members = [[c for c in pop.index if pop.loc[c, "family_component"] == key] for key in keys]
    rng = np.random.default_rng(20261016)
    draws = rng.integers(len(keys), size=(2000, len(keys)))
    sizes = np.array([len(group) for group in members])
    for name in totals:
        deltas = {c: campaign[(c, name)]["hit"] - campaign[(c, "strong_selected")]["hit"] for c in pop.index}
        sums = np.array([sum(deltas[c] for c in group) for group in members])
        interval = np.quantile(sums[draws].sum(1) / sizes[draws].sum(1), [.025, .975])
        assert np.allclose(interval, results["arms"][name]["paired_group_bootstrap_95"], atol=1e-14)
    scores = np.load(HERE / "artifacts/scores.npz")
    for key in ("anchor",):
        updated = scores["strong"] + np.nan_to_num(scores[key])[:, None]
        assert np.array_equal(np.argsort(scores["strong"], axis=1, kind="stable"), np.argsort(updated, axis=1, kind="stable"))
    perm = scores["permutation"]
    assert sorted(perm.tolist()) == list(range(len(pop)))
    p = pop.reset_index()
    assert np.array_equal(p.fold.to_numpy(), p.fold.to_numpy()[perm])
    assert np.array_equal(p.compound_plate.to_numpy(), p.compound_plate.to_numpy()[perm])
    # Exact source provenance check on terminal records, independent CSV parsing.
    import csv
    lookup = {}
    for core, row in pop.iterrows():
        lookup[row.x2] = (core, "x2")
        lookup[row.x3] = (core, "x3")
    raw = ROOT / "data/external/prism_19q4/raw/secondary-screen-logfold-change.csv"
    with raw.open(newline="", encoding="utf-8") as stream:
        reader = csv.reader(stream)
        header = next(reader)
        indices = [(i, *lookup[column]) for i, column in enumerate(header) if column in lookup]
        assert len(indices) == len(pop) * 2
        reconstructed = {}
        for fields in reader:
            cell = fields[0]
            if cell not in contexts:
                continue
            for index, core, replicate in indices:
                text = fields[index]
                reconstructed.setdefault((core, cell), {})[replicate] = None if text in ("NA", "NaN", "nan", "") else float(text)
    for line in (HERE / "artifacts/terminal_records.jsonl").open(encoding="utf-8"):
        row = json.loads(line)
        source = reconstructed.get((row["core"], row["context"]), {"x2": None, "x3": None})
        for replicate in ("x2", "x3"):
            if source[replicate] is None:
                assert row[replicate] is None
            else:
                assert row[replicate] is not None and math.isclose(source[replicate], row[replicate], rel_tol=1e-12, abs_tol=1e-12)
        # Verify the biological criterion separately, at original CSV precision.
        a, b = source["x2"], source["x3"]
        raw_status = "unknown" if a is None or b is None else "hit" if a < 0 and b < 0 and a + b <= -2 else "inactive"
        assert outcomes[(row["core"], row["context"])] == raw_status
    receipt = {"passed": True, "campaigns_per_arm": len(pop), "executed_arms": len(totals),
               "raw_terminal_records_verified": len(outcomes),
               "checks": ["freeze", "metadata eligibility and disjoint identities", "training provenance and heldout mutation",
                          "anchor terminal separation", "budget and full denominator", "unknown distinct from inactive",
                          "utility reconstructed without evaluator import", "paired cluster intervals independently reconstructed",
                          "offset invariance", "shuffle strata", "records verified against original CSV"],
               "wall_seconds": time.perf_counter() - started, "cpu_seconds": time.process_time() - cpu,
               "artifacts": {p.name: sha(p) for p in sorted((HERE / "artifacts").iterdir()) if p.is_file()}}
    (HERE / "VERIFICATION.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
