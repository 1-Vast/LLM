from html.parser import HTMLParser
from pathlib import Path
class Reader(HTMLParser):
 def __init__(self): super().__init__(); self.skip=0; self.parts=[]
 def handle_starttag(self,t,a):
  if t in ('script','style'): self.skip+=1
  if t in ('p','h1','h2','h3','h4','li','section'): self.parts.append('\n')
 def handle_endtag(self,t):
  if t in ('script','style'): self.skip-=1
  if t in ('p','h1','h2','h3','h4','li'): self.parts.append('\n')
 def handle_data(self,d):
  if not self.skip: self.parts.append(d)
r=Reader(); area=Path(__file__).parent;r.feed((area/'sources/proteintalks-publisher.body.hop3').read_text(encoding='utf8')); lines=[' '.join(x.split()) for x in ''.join(r.parts).splitlines()]; (area/'proteintalks-primary-text.txt').write_text('\n'.join(x for x in lines if x),encoding='utf8')
