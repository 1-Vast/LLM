"""Authenticate designs/data links and acquire only small matched source figures."""
import json
import xml.etree.ElementTree as ET
from fetch_sources import P,parallel

def main():
    summaries={}
    for name in ['neuron_fulltext','mechanics_2021_fulltext','caf_rna_2023_fulltext']:
        tree=ET.fromstring((P/(name+'.body')).read_bytes())
        ps=[' '.join(''.join(p.itertext()).split()) for p in tree.iter('p')]
        selected=[p for p in ps if any(w in p.lower() for w in ['availability','deposited','blebb','y27632','washout','2d substrate','2d culture','data are','data is','three replicat','triplicat','stiffness'])]
        links=[dict(attrs=e.attrib,text=' '.join(''.join(e.itertext()).split())) for e in tree.iter('ext-link')]
        supp=[dict(attrs=e.attrib,text=' '.join(''.join(e.itertext()).split())) for e in tree.iter() if e.tag in ['supplementary-material','media']]
        summaries[name]=dict(paragraphs=selected,links=links,supplements=supp)
        print(json.dumps(dict(source=name,selected_paragraphs=selected[-10:],links=[r for r in links if any(w in str(r).lower() for w in ['zenodo','geo','gse','github','figshare','data.'])],supplements=supp),ensure_ascii=False))
    with (P/'RELATED_DESIGN_QUALIFICATION.json').open('x',encoding='utf-8') as f:json.dump(summaries,f,ensure_ascii=False,indent=2)
    record=json.loads((P/'neuron_zenodo_record.body').read_text())
    desired=['3(d)','5(a)','5(b)','6(h)','3(b)'];sources={};files=[]
    for panel in desired:
        asset=next(a for a in record['files'] if 'Figure '+panel+'.xlsx' in a['key'])
        assert asset['size']<100000
        name='neuron_figure_'+panel.replace('(','').replace(')','')
        sources[name]=asset['links']['self'];files.append(dict(name=name,**asset))
    with (P/'SMALL_ASSET_MANIFEST.json').open('x',encoding='utf-8') as f:json.dump(dict(record='neuron_zenodo_record.body',files=files,excluded_large_file='Figure7(g)135625028bytes is STORM pixel CDF, not a firing history or independent task population'),f,ensure_ascii=False,indent=2)
    parallel(sources)

if __name__=='__main__':main()
