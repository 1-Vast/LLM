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

p=Path('log/20261023/sustained_function_task/constructive')
parser=Projection()
parser.feed((p/'causal_event.body').read_text(encoding='utf-8'))
lines=[' '.join(s.split()) for s in ''.join(parser.parts).splitlines() if s.strip()]
(p/'causal_event.text.txt').write_text('\n'.join(lines),encoding='utf-8')
for i,line in enumerate(lines,1):
    if any(s in line.lower() for s in ('assumption','treatment effect','conditional intensity','intervention effect','unbiased','propensity','likelihood')):
        print(i,line[:900])
