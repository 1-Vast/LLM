"""Traceable literature retrieval for mechanism classes (Europe PMC REST, no key).

For each mechanism class in SPLIT.json the retriever stores the exact query, the retrieval time and
the top hits (PMID, year, title, abstract trimmed to 1,200 characters), sorted by citation count so
that established findings come first. Writes ``literature/<slug>.json`` once per class; an
existing file is never refetched, so a rerun reuses the recorded evidence instead of a newer index.

The abstracts are references, not evidence that a mechanism acts in any L1000 line.
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "literature"
API = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
PAGE = 5
TRIM = 1200


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")[:80]


def queries_for(moa: str) -> list[tuple[str, str]]:
    """Title-anchored query sorted by citations first, then an abstract-anchored fallback by relevance."""
    term = moa.replace('"', "")
    ctx = ('(ABSTRACT:transcriptional OR ABSTRACT:"gene expression" OR ABSTRACT:transcriptome '
           'OR ABSTRACT:"cell cycle" OR ABSTRACT:apoptosis)')
    return [(f'TITLE:"{term}" AND {ctx}', "CITED desc"), (f'ABSTRACT:"{term}" AND {ctx} AND ABSTRACT:cells', "")]


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


def fetch(moa: str) -> dict:
    qs = queries_for(moa)
    hits, seen, counts, failed = [], set(), [], False
    for q, sort in qs:
        body = _get(q, sort)
        if body is None:
            failed = True
            counts.append(None)
            continue
        counts.append(body.get("hitCount"))
        for r in body.get("resultList", {}).get("result", []):
            if not r.get("pmid") or r["pmid"] in seen or len(hits) >= PAGE:
                continue
            seen.add(r["pmid"])
            hits.append({"pmid": r["pmid"], "year": r.get("pubYear"), "title": r.get("title", ""),
                         "cited_by": r.get("citedByCount"), "abstract": (r.get("abstractText") or "")[:TRIM]})
        if len(hits) >= PAGE:
            break
    status = "OK" if hits else ("RETRIEVAL_FAILED" if failed else "NO_HITS")
    return {"moa": moa, "queries": [q for q, _ in qs], "retrieved_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "hit_counts": counts, "status": status, "hits": hits}


def _one(moa: str) -> int:
    path = OUT / f"{slug(moa)}.json"
    if path.exists():
        return 0
    rec = fetch(moa)
    tmp = path.with_suffix(".part")
    tmp.write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)
    return 1


def main(classes: list[str], workers: int = 6) -> None:
    from concurrent.futures import ThreadPoolExecutor
    OUT.mkdir(exist_ok=True)
    with ThreadPoolExecutor(workers) as pool:
        done = sum(pool.map(_one, classes))
    print("fetched", done, "of", len(classes))


if __name__ == "__main__":
    split = json.loads((HERE / "SPLIT.json").read_text(encoding="utf-8"))
    classes = sorted({v["moa"] for v in split["drugs"].values()})
    main(classes if len(sys.argv) < 2 else classes[: int(sys.argv[1])])
