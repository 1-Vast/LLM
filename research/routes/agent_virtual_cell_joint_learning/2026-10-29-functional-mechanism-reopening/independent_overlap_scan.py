import csv, json, hashlib, time, ctypes, ctypes.wintypes as wt
from pathlib import Path
start=time.monotonic(); cpu_start=time.process_time()
SRC=Path(r'D:\MAESTRO\tmp\extq1\GDSC2_fitted_dose_response.csv')
OUT=Path(r'D:\MAESTRO\research\2026-10-29-functional-mechanism-reopening\independent_overlap_result.json')
EXPECTED='0883b3ef6e440603094c43c74044e1d333fce61e92e3efa374ea3a54f0b50302'
COLS=('DATASET','CELL_LINE_NAME','SANGER_MODEL_ID','COSMIC_ID','DRUG_ID','DRUG_NAME','MIN_CONC','MAX_CONC')
class PMC(ctypes.Structure):
    _fields_=[('cb',wt.DWORD),('PageFaultCount',wt.DWORD),('PeakWorkingSetSize',ctypes.c_size_t),('WorkingSetSize',ctypes.c_size_t),('QuotaPeakPagedPoolUsage',ctypes.c_size_t),('QuotaPagedPoolUsage',ctypes.c_size_t),('QuotaPeakNonPagedPoolUsage',ctypes.c_size_t),('QuotaNonPagedPoolUsage',ctypes.c_size_t),('PagefileUsage',ctypes.c_size_t),('PeakPagefileUsage',ctypes.c_size_t)]
ctypes.windll.kernel32.GetCurrentProcess.restype=wt.HANDLE
handle=ctypes.windll.kernel32.GetCurrentProcess()
ctypes.windll.psapi.GetProcessMemoryInfo.argtypes=[wt.HANDLE,ctypes.POINTER(PMC),wt.DWORD]
peak_ws=peak_commit=0; samples=0

def check():
    global peak_ws,peak_commit,samples
    p=PMC(); p.cb=ctypes.sizeof(p)
    if not ctypes.windll.psapi.GetProcessMemoryInfo(handle,ctypes.byref(p),p.cb): raise ctypes.WinError()
    peak_ws=max(peak_ws,p.PeakWorkingSetSize); peak_commit=max(peak_commit,p.PeakPagefileUsage); samples+=1
    if time.process_time()-cpu_start>60: raise RuntimeError('CPU budget exceeded')
    if time.monotonic()-start>90: raise RuntimeError('wall budget exceeded')
    if max(peak_ws,peak_commit)>256*1024*1024: raise RuntimeError('sampled peak memory budget exceeded')

def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):
            h.update(b); check()
    return h.hexdigest()

def norm(s): return s.casefold().translate(str.maketrans('','',' -_'))

if OUT.exists(): raise RuntimeError('independent output already exists; refuse rerun')
source_before=digest(SRC)
if source_before!=EXPECTED: raise RuntimeError('source hash mismatch')
cells={'jurkat','hek293'}; drugs={'dasatinib','dinaciclib','crizotinib'}
row_count=0; cell_counts={}; drug_counts={}; joint_counts={}; unique={}
with SRC.open('r',encoding='utf-8-sig',newline='') as f:
    reader=csv.reader(f); header=next(reader)
    indices={k:header.index(k) for k in COLS if k in header}
    if 'CELL_LINE_NAME' not in indices or 'DRUG_NAME' not in indices: raise RuntimeError('matching columns missing')
    for tokens in reader:
        row_count+=1
        # The only data-token accesses are the explicitly whitelisted indices.
        metadata={k:tokens[i] for k,i in indices.items()}
        c=metadata['CELL_LINE_NAME']; d=metadata['DRUG_NAME']
        cm=norm(c) in cells; dm=norm(d) in drugs
        if cm: cell_counts[c]=cell_counts.get(c,0)+1
        if dm: drug_counts[d]=drug_counts.get(d,0)+1
        if cm and dm:
            pair=(c,d); joint_counts[pair]=joint_counts.get(pair,0)+1
            key=tuple(metadata[k] for k in indices)
            if key not in unique: unique[key]={'metadata':metadata,'source_row_count':0}
            unique[key]['source_row_count']+=1
        if row_count%4096==0: check()
check(); source_after=digest(SRC)
if source_after!=source_before: raise RuntimeError('source changed')
result={
 'scope':'independent fixed-source metadata qualification only',
 'source':{'path':str(SRC),'sha256_before':source_before,'sha256_after':source_after,'bytes':SRC.stat().st_size,'total_data_rows':row_count},
 'independence':{'primary_code_read_before_freeze':False,'primary_result_read_before_freeze':False,'metadata_scans':1,'executed_source_path':str(Path(__file__)),'executed_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
 'columns_accessed':list(indices),'columns_missing':[k for k in COLS if k not in indices],
 'normalization':'casefold; remove ASCII space, hyphen, underscore only; no aliases or clone merges',
 'targets':{'cells':['JURKAT','HEK293'],'drugs':['DASATINIB','DINACICLIB','CRIZOTINIB']},
 'individual_cell_name_matches':[{'raw_name':k,'source_row_count':v} for k,v in sorted(cell_counts.items())],
 'individual_drug_name_matches':[{'raw_name':k,'source_row_count':v} for k,v in sorted(drug_counts.items())],
 'joint_pair_matches':[{'raw_cell_name':k[0],'raw_drug_name':k[1],'source_row_count':v} for k,v in sorted(joint_counts.items())],
 'joint_matching_source_rows':sum(joint_counts.values()),'unique_joint_metadata_rows':len(unique),
 'unique_joint_metadata':sorted(unique.values(),key=lambda x:tuple(x['metadata'][k] for k in indices)),
 'concentration_unit':'unknown',
 'limitations':['Name matches do not establish cultured biological equivalence, clone identity, timing, assay system, same-dose function or engagement pairing.','No formal concentration-unit contract was inspected; numerical concentration strings are preserved without response parsing or unit inference.','Absence in this fixed table does not establish absence in all public resources.','Metadata qualification does not validate molecular H, intervention error bounds, a novel algorithm, agent benefit, or scientific PASS.'],
 'resources':{'cpu_seconds_measured':time.process_time()-cpu_start,'wall_seconds_measured':time.monotonic()-start,'peak_working_set_bytes_measured':peak_ws,'peak_pagefile_bytes_measured':peak_commit,'memory_samples':samples,'enforcement':'Cooperative checks after each hash chunk and every 4096 metadata rows: CPU 60 s, wall 90 s, sampled historical peak working set and pagefile 256 MiB. External launcher additionally kills process at 90 s wall. No OS hard CPU or memory cap; checks can detect overshoot. Output bytes strictly checked before exclusive write.','output_limit_bytes':2*1024*1024},
 'model':{'requested':'Sol / medium','effective_settings':'unknown without telemetry','actual_usage':'unknown without telemetry'}
}
blob=(json.dumps(result,indent=2,ensure_ascii=False)+'\n').encode('utf-8')
if len(blob)>2*1024*1024: raise RuntimeError('output budget exceeded')
check()
with OUT.open('xb') as f: f.write(blob)
print(json.dumps({'saved':str(OUT),'result_sha256':hashlib.sha256(blob).hexdigest(),'output_bytes':len(blob),'total_rows':row_count,'joint_rows':sum(joint_counts.values()),'unique_joint_metadata_rows':len(unique),'cells':cell_counts,'drugs':drug_counts,'pairs':[{'cell':k[0],'drug':k[1],'rows':v} for k,v in sorted(joint_counts.items())],'resources':result['resources']}))

