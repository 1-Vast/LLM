# PASS 1 retry for 4 transient SSL-EOF failures (same pass; no new query families).
import json, os, urllib.parse, urllib.request

OUT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(OUT, "raw")
UA = {"User-Agent": "MAESTRO-cellstate-lit/1.0 (research; local)"}


def get(url, timeout=90):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def epmc(qid, query, page=25):
    url = ("https://www.ebi.ac.uk/europepmc/webservices/rest/search?"
           + urllib.parse.urlencode({"query": query, "format": "json",
                                     "pageSize": page, "resultType": "core"}))
    raw = get(url)
    js = json.loads(raw)
    open(os.path.join(RAW, f"epmc_{qid}.json"), "w", encoding="utf-8").write(raw)
    print(f"[EPMC {qid}] hits={js.get('hitCount')}")
    return js


def openalex(qid, search, from_date, per_page=25):
    url = ("https://api.openalex.org/works?"
           + urllib.parse.urlencode({"search": search, "per_page": per_page,
                                     "filter": f"from_publication_date:{from_date}",
                                     "mailto": "local-research@example.invalid"}))
    raw = get(url)
    js = json.loads(raw)
    open(os.path.join(RAW, f"openalex_{qid}.json"), "w", encoding="utf-8").write(raw)
    print(f"[OpenAlex {qid}] hits={js.get('meta', {}).get('count')}")


epmc("P1-e1_cell_unseen_synergy",
     '(TITLE_ABS:"drug synergy" OR TITLE_ABS:"drug combination") AND '
     '(TITLE_ABS:"unseen cell line" OR TITLE_ABS:"unseen cell lines" OR TITLE_ABS:"leave-cell-line-out" OR '
     'TITLE_ABS:"leave one cell line out" OR TITLE_ABS:"cell line holdout" OR TITLE_ABS:"novel cell lines" OR '
     'TITLE_ABS:"cell-line-out" OR TITLE_ABS:"unseen cells")')
epmc("P1-e3_pathway_expression_features",
     '(TITLE_ABS:"pathway activity" OR TITLE_ABS:"pathway activation" OR TITLE_ABS:"transcriptomic features" OR '
     'TITLE_ABS:"gene expression features" OR TITLE_ABS:"molecular features") AND '
     '(TITLE_ABS:"drug synergy" OR TITLE_ABS:"synergy prediction" OR TITLE_ABS:"drug combination prediction") AND '
     'FIRST_PDATE:[2018-01-01 TO 2026-12-31]')
openalex("P1-o5_coldstart_combo", "cold start drug combination synergy cell line", "2023-01-01")
openalex("P1-o6_within_pair_ranking", "within-pair ranking drug combination cell lines", "2018-01-01")
print("RETRY DONE")
