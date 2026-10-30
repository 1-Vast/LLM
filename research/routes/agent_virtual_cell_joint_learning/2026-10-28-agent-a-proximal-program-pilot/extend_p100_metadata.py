"""Check broader chemical coverage without fitting or comparing outcomes."""
import concurrent.futures, json, re
from pathlib import Path
from download_p100 import download

HERE=Path(__file__).resolve().parent
# Four official panel rows across five cancer backgrounds; select before values.
PLATES={15,18,19,17,30,23,24,25,22,31,29,34,33,28,32,60,61,58,59,62}


def main():
    urls=json.loads((HERE/'sources/p100_dataset_links.json').read_text(encoding='utf-8'))
    selected=[]
    missing=[]
    for plate in sorted(PLATES):
        choices=sorted({u.replace('/@files/','/%40files/') for u in urls
            if re.search(rf'Plate{plate}(?:_|[a-z]_)',u) and u.endswith('.gct')
            and not re.search(r'(_LVL[34]|\.processed)\.gct$',u)})
        if not choices:
            missing.append(plate)
            continue
        # Prefer DIA acquisition where official raw links exist; latest timestamp
        # within that acquisition, never based on a measured response.
        selected.append(max(choices,key=lambda u:('_DIA_' in u,u)))
    assert len(selected)<=20
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        receipts=list(pool.map(download,selected))
    result={'scope':'metadata coverage only; P0 remains frozen to original three files',
            'selection':'four official panels x five cancer cells; one raw GCT per plate, DIA then filename preference',
            'missing_plate_links':missing,'receipts':receipts}
    (HERE/'p100_expanded_download_receipts.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'plates_requested':len(PLATES),'files_selected':len(receipts),
        'successful':sum('sha256' in r for r in receipts),'bytes':sum(r.get('bytes',0) for r in receipts),
        'missing':missing,'errors':[{k:r[k] for k in ('filename','error')} for r in receipts if 'error' in r]}))


if __name__=='__main__':
    main()
