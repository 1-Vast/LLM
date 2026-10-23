"""Index author-linked supplements without opening numerical/media payloads."""
from html.parser import HTMLParser
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261023/grounded_feedback_renewal/root'


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = set()

    def handle_starttag(self, tag, attrs):
        url = dict(attrs).get('href', '')
        if tag == 'a' and '/DC' in url and '/embed/' in url:
            self.links.add(url)


parser = Links()
parser.feed((OUT/'longitudinal_supplement.body').read_text(encoding='utf-8'))
record = dict(author_linked_media=sorted(parser.links), payloads_downloaded=False,
              tracked_numeric_table_link_present=any('.csv' in u or '.xlsx' in u for u in parser.links),
              scope='Page link inventory only; not proof of absence inside unseen supplements or final article')
(OUT/'SUPPLEMENT_INDEX.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps(record, indent=2))
