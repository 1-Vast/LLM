from pathlib import Path
from html.parser import HTMLParser
import re
class Text(HTMLParser):
 def __init__(self):super().__init__();self.parts=[]
 def handle_data(self,data):self.parts.append(data)
out=Path('log/20261022/post_almanac_mechanism/skeptic/primary')
for name in ('dgm_2025','sica_2025','gradient_history_2026'):
 h=Text();h.feed((out/(name+'.body')).read_text(encoding='utf-8'));text=re.sub(r'\s+',' ',' '.join(h.parts))
 (out/(name+'.txt')).write_text(text,encoding='utf-8')
 print('\nSOURCE',name,text[:1400])
 for term in ('self-improv','archive','cost','budget','gradient history','optimizer','evaluation'):
  start=0
  for i in range(2):
   j=text.lower().find(term,start)
   if j<0:break
   print(term,text[max(0,j-160):j+550]);start=j+len(term)
