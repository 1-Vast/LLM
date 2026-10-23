"""Reuse authenticated primary HTTP bodies; no biological or network access."""
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OLD = ROOT / "log/20261022/rsi_later_task_literature"
OUT = ROOT / "log/20261022/early_update_mechanism/recursive"


class Paragraphs(HTMLParser):
    def __init__(self):
        super().__init__()
        self.current = None
        self.paragraphs = []

    def handle_starttag(self, tag, attrs):
        if tag == "p":
            self.current = {"id": dict(attrs).get("id"), "parts": []}

    def handle_data(self, data):
        if self.current is not None:
            self.current["parts"].append(data)

    def handle_endtag(self, tag):
        if tag == "p" and self.current is not None:
            self.paragraphs.append({"id": self.current["id"], "text": " ".join(" ".join(self.current["parts"]).split())})
            self.current = None


def main():
    sources = []
    configurations = [
        ("gradient_history", OLD / "skeptic/skeptic_learned_optimizer.body",
         OLD / "skeptic/skeptic_learned_optimizer.receipt.json",
         ("The learned optimizer recombines", "The optimizer is trained to minimize", "Paired comparisons share", "Adam", "single trained policy")),
        ("specrsi", OLD / "skeptic/skeptic_specrsi.body",
         OLD / "skeptic/skeptic_specrsi.receipt.json",
         ("released artifact", "released-artifact", "continuation law", "same starting", "same artifact", "training costs")),
        ("seal", OLD / "advocate/seal_v2.body", None,
         ("Unlike prior approaches", "outer loop iteration", "adaptation strategy", "optimization hyperparameters")),
    ]
    old_receipts = json.loads((OLD / "advocate/SOURCE_RECEIPTS.json").read_text())
    for name, path, receipt_path, needles in configurations:
        body = path.read_bytes()
        receipt = json.loads(receipt_path.read_text()) if receipt_path else next(r for r in old_receipts["primary_works"] if r["name"] == "seal_v2")
        digest = hashlib.sha256(body).hexdigest()
        assert digest == receipt["sha256"] and receipt["status"] == 200
        parser = Paragraphs()
        parser.feed(body.decode("utf-8"))
        quotes = [paragraph for paragraph in parser.paragraphs if any(needle.casefold() in paragraph["text"].casefold() for needle in needles)]
        sources.append({"name": name, "source_path": str(path.relative_to(ROOT)),
                        "sha256": digest, "original_HTTP_receipt": receipt,
                        "this_phase_HTTP_requests": 0, "exact_primary_paragraphs": quotes})
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / "PRIMARY_EVIDENCE.json"
    assert not target.exists()
    target.write_text(json.dumps({"scope": "Three retained primary full-text HTML bodies; original actual HTTP preserved, no repeated download or new biological values", "sources": sources}, indent=2) + "\n", encoding="utf-8")
    for source in sources:
        print(json.dumps({"source": source["name"], "url": source["original_HTTP_receipt"]["url"], "sha256": source["sha256"], "quotes": source["exact_primary_paragraphs"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
