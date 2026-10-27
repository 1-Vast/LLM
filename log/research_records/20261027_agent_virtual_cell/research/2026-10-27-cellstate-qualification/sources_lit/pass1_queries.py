# PASS 1 discovery (single merged pass; R190-D prior-art check).
# Read-only network: Europe PMC REST, OpenAlex API, arXiv API. Raw responses saved under sources_lit/raw/.
# Purpose: cell-state/omics features for drug-combination synergy models; cell-unseen evaluation;
#          within-pair cell ranking; cold-start + cell features; target/pathway expression & CRISPR dependency.
import json, os, re, urllib.parse, urllib.request

OUT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(OUT, "raw")
os.makedirs(RAW, exist_ok=True)
UA = {"User-Agent": "MAESTRO-cellstate-lit/1.0 (research; local)"}


def get(url, timeout=60):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


summary = []


def save(name, text):
    with open(os.path.join(RAW, name), "w", encoding="utf-8") as f:
        f.write(text)


def epmc(qid, query, page=25):
    url = ("https://www.ebi.ac.uk/europepmc/webservices/rest/search?"
           + urllib.parse.urlencode({"query": query, "format": "json",
                                     "pageSize": page, "resultType": "core"}))
    try:
        raw = get(url)
        js = json.loads(raw)
        res = js.get("resultList", {}).get("result", [])
        rows = []
        for r in res:
            rows.append({
                "title": r.get("title"),
                "year": r.get("pubYear"),
                "journal": r.get("journalTitle") or (r.get("bookOrReportDetails") or {}).get("publisher"),
                "doi": r.get("doi"),
                "pmid": r.get("pmid"),
                "pmcid": r.get("pmcid"),
                "abstract": (r.get("abstractText") or "")[:1200],
            })
        save(f"epmc_{qid}.json", raw)
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
        raw = get(url)
        js = json.loads(raw)
        rows = []
        for r in js.get("results", []):
            rows.append({
                "title": r.get("title"),
                "year": r.get("publication_year"),
                "doi": r.get("doi"),
                "id": r.get("id"),
                "cited_by": r.get("cited_by_count"),
            })
        save(f"openalex_{qid}.json", raw)
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
        raw = get(url)
        save(f"arxiv_{qid}.xml", raw)
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


# ---- merged discovery queries, PASS 1 ----
epmc("P1-e1_cell_unseen_synergy",
     '(TITLE_ABS:"drug synergy" OR TITLE_ABS:"drug combination") AND '
     '(TITLE_ABS:"unseen cell line" OR TITLE_ABS:"unseen cell lines" OR TITLE_ABS:"leave-cell-line-out" OR '
     'TITLE_ABS:"leave one cell line out" OR TITLE_ABS:"cell line holdout" OR TITLE_ABS:"novel cell lines" OR '
     'TITLE_ABS:"cell-line-out" OR TITLE_ABS:"unseen cells")')

epmc("P1-e2_synergy_cell_ranking",
     '(TITLE_ABS:"drug synergy" OR TITLE_ABS:"drug combination") AND '
     '(TITLE_ABS:"ranking" OR TITLE_ABS:"rank ordering" OR TITLE_ABS:"to rank") AND '
     '(TITLE_ABS:"cell line" OR TITLE_ABS:"cell lines" OR TITLE_ABS:"cellular context") AND '
     'FIRST_PDATE:[2019-01-01 TO 2026-12-31]')

epmc("P1-e3_pathway_expression_features",
     '(TITLE_ABS:"pathway activity" OR TITLE_ABS:"pathway activation" OR TITLE_ABS:"transcriptomic features" OR '
     'TITLE_ABS:"gene expression features" OR TITLE_ABS:"molecular features") AND '
     '(TITLE_ABS:"drug synergy" OR TITLE_ABS:"synergy prediction" OR TITLE_ABS:"drug combination prediction") AND '
     'FIRST_PDATE:[2018-01-01 TO 2026-12-31]')

epmc("P1-e4_crispr_dependency_synergy",
     '(TITLE_ABS:"CRISPR" OR TITLE_ABS:"gene dependency" OR TITLE_ABS:"genetic dependency" OR TITLE_ABS:"dependency map") AND '
     '(TITLE_ABS:"drug synergy" OR TITLE_ABS:"drug combination" OR TITLE_ABS:"drug sensitivity" OR TITLE_ABS:"drug response") AND '
     'FIRST_PDATE:[2019-01-01 TO 2026-12-31]')

epmc("P1-e5_coldstart_synergy",
     '(TITLE_ABS:"cold-start" OR TITLE_ABS:"cold start" OR TITLE_ABS:"zero-shot" OR TITLE_ABS:"out-of-distribution") AND '
     '(TITLE_ABS:"synergy" OR TITLE_ABS:"drug combination") AND FIRST_PDATE:[2023-01-01 TO 2026-12-31]')

epmc("P1-e6_onehot_synergy",
     '(TITLE_ABS:"one-hot" OR TITLE_ABS:"one hot") AND '
     '(TITLE_ABS:"synergy" OR TITLE_ABS:"drug combination" OR TITLE_ABS:"drug response")')

epmc("P1-e7_within_pair_terms",
     '(TITLE_ABS:"within-pair" OR TITLE_ABS:"within pair" OR TITLE_ABS:"per-drug-pair" OR '
     'TITLE_ABS:"pair-specific ranking" OR TITLE_ABS:"cell ranking" OR TITLE_ABS:"rank cell lines")')

epmc("P1-e8_synergy_selectivity",
     '(TITLE_ABS:"combination selectivity" OR TITLE_ABS:"synergy selectivity" OR TITLE_ABS:"cell-line-specific" OR '
     'TITLE_ABS:"cell line specific" OR TITLE_ABS:"selective synergy") AND '
     '(TITLE_ABS:"synergy" OR TITLE_ABS:"combination")')

epmc("P1-e9_known_pathway_activation",
     'TITLE:"Pathway activation model for personalized prediction of drug synergy"')

epmc("P1-e10_known_coldstart_benchmark",
     'TITLE:"leakage-controlled cold-start benchmark"')

openalex("P1-o1_unseen_cells_expression", "drug synergy prediction unseen cell lines gene expression", "2021-01-01")
openalex("P1-o2_rank_cells_synergy", "ranking cell lines drug combination synergy prediction", "2019-01-01")
openalex("P1-o3_pathway_personalized_synergy", "pathway activity personalized drug synergy prediction", "2022-01-01")
openalex("P1-o4_crispr_dependency_combination", "CRISPR dependency drug combination response prediction", "2019-01-01")
openalex("P1-o5_coldstart_combo", "cold start drug combination synergy cell line", "2023-01-01")
openalex("P1-o6_within_pair_ranking", "within-pair ranking drug combination cell lines", "2018-01-01")

arxiv("P1-a1_synergy_cell", 'abs:"drug synergy" AND (abs:"cell line" OR abs:"cell lines")')
arxiv("P1-a2_synergy_unseen", '(abs:"drug combination" OR abs:"synergy") AND (abs:"unseen" OR abs:"cold-start" OR abs:"cold start")')

save("pass1_summary.json", json.dumps(summary, ensure_ascii=False, indent=1))
print("DONE", len(summary), "queries")
