# Build local verbatim abstract extracts (for stable line anchors in prior_art.md).
# Each file: line 1 = provenance header; remaining lines = verbatim abstract from the source,
# only wrapped at spaces (no words added/removed).
import glob, json, os, re, textwrap

OUT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(OUT, "raw")
ABS = os.path.join(RAW, "abstracts")
os.makedirs(ABS, exist_ok=True)


def records(pattern):
    for f in glob.glob(os.path.join(RAW, pattern)):
        js = json.load(open(f, encoding="utf-8"))
        for r in js.get("resultList", {}).get("result", []):
            yield f, r


def find_ppr(pprid):
    for f, r in records("*epmc*.json"):
        if r.get("id") == pprid:
            return f, r
    return None, None


def find_doi(doi):
    for f, r in records("*epmc*.json"):
        if r.get("doi") == doi:
            return f, r
    return None, None


def write_abs(name, header, abstract):
    path = os.path.join(ABS, name + ".txt")
    body = "\n".join(textwrap.wrap(" ".join(abstract.split()), width=110))
    with open(path, "w", encoding="utf-8") as f:
        f.write("# " + header + "\n" + body + "\n")
    print(name, "->", len(body), "chars")


targets = [
    ("regulon_context_2026_ppr1330660", "PPR", "PPR1330660"),
    ("separating_main_effects_2026_ppr1290788", "PPR", "PPR1290788"),
    ("vcat_2026_doi_10.1093_bib_bbag559", "DOI", "10.1093/bib/bbag559"),
    ("drugcell_2020_doi_10.1016_j.ccell.2020.09.014", "DOI", "10.1016/j.ccell.2020.09.014"),
]
for name, kind, key in targets:
    f, r = (find_ppr(key) if kind == "PPR" else find_doi(key))
    if not r:
        print("MISSING", name, key)
        continue
    abs_txt = re.sub(r"<[^>]+>", " ", r.get("abstractText") or "")
    abs_txt = re.sub(r"\s+", " ", abs_txt).strip()
    hdr = ("item=%s | Europe PMC %s=%s | doi=%s | source=%s | local raw=%s | "
           "line 2+ = verbatim abstract (wrapped at spaces only); abstract-only evidence"
           % (name, "id" if kind == "PPR" else "query", key, r.get("doi"),
              r.get("source"), os.path.relpath(f, OUT).replace("\\", "/")))
    write_abs(name, hdr, abs_txt)

# arXiv abstracts from saved API XML
for name, aid, label in [("ood_graphllm_2026_arxiv", "2605.30247", "OOD-GraphLLM"),
                         ("syncell_2025_arxiv", "2511.17695", "SynCell")]:
    path = os.path.join(RAW, f"arxiv_{'ood_graphllm' if aid.startswith('2605.3') else 'syncell'}.xml")
    if not os.path.exists(path):
        print("MISSING", name, path)
        continue
    xml = open(path, encoding="utf-8").read()
    m = re.search(r"<summary>(.*?)</summary>", xml, re.S)
    t = re.search(r"<title>(.*?)</title>", xml, re.S)
    if not m:
        print("MISSING SUMMARY", name)
        continue
    abs_txt = " ".join(m.group(1).split())
    hdr = ("item=%s | arXiv:%s | title=%s | local raw=%s | "
           "line 2+ = verbatim arXiv abstract (wrapped at spaces only); abstract-only evidence"
           % (name, aid, " ".join(t.group(1).split()) if t else label,
              os.path.relpath(path, OUT).replace("\\", "/")))
    write_abs(name, hdr, abs_txt)
print("DONE")
