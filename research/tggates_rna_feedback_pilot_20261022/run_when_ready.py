"""One-shot continuation of the exact authorized pilot after the live arrival worker completes."""
import argparse,json,subprocess,sys,time
from pathlib import Path
import psutil
import rna_archive_acquire as a
from preserve import verify
ROOT=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;P=ROOT/a.PHASE


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--arrival-pid',type=int,required=True);args=parser.parse_args()
    proc=psutil.Process(args.arrival_pid)
    assert 'process_arrivals.py' in ' '.join(proc.cmdline())
    created=proc.create_time()
    audit=json.loads((P/'IMPLEMENTATION_AUDIT_DISPOSITION.json').read_text())
    assert audit['status']=='CLEARED_FOR_FIXED_NUMERICAL_EXECUTION'
    record=dict(status='WAITING_FOR_AUTHORIZED_172_ARRAYS',utc_started=a.utc_now(),
        arrival_pid=args.arrival_pid,arrival_create_time=created,
        script_sha256=a.sha256_file(Path(__file__)),stages=[])
    with (P/'AUTONOMOUS_PILOT_STARTED.json').open('x') as f:json.dump(record,f,indent=2)
    try:
        terminal=P/'ARRIVAL_PROCESSING_TERMINAL.json'
        while not terminal.exists():
            try:
                live=psutil.Process(args.arrival_pid)
                running=live.create_time()==created and live.is_running()
            except psutil.NoSuchProcess:running=False
            if not running:raise RuntimeError('Confirmed arrival process missing before terminal receipt; stop, no restart')
            time.sleep(5)
        done=json.loads(terminal.read_text())
        assert done['status']=='ALL_172_COMPLETE',done
        preservation=verify()
        assert preservation['passed'],'Earlier finalized evidence changed'
        with (P/'PRE_NUMERICAL_PRESERVATION.json').open('x') as f:json.dump(preservation,f,indent=2)
        steps=[('prepare_inputs',[str(C/'prepare_numeric_inputs.py')]),
            ('freeze_numerics',[str(C/'freeze_numerical_execution.py')]),
            ('predict',[str(C/'run_pilot.py'),'--freeze',str(P/'NUMERICAL_EXECUTION_FREEZE.json')]),
            ('score_sealed',[str(C/'score_pilot.py')])]
        for name,arguments in steps:
            started=a.utc_now()
            print(json.dumps(dict(stage=name,status='STARTED',utc=started)),flush=True)
            with (P/('AUTO_'+name+'.log')).open('x',encoding='utf-8') as output:
                result=subprocess.run([sys.executable,'-B']+arguments,cwd=ROOT,stdout=output,stderr=subprocess.STDOUT)
            stage=dict(stage=name,utc_started=started,utc_finished=a.utc_now(),returncode=result.returncode)
            record['stages'].append(stage)
            a.write_receipt(P/'receipts/autonomous_stages',name,stage)
            print(json.dumps(stage),flush=True)
            if result.returncode:raise RuntimeError('Stage failed; no automatic retry: '+name)
        record.update(status='PILOT_COMPLETE_REQUIRES_RESULT_REVIEW',utc_finished=a.utc_now(),
            full_goal_achieved=False,later_opened=False)
    except Exception as e:
        record.update(status='FAILED_RETAINED',error=f'{type(e).__name__}: {e}',utc_finished=a.utc_now(),full_goal_achieved=False)
    with (P/'AUTONOMOUS_PILOT_TERMINAL.json').open('x') as f:json.dump(record,f,indent=2)
    print(json.dumps(record),flush=True)
    return int(record['status']!='PILOT_COMPLETE_REQUIRES_RESULT_REVIEW')

if __name__=='__main__':raise SystemExit(main())
