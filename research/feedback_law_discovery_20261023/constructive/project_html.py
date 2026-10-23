from html.parser import HTMLParser
from pathlib import Path

class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts=[]
        self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style'): self.skip+=1
        if tag in ('p','h1','h2','h3','h4','div','li'): self.parts.append('\n')
    def handle_endtag(self,tag):
        if tag in ('script','style'): self.skip=max(0,self.skip-1)
        if tag in ('p','h1','h2','h3','h4','div','li'): self.parts.append('\n')
    def handle_data(self,data):
        if not self.skip: self.parts.append(data)

import sys
p=Path('D:/MAESTRO/log/20261023/feedback_law_discovery/constructive')
name=sys.argv[1]
t=Text();t.feed((p/f'{name}.body').read_text(encoding='utf-8'))
lines=[' '.join(x.split()) for x in ''.join(t.parts).splitlines() if x.strip()]
(p/f'{name}.text.txt').write_text('\n'.join(lines),encoding='utf-8')
for i,l in enumerate(lines,1):
    if any(w in l.lower() for w in ('method','saturat','combinatorial','epistas','code availability','github','feedback','sparsity','sparse','interaction')):
        print(i,l[:400])


