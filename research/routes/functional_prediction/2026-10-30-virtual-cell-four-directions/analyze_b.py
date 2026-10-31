"""Apply frozen decision rules to complete out-of-source predictions only."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[3]
OUT=PROJECT/"data/processed/virtual_cell_four_directions_20261030/pilot_b_maestro"
CANDIDATE="conditional_residual"
DIAGNOSTIC="permuted_context"
FITNESS="Fitness / Proliferation / Viability"
DRUG="Drug / Chemical / Environmental Response"


def source_scores(frame, subset="rare"):
    return frame[frame.subset==subset].groupby(["method","group"]).precision.mean().unstack(0)


def strongest(table):
    means=table.mean()
    names=sorted(name for name in means.index if name not in [CANDIDATE,DIAGNOSTIC])
    return sorted(names,key=lambda name:(-means[name],name))[0]


def subgroup(frame, mask):
    part=frame[mask]
    table=source_scores(part)
    if table.empty:
        return {"groups":0,"status":"INCONCLUSIVE"}
    rival=strongest(table)
    delta=float(table[CANDIDATE].mean()-table[rival].mean())
    return {"groups":len(table),"tasks":int(part[part.subset=="rare"].dataset_name.nunique()),"strongest_baseline":rival,
            "candidate":float(table[CANDIDATE].mean()),"baseline":float(table[rival].mean()),"delta":delta,
            "passed":len(table)>=10 and delta>0}


def main():
    status=json.loads((OUT/"result.json").read_text(encoding="utf-8"))
    assert status["status"]=="complete" and status["completed_outer_folds"]==5
    frame=pd.read_csv(OUT/"scores.csv",dtype={"group":str,"dataset_name":str})
    assert not frame.duplicated(["dataset_name","method","subset"]).any()
    populations=frame.groupby(["method","subset"]).dataset_name.apply(lambda x:tuple(sorted(x))).tolist()
    assert all(x==populations[0] for x in populations)
    table=source_scores(frame)
    assert table.notna().all().all()
    baseline=strongest(table)
    delta=table[CANDIDATE]-table[baseline]
    rng=np.random.default_rng(1030)
    bootstrap=delta.to_numpy()[rng.integers(0,len(delta),(2000,len(delta)))].mean(axis=1)
    interval=np.quantile(bootstrap,[.025,.975]).tolist()
    by_fold=frame[(frame.subset=="rare") & frame.method.isin([CANDIDATE,baseline])].groupby(["fold","group","method"]).precision.mean().unstack("method")
    differences=(by_fold[CANDIDATE]-by_fold[baseline]).groupby("fold").mean().to_dict()
    all_scores=source_scores(frame,"all")
    drug=subgroup(frame,frame.category==DRUG)
    nonfitness=subgroup(frame,frame.category!=FITNESS)
    sensitivity=table.drop(index=["29083409","30971826"],errors="ignore")
    sensitivity_rival=strongest(sensitivity)
    absolute=float(delta.mean())
    relative=absolute/float(table[baseline].mean()) if table[baseline].mean()>0 else None
    all_delta=float(all_scores[CANDIDATE].mean()-all_scores[baseline].mean())
    context_delta=float(table[CANDIDATE].mean()-table[DIAGNOSTIC].mean())
    checks={"absolute_gain_at_least_.05":absolute>=.05,"relative_gain_at_least_20pct":relative is not None and relative>=.20,
            "paired_source_interval_lower_above_zero":interval[0]>0,"at_least_three_fold_improvements":sum(v>0 for v in differences.values())>=3,
            "all_library_loss_not_over_.02":all_delta>=-.02,"real_context_beats_permuted":context_delta>0,
            "drug_subset_benefit":drug.get("passed",False),"nonfitness_subset_benefit":nonfitness.get("passed",False)}
    expected=frame[frame.method==CANDIDATE].groupby(["subset","group"]).prevalence.mean().groupby("subset").mean().to_dict()
    result={"status":"CONTINUE_TO_INDEPENDENT_CAPABILITY_TEST" if all(checks.values()) else "NOT_PASSED_NO_AGENT_OR_PROMOTION",
            "eligible_tasks":len(populations[0]),"eligible_source_groups":len(table),"methods":len(table.columns),
            "primary_candidate_precision":float(table[CANDIDATE].mean()),"strongest_baseline":baseline,"baseline_precision":float(table[baseline].mean()),
            "absolute_delta":absolute,"relative_delta":relative,"source_bootstrap95":interval,"by_fold_delta":differences,
            "all_library_delta_vs_primary_rival":all_delta,"candidate_minus_permuted":context_delta,
            "drug":drug,"nonfitness":nonfitness,"gate_checks":checks,"random_expected_precision":expected,
            "excluding_two_largest_source_components":{"groups":len(sensitivity),"strongest_baseline":sensitivity_rival,
                "candidate":float(sensitivity[CANDIDATE].mean()),"baseline":float(sensitivity[sensitivity_rival].mean()),
                "delta":float(sensitivity[CANDIDATE].mean()-sensitivity[sensitivity_rival].mean())},
            "inference_limit":"Conditional source-resampling of exploratory benchmark predictions; no fresh biological or causal validation."}
    (ROOT/"b_decision.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    table.to_csv(OUT/"source_precision.csv")
    print(json.dumps(result,indent=2))


if __name__=="__main__":
    main()
