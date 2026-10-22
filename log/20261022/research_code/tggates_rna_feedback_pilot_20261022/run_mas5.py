"""Serial, whitelist-only MAS5 execution after an explicitly hashed protocol freeze."""
import argparse
import csv
import hashlib
import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PHASE = ROOT / 'log/20261022/tggates_rna_feedback_pilot'
MANIFEST = PHASE / 'RNA_IDENTITY_MANIFEST.json'
MANIFEST_SHA = '5961e44f3efab6182339aa032d49cb74ccecf1ad01fc40cfdf070f2fbdc135b7'
RSCRIPT = Path('C:/Program Files/R/R-4.5.2/bin/x64/Rscript.exe')

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()

def whitelist(manifest):
    samples = manifest['samples']
    assert len(samples) == 172
    by_id = {}
    counts = {}
    for row in samples:
        identity = row['identity']
        barcode = identity['BARCODE']
        role, dose = row['role'], identity['DOSE_LEVEL']
        assert barcode not in by_id and len(barcode) == 12 and barcode.isdigit()
        assert identity['ARR_DESIGN'] == 'HG-U133_Plus_2' and identity['SACRIFICE_PERIOD'] == '2 hr'
        assert (role == 'source' and dose in {'Middle','High','Control'}) or (role == 'development' and dose in {'Middle','Control'})
        assert row['expected_CEL_basename'] == barcode+'.CEL'
        counts[role+'_'+dose] = counts.get(role+'_'+dose,0)+1
        by_id[barcode] = row
    assert counts == {'source_Middle':48,'source_High':48,'source_Control':48,'development_Middle':14,'development_Control':14}
    return by_id

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', type=Path, required=True)
    parser.add_argument('--protocol-sha256', required=True)
    parser.add_argument('--authorization',type=Path,required=True)
    parser.add_argument('--barcode', action='append')
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    assert sha(MANIFEST) == MANIFEST_SHA, 'Identity manifest changed'
    assert sha(args.protocol) == args.protocol_sha256, 'Frozen protocol hash mismatch'
    auth=json.loads(args.authorization.read_text(encoding='utf-8'))
    assert auth['preprocessing_authorized'] is True
    assert auth['protocol_sha256']==args.protocol_sha256
    for relative,digest in auth['artifacts_sha256'].items():
        assert sha(ROOT/relative)==digest,'Preprocessing frozen artifact changed: '+relative
    permitted = whitelist(json.loads(MANIFEST.read_text(encoding='utf-8')))
    chosen = sorted(args.barcode or permitted)
    assert len(chosen) == len(set(chosen)) and set(chosen) <= set(permitted)
    if not args.execute:
        print(json.dumps({'status':'metadata_validation_only','selected':len(chosen),'RNA_read':False}))
        return
    benchmark=auth['first_source_barcode']
    if chosen != [benchmark]:
        previous=json.loads((PHASE/'mas5'/(benchmark+'.receipt.json')).read_text())
        assert previous['status']=='complete' and previous['protocol_sha256']==args.protocol_sha256
        assert previous['sampled_peak_rss_bytes'] < auth['benchmark_peak_rss_limit_bytes']
        assert previous['elapsed_seconds'] < auth['benchmark_elapsed_limit_seconds']
    acquired = {}
    for path in sorted((PHASE/'receipts/cel_extraction').glob('*.json')):
        receipt = json.loads(path.read_text(encoding='utf-8'))
        if receipt.get('outcome') != 'complete':
            continue
        for item in receipt['members']:
            barcode = item['barcode']
            assert barcode in permitted
            if barcode in acquired:
                assert acquired[barcode]['sha256'] == item['sha256']
            acquired[barcode] = item
    assert set(chosen) <= set(acquired), 'Missing complete acquisition receipt'
    outdir = PHASE/'mas5'
    outdir.mkdir(exist_ok=True)
    allow = outdir/'whitelist.tsv'
    with allow.open('w',newline='',encoding='utf-8') as stream:
        writer = csv.writer(stream,delimiter='\t')
        writer.writerow(['barcode'])
        writer.writerows([barcode] for barcode in sorted(permitted))
    for barcode in chosen:
        output = outdir/barcode
        receipt_path = outdir/(barcode+'.receipt.json')
        if receipt_path.exists():
            previous = json.loads(receipt_path.read_text())
            assert previous['status'] == 'complete', 'Previous failure requires audited resolution'
            assert previous['protocol_sha256'] == args.protocol_sha256
            assert all(sha(Path(p)) == value for p,value in previous['outputs'].items())
            continue
        cel = Path(acquired[barcode]['path'])
        if not cel.is_absolute():
            cel = ROOT/cel
        assert cel.resolve().parent == (PHASE/'selected_cel_flat').resolve()
        assert cel.name == barcode+'.CEL' and sha(cel) == acquired[barcode]['sha256']
        command = [str(RSCRIPT),'--vanilla',str(Path(__file__).with_name('mas5_single_array.R')),
                   str(cel),barcode,str(allow),str(output)]
        start = time.monotonic()
        with (outdir/(barcode+'.stdout.txt')).open('w') as stdout, (outdir/(barcode+'.stderr.txt')).open('w') as stderr:
            process = subprocess.Popen(command,stdout=stdout,stderr=stderr)
            peak = 0
            import psutil
            monitored = psutil.Process(process.pid)
            while process.poll() is None:
                try:
                    peak = max(peak,monitored.memory_info().rss)
                except psutil.NoSuchProcess:
                    pass
                time.sleep(.2)
        result = dict(barcode=barcode,status='complete' if process.returncode==0 else 'failed',
                      returncode=process.returncode,command=command,elapsed_seconds=time.monotonic()-start,
                      sampled_peak_rss_bytes=peak,input_sha256=acquired[barcode]['sha256'],
                      protocol_sha256=args.protocol_sha256,manifest_sha256=MANIFEST_SHA,
                      script_sha256=sha(Path(__file__).with_name('mas5_single_array.R')),
                      outputs={str(p):sha(p) for p in outdir.glob(barcode+'.*') if p != receipt_path})
        receipt_path.write_text(json.dumps(result,indent=2))
        print(json.dumps({'barcode':barcode,'status':result['status'],'seconds':result['elapsed_seconds']}),flush=True)
        if process.returncode:
            raise RuntimeError('MAS5 technical failure: '+barcode)

if __name__ == '__main__':
    main()
