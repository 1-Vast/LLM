"""Project time and well metadata without response values."""
import json
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/vuscope_prefix_diagnostic'

if __name__ == '__main__':
    target = OUT / 'SCHEDULE.json'
    assert not target.exists()
    protocol = json.loads((OUT / 'PROTOCOL_METADATA.json').read_text())['sheets']['Sheet1']
    header = [str(x).replace('\n', ' ') for x in protocol['header']]
    records = [dict(zip(header, row)) for row in protocol['records']]
    drug_rows = [r for r in records if r['Fluid name'] != 'DMSO normalization']
    wells = {}
    for row in drug_rows:
        well = row['Dispensed well'][0] + str(int(row['Dispensed well'][1:]))
        assert well not in wells, 'Conflicting schedule entries'
        wells[well] = dict(label=row['Fluid name'], dose=row['Dispensed concentration'])
    result = dict(drug_labels=sorted(set(r['Fluid name'] for r in drug_rows)),
                  units=sorted(set(r['Units'] for r in drug_rows)),
                  drug_rows=len(drug_rows), control_metadata_rows=len(records)-len(drug_rows), files={})
    with ZipFile(ROOT / 'log/20261023/functional_transition_law/root_sources/release.zip.body') as archive:
        for name in archive.namelist():
            if '/input/data/' not in name or not name.endswith('.txt'):
                continue
            with archive.open(name) as stream:
                for raw in stream:
                    fields = raw.decode('utf-8-sig').strip().split('\t')
                    if 'Elapsed' in fields:
                        columns = fields[2:]
                        break
                times = [float(raw.decode('utf-8-sig').split('\t')[1]) for raw in stream if raw.strip()]
            groups = {}
            for well in columns:
                if well in wells:
                    entry = wells[well]
                    groups.setdefault(entry['label'], []).append(dict(well=well, dose=entry['dose']))
            result['files'][name] = dict(times=times, wells=len(columns), groups=groups,
                                         unmatched_wells=[w for w in columns if w not in wells])
    target.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({k: dict(times=v['times'], groups=len(v['groups']), group_sizes=sorted(set(len(g) for g in v['groups'].values())), unmatched_wells=v['unmatched_wells']) for k,v in result['files'].items()}, indent=2))
