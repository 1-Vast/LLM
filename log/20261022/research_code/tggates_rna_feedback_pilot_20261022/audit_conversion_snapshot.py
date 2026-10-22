"""Independent serialization/coordinate checks of completed whitelisted arrays; no selection."""
import csv,hashlib,json,math
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'log/20261022/tggates_rna_feedback_pilot'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    manifest=json.loads((P/'RNA_IDENTITY_MANIFEST.json').read_text())
    allowed={s['identity']['BARCODE'] for s in manifest['samples']}
    ids=(P/'annotation/MANUFACTURER_PROBESETS.txt').read_text().splitlines()
    assert len(ids)==len(set(ids))==54675 and ids==sorted(ids)
    freeze=json.loads((P/'PREPROCESS_FREEZE_V2.json').read_text())
    arrays=[];max_error=0.;pending=[]
    for receipt_path in sorted((P/'mas5_v2').glob('*.receipt.json')):
        try:receipt=json.loads(receipt_path.read_text())
        except json.JSONDecodeError:
            pending.append(receipt_path.name);continue
        assert receipt['status']=='complete'
        barcode=receipt['barcode'];assert barcode in allowed
        assert receipt['protocol_sha256']==freeze['protocol_sha256']
        path=P/'mas5_v2'/(barcode+'.tsv');digest=sha(path)
        assert digest==receipt['outputs'][str(path)]
        names=[];error=0.;calls=0
        with path.open(newline='') as f:
            for row in csv.DictReader(f,delimiter='\t'):
                names.append(row['probeset'])
                signal=float(row['signal']);observed=float(row['log2_signal'])
                assert math.isfinite(signal) and math.isfinite(observed)
                error=max(error,abs(observed-math.log2(max(signal,1.))))
                assert row['detection'] in {'P','M','A'}
                probability=float(row['detection_p']);assert 0<=probability<=1
                calls+=1
        assert names==ids and error<1e-10
        arrays.append(dict(barcode=barcode,rows=calls,output_sha256=digest,max_log2_serialization_error=error))
        max_error=max(max_error,error)
    record=dict(status='PASS',utc=datetime.now(timezone.utc).isoformat(),
        scope='Serialization, fixed coordinates, log transform and QC range only; not an independent MAS5 algorithm implementation.',
        completed_arrays_checked=len(arrays),probeset_rows_checked=sum(r['rows'] for r in arrays),
        max_log2_serialization_error=max_error,pending_incomplete_receipts=pending,arrays=arrays,
        coordinate_reference_sha256=sha(P/'annotation/MANUFACTURER_PROBESETS.txt'),
        scientific_selection_performed=False,later_opened=False)
    with (P/'CONVERSION_SNAPSHOT_AUDIT.json').open('x') as f:json.dump(record,f,indent=2)
    print(json.dumps({k:v for k,v in record.items() if k!='arrays'},indent=2))

if __name__=='__main__':main()
