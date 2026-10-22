"""HCT116 structure only, no biological response column access."""
import csv
import io
import json
from collections import Counter

from root_data_scout import OUT, write


def main():
    result = []
    allowed = ['Date Time', 'Elapsed', 'well', 'img', 'row', 'col', 'seed', 'concentration']
    for name in ['hct116_replicates', 'hct116_dose_response']:
        reader = csv.DictReader(io.StringIO((OUT/(name+'_fresh_object.body')).read_text(encoding='utf-8-sig')))
        rows = [{k: r[k] for k in allowed} for r in reader]
        out = {'file': name, 'response_values_accessed': False, 'rows': len(rows),
               'unique': {k: sorted({r[k] for r in rows}) for k in allowed}}
        groups = Counter((r['concentration'], r['seed'], r['well'], r['img']) for r in rows)
        out['trajectory_count'] = len(groups)
        out['frames_per_trajectory'] = dict(Counter(groups.values()))
        out['well_counts_by_concentration_seed'] = [
            {'concentration': c, 'seed': s, 'wells': len({k[2] for k in groups if k[0] == c and k[1] == s}),
             'images': sorted({k[3] for k in groups if k[0] == c and k[1] == s})}
            for c, s in sorted({(k[0], k[1]) for k in groups})]
        result.append(out)
    write(OUT/'HCT116_IDENTITY_SCHEMA.json', result)
    compact = [{k: v for k, v in r.items() if k != 'unique'} | {'unique': {
        k: v for k, v in r['unique'].items() if k not in ['well', 'Date Time']},
        'date_range': [min(r['unique']['Date Time']), max(r['unique']['Date Time'])]} for r in result]
    print(json.dumps(compact, ensure_ascii=False))


if __name__ == '__main__':
    main()
