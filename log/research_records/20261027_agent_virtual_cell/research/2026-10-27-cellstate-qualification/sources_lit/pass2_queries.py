# PASS 2 targeted gap-filling (single merged pass; R190-D prior-art check).
# Gaps from PASS 1: (a) within-pair / per-treatment cell ranking as an evaluation object;
# (b) the 2026 leakage-controlled cold-start benchmark; (c) OOD/LLM synergy successors;
# (d) CRISPR-dependency as cell feature for combination prediction; (e) "cell line ranking" terms.
import json, os, re, time, urllib.parse, urllib.request

OUT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(OUT, "raw")
UA = {"User-Agent": "MAESTRO-cellstate-lit/1.0 (research; local)"}


def get(url, timeout=90, tries=2):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:
            last = e
            time.sleep(2)
    raise last


summary = []


def epmc(qid, query, page=25):
    url = ("https://www.ebi.ac.uk/europepmc/webservices/rest/search?"
           + urllib.parse.urlencode({"query": query, "format": "json",
                                     "pageSize": page, "resultType": "core"}))
    try:
        raw = get(url)
        js = json.loads(raw)
        res = js.get("resultList", {}).get("result", [])
        rows = [{"title": r.get("title"), "year": r.get("pubYear"), "doi": r.get("doi"),
                 "pmcid": r.get("pmcid"), "pmid": r.get("pmid"),
                 "abstract": (r.get("abstractText") or "")[:1200]} for r in res]
        open(os.path.join(RAW, f"pass2_epmc_{qid}.json"), "w", encoding="utf-8").write(raw)
        summary.append({"id": qid, "db": "EuropePMC", "query": query,
                        "hitCount": js.get("hitCount"), "hits": rows})
        print(f"[EPMC {qid}] hits={js.get('hitCount')} kept={len(rows)}")
    except Exception as e:
        summary.append({"id": qid, "db": "EuropePMC", "query": query, "error": repr(e)})
        print(f"[EPMC {qid}] ERROR {e!r}")


def openalex(qid, search, from_date, per_page=25):
    url = ("https://api.openalex.org/works?"
           + urllib.parse.urlencode({"search": search, "per_page": per_page,
                                     "filter": f"from_publication_date:{from_date}",
                                     "mailto": "local-research@example.invalid"}))
    try:
        raw = get(url, tries=3)
        js = json.loads(raw)
        rows = [{"title": r.get("title"), "year": r.get("publication_year"),
                 "doi": r.get("doi"), "id": r.get("id")} for r in js.get("results", [])]
        open(os.path.join(RAW, f"pass2_openalex_{qid}.json"), "w", encoding="utf-8").write(raw)
        summary.append({"id": qid, "db": "OpenAlex", "query": search,
                        "hitCount": js.get("meta", {}).get("count"), "hits": rows})
        print(f"[OpenAlex {qid}] hits={js.get('meta', {}).get('count')} kept={len(rows)}")
    except Exception as e:
        summary.append({"id": qid, "db": "OpenAlex", "query": search, "error": repr(e)})
        print(f"[OpenAlex {qid}] ERROR {e!r}")


def arxiv(qid, query, max_results=20):
    url = ("http://export.arxiv.org/api/query?"
           + urllib.parse.urlencode({"search_query": query, "start": 0,
                                     "max_results": max_results,
                                     "sortBy": "submittedDate", "sortOrder": "descending"}))
    try:
        raw = get(url, tries=3)
        open(os.path.join(RAW, f"pass2_arxiv_{qid}.xml"), "w", encoding="utf-8").write(raw)
        rows = []
        for e in re.findall(r"<entry>(.*?)</entry>", raw, re.S)[:max_results]:
            t = re.search(r"<title>(.*?)</title>", e, re.S)
            d = re.search(r"<published>(.*?)</published>", e, re.S)
            i = re.search(r"<id>(.*?)</id>", e, re.S)
            rows.append({"title": " ".join(t.group(1).split()) if t else None,
                         "published": d.group(1)[:10] if d else None,
                         "id": i.group(1) if i else None})
        summary.append({"id": qid, "db": "arXiv", "query": query,
                        "hitCount": len(rows), "hits": rows})
        print(f"[arXiv {qid}] entries={len(rows)}")
    except Exception as e:
        summary.append({"id": qid, "db": "arXiv", "query": query, "error": repr(e)})
        print(f"[arXiv {qid}] ERROR {e!r}")


# --- (a) per-treatment / within-cell / cell-ranking evaluation terms ---
epmc("P2-e1_per_treatment_ranking",
     '(TITLE_ABS:"cell line ranking" OR TITLE_ABS:"rank cell lines" OR TITLE_ABS:"ranking of cell lines" OR '
     'TITLE_ABS:"cell-line prioritization" OR TITLE_ABS:"prioritize cell lines" OR TITLE_ABS:"per-drug" OR '
     'TITLE_ABS:"drug-wise" OR TITLE_ABS:"per-treatment" OR TITLE_ABS:"cell-wise" OR TITLE_ABS:"per-combination") AND '
     '(TITLE_ABS:"drug response" OR TITLE_ABS:"drug sensitivity" OR TITLE_ABS:"synergy" OR TITLE_ABS:"drug combination")')

# --- (b) 2026 cold-start benchmark, looser wording ---
epmc("P2-e2_coldstart_benchmark",
     '(TITLE_ABS:"cold-start benchmark" OR TITLE_ABS:"cold start benchmark" OR '
     '(TITLE_ABS:"cold-start" AND TITLE_ABS:"benchmark") OR TITLE_ABS:"leakage-controlled") AND '
     '(TITLE_ABS:"drug combination" OR TITLE_ABS:"drug synergy" OR TITLE_ABS:"synergy")')

# --- (c) cell representation learning for combination response (cell-state route) ---
epmc("P2-e3_cell_state_representation",
     '(TITLE_ABS:"cell state" OR TITLE_ABS:"cellular state" OR TITLE_ABS:"cell-line embedding" OR '
     'TITLE_ABS:"cell line representation" OR TITLE_ABS:"cellular representation") AND '
     '(TITLE_ABS:"drug synergy" OR TITLE_ABS:"drug combination") AND FIRST_PDATE:[2022-01-01 TO 2026-12-31]')

# --- (d) CRISPR dependency as feature for combination prediction ---
epmc("P2-e4_dependency_feature_combo",
     '(TITLE_ABS:"gene dependency" OR TITLE_ABS:"CRISPR screen" OR TITLE_ABS:"dependency map") AND '
     '(TITLE_ABS:"combination prediction" OR TITLE_ABS:"synergy prediction" OR TITLE_ABS:"drug combination prediction" OR '
     'TITLE_ABS:"predict drug synergy")')

# --- (e) unseen cell line phrasing variants ---
epmc("P2-e5_unseen_celllines_variants",
     '(TITLE_ABS:"unseen cell lines" OR TITLE_ABS:"unseen cell line" OR TITLE_ABS:"novel cell lines" OR '
     'TITLE_ABS:"new cell lines") AND (TITLE_ABS:"drug combination" OR TITLE_ABS:"synergy") AND '
     'FIRST_PDATE:[2020-01-01 TO 2026-12-31]')

openalex("P2-o1_leakage_coldstart", "leakage-controlled cold-start benchmark drug-combination synergy classification", "2024-01-01")
openalex("P2-o2_cellline_ranking", "cell line ranking drug sensitivity prediction per drug correlation", "2018-01-01")
openalex("P2-o3_within_treatment", "within-combination across-cell-line variation synergy prediction evaluation", "2019-01-01")
openalex("P2-o4_cell_state_synergy", "cell state representation drug combination synergy unseen cell lines", "2023-01-01")

arxiv("P2-a1_synergy_ranking", 'abs:"drug synergy" AND (abs:"ranking" OR abs:"rank")')
arxiv("P2-a2_ood_graphllm", 'all:"OOD-GraphLLM"')
arxiv("P2-a3_coldstart_combo", 'abs:"cold-start" AND (abs:"drug combination" OR abs:"drug synergy")')

open(os.path.join(OUT, "raw", "pass2_summary.json"), "w", encoding="utf-8").write(
    json.dumps(summary, ensure_ascii=False, indent=1))
print("DONE", len(summary), "queries")
