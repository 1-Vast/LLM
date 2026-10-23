"""Design-only exact single-agent joins for complete3x3 combination grids."""
import csv
import io
import json
from collections import Counter, defaultdict
from pathlib import Path
import zipfile
import time

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/post_decrypte_renewal/root/almanac_archive'
COLUMNS = ('SCREENER','STUDY','PLATE','PANELNBR','CELLNBR','NSC1','SAMPLE1','CONCINDEX1','CONC1','CONCUNIT1',
           'NSC2','SAMPLE2','CONCINDEX2','CONC2','CONCUNIT2')


def main():
    assert not (OUT/'JOIN.json').exists()
    start = time.perf_counter()
    solos = defaultdict(list)
    grids = defaultdict(list)
    nscs, pairs = set(), set()
    lab_patterns = defaultdict(Counter)
    with zipfile.ZipFile(OUT/'archive.zip') as archive:
        with archive.open('ComboDrugGrowth_Nov2017.csv') as handle:
            reader = csv.reader(io.TextIOWrapper(handle,encoding='utf-8-sig',newline=''))
            header = next(reader)
            positions = {key:header.index(key) for key in COLUMNS}
            for line,row in enumerate(reader,2):
                assert len(row) == len(header)
                d = {key:row[i] for key,i in positions.items()}
                context = (d['SCREENER'],d['STUDY'],d['PANELNBR'],d['CELLNBR'])
                a = (d['NSC1'],d['SAMPLE1'],d['CONC1'],d['CONCUNIT1'])
                b = (d['NSC2'],d['SAMPLE2'],d['CONC2'],d['CONCUNIT2'])
                for nsc in (a[0],b[0]):
                    if nsc:
                        nscs.add(nsc)
                lab_patterns[d['SCREENER']][(d['CONCINDEX1'],d['CONCINDEX2'])] += 1
                if d['CONCINDEX2'] == '0' and not d['NSC2'] and d['CONCINDEX1'] in ('1','2','3','4','5'):
                    solos[(context,a)].append((line,d['PLATE']))
                if d['NSC1'] and d['NSC2']:
                    pairs.add(tuple(sorted((a[:2],b[:2]))))
                    key = (context,d['PLATE'],a[:2],b[:2])
                    grids[key].append((d['CONCINDEX1'],d['CONCINDEX2'],a,b,line))
    wanted = {(str(a),str(b)) for a in range(1,4) for b in range(1,4)}
    categories, bylab = Counter(), defaultdict(Counter)
    example = {}
    eligible = []
    crossplate, unique_source_plates = Counter(), Counter()
    for key, rows in grids.items():
        context,plate,drug1,drug2 = key
        if len(rows) != 9 or set((r[0],r[1]) for r in rows) != wanted:
            categories['not_exact3x3'] += 1
            continue
        required = set((r[2] for r in rows)) | set((r[3] for r in rows))
        assert len(required) == 6
        matches = {a:solos.get((context,a),[]) for a in required}
        multiplicities = [len(v) for v in matches.values()]
        kind = 'missing_solo' if min(multiplicities)==0 else 'all_solos_unique' if max(multiplicities)==1 else 'some_solos_repeated'
        categories[kind] += 1
        bylab[context[0]][kind] += 1
        if kind not in example:
            example[kind] = {'context':list(context),'plate':plate,'drug_samples':[list(drug1),list(drug2)],
                             'solo_multiplicities':sorted(multiplicities)}
        if kind == 'all_solos_unique':
            solo_rows = sorted(v[0][0] for v in matches.values())
            solo_plates = set(v[0][1] for v in matches.values())
            unique_source_plates[len(solo_plates)] += 1
            crossplate[str(solo_plates == {plate})] += 1
            eligible.append({'context':list(context),'plate':plate,'drug_samples':[list(drug1),list(drug2)],
                             'combination_rows':sorted(r[4] for r in rows),'single_agent_rows':solo_rows,
                             'single_agent_plates':sorted(solo_plates)})
    result = {'scope':'Exact string concentration/sample joins within lab-study-numericcell; no response values accessed',
              'nonempty_nsc_count':len(nscs),'nonempty_pairs_including_samples':len(pairs),
              'combination_group_count':len(grids),'categories':dict(categories),'by_lab':{k:dict(v) for k,v in bylab.items()},
              'examples_design_only':example,'unique_solo_plate_count_histogram':dict(unique_source_plates),
              'unique_solos_same_plate_as_combo':dict(crossplate),
              'lab_index_patterns':{lab:[{'indices':list(k),'rows':v} for k,v in sorted(c.items())] for lab,c in lab_patterns.items()},
              'eligible_unique_solo_grids':len(eligible),'wall_s':time.perf_counter()-start}
    (OUT/'JOIN.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    (OUT/'ELIGIBLE_DESIGN_ROWS.json').write_text(json.dumps(eligible),encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('nonempty_nsc_count','nonempty_pairs_including_samples','categories','by_lab','unique_solos_same_plate_as_combo','wall_s')},indent=2),flush=True)


if __name__ == '__main__':
    main()
