"""Two declared public queries, no retries or response-data access."""
from urllib.parse import urlencode
from fetch_source import fetch

arxiv = '(all:"matrix completion" OR all:"tensor completion" OR all:"matrix sensing") AND (all:"active" OR all:"adaptive" OR all:"identifiability")'
fetch("q1_adaptive_support.xml", "https://export.arxiv.org/api/query?" + urlencode({"search_query": arxiv,
      "start": 0, "max_results": 20, "sortBy": "submittedDate", "sortOrder": "descending"}), query=True)
pubmed = '("drug response"[Title/Abstract] OR "drug screening"[Title/Abstract]) AND ("matrix completion"[Title/Abstract] OR "missing data"[Title/Abstract] OR "transfer learning"[Title/Abstract]) AND (2025/01/01:2026/10/29[Date - Publication])'
fetch("q2_drug_support.json", "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?" + urlencode({
      "db": "pubmed", "term": pubmed, "retmax": 30, "retmode": "json", "sort": "pub_date"}), query=True)
