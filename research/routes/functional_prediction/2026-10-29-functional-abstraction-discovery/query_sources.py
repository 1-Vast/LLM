"""Two bounded, declared questions; no retries or functional response data."""
from urllib.parse import urlencode
from fetch_source import fetch

donor = '(all:"active perception" OR all:"adaptive sensing" OR all:"active representation" OR all:"task-driven abstraction") AND (all:"multimodal" OR all:"latent" OR all:"world model")'
fetch("q1_active_representation.xml", "https://export.arxiv.org/api/query?" + urlencode({
    "search_query": donor, "start": 0, "max_results": 20,
    "sortBy": "submittedDate", "sortOrder": "descending"}), query=True)
domain = '("drug response"[Title/Abstract] OR "drug screening"[Title/Abstract]) AND ("active learning"[Title/Abstract] OR "representation learning"[Title/Abstract] OR "dose-response"[Title/Abstract]) AND (2025/01/01:2026/10/29[Date - Publication])'
fetch("q2_functional_learning.json", "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?" + urlencode({
    "db": "pubmed", "term": domain, "retmax": 30,
    "retmode": "json", "sort": "pub_date"}), query=True)
