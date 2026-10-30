from html.parser import HTMLParser
from pathlib import Path
class Parser(HTMLParser):
 def __init__(self):super().__init__();self.parts=[];self.skip=0;self.links=[]
 def handle_starttag(self,tag,attrs):
  if tag in ('script','style'):self.skip+=1
  if tag in ('p','div','section','h1','h2','h3','li','tr'):self.parts.append('\n')
  if tag=='a':
   for k,v in attrs:
    if k=='href':self.links.append(v)
 def handle_endtag(self,tag):
  if tag in ('script','style'):self.skip-=1
  if tag in ('p','div','section','h1','h2','h3','li','tr'):self.parts.append('\n')
 def handle_data(self,data):
  if not self.skip:self.parts.append(data)
p=Path(__file__).parent;s=Parser();s.feed((p/'request01-pmc.body').read_text(encoding='utf-8'))
lines=[' '.join(x.split()) for x in ''.join(s.parts).splitlines() if x.strip()]
(p/'pmc-primary-text.txt').write_text('\n'.join(lines),encoding='utf-8')
print('\n'.join(f'{i+1}: {x}' for i,x in enumerate(lines[:100])))
print('LINKS')
for x in s.links:
 if any(z in x.lower() for z in ['supp','41563','figshare','zenodo','xlsx','pdf']):print(x)
