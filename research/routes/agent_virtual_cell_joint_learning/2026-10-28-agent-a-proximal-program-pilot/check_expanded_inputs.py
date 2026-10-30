"""Coordinator-only metadata check, independent of the unfinished worker report."""
import csv, hashlib, itertools, json, re
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def table(path):
    with path.open(encoding='utf-8-sig',newline='') as stream:
        return list(csv.DictReader(stream))


def core(value):
    found=re.match(r'^(BRD-[A-Z]\d{8})(?:-|$)',value)
    return found.group(1) if found else None


def main():
    receipts=json.loads((HERE/'p100_expanded_download_receipts.json').read_text(encoding='utf-8'))['receipts']
    sealed={r['core'] for r in table(ROOT/'research/knowledge_reality_20261013/sealed_compounds.csv')}
    samples=[]
    inputs=[]
    for rec in receipts:
        path=ROOT/rec['path']
        assert sha(path)==rec['sha256']
        with path.open(encoding='utf-8-sig') as stream:
            assert next(stream).strip()=='#1.3'
            nr,nc,nrm,ncm=map(int,next(stream).split())
            rows=csv.reader(stream,delimiter='\t')
            next(rows)
            cm={r[0]:r[nrm+1:] for r in itertools.islice(rows,ncm)}
        inputs.append({'file':rec['filename'],'sha256':rec['sha256'],'shape':[nr,nc],
            'cells':sorted(set(cm['cell_id'])),'provenance':sorted(set(cm['provenance_code']))})
        samples.extend([{**{k:v[i] for k,v in cm.items()},'source_file':rec['filename']} for i in range(nc)])
    prism=ROOT/'data/external/prism_19q4/raw'
    treatments=table(prism/'secondary-screen-replicate-collapsed-treatment-info.csv')
    cells=table(prism/'secondary-screen-cell-line-info.csv')
    pools=table(prism/'secondary-screen-pooling-info.csv')
    cell_ids={r['ccle_name'].split('_')[0]:r['depmap_id'] for r in cells if r['passed_str_profiling']=='TRUE'}
    support={(r['depmap_id'],r['screen_id']) for r in pools if r['passed_str_profiling']=='TRUE'}
    available=defaultdict(list)
    for r in treatments:
        cid=core(r['broad_id'])
        if cid is not None:
            available[(cid,Decimal(r['dose']))].append(r)
    candidates={}
    groups=defaultdict(set)
    for s in samples:
        if s['pert_type']!='trt_cp' or s['pert_iname'].lower() in ('staurosporine','vorinostat') or s['pert_id'] in sealed:
            continue
        cid=core(s['pert_id'])
        if cid is None or s['pert_dose_unit'] not in ('uM','um') or s['pert_time_unit']!='h':
            continue
        key=(cid,s['cell_id'],str(Decimal(s['pert_dose']).normalize()),s['pert_time'])
        groups[key].add((s['det_plate'],s['det_well'],s['pert_batch_internal_replicate']))
        candidates[key]=s
    matches=[]
    same_targets=defaultdict(set)
    for key,s in sorted(candidates.items()):
        cid,cell,dose,time=key
        rows=[r for r in available.get((cid,Decimal(dose)),[])
              if (cell_ids.get(cell),r['screen_id']) in support]
        if not rows:
            continue
        targets=sorted({r['target'] for r in rows if r['target'] not in ('NA','')})
        matches.append({'core':cid,'name':s['pert_iname'],'cell':cell,'dose_um':dose,'p100_time_h':time,
            'screens':sorted({r['screen_id'] for r in rows}),'target_annotation_sets':targets,
            'p100_repeat_metadata_keys':len(groups[key])})
        for annotation in targets:
            same_targets[(cell,annotation)].add(cid)
    target_groups=[{'cell':c,'target_annotation':t,'compounds':sorted(v)} for (c,t),v in sorted(same_targets.items()) if len(v)>=2]
    out={'scope':'metadata only; no PRISM response values; BRD core/dose equality is not exposure/engagement equality',
        'files':inputs,'sample_columns':len(samples),'candidate_drugs':len({k[0] for k in candidates}),
        'candidate_conditions':len(candidates),'nominal_exact_matches':matches,
        'matched_conditions':len(matches),'matched_drugs':len({r['core'] for r in matches}),
        'same_annotation_multiple_compounds_within_cell':target_groups,
        'candidate_repeat_key_counts':dict(Counter(len(v) for v in groups.values())),
        'known_independent_cultures':False,'response_missingness_or_structure_identity_verified':False}
    (HERE/'expanded_metadata_check.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in out.items() if k not in ('files','nominal_exact_matches','same_annotation_multiple_compounds_within_cell')},ensure_ascii=False))
    print(json.dumps(target_groups[:12],ensure_ascii=False))


if __name__=='__main__':
    main()
