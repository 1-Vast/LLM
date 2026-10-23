"""Process verified arrivals serially while the exact authorized downloader is live."""
import argparse,json,subprocess,sys,time
from pathlib import Path
import psutil
import rna_archive_acquire as a

ROOT=Path(__file__).resolve().parents[2];CODE=Path(__file__).resolve().parent
P=ROOT/a.PHASE

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--download-pid',type=int,required=True)
    args=parser.parse_args()
    proc=psutil.Process(args.download_pid)
    assert 'rna_archive_acquire.py' in ' '.join(proc.cmdline())
    created=proc.create_time()
    _,jobs,_=a.load_inputs();seen=set()
    start=a.utc_now()
    record=dict(utc_started=start,download_pid=args.download_pid,download_create_time=created,
                process_script_sha256=a.sha256_file(Path(__file__)),status='STARTED')
    with (P/'ARRIVAL_PROCESSING_STARTED.json').open('x',encoding='utf-8') as f:json.dump(record,f,indent=2)
    try:
        while True:
            available={j['compound_label'] for j in jobs if (P/'raw_archives'/f"{j['compound_label']}.zip").exists()}
            if available-seen:
                result=subprocess.run([sys.executable,'-B',str(CODE/'extract_available.py')],cwd=ROOT)
                assert result.returncode==0,'Acquisition verification/extraction failed'
                barcodes=[]
                for cel in sorted((P/'selected_cel_flat').glob('*.CEL')):
                    if not (P/'mas5_v2'/(cel.stem+'.receipt.json')).exists():barcodes.append(cel.stem)
                if barcodes:
                    command=[sys.executable,'-B',str(CODE/'run_mas5_v2.py'),
                        '--protocol',str(P/'PREPROCESS_PROTOCOL_V2.md'),
                        '--protocol-sha256',a.sha256_file(P/'PREPROCESS_PROTOCOL_V2.md'),
                        '--authorization',str(P/'PREPROCESS_FREEZE_V2.json'),'--execute']
                    for barcode in barcodes:command+=['--barcode',barcode]
                    result=subprocess.run(command,cwd=ROOT)
                    assert result.returncode==0,'MAS5 technical failure; no automatic retry'
                seen=available
                print(json.dumps(dict(utc=a.utc_now(),verified_archives=len(seen),
                    completed_arrays=len(list((P/'mas5_v2').glob('*.receipt.json'))))),flush=True)
            if len(seen)==31:break
            try:
                live=psutil.Process(args.download_pid)
                running=live.create_time()==created and live.is_running()
            except psutil.NoSuchProcess:running=False
            if not running:
                raise RuntimeError('Authorized downloader terminal/missing before all31 archives; inspect its handle, do not restart automatically')
            time.sleep(5)
        receipts=[json.loads(p.read_text()) for p in (P/'mas5_v2').glob('*.receipt.json')]
        assert len(receipts)==172 and all(r['status']=='complete' for r in receipts)
        record.update(status='ALL_172_COMPLETE',utc_finished=a.utc_now())
    except Exception as e:
        record.update(status='FAILED_RETAINED',error=f'{type(e).__name__}: {e}',utc_finished=a.utc_now())
    with (P/'ARRIVAL_PROCESSING_TERMINAL.json').open('x',encoding='utf-8') as f:json.dump(record,f,indent=2)
    return int(record['status']!='ALL_172_COMPLETE')

if __name__=='__main__':raise SystemExit(main())
