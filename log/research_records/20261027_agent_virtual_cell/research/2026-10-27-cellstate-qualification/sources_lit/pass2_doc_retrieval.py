# Document retrieval for items already surfaced in PASS 1/PASS 2 (not a new discovery pass).
# Targets: (1) BMC Bioinformatics 2026 leakage-controlled cold-start benchmark; (2) Research Square
# Tahoe-100M LOCO basal-expression preprint; (3) arXiv abstracts by known id; (4) EPMC records by DOI.
import html, json, os, re, time, urllib.parse, urllib.request

OUT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(OUT, "raw")
UA = {"User-Agent": "Mozilla/5.0 (compatible; MAESTRO-lit/1.0; research; local)",
      "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}


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


def strip_tags(xml):
    txt = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", xml, flags=re.S | re.I)
    txt = re.sub(r"</(p|sec|title|abstract|fig|caption|table|tr|ref|list-item|h1|h2|h3|li|div)>", "\n", txt, flags=re.I)
    txt = re.sub(r"<[^>]+>", " ", txt)
    txt = html.unescape(txt)
    txt = re.sub(r"[ \t]+", " ", txt)
    txt = re.sub(r"\n\s*\n+", "\n", txt)
    return txt.strip()


log = []

# (1) BMC Bioinformatics 2026 cold-start benchmark (open access)
try:
    page = get("https://link.springer.com/article/10.1186/s12859-026-06665-z")
    open(os.path.join(RAW, "bmc_coldstart_2026.html"), "w", encoding="utf-8").write(page)
    txt = strip_tags(page)
    open(os.path.join(RAW, "fulltext", "bmc_coldstart_2026.txt"), "w", encoding="utf-8").write(txt)
    log.append({"item": "bmc_coldstart_2026", "ok": True, "chars": len(txt)})
    print("BMC cold-start OK", len(page), len(txt))
except Exception as e:
    log.append({"item": "bmc_coldstart_2026", "ok": False, "error": repr(e)})
    print("BMC cold-start ERROR", repr(e))

# (2) Research Square preprint: basal expression LOCO Tahoe-100M
for name, doi in [("tahoe_loco_basal_2026", "10.21203/rs.3.rs-10846736/v1")]:
    try:
        page = get("https://doi.org/" + doi)
        open(os.path.join(RAW, f"{name}.html"), "w", encoding="utf-8").write(page)
        txt = strip_tags(page)
        open(os.path.join(RAW, "fulltext", f"{name}.txt"), "w", encoding="utf-8").write(txt)
        log.append({"item": name, "ok": True, "chars": len(txt)})
        print(name, "OK", len(page), len(txt))
    except Exception as e:
        log.append({"item": name, "ok": False, "error": repr(e)})
        print(name, "ERROR", repr(e))

# (3) arXiv abstracts by known id
for name, aid in [("ood_graphllm", "2605.30247"), ("drugblind_ceiling", "2605.20885"),
                  ("syncell", "2511.17695"), ("causaldds", "2511.02146")]:
    try:
        raw = get("http://export.arxiv.org/api/query?" + urllib.parse.urlencode({"id_list": aid}))
        open(os.path.join(RAW, f"arxiv_{name}.xml"), "w", encoding="utf-8").write(raw)
        s = re.search(r"<summary>(.*?)</summary>", raw, re.S)
        t = re.search(r"<title>(.*?)</title>", raw, re.S)
        log.append({"item": name, "ok": True, "title": " ".join(t.group(1).split()) if t else None,
                    "summary": " ".join(s.group(1).split()) if s else None})
        print(name, "OK")
    except Exception as e:
        log.append({"item": name, "ok": False, "error": repr(e)})
        print(name, "ERROR", repr(e))

# (4) EPMC records by DOI (metadata for already-surfaced items)
for name, doi in [("drug_ranking_2021", "10.1038/s41467-021-22170-8"),
                  ("reliable_prioritization_2024", "10.1038/s41598-024-62956-6"),
                  ("general_principles_2025", "10.1038/s41467-025-56827-5"),
                  ("synergyx_2024", "10.1093/bib/bbae015")]:
    try:
        raw = get("https://www.ebi.ac.uk/europepmc/webservices/rest/search?"
                  + urllib.parse.urlencode({"query": f'DOI:"{doi}"', "format": "json",
                                            "pageSize": 5, "resultType": "core"}))
        js = json.loads(raw)
        r = (js.get("resultList", {}).get("result") or [None])[0]
        open(os.path.join(RAW, f"epmc_doi_{name}.json"), "w", encoding="utf-8").write(raw)
        log.append({"item": name, "ok": bool(r), "doi": doi,
                    "title": r.get("title") if r else None,
                    "pmcid": r.get("pmcid") if r else None,
                    "abstract": (r.get("abstractText") or "")[:2500] if r else None})
        print(name, "OK" if r else "NO RECORD")
    except Exception as e:
        log.append({"item": name, "ok": False, "error": repr(e)})
        print(name, "ERROR", repr(e))

json.dump(log, open(os.path.join(RAW, "doc_retrieval_log.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("DONE")
