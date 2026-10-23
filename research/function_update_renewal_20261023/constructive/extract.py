from html.parser import HTMLParser
from pathlib import Path
class Text(HTMLParser):
 def __init__(self):
  super().__init__(); self.parts=[]
 def handle_data(self,data): self.parts.append(data)
p=Path('log/20261023/function_update_renewal/constructive')
for key in ['patchworld','skillgrad','ambimod','primed']:
 parser=Text(); parser.feed((p/f'{key}.body').read_text(encoding='utf8'))
 text=' '.join(' '.join(parser.parts).split())
 (p/f'{key}.text.txt').write_text(text,encoding='utf8')
 print(key,text[:18000], '\n')
