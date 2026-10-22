"""Third and final registered request: primary article XML, no dataset payload."""
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/serial_antibiotic_alternatives"
ledger = json.loads((OUT / "NETWORK.json").read_text(encoding="utf-8"))
if len(ledger) != 2:
    raise RuntimeError("Third request allowed only after exactly two scout requests")
path = OUT / "TRIPARTITE.xml"
if path.exists():
    raise FileExistsError(path)
used = sum(r.get("bytes", 0) or 0 for r in ledger)
url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=12164588&retmode=xml"
receipt = {"name": path.name, "url": url}
payload = b""
try:
    with urllib.request.urlopen(url, timeout=45) as response:
        payload = response.read(1_000_001 - used)
        receipt["status"] = response.status
except urllib.error.HTTPError as exc:
    payload = exc.read(1_000_001 - used)
    receipt.update({"status": exc.code, "error": str(exc)})
except Exception as exc:
    receipt.update({"error": str(exc), "bytes": None})
if payload:
    path.write_bytes(payload)
    receipt.update({"bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()})
ledger.append(receipt)
(OUT / "NETWORK.json").write_text(json.dumps(ledger, indent=2), encoding="utf-8")
if used + len(payload) > 1_000_000:
    raise RuntimeError("Budget reached; source may be truncated, do not parse")
if receipt.get("status") != 200:
    raise RuntimeError("Request failed; do not retry")
tree = ET.fromstring(payload)
excerpts = []
for section in tree.findall(".//sec"):
    title = section.find("title")
    title_text = " ".join(title.itertext()) if title is not None else ""
    if any(term in title_text.lower() for term in ("material", "method", "data avail", "code avail", "supplement")):
        excerpts.append({"title": title_text, "text": " ".join(section.itertext())})
links = [{"type": node.tag, "attributes": node.attrib, "text": " ".join(node.itertext())} for node in tree.iter() if node.tag in ("ext-link", "supplementary-material")]
(OUT / "TRIPARTITE_METHODS.json").write_text(json.dumps({"methods": excerpts, "links": links}, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"status": receipt.get("status"), "bytes": len(payload), "total_bytes": used + len(payload), "methods": [e["title"] for e in excerpts], "links": len(links)}))
