"""Read control-table identity columns only; counts and responses stay unused."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path

E = Path(__file__).resolve().parent.parent
SOURCE = E/'investigator/sources/promoter_425a.csv.hop1'
RAW = ['intron1start_o','intron1end_o','intron2start_o','intron2end_o']
CORRECTED = ['intron1_maxent5_nt','intron1_maxent3_nt','intron2_maxent5_nt','intron2_maxent3_nt']
ALLOWED = ['chr','isoform',*RAW,*CORRECTED]


def normalize(value):
    if value.strip().lower() in ('','nan','none'):
        return 'nan'
    number = float(value)
    assert number.is_integer(), value
    return str(int(number))


rows,variants,keys,examples = 0,set(),{},[]
counts = Counter()
with SOURCE.open(encoding='utf-8-sig',newline='') as stream:
    reader = csv.reader(stream)
    header = next(reader)
    indices = {key:header.index(key) for key in ALLOWED}
    for source_row in reader:
        row = {key:source_row[index] for key,index in indices.items()}
        rows += 1
        variants.add(row['chr'])
        raw = tuple(normalize(row[k]) for k in RAW)
        corrected = tuple(normalize(row[k]) for k in CORRECTED)
        raw_key = '_'.join(raw)
        corrected_key = '_'.join(corrected)
        counts['literal_matches_o'] += row['isoform']==raw_key
        counts['literal_matches_corrected'] += row['isoform']==corrected_key
        counts['o_differs_from_corrected'] += raw!=corrected
        key = (row['chr'],row['isoform'])
        previous = keys.get(key)
        counts['repeated_variant_isoform_key_rows'] += previous is not None
        if previous is None:
            keys[key] = (raw,corrected)
        elif previous!=(raw,corrected):
            counts['key_coordinate_disagreement_rows'] += 1
        if len(examples)<5 and raw!=corrected:
            examples.append({'library_id':row['chr'],'literal_isoform':row['isoform'],
                             'o_coordinates':raw,'corrected_coordinates':corrected})
out = {
    'scope':'Unweighted control-table coordinate identities only, no RNA count/effect analysis',
    'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'contract_sha256':hashlib.sha256((E/'root/coordinate_identity_contract.md').read_bytes()).hexdigest(),
    'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'projected_columns':ALLOWED,'rows':rows,'observed_variant_ids':len(variants),
    'distinct_variant_isoform_keys':len(keys),'identity_checks':dict(counts),
    'examples_of_changed_coordinates':examples,
    'RNA_count_fields_used':False,'upstream_raw_count_preservation_qualified':False,
    'limitation':'Observed exported consistency does not authenticate upstream grouping or recover omitted fates.'}
target = E/'root/coordinate_identity_check.json'
assert not target.exists()
target.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps(out))
