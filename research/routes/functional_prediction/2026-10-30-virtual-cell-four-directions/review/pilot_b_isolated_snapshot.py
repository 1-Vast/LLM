"""Source-grouped exploratory binary-hit ranking; no official evaluation rows."""
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.linalg import cho_factor, cho_solve
from sklearn.decomposition import TruncatedSVD
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.utils.extmath import randomized_svd
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[3]
SOURCE = PROJECT / "data/external/virtual_cell_four_directions_20261030/assaybench"
OUT = PROJECT / "data/processed/virtual_cell_four_directions_20261030/pilot_b"
SEED = 1030
K = 50
ALPHAS = [0.1, 1.0, 10.0]
RANKS = [16, 32, 64]
CALIBRATION_COMPONENT = {"27260156", "29083409", "29038160", "27760321", "28162770"}
SAFE_FIELDS = ["phenotype", "condition_clause", "screen_rationale", "cell_line", "cell_type", "screen_type", "library_type"]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def context(meta, fields):
    return [" ".join(str(row.get(field,"")) for field in fields if str(row.get(field,"")) not in ["", "Not specified", "nan", "None"]) for row in meta]


def make_text(train, query, fields=SAFE_FIELDS):
    vectorizer = TfidfVectorizer(max_features=5000, stop_words="english", ngram_range=(1,2), min_df=2, dtype=np.float32)
    a = vectorizer.fit_transform(context(train, fields))
    b = vectorizer.transform(context(query, fields))
    return a, b


def weights(meta):
    counts = pd.Series([m["group"] for m in meta]).value_counts()
    w = np.array([1/counts[m["group"]] for m in meta], dtype=np.float64)
    return w / w.mean()


def prior_and_rare(measured, hit, meta):
    count = measured.sum(axis=0).astype(np.float64)
    prior = np.divide(hit.sum(axis=0), count, out=np.zeros_like(count), where=count>0)
    source_count = np.zeros(measured.shape[1], dtype=np.int32)
    groups = np.array([m["group"] for m in meta])
    for group in sorted(set(groups)):
        source_count += measured[groups == group].any(axis=0)
    return prior, (prior <= .10) & (source_count >= 3)


def evaluate(scores, measured, hit, rare, meta, method, fold, save=False):
    records, tops = [], []
    gene_order = np.arange(measured.shape[1])  # source vocabulary is lexical
    for i, row in enumerate(meta):
        for subset in ["all", "rare"]:
            eligible = measured[i] & (rare if subset == "rare" else True)
            ids = gene_order[eligible]
            if len(ids) < K or np.count_nonzero(measured[i] & rare) < K:
                continue
            rank = np.lexsort((ids, -np.asarray(scores[i,ids], dtype=float)))[:K]
            chosen = ids[rank]
            n_hit = int(hit[i,chosen].sum())
            total_hit = int(hit[i,ids].sum())
            prevalence = total_hit / len(ids)
            precision = n_hit/K
            records.append({"dataset_name":row["dataset_name"],"group":row["group"],"fold":fold,"method":method,
                            "subset":subset,"category":row["cleaned_phenotype"],"n_eligible":len(ids),
                            "n_true_hits":total_hit,"top50_hits":n_hit,"precision":precision,
                            "recall":n_hit/total_hit if total_hit else np.nan,"prevalence":prevalence,
                            "adjusted_precision":(precision-prevalence)/(1-prevalence) if prevalence<1 else np.nan})
            if save:
                tops.append({"dataset_name":row["dataset_name"],"method":method,"subset":subset,"genes":chosen.tolist()})
    return records, tops


def score_for_selection(scores, measured, hit, rare, meta):
    rows, _ = evaluate(scores, measured, hit, rare, meta, "selection", -1)
    rows = [r for r in rows if r["subset"] == "rare"]
    if not rows:
        return -np.inf
    frame = pd.DataFrame(rows)
    return float(frame.groupby("group").precision.mean().mean())


def kernel_predict(train_text, query_text, targets, w, alpha):
    sw = np.sqrt(w)
    gram = (train_text @ train_text.T).toarray().astype(np.float64)
    gram *= sw[:,None]*sw[None,:]
    gram.flat[::len(gram)+1] += alpha
    cross = (query_text @ train_text.T).toarray().astype(np.float64)
    transfer = cho_solve(cho_factor(gram, lower=True, check_finite=False), (cross*sw).T, check_finite=False).T
    return (transfer*sw) @ targets


def predictions(train_meta, query_meta, measured, hit, settings=None, include_controls=False):
    """Yield one prediction matrix at a time; targets only belong to train_meta."""
    prior, rare = prior_and_rare(measured, hit, train_meta)
    nq, ng = len(query_meta), measured.shape[1]
    w = weights(train_meta)
    yield "global", {}, np.broadcast_to(prior,(nq,ng)), rare
    balanced = np.divide(w@hit, w@measured, out=np.zeros(ng), where=(w@measured)>0)
    yield "source_balanced_global", {}, np.broadcast_to(balanced,(nq,ng)), rare
    for field, method in [("screen_type","screen_type"),("cleaned_phenotype","coarse_phenotype"),("screen_rationale","rationale")]:
        matrix = np.empty((nq,ng),dtype=np.float32)
        train_groups = np.array([m[field] for m in train_meta])
        for value in set(m[field] for m in query_meta):
            idx = train_groups == value
            pred = (hit[idx].sum(axis=0)+10*prior)/(measured[idx].sum(axis=0)+10)
            matrix[[i for i,m in enumerate(query_meta) if m[field]==value]] = pred
        yield method, {}, matrix, rare
        matrix = np.empty((nq,ng),dtype=np.float32)
        for value in set(m[field] for m in query_meta):
            idx = train_groups == value
            pred = (w[idx]@hit[idx]+10*balanced)/(w[idx]@measured[idx]+10)
            matrix[[i for i,m in enumerate(query_meta) if m[field]==value]] = pred
        yield "balanced_"+method, {}, matrix, rare
    a,b = make_text(train_meta,query_meta,["phenotype","condition_clause","screen_rationale"])
    similarities = (b@a.T).toarray()
    nearest = np.argsort(-similarities,axis=1,kind="stable")[:,:10]
    matrix = np.empty((nq,ng),dtype=np.float32)
    for i,idx in enumerate(nearest):
        den=measured[idx].sum(axis=0)
        matrix[i]=np.divide(hit[idx].sum(axis=0),den,out=np.zeros(ng),where=den>0)
    yield "official_style_knn", {"k":10}, matrix, rare
    a,b=make_text(train_meta,query_meta)
    similarity=(b@a.T).toarray()
    neighbor_settings = [settings["same_info_knn"]] if settings else [{"k":k} for k in [5,10,30]]
    for config in neighbor_settings:
        nearest=np.argsort(-similarity,axis=1,kind="stable")[:,:config["k"]]
        matrix=np.empty((nq,ng),dtype=np.float32)
        for i,idx in enumerate(nearest):
            den=measured[idx].sum(axis=0)
            matrix[i]=np.divide(hit[idx].sum(axis=0),den,out=np.zeros(ng),where=den>0)
        yield "same_info_knn", config, matrix, rare
    neighbor_settings = [settings["balanced_same_info_knn"]] if settings else [{"k":k} for k in [5,10,30]]
    for config in neighbor_settings:
        nearest=np.argsort(-similarity,axis=1,kind="stable")[:,:config["k"]]
        matrix=np.empty((nq,ng),dtype=np.float32)
        for i,idx in enumerate(nearest):
            den=w[idx]@measured[idx]
            matrix[i]=np.divide(w[idx]@hit[idx],den,out=np.zeros(ng),where=den>0)
        yield "balanced_same_info_knn", config, matrix, rare
    residual = (hit.astype(np.float32)-prior.astype(np.float32))*measured
    full_settings = [settings["full_rank_ridge"]] if settings else [{"alpha":x} for x in ALPHAS]
    for config in full_settings:
        yield "full_rank_ridge",config,prior+kernel_predict(a,b,residual,w,config["alpha"]),rare
    scale = np.sqrt(prior*(1-prior)+.01).astype(np.float32)
    standardized=residual/scale
    _,_,basis=randomized_svd(standardized*np.sqrt(w).astype(np.float32)[:,None],n_components=min(64,len(train_meta)-1),random_state=SEED,n_iter=3)
    latent=standardized@basis.T
    configs=[settings["conditional_residual"]] if settings else [{"rank":r,"alpha":alpha} for r in RANKS for alpha in ALPHAS]
    for config in configs:
        rank=min(config["rank"],len(basis))
        pred=kernel_predict(a,b,latent[:,:rank],w,config["alpha"])
        yield "conditional_residual",config,prior+(pred@basis[:rank])*scale,rare
    if include_controls:
        permutation=np.random.default_rng(SEED).permutation(len(train_meta))
        shuffled=[train_meta[i] for i in permutation]
        aa,bb=make_text(shuffled,query_meta)
        config=settings["conditional_residual"]
        rank=min(config["rank"],len(basis))
        pred=kernel_predict(aa,bb,latent[:,:rank],w,config["alpha"])
        yield "permuted_context",config,prior+(pred@basis[:rank])*scale,rare
    # Ordinary residual modes and a nonlinear tree on the same allowed context.
    _,_,ordinary_basis=randomized_svd(residual*np.sqrt(w).astype(np.float32)[:,None],n_components=min(64,len(train_meta)-1),random_state=SEED,n_iter=3)
    ordinary_latent=residual@ordinary_basis.T
    encoder=TruncatedSVD(n_components=min(64,min(a.shape)-1),random_state=SEED,n_iter=5)
    encoded=encoder.fit_transform(a)
    query_encoded=encoder.transform(b)
    configs=[settings["nonlinear_tree"]] if settings else [{"depth":d} for d in [4,8]]
    for config in configs:
        model=ExtraTreesRegressor(n_estimators=128,max_depth=config["depth"],min_samples_leaf=2,n_jobs=4,random_state=SEED)
        model.fit(encoded,ordinary_latent,sample_weight=w)
        yield "nonlinear_tree",config,prior+model.predict(query_encoded)@ordinary_basis,rare


def main():
    started=time.monotonic()
    cpu_started=time.process_time()
    OUT.mkdir(parents=True,exist_ok=True)
    if (OUT/"result.json").exists() or (OUT/"run_started.json").exists():
        raise SystemExit("Existing execution receipt; preserve evidence before any correction")
    z=np.load(SOURCE/"biogrid_temporal_train_gene_hits_csr.npz")
    meta=json.loads((SOURCE/"biogrid_temporal_train_metadata.json").read_text(encoding="utf-8"))
    genes=z["genes"]
    assert list(genes)==sorted(genes.tolist())
    assert [m["dataset_name"] for m in meta]==z["dataset_names"].tolist()
    assert all(m["yearfold0"]=="train" for m in meta)
    shape=tuple(z["shape"])
    measured=sparse.csr_matrix((np.ones(len(z["measured_indices"]),dtype=bool),z["measured_indices"],z["measured_indptr"]),shape=shape)
    hit=sparse.csr_matrix((np.ones(len(z["hit_indices"]),dtype=bool),z["hit_indices"],z["hit_indptr"]),shape=shape)
    assert (hit-hit.multiply(measured)).nnz==0
    keep=[i for i,m in enumerate(meta) if m["screen_category"]=="unidirectional" or m["dataset_name"].endswith(("_dec","_inc"))]
    meta=[meta[i] for i in keep]
    measured=measured[keep].toarray()
    hit=hit[keep].toarray()
    for row in meta:
        row["group"]="29083409" if row["source_id"] in CALIBRATION_COMPONENT else row["source_id"]
        row["fold"]=int(hashlib.sha256(("maestro-vc-b1:"+row["group"]).encode()).hexdigest()[:8],16)%5
    assert len(meta)==1231
    roster=pd.DataFrame(meta)[["dataset_name","source_id","group","fold","screen_category","cleaned_phenotype"]]
    roster.to_csv(OUT/"roster.csv",index=False)
    receipt={"status":"running","rows":len(meta),"sources":roster.group.nunique(),"source_sha256":digest(SOURCE/"biogrid_temporal_train_gene_hits_csr.npz"),
             "metadata_sha256":digest(SOURCE/"biogrid_temporal_train_metadata.json"),"script_sha256":digest(Path(__file__)),
             "protocol_sha256":digest(ROOT/"protocol_b_v1_1.md"),"roster_sha256":digest(OUT/"roster.csv"),"safe_fields":SAFE_FIELDS,
             "base_protocol_sha256":digest(ROOT/"protocol_b.md"),
             "calibration_component":sorted(CALIBRATION_COMPONENT),
             "python_executable":sys.executable,"seed":SEED,"compute_threads":4}
    (OUT/"run_started.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    rows,tops,selected=[],[],{}
    with threadpool_limits(limits=4):
        for fold in range(5):
            fits=np.array([i for i,m in enumerate(meta) if m["fold"] not in [fold,(fold+1)%5]])
            valid=np.array([i for i,m in enumerate(meta) if m["fold"]==(fold+1)%5])
            test=np.array([i for i,m in enumerate(meta) if m["fold"]==fold])
            choices={};best={};validation=[]
            for method,config,pred,rare in predictions([meta[i] for i in fits],[meta[i] for i in valid],measured[fits],hit[fits]):
                score=score_for_selection(pred,measured[valid],hit[valid],rare,[meta[i] for i in valid])
                validation.append({"method":method,"config":config,"source_macro_rare_precision":score})
                if method not in best or score>best[method]+1e-12:
                    best[method]=score;choices[method]=config
            if not all(np.isfinite(value) for value in best.values()):
                raise RuntimeError("INCONCLUSIVE: an inner fold has no scoreable rare tasks")
            selected[str(fold)]={"selected":choices,"validation":validation}
            train=np.array([i for i,m in enumerate(meta) if m["fold"]!=fold])
            for method,config,pred,rare in predictions([meta[i] for i in train],[meta[i] for i in test],measured[train],hit[train],choices,include_controls=True):
                assert np.isfinite(pred).all(),method
                metrics,top=evaluate(pred,measured[test],hit[test],rare,[meta[i] for i in test],method,fold,save=True)
                rows.extend(metrics);tops.extend(top)
            pd.DataFrame(rows).to_csv(OUT/"scores_interim.csv",index=False)
            (OUT/"selection_interim.json").write_text(json.dumps(selected,indent=2)+"\n",encoding="utf-8")
            print(json.dumps({"completed_fold":fold,"fit_rows":len(fits),"validation_rows":len(valid),"test_rows":len(test),"wall_seconds":time.monotonic()-started}),flush=True)
            if time.monotonic()-started>900:
                raise RuntimeError("Declared 15-minute job budget exceeded")
    scores=pd.DataFrame(rows)
    scores.to_csv(OUT/"scores.csv",index=False)
    (OUT/"top50.json").write_text(json.dumps({"gene_symbols":genes.tolist(),"predictions":tops}),encoding="utf-8")
    (OUT/"selection.json").write_text(json.dumps(selected,indent=2)+"\n",encoding="utf-8")
    summary=scores.groupby(["method","subset","group"])[["precision","adjusted_precision","recall"]].mean().groupby(["method","subset"]).mean().reset_index()
    summary.to_csv(OUT/"summary.csv",index=False)
    result={**receipt,"status":"complete","completed_outer_folds":5,"score_rows":len(scores),"prediction_rows":len(tops),"wall_seconds":time.monotonic()-started,
            "cpu_seconds":time.process_time()-cpu_started,"peak_working_set_bytes":None,"memory_measurement":"psutil unavailable in maestro; peak memory not measured by the script",
            "summary":summary.to_dict("records"),"interpretation":"Exploratory internal publication-grouped prediction only; no independent biological/causal/Agent/promotion claim."}
    (OUT/"result.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(summary.to_string(index=False),flush=True)


if __name__=="__main__":
    main()
