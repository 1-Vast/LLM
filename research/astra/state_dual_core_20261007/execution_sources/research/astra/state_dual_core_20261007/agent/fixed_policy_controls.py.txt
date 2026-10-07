"""Both declared fixed policies, no selection from held-out outcomes, no API."""
import json
from pathlib import Path
import time

import numpy as np

from replay import load_records, paired_doses, fit_transfer, replay_pair, sensitivity_choice, empirical_value_choice

root = Path(__file__).resolve().parent
main = root / "factorial_run1"
protocol = json.loads((main / "FACTORIAL_PROTOCOL.json").read_text())
supplement = json.loads((main / "FIXED_POLICY_SUPPLEMENT.json").read_text())
assert supplement["policies"] == ["sensitivity", "empirical_value"]
pairs = paired_doses(load_records(root / "technical_screen_bound_records.csv"))
lookup = {pair[0]["drug"]: pair for pair in pairs if pair[0]["split"] == "evaluation"}
agent_results = [json.loads(line) for line in (main / "factorial_actions.jsonl").read_text().splitlines()]
results = []
start = time.perf_counter()
for name, policy in (("sensitivity", sensitivity_choice), ("empirical_value", empirical_value_choice)):
    for index, drugs in enumerate(protocol["pairs"]):
        for world in ("reference", "state"):
            row = replay_pair(tuple(lookup[drug] for drug in drugs), world, fit_transfer(pairs, world),
                              main / "fixed_policy_runs", f"fixed-{name}-{world}-{index}", policy)
            row.update(policy=name, episode=index)
            results.append(row)
summary = {}
for policy in supplement["policies"]:
    effects = np.array([next(row["observed_selected_rms"] for row in results if row["policy"] == policy and row["world"] == "state" and row["episode"] == index) -
                       next(row["observed_selected_rms"] for row in results if row["policy"] == policy and row["world"] == "reference" and row["episode"] == index)
                       for index in range(len(protocol["pairs"]))])
    cd = np.array([next(row["decision_utility"] for row in agent_results if row["arm"] == "D" and row["episode"] == index) -
                   next(row["decision_utility"] for row in agent_results if row["arm"] == "C" and row["episode"] == index)
                   for index in range(len(protocol["pairs"]))])
    interaction = cd - effects
    rng = np.random.default_rng(719)
    boot = interaction[rng.integers(0, len(interaction), (10000, len(interaction)))].mean(axis=1)
    summary[policy] = {"mean_rms": {world: float(np.mean([row["observed_selected_rms"] for row in results if row["policy"] == policy and row["world"] == world])) for world in ("reference", "state")},
        "world_effect_fixed_policy": float(effects.mean()), "interaction_fixed_policy": float(interaction.mean()),
        "interaction_95_interval": np.quantile(boot, [.025, .975]).tolist()}
summary["resources"] = {"replay_access_units": sum(row["budget"]["recorded_use"] for row in results),
                        "API_calls": 0, "elapsed_seconds": time.perf_counter() - start, "laboratory_credits": 0}
(main / "fixed_policy_actions.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
(main / "fixed_policy_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
