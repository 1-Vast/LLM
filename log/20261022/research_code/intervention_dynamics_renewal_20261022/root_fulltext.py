"""One selected official primary XML and narrative/asset projection."""
import xml.etree.ElementTree as ET

import root_search as scout


def main():
    receipt, raw = scout.get('selected_fulltext', scout.BASE+'efetch.fcgi?db=pmc&id=11264686&retmode=xml')
    if receipt.get('status') != 200 or 'error_type' in receipt:
        print('SELECTED_FULLTEXT_ACCESS_FAILED_RETAINED')
        return 1
    try:
        doc = ET.fromstring(raw)
        article = doc.find('article') if doc.tag != 'article' else doc
        if article is None:
            raise ValueError('article_missing')
        narrative = []
        for section in article.findall('./body//sec') + article.findall('./back//sec'):
            title = ''.join(section.find('title').itertext()) if section.find('title') is not None else ''
            paragraphs = [''.join(p.itertext()) for p in section.findall('./p')]
            narrative.append({'title': title, 'paragraphs': paragraphs})
        links = []
        for element in article.iter():
            href = element.attrib.get('{http://www.w3.org/1999/xlink}href')
            if href:
                links.append({'tag': element.tag, 'href': href, 'text': ''.join(element.itertext())[:300]})
        scout.write(scout.OUT/'FULLTEXT_NARRATIVE.json', {'sections': narrative, 'asset_links': links,
                    'exposure': 'Primary narrative/results and asset identity designer-exposed; no downloaded dataset arrays.'})
        for s in narrative:
            if any(word in s['title'].lower() for word in ['method', 'material', 'availability', 'supplement', 'experiment', 'microfluid', 'data']):
                print(s)
        print({'asset_links': links})
        return 0
    except Exception as error:
        scout.write(scout.OUT/'FULLTEXT_PARSE_FAILURE.json', {'error_type': type(error).__name__})
        print('FULLTEXT_PARSE_FAILED_RETAINED')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
