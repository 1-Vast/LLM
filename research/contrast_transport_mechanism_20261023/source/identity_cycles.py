"""Selected-action identity/role/guide structure only; never casts counts."""
from collections import defaultdict
from itertools import combinations, product
from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parents[3]
out = root/'log/20261023/contrast_transport_mechanism/source'
out.mkdir(parents=True, exist_ok=True)
prior = root/'log/20261023/replicated_contrast'
pairs = {tuple(p) for p in json.loads((prior/'SELECTED_PAIR_IDS.json').read_text())}
saved_ids = set(json.loads((prior/'CONSTRUCT_IDS.json').read_text()))
edges = defaultdict(list)
identity_rows = []
with (prior/'counts.body').open('rb') as source:
    header = source.readline().split(b',')
    assert [x.decode() for x in header[:5]] == ['construct_id','target_a_id','probe_a_id','target_b_id','probe_b_id']
    for line in source:
        fields = line.split(b',',5)
        name,a,ga,b,gb = [x.decode('utf-8') for x in fields[:5]]
        if tuple(sorted((a,b))) not in pairs:
            continue
        edges[a,b].append((ga,gb,name))
        identity_rows.append((name,a,ga,b,gb))
assert {x[0] for x in identity_rows} == saved_ids
assert len(identity_rows) == len(saved_ids)
left, right = defaultdict(set), defaultdict(set)
complete = True
for (a,b), rows in edges.items():
    left[a].add(b)
    right[b].add(a)
    ga,gb = {x[0] for x in rows},{x[1] for x in rows}
    complete &= len(rows) == 9 and len(ga) == len(gb) == 3 and {(x[0],x[1]) for x in rows} == set(product(ga,gb))
rectangles = []
for a,c in combinations(sorted(left),2):
    for b,d in combinations(sorted(left[a] & left[c]),2):
        rectangles.append([a,c,b,d])
adjacency = defaultdict(set)
for a,b in edges:
    adjacency['L:'+a].add('R:'+b)
    adjacency['R:'+b].add('L:'+a)
remaining, components = set(adjacency), 0
while remaining:
    components += 1
    stack = [remaining.pop()]
    while stack:
        for node in adjacency[stack.pop()]:
            if node in remaining:
                remaining.remove(node)
                stack.append(node)
slots = defaultdict(set)
for _,a,ga,b,gb in identity_rows:
    slots['L:'+a].add(ga)
    slots['R:'+b].add(gb)
stable3 = all(len(g) == 3 for g in slots.values())
guide_rectangles = 0
for a,c,b,d in rectangles:
    for ga,gc,gb,gd in product(slots['L:'+a],slots['L:'+c],slots['R:'+b],slots['R:'+d]):
        if all((x,y) in {(u,v) for u,v,_ in edges[A,B]} for A,B,x,y in [(a,b,ga,gb),(a,d,ga,gd),(c,b,gc,gb),(c,d,gc,gd)]):
            guide_rectangles += 1
manifest = out/'IDENTITY_RECTANGLES.json'
manifest.write_text(json.dumps(rectangles,indent=2),encoding='utf-8')
summary = dict(selected_actions=len(pairs), identity_rows=len(identity_rows), ordered_edges=len(edges),
               left_genes=len(left),right_genes=len(right), connected_components=components,
               additive_cycle_dimension=len(edges)-len(adjacency)+components,
               ordered_gene_rectangles=len(rectangles), guide_rectangles=guide_rectangles,
               each_ordered_edge_exact_3x3=bool(complete), each_slot_gene_exact_3guides=stable3,
               selected_identity_match_saved_construct_ids=True,
               rectangle_manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),
               code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               numeric_count_fields_decoded=False, numeric_count_fields_cast=False,
               raw_count_body_opened_for_first5_identity_only=True,
               note='Graph counts are identity metadata, not biological sample sizes or new endpoint observations')
(out/'IDENTITY_GRAPH_AUDIT.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary))
