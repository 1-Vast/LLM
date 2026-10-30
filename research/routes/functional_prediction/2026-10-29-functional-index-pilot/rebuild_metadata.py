import csv, gzip, hashlib, io, json, time, zipfile
from collections import defaultdict, Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path

OUT = Path(__file__).resolve().parent
RAW = OUT.parents[1] / 'tmp/extq1/gsdc_well_stats.zip'
EXPECTED = 'e8cb50f6ce860fa17586a555130cb3b019f6011ed1976c0f0d3e00fb072d3259'
MEMBER = 'combo_well_stats_GDSC_007_05May22.csv'
start, cpu = time.monotonic(), time.process_time()
sha = hashlib.sha256()
with RAW.open('rb') as f:
    for block in iter(lambda: f.read(1024*1024), b''):
        sha.update(block)
assert sha.hexdigest() == EXPECTED, 'ZIP SHA mismatch'
groups = {}
master_to_line, line_to_master = defaultdict(set), defaultdict(set)
counts = Counter()
with zipfile.ZipFile(RAW) as z:
    info = z.getinfo(MEMBER)
    with z.open(info) as f:
        r = csv.reader(io.TextIOWrapper(f, encoding='utf-8-sig', newline=''))
        header = next(r)
        fields = ['PROJECT_ID','MASTER_CELL_ID'] + [f'lib{s}_{v}' for s in (1,2) for v in ('drug_id','drug','conc')]
        idx = {k: header.index(k) for k in fields}
        line_idx = header.index('CELL_LINE_ID') if 'CELL_LINE_ID' in header else None
        (OUT/'metadata_header_receipt.json').write_text(json.dumps({'sha256':sha.hexdigest(),'member':MEMBER,'member_crc':info.CRC,'compressed_bytes':info.compress_size,'uncompressed_bytes':info.file_size,'header':header,'semantic_whitelist':fields + (['CELL_LINE_ID'] if line_idx is not None else []),'whole_row_tokenization':True},indent=2))
        for row in r:
            counts['rows'] += 1
            project, cell = row[idx['PROJECT_ID']], row[idx['MASTER_CELL_ID']]
            if line_idx is not None:
                line = row[line_idx]
                master_to_line[cell].add(line)
                line_to_master[line].add(cell)
            for side in (1,2):
                drug, ref, rawq = (row[idx[f'lib{side}_{v}']] for v in ('drug_id','drug','conc'))
                key = (project,cell,drug)
                if key not in groups:
                    groups[key] = [ref, {}, set()]
                g = groups[key]
                g[2].add(ref)
                if ref < g[0]:
                    g[0], g[1] = ref, {}
                counts[f'side{side}_occurrences'] += 1
                try:
                    q = Decimal(rawq)
                    valid = q.is_finite() and q > 0
                except InvalidOperation:
                    valid = False
                if not valid:
                    counts['invalid_dose_occurrences'] += 1
                elif ref == g[0]:
                    old = g[1].get(q, [0,0])
                    old[side-1] += 1
                    g[1][q] = old
            if counts['rows'] % 10000 == 0:
                assert time.monotonic()-start <= 180, 'wall guard'
                assert time.process_time()-cpu <= 120, 'CPU guard'

records = []
for (p,c,d), (ref, doses, refs) in sorted(groups.items()):
    records.append({'project':p,'cell':c,'drug':d,'ref':ref,'doses':[str(q) for q in sorted(doses)],'refs':sorted(refs)})
    counts['selected_dose_keys'] += len(doses)
    counts['selected_cross_side_keys'] += sum(a>0 and b>0 for a,b in doses.values())
    counts['selected_repeated_keys'] += sum(a+b>1 for a,b in doses.values())
    counts['selected_occurrences'] += sum(a+b for a,b in doses.values())
    counts['multiple_ref_groups'] += len(refs)>1
projection = OUT/'independent_metadata.json.gz'
with gzip.open(projection,'wt',encoding='utf-8',newline='\n') as f:
    json.dump(records,f,separators=(',',':'))
targets = {'2428':Decimal('0.00100053'),'2429':Decimal('0.00100053'),'2430':Decimal('0.01000527')}
support = {d:{c for (p,c,drug),g in groups.items() if p=='2' and drug==d and q in g[1]} for d,q in targets.items()}
common = sorted(set.intersection(*support.values()))
summary = {'input_sha256':sha.hexdigest(),'member':MEMBER,'counts':dict(counts),'groups':len(groups),'projects':sorted({k[0] for k in groups}),'master_cell_count':len({k[1] for k in groups}),'drug_count':len({k[2] for k in groups}),'cell_line_id_present':line_idx is not None,'master_to_line_conflicts':{k:sorted(v) for k,v in master_to_line.items() if len(v)>1} if line_idx is not None else 'unknown: field absent','line_to_master_conflicts':{k:sorted(v) for k,v in line_to_master.items() if len(v)>1} if line_idx is not None else 'unknown: field absent','target_support_counts':{d:len(v) for d,v in support.items()},'target_common_cells':common,'target_common_count':len(common),'projection_sha256':hashlib.sha256(projection.read_bytes()).hexdigest(),'wall_seconds':time.monotonic()-start,'cpu_seconds':time.process_time()-cpu,'comparison_read':False,'cross_side_scope':'selected lexicographic refs only; both side occurrences counted','biological_independence':'not authenticated','functional_relation':'not accessed'}
(OUT/'independent_metadata_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
assert sum(p.stat().st_size for p in OUT.iterdir() if p.is_file()) <= 20_000_000, 'output budget'
print(json.dumps({'rows':counts['rows'],'groups':len(groups),'common_target_cells':len(common),'wall_seconds':summary['wall_seconds'],'cpu_seconds':summary['cpu_seconds']}))
