"""Bounded primary arXiv discovery; preserves query responses and receipts."""
from urllib.parse import urlencode
from acquire_primary import fetch

QUERIES = [
    ('search2026_cv_ttt', 'submittedDate:[202601010000 TO 202610222359] AND cat:cs.CV AND (all:"test-time" OR all:"world model")'),
    ('search2026_nlp_update', 'submittedDate:[202601010000 TO 202610222359] AND cat:cs.CL AND (all:"self-improvement" OR all:"learned optimizer")'),
]

if __name__ == '__main__':
    for label, query in QUERIES:
        fetch(label, 'https://export.arxiv.org/api/query?' + urlencode({
            'search_query': query, 'start': 0, 'max_results': 8,
            'sortBy': 'submittedDate', 'sortOrder': 'descending'}))
