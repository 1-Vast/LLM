"""Audit identities/time only; response columns are never converted or emitted."""
import csv
import hashlib
import io
import json
from collections import Counter

from acquire_functional_csv import FILES
from root_data_scout import OUT, get, write


def main():
    headers = []
    for name, _, size, md5 in FILES[:2]:
        file_id = '56428388' if name == 'hct116_replicates' else '56428391'
        fname = ('HCT116_Cisplatin_Replicates.csv' if name == 'hct116_replicates'
                 else 'HCT116_Cisplatin_DoseResponse.csv')
        receipt, raw = get(name+'_public',
            'https://s3-eu-west-1.amazonaws.com/pfigshare-u-files/'+file_id+'/'+fname,
            cap=4_000_000)
        row = {'name': name, 'status': receipt.get('status'), 'bytes': len(raw)}
        if receipt.get('status') == 200 and 'error_type' not in receipt:
            if len(raw) != size or hashlib.md5(raw).hexdigest() != md5:
                raise ValueError('manifest_mismatch')
            reader = csv.reader(io.StringIO(raw.decode('utf-8-sig')))
            row.update(header=next(reader), rows=sum(1 for _ in reader))
        headers.append(row)
    write(OUT/'HCT116_HEADERS.json', headers)
    reader = csv.DictReader(io.StringIO((OUT/'hts001.body').read_text(encoding='utf-8-sig')))
    allowed = ['drug1', 'cell.line', 'drug1.conc', 'well', 'upid', 'time', 'drug1.units']
    identities = [{k: r[k] for k in allowed} for r in reader]
    out = {'file': 'hts001', 'response_values_accessed': False,
           'rows': len(identities),
           'unique': {k: sorted({r[k] for r in identities}) for k in allowed if k != 'well'}}
    groups = Counter((r['drug1'], r['cell.line'], r['drug1.conc'], r['upid'], r['well'])
                     for r in identities)
    out['trajectory_count'] = len(groups)
    out['frames_per_trajectory'] = dict(Counter(groups.values()))
    out['trajectory_counts_by_plate_background'] = [
        {'plate': p, 'cell_line': c, 'trajectories': sum(1 for k in groups if k[3] == p and k[1] == c)}
        for p, c in sorted({(k[3], k[1]) for k in groups})]
    write(OUT/'HTS001_IDENTITY_SCHEMA.json', out)
    print(json.dumps({'hct116': headers, 'hts001': out}, ensure_ascii=False))


if __name__ == '__main__':
    main()
