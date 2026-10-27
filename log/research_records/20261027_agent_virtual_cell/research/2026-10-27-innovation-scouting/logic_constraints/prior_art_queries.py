# R198-A2 prior-art check (single merged pass, metadata only; no full-text download).
# Writes raw responses to this directory; no responses read, no effect run.
import json, urllib.request, urllib.parse, os

OUT = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "MAESTRO-R198-A2/1.0 (metadata-only prior-art check)"}
summary = []

def get(url, timeout=40):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")

def epmc(qid, query, page=15):
    url = ("https://www.ebi.ac.uk/europepmc/webservices/rest/search?"
           + urllib.parse.urlencode({"query": query, "format": "json", "pageSize": page, "resultType": "lite"}))
    try:
        raw = get(url); js = json.loads(raw); res = js.get("resultList", {}).get("result", [])
        top = [{"title": r.get("title"), "year": r.get("pubYear"), "doi": r.get("doi"), "journal": r.get("journalTitle")} for r in res[:12]]
        open(os.path.join(OUT, f"qa_epmc_{qid}.json"), "w", encoding="utf-8").write(raw)
        summary.append({"id": qid, "db": "EuropePMC", "query": query, "hitCount": js.get("hitCount"), "top": top})
        print(f"[EPMC {qid}] hits={js.get('hitCount')}")
    except Exception as e:
        summary.append({"id": qid, "db": "EuropePMC", "query": query, "error": repr(e)}); print(f"[EPMC {qid}] ERR {e!r}")

def oa(qid, filt, label, page=12):
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode({"filter": filt, "per_page": page})
    try:
        raw = get(url); js = json.loads(raw); res = js.get("results", [])
        top = [{"title": r.get("title"), "year": r.get("publication_year"), "doi": r.get("doi")} for r in res]
        open(os.path.join(OUT, f"qa_openalex_{qid}.json"), "w", encoding="utf-8").write(raw)
        summary.append({"id": qid, "db": "OpenAlex", "query": label, "hitCount": js.get("meta", {}).get("count"), "top": top})
        print(f"[OA {qid}] hits={js.get('meta', {}).get('count')}")
    except Exception as e:
        summary.append({"id": qid, "db": "OpenAlex", "query": label, "error": repr(e)}); print(f"[OA {qid}] ERR {e!r}")

epmc("Q1_logic_knowledge_drugcombo",
     '(TITLE_ABS:"logic rule" OR TITLE_ABS:"first-order logic" OR TITLE_ABS:"logical rule" OR TITLE_ABS:"knowledge graph") AND (TITLE_ABS:"drug combination" OR TITLE_ABS:"synergy prediction" OR TITLE_ABS:"combination therapy") AND FIRST_PDATE:[2020-01-01 TO 2026-12-31]')
epmc("Q2_constraint_active_learning_drug",
     '(TITLE_ABS:"constraint" OR TITLE_ABS:"prior knowledge") AND (TITLE_ABS:"active learning" OR TITLE_ABS:"sequential experimental design") AND (TITLE_ABS:"drug" OR TITLE_ABS:"combination") AND FIRST_PDATE:[2020-01-01 TO 2026-12-31]')
oa("Q3_kg_synergy_falsify", 'title_and_abstract.search:"knowledge graph",title_and_abstract.search:"drug combination",from_publication_date:2022-01-01',
   'OpenAlex title/abstract: "knowledge graph" AND "drug combination" since 2022')
oa("Q4_rule_violation_biology", 'title_and_abstract.search:"rule violation",title_and_abstract.search:"perturbation"',
   'OpenAlex title/abstract: "rule violation" AND "perturbation"')

open(os.path.join(OUT, "qa_summary.json"), "w", encoding="utf-8").write(json.dumps(summary, ensure_ascii=False, indent=1))
print("DONE")
