# Document retrieval round 2 (already-surfaced items only).
import html, json, os, re, urllib.parse, urllib.request

OUT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(OUT, "raw")
UA = {"User-Agent": "Mozilla/5.0 (compatible; MAESTRO-lit/1.0; research; local)"}


def get(url, timeout=90):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "replace")


def strip(x):
    t = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", x, flags=re.S | re.I)
    t = re.sub(r"</(p|div|h1|h2|h3|h4|li|section|figcaption|table|tr)>", "\n", t, flags=re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    t = html.unescape(t)
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n\s*\n+", "\n", t)
    return t.strip()


# DrugCell 2020 record
try:
    q = urllib.parse.urlencode({"query": 'DOI:"10.1016/j.ccell.2020.09.014"', "format": "json",
                                "pageSize": 5, "resultType": "core"})
    raw = get("https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + q)
    js = json.loads(raw)
    r = (js.get("resultList", {}).get("result") or [None])[0]
    open(os.path.join(RAW, "epmc_doi_drugcell_2020.json"), "w", encoding="utf-8").write(raw)
    print("DrugCell:", r.get("title") if r else None, "|", r.get("pmcid") if r else None)
    print((r.get("abstractText") or "")[:1800] if r else "")
except Exception as e:
    print("DrugCell ERROR", repr(e))

# Regulon preprint full text (bioRxiv-style DOI) attempt 1
try:
    page = get("https://doi.org/10.64898/2026.09.23.753774")
    open(os.path.join(RAW, "regulon_2026.html"), "w", encoding="utf-8").write(page)
    txt = strip(page)
    open(os.path.join(RAW, "fulltext", "regulon_2026.txt"), "w", encoding="utf-8").write(txt)
    print("REGULON OK", len(page), len(txt))
except Exception as e:
    print("REGULON ERROR", repr(e))
