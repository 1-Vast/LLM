"""Capture live process identities, technical counts, API costs and preservation; no assay reads."""
import json
from pathlib import Path
import psutil
import rna_archive_acquire as a
from preserve import verify
ROOT=Path(__file__).resolve().parents[2];P=ROOT/a.PHASE


def main():
    live=[]
    for proc in psutil.process_iter(['pid','name','cmdline','create_time']):
        try:
            command=proc.info['cmdline'] or []
            if proc.info['name']=='python.exe' and any(s in ' '.join(command) for s in
                ['rna_archive_acquire.py','process_arrivals.py','run_when_ready.py','reference_assembly.py','post_result_reviews.py']):
                live.append(proc.info)
        except (psutil.NoSuchProcess,psutil.AccessDenied):continue
    raw=[json.loads(p.read_text(encoding='utf-8')) for p in (P/'receipts/archive_downloads').glob('*.json')]
    cel=[json.loads(p.read_text()) for p in (P/'mas5_v2').glob('*.receipt.json')]
    apis=[dict(role=p.parent.name,**json.loads(p.read_text())) for p in (P/'api_reviews').glob('*/RECEIPT.json')]
    preservation=verify();assert preservation['passed']
    record=dict(utc=a.utc_now(),classification='PROGRESS',full_goal='ACTIVE_NOT_ACHIEVED',live_processes=live,
        archive_completed=sum(r['outcome']=='complete' for r in raw),archive_failed=sum(r['outcome']=='failed' for r in raw),
        body_bytes_received=sum(r['actual_body_bytes'] for r in raw),
        mas5_v2_completed=sum(r['status']=='complete' for r in cel),mas5_v2_failed=sum(r['status']=='failed' for r in cel),
        original_qc_technical_failures=1,
        api_calls=len(apis),api_tokens=sum(r.get('usage',{}).get('total_tokens',0) for r in apis),
        api_receipts=[dict(role=r['role'],status=r['status'],finish_reason=r.get('finish_reason'),
            tokens=r.get('usage',{}).get('total_tokens',0)) for r in apis],
        earlier_finalized_files_verified=len(preservation['checks']),earlier_preservation_passed=True,
        real_model_fits_started=(P/'NUMERICAL_STARTED.json').exists(),
        real_prediction_seal_exists=(P/'PREDICTION_SEAL.json').exists(),
        later_opened=False,az413_reserve_opened=False,
        handles=dict(download=83044,arrivals=79047,autonomous=22498,reference_assembly=80367,post_result_reviews=3756),
        next='Poll same live handles; arrival completion automatically triggers prepared-input projection, '
             'separate code/data freeze, fixed source selection, prediction seal then separate development scoring. '
             'On any failure inspect preserved terminal/log; no automatic restarts or gate changes.')
    path=a.write_receipt(P/'checkpoints','progress',record)
    print(json.dumps(dict(checkpoint=str(path),**{k:v for k,v in record.items() if k not in {'api_receipts','live_processes'}}),indent=2))

if __name__=='__main__':main()
