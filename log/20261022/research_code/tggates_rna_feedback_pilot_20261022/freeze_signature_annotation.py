"""Fetch only official platform annotation and primary article, never expression."""
import csv
import hashlib
import io
import json
from pathlib import Path
import urllib.request

OUT = Path('log/20261022/tggates_rna_feedback_pilot/annotation')
OUT.mkdir(parents=True, exist_ok=True)
sources = {
    'GPL570.txt': 'https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GPL570&targ=self&form=text&view=full',
    'ZHANG_PUBMED.html': 'https://pubmed.ncbi.nlm.nih.gov/24217556/',
}
receipts = []
for name, url in sources.items():
    with urllib.request.urlopen(url, timeout=120) as response:
        data = response.read()
        receipts.append(dict(url=url, final_url=response.url, status=response.status,
                             bytes=len(data), sha256=hashlib.sha256(data).hexdigest()))
    (OUT / name).write_bytes(data)
(OUT / 'SOURCE_RECEIPTS.json').write_text(json.dumps(receipts, indent=2))
text = (OUT / 'GPL570.txt').read_text(encoding='utf-8')
table = text.split('!platform_table_begin\n', 1)[1].split('!platform_table_end', 1)[0]
genes = ['EGR1', 'ATF3', 'GDF15', 'FGF21']
mapping = {g: [] for g in genes}
for row in csv.DictReader(io.StringIO(table), delimiter='\t'):
    gene = row['Gene Symbol'].strip()
    if gene in mapping:
        mapping[gene].append(row['ID'])
for gene in genes:
    mapping[gene] = sorted(set(mapping[gene]))
    assert mapping[gene], gene
result = dict(genes=genes, mapping=mapping, rule='Exact single Gene Symbol; all matching probesets, arithmetic mean of log signals; no outcome selection',
              provenance='Zhang et al DOI10.1038/tpj.2013.39, PubMed24217556 abstract; NCBI official GPL570 platform annotation',
              source_receipts=receipts)
dest = OUT / 'FOUR_GENE_MAPPING.json'
dest.write_text(json.dumps(result, indent=2))
(OUT / 'FOUR_GENE_MAPPING.sha256').write_text(hashlib.sha256(dest.read_bytes()).hexdigest()+'\n')
print(json.dumps(mapping))
