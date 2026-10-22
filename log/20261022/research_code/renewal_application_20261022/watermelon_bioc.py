"""Official NCBI BioC representation after retained Europe PMC failure."""
import json
import xml.etree.ElementTree as ET

from lineage_followup import OUT, get


if __name__ == '__main__':
    response = get('watermelon_ncbi_bioc', 'https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_xml/PMC9209846/unicode')
    print(json.dumps({'status': response.status_code, 'bytes': len(response.content)}))
    if response.status_code == 200:
        tree = ET.fromstring(response.content)
        paragraphs = [node.text or '' for node in tree.iter('text')]
        (OUT / 'watermelon_ncbi_bioc.txt').write_text('\n\n'.join(paragraphs) + '\n', encoding='utf-8')
        selected = [p for p in paragraphs if any(word in p.lower() for word in
                    ('gse', 'data availability', 'code availability', 'github', 'cell lines', 'cell line', 'watermelon', 'barcode'))]
        print(json.dumps(selected[:18], ensure_ascii=False))
