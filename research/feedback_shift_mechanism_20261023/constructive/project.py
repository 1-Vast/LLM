from html.parser import HTMLParser
from pathlib import Path

class Projection(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts=[]
    def handle_data(self,text):
        self.parts.append(text)
    def handle_starttag(self,tag,attrs):
        if tag in ('p','div','h1','h2','h3','li','tr'):
            self.parts.append('\n')

p=Path('log/20261023/feedback_shift_mechanism/constructive')
parser=Projection()
parser.feed((p/'shift_primary.body').read_text(encoding='utf-8'))
lines=[' '.join(s.split()) for s in ''.join(parser.parts).splitlines() if s.strip()]
(p/'shift_primary.text.txt').write_text('\n'.join(lines),encoding='utf-8')
for i,line in enumerate(lines,1):
    if any(s in line.lower() for s in ('importance weight','truncat','conditional distribution','algorithm','density ratio','weighted empirical')):
        print(i,line[:600])
