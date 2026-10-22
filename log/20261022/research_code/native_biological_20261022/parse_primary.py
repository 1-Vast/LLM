from html.parser import HTMLParser
from pathlib import Path
class Paragraphs(HTMLParser):
 def __init__(self):super().__init__();self.active=False;self.current=[];self.rows=[]
 def handle_starttag(self,tag,attrs):
  if tag=='p':self.active=True;self.current=[]
 def handle_data(self,data):
  if self.active:self.current.append(data)
 def handle_endtag(self,tag):
  if tag=='p' and self.active:self.rows.append(''.join(self.current));self.active=False
out=Path('D:/MAESTRO/log/20261022/native_operation/biology')
s=Paragraphs();s.feed((out/'nature.txt').read_text(encoding='utf8'))
(out/'nature_paragraphs.txt').write_text('\n\n'.join(f'{i}: {x}' for i,x in enumerate(s.rows)),encoding='utf8')
for i,x in enumerate(s.rows):
 if any(k in x.lower() for k in ['co-culture','cd58','data availability','gse','cytotoxicity','github','96 h','48 h']):print(f'{i}: {x}\n')
