"""Export only selected first-five-field identities and fixed incidence weights."""
from collections import defaultdict
from pathlib import Path
import hashlib
import json
import numpy as np

root = Path(__file__).resolve().parents[3]
prior = root/'log/20261023/replicated_contrast'
out = root/'log/20261023/contrast_transport_mechanism/source'
pairs = [tuple(p) for p in json.loads((prior/'SELECTED_PAIR_IDS.json').read_text())]
positions = {p:i for i,p in enumerate(pairs)}
saved_ids = json.loads((prior/'CONSTRUCT_IDS.json').read_text())
wanted = set(saved_ids)
rows = {}
with (prior/'counts.body').open('rb') as handle:
    handle.readline()
    for line in handle:
        first = line.split(b',',5)[:5]
        name = first[0].decode('utf-8')
        if name not in wanted:
            continue
        name,a,ga,b,gb = [x.decode('utf-8') for x in first]
        assert name not in rows
        rows[name] = dict(construct_id=name,target_a_id=a,probe_a_id=ga,
                          target_b_id=b,probe_b_id=gb,pair_row=positions[tuple(sorted((a,b)))])
assert set(rows) == wanted
records = [rows[name] for name in saved_ids]
assert len(records) == 9306
path = out/'SELECTED_CONSTRUCT_METADATA.json'
path.write_text(json.dumps(records,indent=2),encoding='utf-8')
gene_labels = sorted({slot+row[field] for row in records for slot,field in [('L:','target_a_id'),('R:','target_b_id')]})
guide_labels = sorted({slot+row[field] for row in records for slot,field in [('L:','probe_a_id'),('R:','probe_b_id')]})
gi,hi = {x:i for i,x in enumerate(gene_labels)},{x:i for i,x in enumerate(guide_labels)}
sizes = np.bincount([row['pair_row'] for row in records],minlength=len(pairs))
gene,guide = np.zeros((1024,len(gi))),np.zeros((1024,len(hi)))
guide_parent = {}
for row in records:
    i = row['pair_row']
    for slot,g,h in [('L:',row['target_a_id'],row['probe_a_id']),('R:',row['target_b_id'],row['probe_b_id'])]:
        gene[i,gi[slot+g]] += 1/sizes[i]
        guide[i,hi[slot+h]] += 1/sizes[i]
        if slot+h in guide_parent:
            assert guide_parent[slot+h] == slot+g
        guide_parent[slot+h] = slot+g
by_parent = defaultdict(list)
for h,g in guide_parent.items():
    by_parent[g].append(h)
assert all(len(by_parent[g]) == 3 for g in gene_labels)
errors = [float(np.max(np.abs(3*guide[:,hi[h]]-gene[:,gi[g]]))) for h,g in guide_parent.items()]
assert max(errors) < 1e-14
for g, hs in by_parent.items():
    assert np.allclose(guide[:,[hi[h] for h in hs]].sum(axis=1),gene[:,gi[g]],rtol=0,atol=1e-14)
matrix_path = out/'IDENTITY_NUISANCE_MATRICES.npz'
np.savez_compressed(matrix_path,role_gene=gene,role_guide=guide,construct_sizes=sizes)
label_path = out/'IDENTITY_NUISANCE_LABELS.json'
label_path.write_text(json.dumps(dict(role_gene=gene_labels,role_guide=guide_labels,
                                    guide_parent=guide_parent),indent=2),encoding='utf-8')
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
summary = dict(actions=1024,constructs=len(records),gene_columns=len(gi),guide_columns=len(hi),
               all_parent_guides3=True,guide_column_equals_one_third_parent=True,
               maximum_identity_weight_discrepancy=max(errors),column_spaces_equal=True,
               proof='For each role-guide h of role-gene g, H_h=B_g/3 and B_g=sum_{h child of g} H_h.',
               metadata_sha256=sha(path),matrix_sha256=sha(matrix_path),labels_sha256=sha(label_path),
               script_sha256=sha(Path(__file__)),count_fields_decoded=False,count_fields_cast=False,
               raw_body_first5_fields_only=True)
(out/'IDENTIFIER_EXPORT_AUDIT.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary))
