from pathlib import Path
from html.parser import HTMLParser

base = Path('log/20261022/post_almanac_mechanism/frontier/sources')
text = (base / 'biology_loop.readable.txt').read_text(encoding='utf8')
for key in ['4.2 Dataset and benchmark construction', '4.5 Training procedure', 'RL context-delta reward.', 'Data availability', 'Code availability']:
    start = text.rfind(key)
    print('\n', key, '\n', text[start:start + 5500] if start >= 0 else 'Not located')

class Links(HTMLParser):
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            href = dict(attrs).get('href', '')
            if any(site in href for site in ['github', 'huggingface', 'zenodo']):
                print(href)

Links().feed((base / 'biology_loop.txt').read_text(encoding='utf8'))
