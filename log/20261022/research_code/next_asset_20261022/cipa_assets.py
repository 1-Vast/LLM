from discover import OUT
import hashlib
import json
import requests
from html.parser import HTMLParser

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links=[]
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='a' and attrs.get('href'):
            self.links.append(attrs['href'])

def get(name,url):
    response=requests.get(url,timeout=90)
    with (OUT/(name+'.body')).open('xb') as f:
        f.write(response.content)
    receipt={'url':url,'final_url':response.url,'status':response.status_code,'bytes':len(response.content),'sha256':hashlib.sha256(response.content).hexdigest(),'content_type':response.headers.get('Content-Type')}
    (OUT/(name+'.receipt.json')).write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print(json.dumps(receipt))
    return response

if __name__=='__main__':
    response=get('cipa_resource_page','https://cipaproject.org/data-resources/')
    parser=Links(); parser.feed(response.text)
    (OUT/'cipa_resource_links.json').write_text(json.dumps(parser.links,indent=2),encoding='utf-8')
    print(json.dumps(parser.links))
