"""Metadata-only feasibility of paid tumour/normal rank contrasts."""
from pathlib import Path
from collections import defaultdict
import hashlib, json
import pandas as pd
HERE=Path(__file__).resolve().parent
RAW=HERE.parents[1]/"research/eight_directions_20261026/evidence_audit/raw/PAIR_SCREEN.csv"
CELLS=["A673","MSKEWS-33838","MSKEWS-66647","SKNEP","TC-71","BJ","RPE"]
NORMAL={"BJ","RPE"}

def main():
    cols=["Cell line","Iteration","file","Well","Drug 1","Drug 2","Conc 1 (uM)","Conc 2 (uM)"]
    raw=pd.read_csv(RAW,usecols=cols,low_memory=False)
    controls={"dmso","high control","low control"}
    combo=raw[~raw["Drug 1"].isin(controls)&~raw["Drug 2"].isin(controls)&raw["Drug 1"].ne(raw["Drug 2"])].copy()
    combo["key"]=[tuple(sorted(((a,float(da)),(b,float(db))))) for a,b,da,db in combo[["Drug 1","Drug 2","Conc 1 (uM)","Conc 2 (uM)"]].itertuples(index=False,name=None)]
    hit=combo[combo.Iteration.eq("validation (ews hits, round 15)")]
    terminal=set.intersection(*(set(hit.loc[hit["Cell line"].eq(c),"key"]) for c in CELLS))
    low={k for k in terminal if all(d==.1 for _,d in k)}
    assert len(terminal)==1449 and len(low)==23
    query=raw[pd.to_numeric(raw.Iteration,errors="coerce").between(11,15)&raw["Cell line"].isin(CELLS)]
    groups=defaultdict(list)
    for (cell,stage,file),frame in query.groupby(["Cell line","Iteration","file"]):
        rows=sorted(tuple(map(str,r)) for r in frame[["Well","Drug 1","Drug 2","Conc 1 (uM)","Conc 2 (uM)"]].itertuples(index=False,name=None))
        sig=hashlib.sha256(json.dumps(rows).encode()).hexdigest()
        groups[(cell,stage,sig)].append(file)
    actions=[]
    for (cell,stage,sig),files in groups.items():
        assert len(files)==2
        keys=set(combo.loc[combo.file.isin(files),"key"])&low
        actions.append(dict(cell=cell,stage=stage,signature=sig,files=files,paid_plates=2,low_panel_keys=sorted(keys)))
    witnesses=[]
    for i,a in enumerate(actions):
        for j,b in enumerate(actions[:i]):
            if (a["cell"] in NORMAL)==(b["cell"] in NORMAL): continue
            common=set(a["low_panel_keys"])&set(b["low_panel_keys"])
            if len(common)>=2:
                witnesses.append(dict(actions=[j,i],cells=[b["cell"],a["cell"]],common_candidates=sorted(common),contrast_opportunities=len(common)*(len(common)-1)//2,paid_plates=4))
    old=combo[pd.to_numeric(combo.Iteration,errors="coerce").between(1,10)]
    result=dict(response_columns_loaded=False,QC_used=False,terminal_low_keys=sorted(low),source_pair_overlap=len(set(old.key)&low),
      source_low_keys_by_cell={c:len(set(old.loc[old["Cell line"].eq(c),"key"])&low) for c in CELLS},
      paired_actions=actions,four_plate_tumor_normal_contrast_designs=witnesses,
      summary=dict(actions=len(actions),actions_with_at_least_two_low_candidates=sum(len(a["low_panel_keys"])>=2 for a in actions),four_plate_designs_with_two_shared_candidates=len(witnesses)),
      limits=["Design opportunities, not observed rank reversal or mechanism.","Original labels, no authenticated stock/culture independence.","No QC or response used for selection."])
    (HERE/"contrast_design.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:result[k] for k in ["summary","source_low_keys_by_cell"]}))
if __name__=="__main__": main()
