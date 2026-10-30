"""One preregistered P0 analysis; no PRISM outcomes or predictive training."""
import csv, hashlib, itertools, json, re, time
from pathlib import Path
import numpy as np
from scipy.stats import spearmanr

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def fingerprint(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_gct(path, sealed):
    with path.open(encoding='utf-8-sig') as stream:
        assert next(stream).strip() == '#1.3'
        nr, nc, nrm, ncm = map(int, next(stream).split())
        reader = csv.reader(stream, delimiter='\t')
        header = next(reader)
        meta = {row[0]: row[nrm+1:] for row in itertools.islice(reader, ncm)}
        keep = [i for i, cid in enumerate(meta['pert_id'])
                if meta['pert_type'][i] == 'ctrl_vehicle' or
                (re.fullmatch(r'BRD-[A-Z]\d{8}', cid) and cid not in sealed)]
        probes, values = [], []
        for row in reader:
            assert len(row) == 1+nrm+nc
            probes.append(dict(zip(header[:nrm+1], row[:nrm+1])))
            values.append([float('nan') if row[nrm+1+i] in ('#N/A','NA','') else float(row[nrm+1+i]) for i in keep])
    assert len(probes) == nr and len(header[nrm+1:]) == nc
    return probes, {k: [v[i] for i in keep] for k, v in meta.items()}, np.array(values)


def main():
    start, cpu_start = time.perf_counter(), time.process_time()
    sealpath = ROOT/'research/knowledge_reality_20261013/sealed_compounds.csv'
    with sealpath.open(encoding='utf-8-sig') as stream:
        sealed = {x['core'] for x in csv.DictReader(stream)}
    receipts = json.loads((HERE/'p100_download_receipts.json').read_text(encoding='utf-8'))
    loaded = []
    for rec in receipts:
        path = ROOT/rec['path']
        assert fingerprint(path) == rec['sha256']
        loaded.append((path, rec, *read_gct(path, sealed)))
    common = set.intersection(*[{r['pr_id'] for r in probes if r['pr_probe_suitability_manual']=='TRUE'}
                               for _, _, probes, _, _ in loaded])
    rng = np.random.default_rng(2026102801)
    results = []
    for path, rec, probes, meta, raw in loaded:
        indices = [i for i, r in enumerate(probes) if r['pr_id'] in common]
        raw = raw[indices]
        finite = np.isfinite(raw)
        prov = sorted(set(meta['provenance_code']))
        result = {'file':path.name,'sha256':rec['sha256'],'cells':sorted(set(meta['cell_id'])),
            'plates':sorted(set(meta['det_plate'])),'provenance':prov,'shape_after_ID_probe_selection':list(raw.shape),
            'finite':int(finite.sum()),'missing':int((~finite).sum()),
            'positive':int((finite & (raw>0)).sum()),'zero':int((finite & (raw==0)).sum()),
            'negative':int((finite & (raw<0)).sum())}
        already_logged = all('L2X' in p.split('+') for p in prov)
        if not already_logged and result['negative']:
            result['status']='source_semantics_unresolved'
            results.append(result)
            continue
        logged = raw.copy() if already_logged else np.log2(np.where(raw>0,raw,np.nan))
        controls = [i for i,t in enumerate(meta['pert_type']) if t=='ctrl_vehicle']
        assert len(controls)==3
        response = logged - np.nanmean(logged[:,controls],axis=1,keepdims=True)
        treated = [i for i,t in enumerate(meta['pert_type']) if t=='trt_cp']
        ids = np.array(meta['pert_id'])[treated]
        profiles = response[:,treated].T
        correlations = np.full((len(treated),len(treated)),np.nan)
        for i,j in itertools.combinations(range(len(treated)),2):
            mask = np.isfinite(profiles[i]) & np.isfinite(profiles[j])
            if mask.sum()>=20 and np.ptp(profiles[i,mask])>0 and np.ptp(profiles[j,mask])>0:
                correlations[i,j]=correlations[j,i]=spearmanr(profiles[i,mask],profiles[j,mask]).statistic
        per_drug = []
        for cid in sorted(set(ids)):
            own = np.flatnonzero(ids==cid)
            assert len(own)==3
            within = np.array([correlations[i,j] for i,j in itertools.combinations(own,2)])
            between = correlations[np.ix_(own,np.flatnonzero(ids!=cid))].ravel()
            if np.isfinite(within).any() and np.isfinite(between).any():
                w,b = float(np.nanmean(within)),float(np.nanmean(between))
                per_drug.append({'id':cid,'within':w,'between':b,'difference':w-b})
        delta = np.array([x['difference'] for x in per_drug])
        bootstrap = rng.choice(delta,size=(1000,len(delta)),replace=True).mean(axis=1)
        result.update(status='descriptive_QC_completed',drugs=len(delta),per_drug=per_drug,
            mean_within=float(np.mean([x['within'] for x in per_drug])),
            mean_between=float(np.mean([x['between'] for x in per_drug])),mean_difference=float(delta.mean()),
            compound_resampling_interval=np.quantile(bootstrap,[.025,.975]).tolist(),
            biological_CI=None,biological_CI_reason='no independent culture/batch units established; one plate per cell',
            controls=len(controls),independent_function_outcome_read=False)
        results.append(result)
    import ctypes
    from ctypes import wintypes
    class Memory(ctypes.Structure):
        _fields_=[('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD)]+[(k,ctypes.c_size_t) for k in
            ('PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage',
             'QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage')]
    memory=Memory()
    memory.cb=ctypes.sizeof(memory)
    assert ctypes.windll.psapi.GetProcessMemoryInfo(ctypes.c_void_p(-1),ctypes.byref(memory),ctypes.sizeof(memory))
    out={'scope':'P0 measurement qualification only, not mechanism or decision benefit',
         'protocol_sha256':fingerprint(HERE/'PROTOCOL_P0_P100.md'),'sealed_metadata_sha256':fingerprint(sealpath),
         'common_suitable_probe_count':len(common),'strata':results,
         'wall_seconds':time.perf_counter()-start,'cpu_seconds':time.process_time()-cpu_start,
         'peak_working_set_bytes':memory.PeakWorkingSetSize,'scientific_model_training':0}
    (HERE/'p100_qc.json').write_text(json.dumps(out,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps({**out,'strata':[{k:v for k,v in s.items() if k!='per_drug'} for s in results]},ensure_ascii=False))


if __name__=='__main__':
    main()
