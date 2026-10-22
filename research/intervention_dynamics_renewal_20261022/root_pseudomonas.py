"""Read one selected primary; never open its linked response assets."""
import xml.etree.ElementTree as ET

import root_search as scout


def text(node):
    return ''.join(node.itertext()) if node is not None else ''


def main():
    receipt, raw = scout.get('pseudomonas_fulltext',
        scout.BASE+'efetch.fcgi?db=pmc&id=11430049&retmode=xml')
    if receipt.get('status') != 200 or 'error_type' in receipt:
        print('PSEUDOMONAS_ACCESS_FAILURE_RETAINED')
        return 1
    doc = ET.fromstring(raw)
    article = doc if doc.tag == 'article' else doc.find('article')
    if article is None:
        raise ValueError('article_missing')
    sections = [{'title': text(s.find('title')),
                 'paragraphs': [text(p) for p in s.findall('p')]}
                for s in article.findall('./body//sec')+article.findall('./back//sec')]
    captions = [{'id': f.get('id'), 'caption': text(f.find('caption'))}
                for f in article.iter('fig')]
    links = [{'tag': e.tag, 'href': e.attrib['{http://www.w3.org/1999/xlink}href'],
              'text': text(e)[:180]} for e in article.iter()
             if '{http://www.w3.org/1999/xlink}href' in e.attrib]
    result = {'sections': sections, 'captions': captions, 'asset_links': links,
              'exposure': 'Published primary prose and captions; no numerical data asset opened.'}
    scout.write(scout.OUT/'PSEUDOMONAS_PRIMARY.json', result)
    for s in sections:
        if any(k in s['title'].lower() for k in ('method', 'data', 'availab', 'microfluid', 'assay')):
            print(s)
    print({'captions': captions, 'links': links})
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
