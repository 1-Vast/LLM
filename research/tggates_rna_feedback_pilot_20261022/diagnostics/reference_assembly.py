"""Separate Decimal reference for frozen RNA-state assembly; no predictor imports."""
import argparse,csv,hashlib,json,time
from decimal import Decimal
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
import psutil
ROOT=Path(__file__).resolve().parents[3];P=ROOT/'log/20261022/tggates_rna_feedback_pilot'
OLD=ROOT/'log/20261022/tggates_feedback_headroom'


def contrast(treated,controls):
    assert len(treated)==len(controls)==2
    return np.asarray([float((Decimal(a)+Decimal(b)-Decimal(c)-Decimal(d))/2)
                       for a,b,c,d in zip(treated[0],treated[1],controls[0],controls[1])])


def load_log_vector(barcode,probes):
    path=P/'mas5_v2'/(barcode+'.tsv')
    with path.open(newline='') as f:rows=list(csv.DictReader(f,delimiter='\t'))
    assert [r['probeset'] for r in rows]==probes
    return [r['log2_signal'] for r in rows]


def audit():
    start=time.monotonic()
    meta=json.loads((P/'numeric_inputs/METADATA.json').read_text())
    with (P/'numeric_inputs/DATA.npz').open('rb') as f:
        assert hashlib.file_digest(f,'sha256').hexdigest()==meta['data_sha256']
    manifest=json.loads((P/'RNA_IDENTITY_MANIFEST.json').read_text())
    prior=json.loads((OLD/'MANIFEST.json').read_text(encoding='utf-8'),parse_float=str)
    expected={r['compound_label']:r for r in prior['compounds'] if r['role'] in {'source','development'}}
    assert [r['compound_label'] for r in meta['rows']]==sorted(expected)
    probes=(P/'annotation/MANUFACTURER_PROBESETS.txt').read_text().splitlines()
    assert probes==meta['probesets']
    by_group={}
    for s in manifest['samples']:
        ident=s['identity'];by_group.setdefault((ident['COMPOUND_NAME'],ident['DOSE_LEVEL']),[]).append(s)
    oldmeans=json.loads((OLD/'CONDITION_MEANS.json').read_text(encoding='utf-8'),parse_float=str)
    oldmeans={r['compound_label']:r for r in oldmeans}
    checks=[];state_values=0;function_values=0;maximum=0.
    with np.load(P/'numeric_inputs/DATA.npz',allow_pickle=False) as arrays:
        for index,row in enumerate(meta['rows']):
            label=row['compound_label'];official=expected[label]
            assert row['role']==official['role'] and row['block_id']==official['block_id']
            controls=by_group[(label,'Control')];assert len(controls)==2
            cv=[load_log_vector(s['identity']['BARCODE'],probes) for s in controls]
            for level in ['Middle']+(['High'] if row['role']=='source' else []):
                treated=by_group[(label,level)];assert len(treated)==2
                assert len({s['identity']['EXP_ID'] for s in treated+controls})==1
                assert {s['identity']['INDIVIDUAL_ID'] for s in treated}=={'1','2'}
                tv=[load_log_vector(s['identity']['BARCODE'],probes) for s in treated]
                reference=contrast(tv,cv)
                observed=arrays['xm' if level=='Middle' else 'xh'][index]
                error=float(np.max(np.abs(reference-observed)))
                assert error<1e-12,(label,level,error)
                maximum=max(maximum,error);state_values+=len(reference)
                checks.append(dict(label=label,level=level,max_decimal_contrast_difference=error))
            for j,level in enumerate(['Low','Middle','High']):
                assert arrays['dose'][index,j]==float(Decimal(str(oldmeans[label]['doses'][level]['concentration'])))
                if row['role']=='source' or level=='Middle':
                    for target,name in [('y','mean'),('sd','sd')]:
                        expected_value=[float(Decimal(str(v))) for v in oldmeans[label]['doses'][level][name]]
                        np.testing.assert_array_equal(arrays[target][index,j],expected_value)
                        function_values+=2
                else:
                    assert np.isnan(arrays['y'][index,j]).all() and np.isnan(arrays['sd'][index,j]).all()
            if row['role']=='development':assert np.isnan(arrays['xh'][index]).all()
            print(json.dumps(dict(compound=label,status='PASS')),flush=True)
    result=dict(status='PASS',utc=datetime.now(timezone.utc).isoformat(),checks=checks,
        state_scalar_comparisons=state_values,function_mean_sd_comparisons=function_values,
        maximum_decimal_state_difference=maximum,development_high_function_casts=0,
        later_opened=False,elapsed_seconds=time.monotonic()-start,
        scope='Separate Decimal aggregation and identity/absence implementation; not independent MAS5 or biological validation.')
    with (P/'REFERENCE_ASSEMBLY_AUDIT.json').open('x') as f:json.dump(result,f,indent=2)
    print(json.dumps({k:v for k,v in result.items() if k!='checks'}),flush=True)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--pilot-pid',type=int,required=True);args=parser.parse_args()
    live=psutil.Process(args.pilot_pid);assert 'run_when_ready.py' in ' '.join(live.cmdline())
    created=live.create_time();ready=P/'numeric_inputs/METADATA.json'
    with (P/'REFERENCE_ASSEMBLY_STARTED.json').open('x') as f:
        json.dump(dict(status='WAITING_FOR_INPUTS',pilot_pid=args.pilot_pid,create_time=created),f)
    try:
        while True:
            if ready.exists():
                try:json.loads(ready.read_text());break
                except json.JSONDecodeError:pass
            try:
                live=psutil.Process(args.pilot_pid)
                running=live.create_time()==created and live.is_running()
            except psutil.NoSuchProcess:running=False
            if not running:raise RuntimeError('Pilot process terminal before inputs ready; inspect same handle, do not restart')
            if (P/'AUTONOMOUS_PILOT_TERMINAL.json').exists():
                raise RuntimeError('Pilot terminal receipt before inputs ready')
            time.sleep(5)
        audit()
    except Exception as e:
        with (P/'REFERENCE_ASSEMBLY_FAILURE.json').open('x') as f:json.dump(dict(status='FAILED_RETAINED',error=f'{type(e).__name__}: {e}'),f)
        raise

if __name__=='__main__':main()
