import re
from pathlib import Path
for name in ['action_search','dynamics_search']:
    body=Path('log/20261023/action_rule_search/frontier',name+'.html').read_text(encoding='utf-8')
    print(name)
    blocks=re.split(r'<li class="arxiv-result">',body)[1:]
    for b in blocks[:25]:
        title=re.search(r'<p class="title[^>]*>(.*?)</p>',b,re.S)
        ident=re.search(r'https://arxiv.org/abs/([\d.]+)',b)
        print(ident.group(1) if ident else '?',re.sub('<[^>]+>',' ',title.group(1)).strip() if title else '?')
