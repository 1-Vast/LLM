# PASS 1 final retry (2nd retry) for the two OpenAlex queries that failed twice with transient
# SSL EOF; saved for reproducibility. Same query text as pass1_queries.py, O5/O6.
import json, os, time, urllib.parse, urllib.request

OUT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(OUT, "raw")
UA = {"User-Agent": "MAESTRO-cellstate-lit/1.0 (research; local)"}

for qid, search, fd in [
    ("P1-o5_coldstart_combo", "cold start drug combination synergy cell line", "2023-01-01"),
    ("P1-o6_within_pair_ranking", "within-pair ranking drug combination cell lines", "2018-01-01"),
]:
    url = ("https://api.openalex.org/works?"
           + urllib.parse.urlencode({"search": search, "per_page": 25,
                                     "filter": "from_publication_date:" + fd,
                                     "mailto": "local-research@example.invalid"}))
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=90) as r:
                raw = r.read().decode("utf-8", "replace")
            js = json.loads(raw)
            open(os.path.join(RAW, "openalex_%s.json" % qid), "w", encoding="utf-8").write(raw)
            print(qid, "hits=", js.get("meta", {}).get("count"))
            break
        except Exception as e:
            print(qid, "attempt", attempt, "ERROR", repr(e))
            time.sleep(3)
