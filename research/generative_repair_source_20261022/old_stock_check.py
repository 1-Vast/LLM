"""Read original released experiment identifiers only, never phenotype labels."""
from pathlib import Path
from collections import Counter, defaultdict
import csv
import hashlib
import json
import re

root = Path('D:/MAESTRO')
out = root/'log/20261022/generative_repair_renewal/source/archive_followup'
source = root/'data/external/ptv1_proteintalks_20261021/drive/allcelltype_drugpair_crossdrug_loo_label.csv'
# The observed first row is data [BT20_#10,24], not a header. This matches the
# retained study loader: header=None; cell=exp.split('_')[0]. Do not import it,
# because Release() would also load pheno.csv and expression quantities.
with source.open(encoding='utf-8-sig',newline='') as stream:
    identifiers = [row[0] for row in csv.reader(stream)]
stocks = sorted(set(identity.split('_',1)[0] for identity in identifiers))
lineages = sorted(set(stock.replace('(ATCC)','').strip() for stock in stocks))
rows = json.loads((out/'S8_IDENTITY_ROWS.json').read_text(encoding='utf-8'))
normalize = lambda text: re.sub(r'[^A-Z0-9]','',text.upper())
new_lines = sorted(set(row['Cell_line'] for row in rows))
controls = [row for row in rows if row['Compound_name'].lower()=='control']
groups = defaultdict(list)
for row in rows:
    groups[row['Sample_ID']].append(row)
duplicate_rep_patterns = Counter('|'.join(sorted(row['Rep'] or 'base' for row in group))
                                 for group in groups.values() if len(group)>1)
result = dict(old_source=str(source.relative_to(root)),
              sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
              first_row_is_data=True,parse_rule="Read only first field; stock before first underscore; lineage removes literal (ATCC)",
              old_stocks=stocks,old_stock_count=len(stocks),old_lineages=lineages,old_lineage_count=len(lineages),
              new_lines=new_lines,paper_to_actual_alias={'Panc 10.05':'Panc1005'},
              normalized_stock_overlap=sorted(set(map(normalize,stocks))&set(map(normalize,new_lines))),
              normalized_lineage_overlap=sorted(set(map(normalize,lineages))&set(map(normalize,new_lines))),
              S8_control_design_rows=controls,
              S8_unique_sample_ids=len(groups),S8_duplicate_sample_rep_patterns=dict(duplicate_rep_patterns),
              S8_unique_line_pert_time_groups=len(set((row['Cell_line'],row['Pert_ID'],row['Pert_time_(hrs)']) for row in rows)),
              outcomes_read=False)
(out/'OLD_STOCK_AND_CONTROL_CHECK.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
