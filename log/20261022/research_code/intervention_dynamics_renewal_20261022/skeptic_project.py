"""Project source identity and published abstracts, never response arrays."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET

BASE = Path('log/20261022/intervention_dynamics_renewal/skeptic')


def txt(node):
    return ''.join(node.itertext()).strip() if node is not None else ''


def main():
    root = ET.fromstring((BASE / 'ADAPTATION_ABSTRACTS.body').read_bytes())
    bio = []
    for a in root.findall('.//PubmedArticle'):
        ids = {v.attrib.get('IdType'): txt(v) for v in a.findall('./PubmedData/ArticleIdList/ArticleId')}
        bio.append({'pmid': txt(a.find('./MedlineCitation/PMID')), 'title': txt(a.find('./MedlineCitation/Article/ArticleTitle')),
                    'ids': ids, 'types': [txt(v) for v in a.findall('./MedlineCitation/Article/PublicationTypeList/PublicationType')],
                    'abstract': [txt(v) for v in a.findall('./MedlineCitation/Article/Abstract/AbstractText')],
                    'references': [{'citation': txt(v.find('Citation')), 'ids': {w.attrib.get('IdType'): txt(w) for w in v.findall('./ArticleIdList/ArticleId')}} for v in a.findall('./PubmedData/ReferenceList/Reference')]})
    (BASE / 'ADAPTATION_PRIMARY_LEADS.json').write_text(json.dumps(bio, ensure_ascii=False, indent=2), encoding='utf-8')
    ns = {'a': 'http://www.w3.org/2005/Atom'}
    root = ET.fromstring((BASE / 'ARXIV_SEMIGROUP_DISCOVERY.body').read_bytes())
    math = [{'id': txt(e.find('a:id', ns)), 'title': txt(e.find('a:title', ns)),
             'published': txt(e.find('a:published', ns)), 'summary': txt(e.find('a:summary', ns))}
            for e in root.findall('a:entry', ns)]
    (BASE / 'SEMIGROUP_PRIMARY_LEADS.json').write_text(json.dumps(math, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'biology': bio, 'math': math}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
