"""Traceable per-drug literature retrieval (Europe PMC REST, no key), stored once per drug.

Query: the drug name in title or abstract together with a cytotoxicity / mechanism context, sorted
by citations, with a relevance-sorted fallback. Leakage guard: hits that report or reuse the PRISM
viability screen itself are dropped (text mentions "PRISM", "Corsello", "Repurposing Hub" or
"DepMap"), so the agent never reads the outcome data's own publications. ``literature/<slug>.json``
records the exact queries, retrieval time, kept hits (PMID, year, title, abstract trimmed to 1,000
characters) and the dropped PMIDs with reasons. Existing files are never refetched.
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "literature"
API = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
PAGE = 8
KEEP = 6
TRIM = 1000
LEAK = re.compile(r"PRISM|Corsello|Repurposing Hub|DepMap|Dependency Map", re.I)


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")[:80]


def clean(name: str) -> str:
    return re.sub(r"[\"()\[\]]", " ", name).strip()


def queries_for(drug: str) -> list[tuple[str, str]]:
    term = clean(drug)
    ctx = ('(ABSTRACT:cytotoxic* OR ABSTRACT:apoptosis OR ABSTRACT:"cancer cell" OR ABSTRACT:"cancer cells" '
           'OR ABSTRACT:"cell line" OR ABSTRACT:"cell lines" OR ABSTRACT:mechanism OR ABSTRACT:inhibit*)')
    return [(f'(TITLE:"{term}" OR ABSTRACT:"{term}") AND {ctx}', "CITED desc"),
            (f'(TITLE:"{term}" OR ABSTRACT:"{term}")', "")]


def _get(q: str, sort: str) -> dict | None:
    params = {"query": q, "format": "json", "resultType": "core", "pageSize": str(PAGE)}
    if sort:
        params["sort"] = sort
    url = API + "?" + urllib.parse.urlencode(params)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception:  # transport failure: retry, then record the failure by name
            time.sleep(2 * (attempt + 1))
    return None


def fetch(drug: str) -> dict:
    hits, seen, dropped, counts, failed = [], set(), [], [], False
    for q, sort in queries_for(drug):
        body = _get(q, sort)
        if body is None:
            failed = True
            counts.append(None)
            continue
        counts.append(body.get("hitCount"))
        for r in body.get("resultList", {}).get("result", []):
            pmid = r.get("pmid")
            if not pmid or pmid in seen:
                continue
            seen.add(pmid)
            text = f"{r.get('title', '')} {r.get('abstractText', '')}"
            if LEAK.search(text):
                dropped.append({"pmid": pmid, "reason": "mentions the PRISM screen or its resources"})
                continue
            abstract = re.sub(r"<[^>]+>", "", r.get("abstractText", "") or "")
            if not abstract:
                continue
            hits.append({"pmid": pmid, "year": r.get("pubYear"), "title": re.sub(r"<[^>]+>", "", r.get("title", "")),
                         "abstract": abstract[:TRIM], "cited": r.get("citedByCount")})
        if len(hits) >= KEEP:
            break
    return {"drug": drug, "queries": [q for q, _ in queries_for(drug)], "hit_counts": counts,
            "retrieved_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "status": "failed" if failed and not hits else "ok", "hits": hits[:KEEP], "dropped": dropped}


def run(drugs: list[str], workers: int = 4) -> dict:
    OUT.mkdir(exist_ok=True)

    def one(d: str) -> str:
        p = OUT / f"{slug(d)}.json"
        if p.exists():
            return "cached"
        rec = fetch(d)
        p.write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
        return rec["status"]
    with ThreadPoolExecutor(workers) as pool:
        st = list(pool.map(one, drugs))
    return {s: st.count(s) for s in set(st)}


if __name__ == "__main__":
    split = json.loads((HERE / "SPLIT.json").read_text(encoding="utf-8"))["units"]
    roles = sys.argv[1].split(",")
    todo = sorted(d for d, u in split.items() if u["role"] in roles)
    print(len(todo), run(todo))
