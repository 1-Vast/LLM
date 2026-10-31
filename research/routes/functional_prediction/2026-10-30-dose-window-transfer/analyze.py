"""Compute the frozen C2 utility and continuation rule from completed predictions."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from pilot import ROOT, OUTPUT, ANCHORS, QUERIES, METHODS, choice_loss, load_data, sha


def main():
    if (OUTPUT/"summary.json").exists() or (OUTPUT/"decision.json").exists():
        raise SystemExit("Existing analysis: preserve outputs")
    run = json.loads((OUTPUT/"run.json").read_text())
    assert run["status"] == "complete" and len(run["completed_outer_cells"]) == 6
    cells, drugs, doses, wells = load_data()
    frame = pd.read_csv(OUTPUT/"predictions.csv", float_precision="round_trip")
    assert len(frame) == len(METHODS)*6*14*10
    assert not frame.duplicated(["method", "cell", "drug", "dose_index"]).any()
    truth = wells.mean(axis=-1)
    pair_roster = []
    from itertools import combinations
    for a,b in combinations(range(14), 2):
        lookup = {doses[b,qi]: qi for qi in QUERIES}
        points = [(qi,lookup[doses[a,qi]]) for qi in QUERIES if doses[a,qi] in lookup]
        if points:
            pair_roster.append((a,b,points))
    menus = {}
    for di in range(14):
        for qi in QUERIES:
            menus.setdefault(float(doses[di,qi]), []).append((di,qi))
    menus = {dose:menu for dose,menu in sorted(menus.items()) if len(menu)>=2}
    metrics, choice_rows = {}, []
    for method in METHODS:
        prediction = np.empty((6,14,10))
        part = frame[frame.method == method]
        for ci,cell in enumerate(cells):
            for di,drug in enumerate(drugs):
                rows = part[(part.cell == cell)&(part.drug == drug)].sort_values("dose_index")
                assert rows.dose_index.to_list() == list(range(10))
                assert np.allclose(rows.dose_M,doses[di],rtol=1e-14,atol=0)
                assert np.allclose(rows.y0,wells[ci,di,:,0],rtol=0,atol=1e-12)
                assert np.allclose(rows.y1,wells[ci,di,:,1],rtol=0,atol=1e-12)
                prediction[ci,di] = rows.prediction.to_numpy()
        assert np.isfinite(prediction).all()
        primary, technical0, technical1, best_drug, mse = {}, {}, {}, {}, {}
        counts = {"units":0,"observed":0,"predicted":0,"true_positive":0,"false_positive":0,"false_negative":0}
        flip_rows = []
        for ci,cell in enumerate(cells):
            p,t,w = prediction[ci],truth[ci],wells[ci]
            primary[cell] = choice_loss(p,t,pair_roster)
            technical0[cell] = choice_loss(p,w[:,:,0],pair_roster)
            technical1[cell] = choice_loss(p,w[:,:,1],pair_roster)
            mse[cell] = float(np.mean((p[:,QUERIES]-t[:,QUERIES])**2))
            menu_losses = []
            for dose,menu in menus.items():
                selected = min(menu,key=lambda k:(p[k],drugs[k[0]]))
                menu_losses.append(float(t[selected]-min(t[k] for k in menu)))
            best_drug[cell] = float(np.mean(menu_losses))
            for a,b,points in pair_roster:
                positive,negative,pred_pos,pred_neg = False,False,False,False
                for ia,ib in points:
                    pred_delta = float(p[a,ia]-p[b,ib])
                    pred_pos |= pred_delta>=.25
                    pred_neg |= pred_delta<=-.25
                    contrast = w[a,ia]-w[b,ib]
                    positive |= bool(np.all(contrast>=.25) and min(w[a,ia])>max(w[b,ib]))
                    negative |= bool(np.all(contrast<=-.25) and max(w[a,ia])<min(w[b,ib]))
                    chosen = a if p[a,ia]<=p[b,ib] else b
                    chosen_index = ia if chosen==a else ib
                    choice_rows.append({"method":method,"cell":cell,"first":drugs[a],"second":drugs[b],
                        "dose_M":doses[a,ia],"selected":drugs[chosen],"predicted_contrast":pred_delta,
                        "observed_contrast":float(t[a,ia]-t[b,ib]),
                        "regret":float(t[chosen,chosen_index]-min(t[a,ia],t[b,ib]))})
                observed,predicted = bool(positive and negative),bool(pred_pos and pred_neg)
                counts["units"] += 1
                counts["observed"] += observed
                counts["predicted"] += predicted
                counts["true_positive"] += observed and predicted
                counts["false_positive"] += predicted and not observed
                counts["false_negative"] += observed and not predicted
                flip_rows.append({"cell":cell,"first":drugs[a],"second":drugs[b],
                                  "observed":observed,"predicted":predicted})
        def aggregate(values):
            return {"aggregate":float(np.mean(list(values.values()))),"per_background":values}
        metrics[method] = {"primary":aggregate(primary),"technical_primary":{"well0":aggregate(technical0),"well1":aggregate(technical1)},
            "best_drug":aggregate(best_drug),"mse":aggregate(mse),"flips":{
                **counts,"sensitivity":counts["true_positive"]/counts["observed"] if counts["observed"] else None,
                "precision":counts["true_positive"]/counts["predicted"] if counts["predicted"] else None,
                "units_detail":flip_rows}}
    rivals = [m for m in METHODS if m not in ["candidate","wrong_shape"]]
    rival = min(rivals,key=lambda m:metrics[m]["primary"]["aggregate"])
    c,b = metrics["candidate"],metrics[rival]
    baseline,candidate = b["primary"]["aggregate"],c["primary"]["aggregate"]
    improvement = baseline-candidate
    per_cell = {cell:b["primary"]["per_background"][cell]-c["primary"]["per_background"][cell] for cell in cells}
    paired = np.array(list(per_cell.values()))
    indices = np.random.default_rng(1031).integers(0,6,size=(2000,6))
    interval = np.percentile(paired[indices].mean(axis=1),[2.5,97.5]).tolist()
    contrasts = {method:metrics[method]["primary"]["aggregate"]-candidate for method in ["linear","pooled_shape","wrong_shape"]}
    technical = {well:b["technical_primary"][well]["aggregate"]-c["technical_primary"][well]["aggregate"] for well in ["well0","well1"]}
    checks = {"matrix_complete":True,"absolute_gain":improvement>=.05,
        "relative_gain":baseline>0 and improvement/baseline>=.2,
        "improving_backgrounds":int(np.count_nonzero(paired>0))>=4,
        "conditional_interval":interval[0]>0,
        "linear_ablation":contrasts["linear"]>=.01,"pooled_ablation":contrasts["pooled_shape"]>=.01,
        "wrong_shape_ablation":contrasts["wrong_shape"]>=.01,
        "best_drug_safeguard":c["best_drug"]["aggregate"]<=b["best_drug"]["aggregate"],
        "technical_safeguard":all(value>=0 for value in technical.values())}
    summary = {"scope":"Retrospective exposed HTS001 background-held-out predictions; no independent cultures or unseen-chemical claim",
        "methods":metrics,"backgrounds":cells,"drug_count":14,"pair_count_per_background":len(pair_roster),
        "pair_dose_units_per_background":sum(len(p) for _,_,p in pair_roster),
        "query_conditions_per_background":84,"anchor_conditions_per_background":28,
        "best_drug_menus":[{"dose_M":d,"drugs":[drugs[di] for di,qi in menu]} for d,menu in menus.items()],
        "predictions_sha256":sha(OUTPUT/"predictions.csv"),"script_sha256":sha(Path(__file__))}
    decision = {"status":"PASSED_INTERNAL_GATE_ONLY" if all(checks.values()) else "NOT_PASSED_NO_HTS031_RELEASE",
        "strongest_baseline":rival,"candidate_primary":candidate,"baseline_primary":baseline,
        "baseline_oracle_headroom":baseline,"absolute_margin_attainable":baseline>=.05,
        "absolute_improvement":improvement,"relative_improvement":improvement/baseline if baseline>0 else None,
        "per_background_improvement":per_cell,"conditional_paired_background_bootstrap95":interval,
        "contrast_improvements":contrasts,"technical_improvements":technical,"gate_checks":checks,
        "gate_pass":all(checks.values()),"scope":"Fixed internal continuation heuristics, not statistical biological confirmation or core-promotion evidence"}
    pd.DataFrame(choice_rows).to_csv(OUTPUT/"choices.csv",index=False)
    (OUTPUT/"summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    (OUTPUT/"decision.json").write_text(json.dumps(decision,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"methods":{m:metrics[m]["primary"]["aggregate"] for m in METHODS},"decision":decision},indent=2))


if __name__ == "__main__":
    main()
