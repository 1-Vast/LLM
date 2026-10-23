from html.parser import HTMLParser
from pathlib import Path

class Reader(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts=[]
    def handle_data(self,data):
        self.parts.append(data)
base=Path('log/20261022/update_rule_renewal/frontier/sources')
for name in ['deltattt','doubletake']:
    p=Reader(); p.feed((base/(name+'.body')).read_text(encoding='utf8'))
    t=' '.join(' '.join(p.parts).split())
    (base/(name+'.txt')).write_text(t,encoding='utf8')
    print('\nSOURCE',name,'\n',t[2000:27000])
