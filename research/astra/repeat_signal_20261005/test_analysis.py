"""Targeted invariants: condition matching, missingness and history separation."""
import numpy as np
import pandas as pd

from .analyze import COND, ID, choose_repeats, history_priors, metrics, add_ranks, top, wcorr


def fixture():
    rows=[]
    for sidm in ["target","h1","h2","h3","h4"]:
        for pair in range(2):
            for event in range(3):
                rows.append(dict(Tissue="Colon",SIDM=sidm,ANCHOR_ID=str(pair),LIBRARY_ID="9",
                    event=f"{sidm}_{event}",seeded=f"2020-01-{event+1:02d}",LIBRARY_CONC="10",
                    anchor_set="0.1;1",SEEDING_DENSITY="300",RESEARCH_PROJECT="GDSC_Colon",
                    DRUGSET_ID="1",local_days=4,CELL_ID="11",role="SV",pair=f"{pair}|9",
                    in_menu=True,n_anchor=2,design_plates=1,no_day1=False,y=float(pair+event),
                    hit=bool(pair),strict_hit=bool(pair),valid=True))
    return pd.DataFrame(rows)


def test_density_change_not_a_repeat():
    e=fixture();e.loc[e.SIDM.eq("target") & e.event.eq("target_0"),"SEEDING_DENSITY"]="600"
    strict,_=choose_repeats(e,{"target"});loose,_=choose_repeats(e,{"target"},False)
    assert strict.event1.eq("target_1").all()
    assert not loose.matches_all_conditions_12.any()


def test_qc_does_not_replace_earliest_event():
    e=fixture();e.loc[e.SIDM.eq("target") & e.event.eq("target_0"),"y"]=np.nan
    strict,a=choose_repeats(e,{"target"})
    assert strict.empty and a["qc_lost_primary"]==2


def test_incomplete_concentrations_excluded_by_design():
    e=fixture();e.loc[e.event.eq("target_0"),["n_anchor","anchor_set"]]=[1,"0.1"]
    strict,_=choose_repeats(e,{"target"})
    assert strict.event1.eq("target_1").all()


def test_history_excludes_all_target_events_and_disjoint_halves():
    e=fixture();target,_=choose_repeats(e,{"target"})
    a,meta=history_priors(e,target.copy(),{"target"})
    e.loc[e.SIDM.eq("target"),"y"]=1e9
    b,_=history_priors(e,target.copy(),{"target"})
    assert np.allclose(a.prior_full,b.prior_full)
    assert not set(meta["assignments"]["Colon"]["A"]) & set(meta["assignments"]["Colon"]["B"])
    assert a.history_n_full.eq(4).all()


def test_perfect_repeat_and_stable_ties():
    d=pd.DataFrame(dict(Tissue=["Colon"]*5,SIDM=["target"]*5,role=["SV"]*5,pair=list("edcba"),
         y1=np.arange(5.),y2=np.arange(5.),hit1=[0,0,0,1,1],hit2=[0,0,0,1,1],
         prior_full=np.zeros(5),prior_A=np.zeros(5),prior_B=np.zeros(5)))
    m=metrics(add_ranks(d))
    assert m["pearson"]==1 and m["positive_agreement"]==1 and m["top20_overlap"]==1
    assert np.flatnonzero(top(np.zeros(5),list("edcba"))).tolist()==[4]
    assert np.isnan(wcorr(np.ones(4),np.arange(4),np.ones(4)))
