"""Paired exploratory comparisons, keeping LLM prompt batches as clusters."""
import itertools
import json
import numpy as np
import pandas as pd
from experiment import HERE, interval, write


def signflip(x):
    x = np.asarray(x, float)
    signs = np.array(list(itertools.product((-1, 1), repeat=len(x))))
    return float(((signs*x).mean(1) >= x.mean()-1e-12).mean())


def main():
    rows = pd.DataFrame(json.loads((HERE / "policy_rows.json").read_text()))
    p = rows.pivot(index="key", columns="arm", values="hit")
    margin = rows.pivot(index="key", columns="arm", values="margin_hit")
    comparisons = {}
    for arm in ("sparse_hub", "fixed_pair", "empirical", "empirical_knn", "rkt_feedback_shuffled"):
        comparisons["rkt-"+arm] = {"hit":interval(p.rkt-p[arm]), "margin":interval(margin.rkt-margin[arm])}
    meta = json.loads((HERE / "metadata.json").read_text())
    keys = [meta["compounds"][i]["key"] for i in meta["pilot"]]
    records = json.loads((HERE / "agent_results.json").read_text())["records"]
    pilot = {a:p.loc[keys,a].to_numpy() for a in p.columns}
    pilot_margin = {a:margin.loc[keys,a].to_numpy() for a in margin.columns}
    fallbacks = {}
    agreement = {}
    for arm in ("C_agent_only","D_conventional","E_integrated"):
        ar = sorted([r for r in records if r["arm"]==arm], key=lambda r:r["batch"])
        assert [i for r in ar for i in r["indices"]] == meta["pilot"]
        pilot[arm] = np.array([h for r in ar for h in r["hits"]])
        pilot_margin[arm] = np.array([h for r in ar for h in r["margin_hits"]])
        fallbacks[arm] = sum(len(r["fallbacks"]) for r in ar)
        choices = np.array([t for r in ar for t in r["second"]])
        rp = rows[rows.arm == "rkt"].set_index("key").loc[keys,"second"].to_numpy()
        agreement[arm] = int((choices == rp).sum())
    strongest = max((a for a in p.columns if a != "rkt_feedback_shuffled"),key=lambda a:pilot[a].mean())
    # The strongest arm is selected after observing the pilot. Conservative max-baseline
    # comparison is descriptive; it is not a new independent confirmatory test.
    contrasts = {"E-C":pilot["E_integrated"]-pilot["C_agent_only"],
                 "E-D":pilot["E_integrated"]-pilot["D_conventional"],
                 "E-strongest":pilot["E_integrated"]-pilot[strongest],
                 "interaction":(pilot["E_integrated"]-pilot["C_agent_only"])-(pilot["rkt"]-pilot["empirical"])}
    stats = {name:{**interval(x.reshape(12,7).mean(1), alpha=.0125),
                   "p_one_sided":signflip(x.reshape(12,7).mean(1))} for name,x in contrasts.items()}
    ordered = sorted(stats,key=lambda k:stats[k]["p_one_sided"])
    adjusted = 0.
    for rank,name in enumerate(ordered):
        adjusted = max(adjusted,min(1.,stats[name]["p_one_sided"]*(4-rank)))
        stats[name]["p_holm"] = adjusted
    write("comparisons.json", {"full_library":comparisons, "pilot":{
        a:{"hits":int(x.sum()), "rate":float(x.mean()), "margin_hits":int(pilot_margin[a].sum()),
           "batch_ci95":interval(x.reshape(12,7).mean(1))["ci"]} for a,x in pilot.items()},
        "pilot_contrasts":stats, "strongest_pilot_baseline":strongest, "fallbacks":fallbacks,
        "same_second_line_as_rkt":agreement,
        "verdict":"EXPLORATORY_ONLY; NO_COMPONENT_PROMOTED"})
    print(json.dumps({"pilot":{a:int(x.sum()) for a,x in pilot.items()},"contrasts":stats}))


if __name__ == "__main__":
    main()
