"""Independent frozen-prefix DQ1 audit; standard-library only. No author code executed."""
import csv, io, zipfile, hashlib, json, itertools, time
from decimal import Decimal, InvalidOperation
from collections import defaultdict, Counter
from pathlib import Path

BASE=Path(r'D:\MAESTRO')
OUT=BASE/'research/2026-10-29-dose-measurement-learning/dq1_independent_result.json'
ZIP=BASE/'tmp/extq1/gsdc_well_stats.zip'
EXPECTED='e8cb50f6ce860fa17586a555130cb3b019f6011ed1976c0f0d3e00fb072d3259'
MEMBER='combo_well_stats_GDSC_007_05May22.csv'
ALLOWED=['PROJECT_ID','BARCODE','MASTER_CELL_ID','CELL_ID','POSITION','cmatrix','lib1_drug_id','lib2_drug_id','lib1_drug','lib2_drug','lib1_conc','lib2_conc','lib1_y','lib2_y']

def number(s):
    if not s.strip() or s.strip().lower() in ('na','null','none'):
        return 'missing',None
    try: n=Decimal(s)
    except InvalidOperation: return 'nonnumeric',None
    if not n.is_finite(): return 'nonfinite',None
    return 'finite',n

def main():
    wall=time.perf_counter(); cpu=time.process_time()
    h=hashlib.sha256()
    with ZIP.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    digest=h.hexdigest()
    if digest != EXPECTED: raise RuntimeError('Frozen ZIP hash mismatch; scan prohibited')
    groups=defaultdict(lambda: {'n':0,'raw':set(),'nums':set(),'status':Counter(),'out_of_range':0,'side':Counter()})
    side_groups={'lib1':set(),'lib2':set()}; counts=Counter(); identity_missing=Counter()
    refmap=defaultdict(set); drugrefs=defaultdict(set); cellmap=defaultdict(set)
    positions=set(); matrices=set(); projects=set(); plates=set(); cells=set()
    with zipfile.ZipFile(ZIP) as z:
        with z.open(MEMBER) as b:
            r=csv.reader(io.TextIOWrapper(b,encoding='utf-8-sig',newline=''))
            header=next(r); indices={name:header.index(name) for name in ALLOWED}
            # CSV parsing necessarily transiently tokenizes the entire row. Only allowed
            # fields are projected below; other fields are never named, retained, numeric-parsed,
            # logged, or used as labels. islice prevents requesting row 20001.
            for values in itertools.islice(r,20000):
                row={name:values[i] for name,i in indices.items()}; del values
                counts['rows']+=1
                project,plate,cell,cellid=(row[n] for n in ('PROJECT_ID','BARCODE','MASTER_CELL_ID','CELL_ID'))
                projects.add(project); plates.add(plate); cells.add(cell)
                positions.add((project,plate,row['POSITION'])); matrices.add((project,plate,row['cmatrix']))
                cellmap[cell].add(cellid)
                for s in ('lib1','lib2'):
                    counts[s+'_appearances']+=1
                    ref,drug,conc,y=(row[s+n] for n in ('_drug','_drug_id','_conc','_y'))
                    for name,value in [('project',project),('plate',plate),('master_cell',cell),('cell_id',cellid),('ref',ref),('drug',drug)]:
                        if not value.strip() or value.strip().lower()=='na': identity_missing[name]+=1
                    refmap[ref].add((project,plate,cell,cellid,drug))
                    drugrefs[(project,cell,drug)].add(ref)
                    counts['ref_plate_prefix_mismatch']+=int(not ref.startswith(plate+'_'))
                    cs,cn=number(conc); ys,yn=number(y)
                    counts['concentration_'+cs]+=1; counts['y_'+ys]+=1
                    if cn is not None:
                        counts['negative_concentrations']+=int(cn<0)
                        counts['zero_concentrations']+=int(cn==0)
                    if yn is not None: counts['y_outside_0_1']+=int(yn<0 or yn>1)
                    if cs!='finite' or cn<0:
                        counts['invalid_key_appearances']+=1
                        continue
                    key=(project,cell,ref,cn)
                    g=groups[key]; g['n']+=1; g['raw'].add(y); g['status'][ys]+=1; g['side'][s]+=1
                    if yn is not None:
                        g['nums'].add(yn); g['out_of_range']+=int(yn<0 or yn>1)
                    side_groups[s].add(key)
    summary=dict(counts)
    summary.update(unique_exported_keys=len(groups),projects=len(projects),plates=len(plates),master_cells=len(cells),combo_positions=len(positions),plate_matrices=len(matrices),refs=len(refmap),ref_mapping_conflicts=sum(len(x)>1 for x in refmap.values()),master_to_cell_id_conflicts=sum(len(x)>1 for x in cellmap.values()),drug_cell_groups_with_multiple_refs=sum(len(x)>1 for x in drugrefs.values()),identity_missing=dict(identity_missing))
    summary.update(repeated_keys=sum(g['n']>1 for g in groups.values()),raw_string_conflict_keys=sum(len(g['raw'])>1 for g in groups.values()),numeric_conflict_keys=sum(len(g['nums'])>1 for g in groups.values()),keys_with_invalid_y=sum(g['status']['finite']!=g['n'] for g in groups.values()),keys_with_outside_y=sum(g['out_of_range']>0 for g in groups.values()),zero_concentration_keys=sum(k[3]==0 for k in groups))
    summary['side_unique_keys']={s:len(ks) for s,ks in side_groups.items()}
    overlap=side_groups['lib1'] & side_groups['lib2']; summary['cross_side_shared_keys']=len(overlap)
    summary['cross_side_shared_conflicts']=sum(len(groups[k]['nums'])>1 for k in overlap)
    eligible=[k for k,g in groups.items() if len(g['nums'])==1 and g['status']['finite']==g['n'] and not g['out_of_range'] and len(refmap[k[2]])==1]
    summary['eligible_exported_keys']=len(eligible)
    def packet(k):
        g=groups[k]
        return {'key':[str(v) for v in k],'appearances':g['n'],'raw_y_unique_count':len(g['raw']),'raw_y':sorted(g['raw']),'finite_y_count':g['status']['finite'],'numeric_y_unique_count':len(g['nums']),'numeric_y':sorted(str(n) for n in g['nums']),'status':dict(g['status']),'out_of_range':g['out_of_range'],'sides':dict(g['side'])}
    # Lexical ordering of serialized key components, including concentration text.
    ordered=sorted(groups,key=lambda k:tuple(str(v) for v in k))
    result={'audit':'independent single standard-library csv+Decimal rewrite','zip_sha256':digest,'zip_sha256_matches_protocol':True,'member':MEMBER,'prefix_rows_requested':20000,'summary':summary,'packets':[packet(k) for k in ordered[:16]],'conflict_examples':[packet(k) for k in ordered if len(groups[k]['nums'])>1][:16],
    'rules':{'key':['PROJECT_ID','MASTER_CELL_ID','libN_drug','Decimal(libN_conc)'],'concentration_unit':'micromolar per frozen protocol; no separate dictionary read','numeric_equality':'exact Decimal equality; tolerance 0; no rounding/averaging/clipping','missing':'blank or NA/null/none, case-insensitive','nonfinite':'Decimal NaN/Infinity classified separately','identity_mapping':'ref -> (project,barcode,master_cell_id,cell_id,drug_id); drug multiplicity grouped by (project,master_cell_id,drug_id)','source_well':'combination POSITION is not asserted to be monotherapy source POSITION'},
    'reading_boundary':'Only fixed first 20000 CSV data rows. CSV parser transiently tokenizes other columns; immediately project 14 allowed fields, never retain/number-parse/use yhat, IC50, AUC or combination inhibition. No other data or functional files read.',
    'execution_deviation':'Before formal hash-gated scan, header and first two rows allowed projection were inspected to resolve ref identity. Thus protocol hash-before-any-source-inspection order was not fully respected; bytes were subsequently verified before the independent full-prefix scan.',
    'source_semantics':{'classes_R_313_350':'Monotherapy layout S joined by POSITION; normalized_intensity=calc_viability(...,trim=TRUE); prepNlmeData drug_specifiers=(BARCODE,lib_drug), cl_id=MASTER_CELL_ID.','classes_R_402_410':'viability=(intensity-mean_B)/(mean_NC1-mean_B), trimmed to [0,1].','nlme_fit_prep_R_779_824':'normalized_intensity renamed y; ref formed by BARCODE + underscore + lib_drug; y then set to 1-y. Therefore cached source suggests exported y represents inhibition-like normalized response, not untransformed viability.','matrix_well_stats_R_48_66':'Library statistics joined onto combination rows via dose; source POSITION and CL removed before join, so exported combination POSITION does not recover the monotherapy source well.','version_gap':'Only specified old official-cache source fragments inspected; these are not authenticated as actual exporter runtime, full commit, or complete pipeline.'},
    'qualification':{'supports':'If finite unique y and conflict-free identity mapping hold, each qualifying exported reference key is a deterministic same-screen export observation unit eligible for later separately frozen development prediction.','does_not_support':'No original instrument well identity authentication, independent culture count, replicate-noise estimate, raw untrimmed measurement recovery, cross-screen transfer or scientific/method advantage. Exact repetition may reflect joins of the same exported response.','scope':'Fixed prefix has been exposed during development; cannot be relabelled pristine confirmation. No automatic positive-subset algorithm experiment performed; no RNA/orthogonal/culture requirement imposed as blanket rejection of same-screen exported-response prediction.'},
    'budget':{'new_cap':3,'old_count':23,'old_cap':24,'pass':1,'activity':'one independent source-data check; no additional discovery pass','requested_model':'Sol','requested_reasoning':'medium','effective_model':'unknown','usage':'unknown','installations':0,'GPU':0,'network':0,'API':0,'new_agents':0},'timing':{'cpu_seconds':time.process_time()-cpu,'wall_seconds':time.perf_counter()-wall}}
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'saved':str(OUT),'summary':summary,'timing':result['timing'],'output_bytes':OUT.stat().st_size},ensure_ascii=False))
if __name__=='__main__': main()
