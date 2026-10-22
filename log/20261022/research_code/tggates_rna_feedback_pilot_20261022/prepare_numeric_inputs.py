"""Build fixed-coordinate input arrays; never cast development High function."""
import csv,hashlib,json,math
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
P=ROOT/'log/20261022/tggates_rna_feedback_pilot'
def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def project_function(rows):
    output=[];casts={'source':0,'development':0}
    for row in rows:
        assert row['role'] in {'source','development'}
        keep={k:row[k] for k in ['compound_label','block_id','role','fingerprint_on_bits','unit']}
        keep['doses']={}
        for level,dose in row['doses'].items():
            result={'concentration':float(dose['concentration'])}
            if row['role']=='source' or level=='Middle':
                for key in ['mean','sd']:
                    result[key]=[float(v) for v in dose[key]]
                    assert all(math.isfinite(v) for v in result[key])
                    casts[row['role']]+=len(result[key])
            keep['doses'][level]=result
        output.append(keep)
    return output,casts


def main():
    dest=P/'numeric_inputs';dest.mkdir(exist_ok=True)
    assert not (dest/'DATA.npz').exists()
    old=ROOT/'log/20261022/tggates_feedback_headroom/CONDITION_MEANS.json'
    # JSON decimal tokens stay strings; only selected means/SD are cast above.
    rows,casts=project_function(json.loads(old.read_text(encoding='utf-8'),parse_float=str))
    rows=sorted(rows,key=lambda x:x['compound_label'])
    assert len(rows)==31 and sum(r['role']=='source' for r in rows)==24
    assert len({r['block_id'] for r in rows})==31
    manifest=json.loads((P/'RNA_IDENTITY_MANIFEST.json').read_text(encoding='utf-8'))
    freeze=json.loads((P/'PREPROCESS_FREEZE_V2.json').read_text(encoding='utf-8'))
    grouped=defaultdict(list);values={};ids=None;inputs={}
    for sample in manifest['samples']:
        identity=sample['identity'];barcode=identity['BARCODE']
        receipt_path=P/'mas5_v2'/(barcode+'.receipt.json')
        receipt=json.loads(receipt_path.read_text())
        assert receipt['status']=='complete' and receipt['protocol_sha256']==freeze['protocol_sha256']
        table=P/'mas5_v2'/(barcode+'.tsv')
        assert receipt['outputs'][str(table)]==sha(table)
        with table.open(newline='',encoding='utf-8') as f:
            records=list(csv.DictReader(f,delimiter='\t'))
        names=[r['probeset'] for r in records]
        assert len(names)==54675 and names==sorted(names) and len(set(names))==54675
        if ids is None:ids=names
        assert names==ids
        vector=np.array([float(r['log2_signal']) for r in records]);assert np.isfinite(vector).all()
        values[barcode]=vector
        grouped[(identity['COMPOUND_NAME'],identity['DOSE_LEVEL'])].append(sample)
        inputs[table.relative_to(ROOT).as_posix()]=sha(table)
    n,p=len(rows),len(ids);xm=np.empty((n,p));xh=np.full((n,p),np.nan)
    y=np.full((n,3,2),np.nan);sd=y.copy();dose=np.empty((n,3));chem=np.zeros((n,2048))
    categories=sorted({r['unit'] for r in rows});units=np.zeros((n,len(categories)));joins=[]
    for i,row in enumerate(rows):
        label=row['compound_label'];control=grouped[(label,'Control')]
        assert len(control)==2
        cmean=np.mean([values[s['identity']['BARCODE']] for s in control],axis=0)
        for level in ['Middle']+(['High'] if row['role']=='source' else []):
            samples=grouped[(label,level)];assert len(samples)==2
            for field in ['EXP_ID','COMPOUND_NO','MATERIAL_ID','ARR_DESIGN','DOSE_UNIT','SACRIFICE_PERIOD']:
                assert len({s['identity'][field] for s in samples+control})==1,(label,level,field)
            assert {s['identity']['INDIVIDUAL_ID'] for s in samples}=={'1','2'}
            assert {Decimal(s['identity']['DOSE']) for s in samples}=={Decimal(str(row['doses'][level]['concentration']))}
            state=np.mean([values[s['identity']['BARCODE']] for s in samples],axis=0)-cmean
            if level=='Middle':xm[i]=state
            else:xh[i]=state
            joins.append(dict(compound=label,level=level,treated=[s['identity']['BARCODE'] for s in samples],
                              controls=[s['identity']['BARCODE'] for s in control]))
        for j,level in enumerate(['Low','Middle','High']):
            dose[i,j]=row['doses'][level]['concentration']
            if row['role']=='source' or level=='Middle':
                y[i,j]=row['doses'][level]['mean'];sd[i,j]=row['doses'][level]['sd']
        chem[i,[int(v) for v in row['fingerprint_on_bits']]]=1
        units[i,categories.index(row['unit'])]=1
    mapping=json.loads((P/'annotation/FOUR_GENE_MAPPING.json').read_text())
    gene_indices=[[ids.index(probe) for probe in mapping['mapping'][gene]] for gene in mapping['genes']]
    source=[i for i,r in enumerate(rows) if r['role']=='source'];dev=[i for i,r in enumerate(rows) if r['role']=='development']
    assert np.isnan(y[dev,2]).all() and np.isnan(xh[dev]).all()
    with (dest/'DATA.npz').open('xb') as f:np.savez(f,chem=chem,units=units,dose=dose,y=y,sd=sd,xm=xm,xh=xh)
    metadata=dict(rows=rows,source=source,development=dev,unit_categories=categories,gene_indices=gene_indices,
        gene_order=mapping['genes'],probesets=ids,joins=joins,function_numeric_casts=casts,
        development_high_function_casts=0,later_function_casts=0,inputs_sha256=inputs,
        historical_function_input_sha256=sha(old),data_sha256=sha(dest/'DATA.npz'))
    with (dest/'METADATA.json').open('x',encoding='utf-8') as f:json.dump(metadata,f,indent=2)
    print(json.dumps(dict(status='PREPARED',arrays=len(values),source=len(source),development=len(dev),
                         development_high_absent=True)))

if __name__=='__main__':main()
