from pathlib import Path
from html.parser import HTMLParser
import json

class Extract(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts=[]
        self.meta={}
        self.skip=0
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag in ('script','style'): self.skip+=1
        if tag=='meta' and a.get('name','').startswith('citation_'):
            self.meta.setdefault(a['name'],[]).append(a.get('content'))
        if tag in ('p','div','h1','h2','h3','tr','li'): self.parts.append('\n')
        if tag=='math' and a.get('alttext'): self.parts.append(' [LATEX '+a['alttext']+'] ')
    def handle_endtag(self, tag):
        if tag in ('script','style'): self.skip-=1
    def handle_data(self, data):
        if not self.skip: self.parts.append(data)

root=Path('D:/MAESTRO/log/20261022/frontier_transfer/sources')
for f in sorted(root.glob('*.body')):
    p=Extract();p.feed(f.read_text(encoding='utf-8'))
    content='\n'.join(' '.join(line.split()) for line in ''.join(p.parts).splitlines() if line.strip())
    f.with_suffix('.txt').write_text(content,encoding='utf-8')
    if '_abs' in f.name:
        i=content.find('Submission history')
        print(f.name, json.dumps(p.meta), content[i:i+900])
        f.with_suffix('.metadata.json').write_text(json.dumps(p.meta,indent=2),encoding='utf-8')
