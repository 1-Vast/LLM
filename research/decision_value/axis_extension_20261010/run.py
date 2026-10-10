"""One newly registered c45 numerical extension; only frozen ranges may be read."""
from datetime import datetime, timezone
import hashlib
import json

import requests

from .audit import HERE, PRIOR, REVISION, check_freeze, lines, matching, read, sha, vectors, write


def fetch():
    protocol=read(HERE/'PROTOCOL.json')
    plan=read(HERE/'C45_SELECTION_VERIFIED.json')
    size=read(PRIOR/'CENSUSES.json')['c45.h5ad']['file_bytes']
    public=f'https://huggingface.co/datasets/arcinstitute/State-Tahoe-Filtered/resolve/{REVISION}/c45.h5ad'
    session=requests.Session()
    response=session.head(public,allow_redirects=False,timeout=(15,30))
    append(dict(file='c45.h5ad',source_revision=REVISION,public_url=public,status='HEAD',http_status=response.status_code,bytes=0))
    assert response.status_code in (301,302,307,308), 'source_redirect_missing'
    location=response.headers['Location']
    for kind in ['value_ranges','HVG_ranges']:
        for number,(start,end) in enumerate(plan[kind]):
            expected=end-start+1
            charged=sum(r['bytes'] for r in lines(HERE/'NETWORK.jsonl'))
            assert charged+expected<=protocol['new_received_body_cap_bytes']
            body=bytearray()
            record=dict(file='c45.h5ad',source_revision=REVISION,public_url=public,start=start,end=end,purpose=kind,utc=datetime.now(timezone.utc).isoformat())
            try:
                with session.get(location,headers={'Range':f'bytes={start}-{end}','Accept-Encoding':'identity'},allow_redirects=False,stream=True,timeout=(15,40)) as response:
                    record.update(http_status=response.status_code,content_range=response.headers.get('Content-Range'),content_length=response.headers.get('Content-Length'))
                    valid=response.status_code==206 and response.headers.get('Content-Range')==f'bytes {start}-{end}/{size}'
                    limit=expected if valid else min(8192,protocol['new_received_body_cap_bytes']-charged)
                    declared=response.headers.get('Content-Length')
                    if declared and int(declared)>limit:
                        record['status']='REFUSED_OVERSIZE'
                    else:
                        while len(body)<limit:
                            block=response.raw.read(min(65536,limit-len(body)))
                            if not block:break
                            body.extend(block)
                        record['status']='RETAINED' if valid and len(body)==expected else 'FAILED_RANGE'
            except Exception as error:
                record.update(status='NETWORK_ERROR',error_type=type(error).__name__,unknown_transport_bytes=True)
            path=HERE/'assets'/f'{kind}_{number}.bin'
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(body)
            record.update(bytes=len(body),sha256=sha(path),path=path.relative_to(HERE).as_posix())
            append(record)
            if record['status']!='RETAINED':raise RuntimeError('one_attempt_source_range_failed')


def append(record):
    with (HERE/'NETWORK.jsonl').open('a',encoding='utf-8') as stream:
        stream.write(json.dumps(record)+'\n')


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute',required=True,action='store_true')
    parser.parse_args()
    if (HERE/'NETWORK.jsonl').exists() or (HERE/'C45_NUMERIC.json').exists():
        raise FileExistsError('Single extension refuses repeated execution')
    check_freeze(HERE/'C45_FREEZE.json')
    assert read(HERE/'C44_UNION.json')['union_passes']==39
    plan=read(HERE/'C45_SELECTION_VERIFIED.json')
    protocol=read(HERE/'PROTOCOL.json')
    error,records=None,[]
    try:
        fetch()
        discovery=plan['existing_discovery_rows']+plan['rows']
        held=plan['existing_consistency_rows']
        names,raw,target=vectors('c45.h5ad',discovery+held,extension=True)
        split=len(discovery)
        records=matching(names,raw[:split],target[:split],protocol['endpoint']['symbols'],consistency=(raw[split:],target[split:]))
    except Exception as exc:
        error=dict(type=type(exc).__name__,reason=str(exc))
    passed=len(records)==39 and all(r['passed'] for r in records) and error is None
    charged=sum(r['bytes'] for r in lines(HERE/'NETWORK.jsonl'))
    result=dict(status='PASS_FILE_LOCAL_ENDPOINT39_WITH_EXPOSED_CONSISTENCY' if passed else 'BLOCKED_NUMERIC_EXTENSION',source_file='c45.h5ad',source_revision=REVISION,new_rows=plan['rows'],discovery_rows=plan['existing_discovery_rows']+plan['rows'],consistency_rows=plan['existing_consistency_rows'],records=records,passed_coordinates=sum(x['passed'] for x in records),new_received_body_bytes=charged,error=error,consistency_is_fresh_holdout=False,original_P05R_failure_unchanged=True,model_axis_certified=False,P06_execution_released=False)
    write(HERE/'C45_NUMERIC.json',result)
    write(HERE/'CERTIFICATE.json',dict(schema='new_extension_file_local_data_coordinate_qualification_v1',status='PASS_DATA_ENDPOINT39_QUALIFICATION' if passed else 'BLOCKED',source_revision=REVISION,source_files=['c44.h5ad','c45.h5ad'],endpoint_coordinates=protocol['endpoint']['coordinates'],endpoint_symbols=protocol['endpoint']['symbols'],absolute_tolerance=1e-5,transform='log1p(stored normalized X) once',c44_record_sha256=sha(HERE/'C44_UNION.json'),c45_record_sha256=sha(HERE/'C45_NUMERIC.json'),execution_freeze_sha256=sha(HERE/'C45_FREEZE.json'),prior_certificates_superseded=False,fresh_holdout=False,all2000_axis_certified=False,STATE_checkpoint_axis_certified=False,old_c40_c44_noise_plan_released=False,P06_execution_released=False,P2_released=False,independent_biological_validation=False,independent_arithmetic_receipt_required=True))
    print(json.dumps(dict(status=result['status'],passed_coordinates=result['passed_coordinates'],actual_new_body_bytes=charged,error=error)),flush=True)


if __name__=='__main__':main()
