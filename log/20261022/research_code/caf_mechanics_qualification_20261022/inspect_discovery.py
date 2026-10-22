"""Keep bounded registry/institution evidence and exact discovered links."""
from html.parser import HTMLParser
import json
from fetch_sources import P

class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[];self.parts=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='a' and 'href' in a:self.links.append(a['href'])
    def handle_data(self,data):
        if data.strip():self.parts.append(data.strip())

def main():
    data=json.loads((P/'datacite_emon.body').read_text());rows=[]
    for entry in data['data']:
        a=entry['attributes'];authors=[c.get('name','') for c in a.get('creators',[])]
        if any('emon' in name.lower() for name in authors):
            rows.append({k:a.get(k) for k in ['doi','titles','creators','url','relatedIdentifiers','types','descriptions']})
    crossref=json.loads((P/'crossref_mechanics_doi.body').read_text())['message']
    openalex=json.loads((P/'openalex_mechanics_doi.body').read_text())
    parser=Links();parser.feed((P/'illinois_saif_official.body').read_text())
    links=list(dict.fromkeys(u for u in parser.links if any(word in u.lower() for word in ['saif','lab','research','publication','emon','752881','collagen'])))
    text='\n'.join(parser.parts)
    with (P/'illinois_saif_official_text.txt').open('x',encoding='utf-8',newline='\n') as f:f.write(text)
    result=dict(datacite=dict(meta=data.get('meta'),returned=len(data['data']),creator_matching_rows=rows),crossref={k:crossref.get(k) for k in ['DOI','title','author','link','resource','relation','URL','abstract']},openalex={k:openalex.get(k) for k in ['id','doi','title','open_access','primary_location','locations','best_oa_location','has_fulltext','content_urls']},institution_links=links)
    with (P/'DISCOVERY_EXTRACTION.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps(dict(datacite_meta=data.get('meta'),creator_matches=[dict(doi=r['doi'],titles=r['titles'],names=[c.get('name') for c in r['creators']]) for r in rows],crossref_links=result['crossref']['link'],openalex=result['openalex'],institution_links=links),ensure_ascii=False))

if __name__=='__main__':main()
