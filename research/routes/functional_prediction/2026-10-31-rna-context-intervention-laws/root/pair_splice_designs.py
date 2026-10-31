"""Authenticate labelled GT/GC design pairs; no RNA data or response fields."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path

E = Path(__file__).resolve().parent.parent
with (E/'root/promoter_design_identities.tsv').open(encoding='utf-8') as stream:
    rows = list(csv.DictReader(stream,delimiter='\t'))
groups = {}
typed = Counter()
for row in rows:
    if row['subset']=='cassetteconstvar':
        typed[(row['first_ss'],row['second_ss'])] += 1
    if row['subset']=='cassetteconstvar' and row['first_ss']=='constitutive' and row['second_ss'] in ('constitutive','GC'):
        key = (row['gene name'],row['exonstart in sequence'],row['exonend in sequence'])
        group = groups.setdefault(key,{})
        assert row['second_ss'] not in group
        group[row['second_ss']] = row
pairs, ambiguous = [], []
for key,group in groups.items():
    if len(group)!=2:
        ambiguous.append(key)
        continue
    a,b = group['constitutive'],group['GC']
    assert len(a['sequence'])==len(b['sequence'])==210
    diffs = [i for i,(x,y) in enumerate(zip(a['sequence'],b['sequence'])) if x!=y]
    outside = [i for i in diffs if not 18<=i<30]
    pairs.append({'gene_label':key[0],'exon_start':key[1],'exon_end':key[2],
                  'reference_id':a['library index'],'edited_id':b['library index'],
                  'all_different_positions':diffs,'outside_barcode_differences':outside,
                  'barcode_differences':[i for i in diffs if 18<=i<30],
                  'qualified_local_donor_difference':outside==[163] and a['sequence'][163]=='T' and b['sequence'][163]=='C'})
result = {'scope':'Design sequence comparison only; no RNA outcome/support interpretation',
          'identity_tsv_sha256':hashlib.sha256((E/'root/promoter_design_identities.tsv').read_bytes()).hexdigest(),
          'contract_sha256':hashlib.sha256((E/'root/pairing_contract.md').read_bytes()).hexdigest(),
          'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'typed_constvar_combinations':{' / '.join(k):v for k,v in typed.items()},
          'labelled_pair_groups':len(groups),'complete_pairs':len(pairs),'ambiguous_groups':ambiguous,
          'qualified_one_donor_difference_pairs':sum(p['qualified_local_donor_difference'] for p in pairs),
          'same_barcode_pairs':sum(not p['barcode_differences'] for p in pairs),'pairs':pairs,
          'pure_cis_causal_attribution_qualified':False,'RNA_support_qualified':False,
          'limitation':'Each reference/edited construct also changes its12ntbarcode; no complete typed native/donor/acceptor/double factorial is inferred.'}
out = E/'root/local_donor_design_pairs.json'
assert not out.exists()
out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:result[k] for k in ['labelled_pair_groups','complete_pairs','ambiguous_groups',
      'qualified_one_donor_difference_pairs','same_barcode_pairs','typed_constvar_combinations']}))
