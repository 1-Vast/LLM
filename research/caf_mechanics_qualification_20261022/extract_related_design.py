"""Record paper designs and data links, keeping distinct studies distinct."""
import json
import xml.etree.ElementTree as ET
from fetch_sources import P,parallel

def extract(name):
    tree=ET.fromstring((P/(name+'.body')).read_bytes())
    paragraphs=[' '.join(''.join(p.itertext()).split()) for p in tree.iter('p')]
    figures=[dict(id=f.attrib.get('id'),text=' '.join(''.join(f.itertext()).split())) for f in tree.iter('fig')]
    links=[dict(attrs=e.attrib,text=' '.join(''.join(e.itertext()).split())) for e in tree.iter('ext-link')]
    result=dict(source=name+'.body',paragraphs=paragraphs,figures=figures,links=links)
    with (P/(name+'_extraction.json')).open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps(dict(source=name,figures=figures,paragraphs=[v for v in paragraphs if any(w in v.lower() for w in ['blebbi','wash','availab','zenodo','drug','cytochalasin'])]),ensure_ascii=False))

if __name__=='__main__':
    extract('neuron_fulltext')
    sources={}
    for name in ['mechanics_2021_index','mechanics_protocol_2025_index','caf_rna_2023_index','caf_yap_2024_index']:
        payload=json.loads((P/(name+'.body')).read_text())
        rows=payload['resultList']['result']
        print(json.dumps(dict(source=name,results=[{k:r.get(k) for k in ['title','doi','pmcid','abstractText','firstPublicationDate']} for r in rows]),ensure_ascii=False))
        pmcs={r['pmcid'] for r in rows if r.get('pmcid')}
        assert len(pmcs)<=1
        if pmcs:sources[name.removesuffix('_index')+'_fulltext']='https://www.ebi.ac.uk/europepmc/webservices/rest/'+next(iter(pmcs))+'/fullTextXML'
    parallel(sources)
