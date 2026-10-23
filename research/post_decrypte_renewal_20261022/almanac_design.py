"""Stream only allowed experimental-design fields; all response fields ignored."""
from collections import Counter, defaultdict
import csv
import io
import json
import hashlib
from pathlib import Path
import time
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/post_decrypte_renewal/root/almanac_archive'
ALLOWED = ('SCREENER','STUDY','TESTDATE','PLATE','PANELNBR','CELLNBR','PREFIX1','NSC1','SAMPLE1',
           'CONCINDEX1','CONC1','CONCUNIT1','PREFIX2','NSC2','SAMPLE2','CONCINDEX2','CONC2','CONCUNIT2',
           'VALID','PANEL','CELLNAME')
FORBIDDEN = ('PERCENTGROWTH','PERCENTGROWTHNOTZ','TESTVALUE','CONTROLVALUE','TZVALUE','EXPECTEDGROWTH','SCORE')


def main():
    assert not (OUT/'DESIGN.json').exists()
    start = time.perf_counter()
    cells, labs, units, valid, prefixes = defaultdict(set), Counter(), Counter(), Counter(), Counter()
    studies, plates, dates, samples = set(), defaultdict(set), Counter(), defaultdict(set)
    patterns = defaultdict(Counter)
    bundle_counts = Counter()
    pair_cells = defaultdict(set)
    cell_pairs = defaultdict(set)
    all_indices, missing = Counter(), Counter()
    rows = 0
    with zipfile.ZipFile(OUT/'archive.zip') as archive:
        info = archive.infolist()[0]
        assert info.filename == 'ComboDrugGrowth_Nov2017.csv'
        with archive.open(info) as source:
            reader = csv.reader(io.TextIOWrapper(source,encoding='utf-8-sig',newline=''))
            header = next(reader)
            assert len(header) == len(set(header))
            positions = {key:header.index(key) for key in ALLOWED}
            assert not (set(positions) & set(FORBIDDEN))
            for row in reader:
                assert len(row) == len(header)
                d = {key:row[index] for key,index in positions.items()}
                rows += 1
                for key,value in d.items():
                    if not value.strip():
                        missing[key] += 1
                cell = (d['PANELNBR'],d['CELLNBR'])
                cells[cell].add((d['PANEL'],d['CELLNAME']))
                labs[d['SCREENER']] += 1
                valid[d['VALID']] += 1
                dates[d['TESTDATE']] += 1
                studies.add((d['SCREENER'],d['STUDY']))
                plates[(d['SCREENER'],d['STUDY'],d['PLATE'])].add(cell)
                for axis in ('1','2'):
                    units[d['CONCUNIT'+axis]] += 1
                    prefixes[d['PREFIX'+axis]] += 1
                    samples[d['NSC'+axis]].add(d['SAMPLE'+axis])
                pair = tuple(sorted(((d['NSC1'],d['SAMPLE1']),(d['NSC2'],d['SAMPLE2']))))
                pair_cells[pair].add(cell)
                cell_pairs[cell].add(pair)
                bundle = (d['SCREENER'],d['STUDY'],d['PLATE'],*cell,d['NSC1'],d['SAMPLE1'],d['NSC2'],d['SAMPLE2'])
                indices = (d['CONCINDEX1'],d['CONCINDEX2'])
                patterns[bundle][indices] += 1
                all_indices[indices] += 1
                bundle_counts[bundle] += 1
    signature_counts = Counter(tuple(sorted(p.items())) for p in patterns.values())
    result = {'scope':'DESIGN_COLUMNS_ONLY; no response payload conversion or output',
        'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'rows':rows,'selected_columns':list(ALLOWED),'forbidden_columns':list(FORBIDDEN),
        'labs':dict(labs),'valid':dict(valid),'units':dict(units),'prefixes':dict(prefixes),
        'cell_count':len(cells),'cells':[{'key':list(k),'names':sorted(v),'pairs':len(cell_pairs[k])} for k,v in sorted(cells.items())],
        'ambiguous_cell_keys':sum(len(v)!=1 for v in cells.values()),
        'studies':len(studies),'plates':len(plates),'plate_cell_count_histogram':dict(Counter(map(len,plates.values()))),
        'test_date_count':len(dates),'drugs_by_nsc':len(samples),'multiple_sample_nsc':{k:sorted(v) for k,v in samples.items() if len(v)>1},
        'pairs_including_samples':len(pair_cells),'pair_cell_coverage_histogram':dict(Counter(map(len,pair_cells.values()))),
        'bundles_defined_by_lab_study_plate_cell_ordered_sample_pair':len(patterns),
        'bundle_row_count_histogram':dict(Counter(bundle_counts.values())),
        'concentration_index_pattern_histogram':[{'indices':list(k),'rows':v} for k,v in sorted(all_indices.items())],
        'bundle_pattern_signatures':[{'pattern':[{'indices':list(k),'count':v} for k,v in sig],'bundles':count}
                                     for sig,count in signature_counts.most_common()],
        'missing_design_fields':dict(missing),'wall_s':time.perf_counter()-start}
    (OUT/'DESIGN.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('rows','labs','cell_count','studies','plates','pairs_including_samples',
                     'bundles_defined_by_lab_study_plate_cell_ordered_sample_pair','bundle_row_count_histogram','ambiguous_cell_keys','wall_s')},indent=2),flush=True)


if __name__ == '__main__':
    main()
