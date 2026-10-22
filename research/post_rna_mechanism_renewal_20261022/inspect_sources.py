"""Extract bounded author evidence and retain separately named access attempts."""
import json
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from fetch_primary import fetch, P

def main():
    tree=ET.fromstring((P/'caf_fulltext.body').read_bytes())
    paragraphs=[]
    for element in tree.iter():
        if element.tag in ('p','title','supplementary-material'):
            value=' '.join(''.join(element.itertext()).split())
            if any(word in value.lower() for word in ('availability','geo','accession','proliferation','migration','cytokine','supplement','cell line','patient','scrna','concentration')):
                paragraphs.append(dict(tag=element.tag,text=value))
    links=[dict(tag=e.tag,attrs=e.attrib,text=' '.join(''.join(e.itertext()).split())) for e in tree.iter() if e.tag in ('ext-link','supplementary-material','media')]
    result=dict(source='caf_fulltext.body',sections=paragraphs,links=links)
    with (P/'caf_author_extraction.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps(dict(caf_paragraphs=len(paragraphs),links=links),ensure_ascii=False))
    sources={
      'labcompass_corrected_doi_metadata':'https://api.biorxiv.org/details/biorxiv/10.64898/2026.10.07.756550',
      'resolution_corrected_doi_metadata':'https://api.biorxiv.org/details/biorxiv/10.64898/2026.09.30.755756',
      'labcompass_author_full':'https://www.biorxiv.org/content/10.64898/2026.10.07.756550v1.full',
      'podocyte_fulltext':'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13665701/fullTextXML'}
    with ThreadPoolExecutor(max_workers=4) as pool:
        for receipt in pool.map(fetch,sources.items()):print(json.dumps(receipt),flush=True)

if __name__=='__main__':main()
