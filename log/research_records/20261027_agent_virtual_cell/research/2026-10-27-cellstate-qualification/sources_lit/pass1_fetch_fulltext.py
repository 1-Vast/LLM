# PASS 1 follow-up: fetch full texts of selected OA hits (document retrieval, not a new discovery pass).
# Europe PMC fullTextXML for OA records; saves XML + plain text under sources_lit/raw/fulltext/.
import html, json, os, re, urllib.request

OUT = os.path.dirname(os.path.abspath(__file__))
FT = os.path.join(OUT, "raw", "fulltext")
os.makedirs(FT, exist_ok=True)
UA = {"User-Agent": "MAESTRO-cellstate-lit/1.0 (research; local)"}
BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest/"


def get(url, timeout=90):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def strip_tags(xml):
    txt = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", xml, flags=re.S | re.I)
    txt = re.sub(r"</(p|sec|title|abstract|fig|caption|table|tr|ref|list-item|disp-quote)>", "\n", txt, flags=re.I)
    txt = re.sub(r"<[^>]+>", " ", txt)
    txt = html.unescape(txt)
    txt = re.sub(r"[ \t]+", " ", txt)
    txt = re.sub(r"\n\s*\n+", "\n", txt)
    return txt.strip()


targets = [
    ("deepsynergy_2018", "PMC5925774"),
    ("baptista_systematic_eval_2023", "PMC10072473"),
    ("synverse_2025", "PMC12753315"),
    ("pdtsyn_2026", "PMC13109062"),
    ("synprotx_2025", "PMC12343095"),
    ("dipx_elife_2025", "PMC12133153"),
    ("beyond_synergy_scores_2025", "PMC12152377"),
    ("forge_2026", "PMC13396380"),
    ("reliable_eval_2026", "PMC13358880"),
    ("cellline_embedding_2025", "PMC12205321"),
    ("metasynergy_2025", "PMC12710477"),
]

log = []
for name, pmcid in targets:
    try:
        xml = get(BASE + pmcid + "/fullTextXML")
        open(os.path.join(FT, name + ".xml"), "w", encoding="utf-8").write(xml)
        txt = strip_tags(xml)
        open(os.path.join(FT, name + ".txt"), "w", encoding="utf-8").write(txt)
        log.append({"name": name, "pmcid": pmcid, "xml_chars": len(xml), "txt_chars": len(txt), "ok": True})
        print(f"[{name}] OK xml={len(xml)} txt={len(txt)}")
    except Exception as e:
        log.append({"name": name, "pmcid": pmcid, "ok": False, "error": repr(e)})
        print(f"[{name}] ERROR {e!r}")

json.dump(log, open(os.path.join(OUT, "raw", "fulltext_fetch_log.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("DONE", len(targets))
