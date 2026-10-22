"""Retain relevant author paragraphs, figures and links without XML console dumps."""
import json
import xml.etree.ElementTree as ET
from fetch_primary import P

def main():
    for name,words in {
        'lcd_fulltext':('availability','identif','assum','linear','perturbation','stationary','github','data set'),
        'podocyte_fulltext':('fdr','replicat','limitation','availability','accession','nominal')}.items():
        tree=ET.fromstring((P/(name+'.body')).read_bytes())
        paragraphs=[]
        for element in tree.iter('p'):
            value=' '.join(''.join(element.itertext()).split())
            if any(word in value.lower() for word in words):paragraphs.append(value)
        links=[dict(attrs=e.attrib,text=' '.join(''.join(e.itertext()).split())) for e in tree.iter('ext-link')]
        with (P/(name+'_extraction.json')).open('x',encoding='utf-8') as f:json.dump(dict(source=name+'.body',paragraphs=paragraphs,links=links),f,ensure_ascii=False,indent=2)
        print(json.dumps(dict(source=name,paragraphs=len(paragraphs),links=links),ensure_ascii=False))

if __name__=='__main__':main()
