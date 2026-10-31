"""Print one bounded original-source passage without executing source code."""
import argparse
from pathlib import Path
import xml.etree.ElementTree as ET

parser = argparse.ArgumentParser()
parser.add_argument('source')
parser.add_argument('--section')
parser.add_argument('--start', type=int, default=0)
parser.add_argument('--limit', type=int, default=4500)
args = parser.parse_args()
root = ET.fromstring(Path(args.source).read_bytes())
if args.section is None:
    print('TITLE:', ' '.join(root.find('.//article-title').itertext()))
    print('DOI:', [n.text for n in root.findall('.//article-id') if n.get('pub-id-type') == 'doi'])
    for index, section in enumerate(root.findall('.//body//sec')):
        print(index, section.get('id'), ' '.join(section.findtext('title','').split()))
else:
    sections = root.findall('.//body//sec')
    section = sections[int(args.section)]
    content = '\n'.join(' '.join(element.itertext()) for element in section if element.tag not in ('sec','fig','table-wrap'))
    print('SECTION:', section.get('id'), ' '.join(section.findtext('title','').split()))
    print(content[args.start:args.start+args.limit])
    print('CURSOR:', args.start+args.limit, 'TOTAL_CHARACTERS:', len(content))
