"""Frozen E003 diagnostic. Parse numeric outcomes only for source/fixed probes."""
from pathlib import Path
from collections import Counter, defaultdict
from decimal import Decimal
import csv, hashlib, json, math
import numpy as np

HERE=Path(__file__).resolve().parent
RAW=HERE.parents[1]/"research/eight_directions_20261026/evidence_audit/raw/PAIR_SCREEN.csv"
PROBES={"a":tuple(sorted([("Axitinib","0.1"),("Dexrazoxane","0.1")])),
        "b":tuple(sorted([("Axitinib","0.1"),("Lestaurtinib","0.1")]))}
PLATES={"147":"BJ","148":"BJ","157":"A673","158":"A673"}

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""): h.update(block)
    return h.hexdigest()

def probe(row):
    names={row["Drug 1"],row["Drug 2"]}
    if "Axitinib" not in names or not names&{"Dexrazoxane","Lestaurtinib"}: return None
    key=tuple(sorted([(row["Drug 1"],str(Decimal(row["Conc 1 (uM)"]).normalize())),
                      (row["Drug 2"],str(Decimal(row["Conc 2 (uM)"]).normalize()))]))
    return next((label for label,value in PROBES.items() if value==key),None)

def main():
    assert sha(RAW)=="56a4e4a195673160edcb1baa209a15409b3639ff6ab0405558cc5ab3198d5f23"
    fees=Counter(); paid=[]; source=[]; parsed=Counter()
    with RAW.open(encoding="utf-8-sig",newline="") as stream:
        for row in csv.DictReader(stream):
            stage=row["Iteration"]
            is_source=stage.isdigit() and 1<=int(stage)<=10
            is_paid=stage=="11" and row["Plate"] in PLATES
            if not(is_source or is_paid): continue
            if is_paid:
                assert row["Cell line"]==PLATES[row["Plate"]]
                fees[(row["Cell line"],row["Plate"],row["file"])]+=1
            label=probe(row)
            if label is None: continue
            qc=row["Failed QC"].strip().lower()
            assert qc in ["true","false"]
            value=float(row["Viability"])
            assert math.isfinite(value)
            item=dict(cell=row["Cell line"],stage=stage,plate=row["Plate"],file=row["file"],well=row["Well"],probe=label,y=value,failed_QC=qc=="true")
            (source if is_source else paid).append(item); parsed[stage]+=1
    assert len(fees)==4 and sum(fees.values())==1532 and len(paid)==8
    grouped=defaultdict(dict)
    for item in paid:
        assert item["probe"] not in grouped[(item["cell"],item["plate"])]
        grouped[(item["cell"],item["plate"])][item["probe"]]=item
    differences=[]
    for (cell,plate),values in sorted(grouped.items()):
        assert set(values)=={"a","b"}
        differences.append(dict(cell=cell,plate=plate,d=values["a"]["y"]-values["b"]["y"],
                                any_probe_failed=any(v["failed_QC"] for v in values.values())))
    source_groups=defaultdict(lambda:defaultdict(list))
    for item in source:
        if not item["failed_QC"]: source_groups[(item["cell"],item["file"])][item["probe"]].append(item["y"])
    source_orders=[]
    for (cell,file),values in source_groups.items():
        if set(values)=={"a","b"}:
            source_orders.append(dict(cell=cell,file=file,d=float(np.mean(values["a"])-np.mean(values["b"]))))
    positive=any(x["d"]>0 for x in source_orders); negative=any(x["d"]<0 for x in source_orders)
    sensitivity=[]
    for epsilon in [0,.01,.05,.1]:
        signs={c:[int(np.sign(x["d"])) if abs(x["d"])>epsilon else 0 for x in differences if x["cell"]==c] for c in ["A673","BJ"]}
        valid=not any(x["any_probe_failed"] for x in differences)
        consistent=all(len(v)==2 and v[0]==v[1] and v[0]!=0 for v in signs.values())
        crossing=valid and consistent and signs["A673"][0]!=signs["BJ"][0]
        sensitivity.append(dict(epsilon=epsilon,signs=signs,repeat_consistent_crossing=crossing,
                                outcome="observed_crossing_not_calibrated_latent_rejection" if crossing else "not_demonstrated_or_inconclusive"))
    out=dict(kind="functional_model_diagnostic_not_learning_gain",source_probe_rows=source,
      source_same_file_orders=source_orders,source_already_has_observed_order_discordance=positive and negative,
      paid_probe_rows=paid,differences=differences,sensitivity=sensitivity,
      budget=dict(physical_plates=4,exported_well_records=sum(fees.values()),new_wet_experiments=0),
      numerically_parsed_stage_counts=dict(parsed),terminal_stage_outcomes_used=False,
      files={str(p.relative_to(HERE.parents[1])):sha(p) for p in [RAW,HERE/"PROTOCOL.md",HERE/"CANDIDATE.md",Path(__file__)]},
      uncertainty=dict(CI95=None,reason="two unauthenticated technical files per cell; no independent culture/noise model"),
      limits=["Raw label/dose correspondence only.","Rank contradiction rejects only the noise-free shared scalar order, not a biological mechanism.",
              "No new predictor, selected action advantage, independent decision gain, unseen drug or cross-source transfer tested."])
    (HERE/"CONTRAST_RESULTS.json").write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:out[k] for k in ["source_same_file_orders","source_already_has_observed_order_discordance","differences","sensitivity","budget"]},indent=2))
if __name__=="__main__": main()
