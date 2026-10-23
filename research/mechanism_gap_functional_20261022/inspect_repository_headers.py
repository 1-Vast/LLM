"""Exact accession metadata only; do not download listed data files."""
import json

from search_sources import BASE, request


if __name__ == "__main__":
    receipts = []
    for article in (22798952, 22802888, 22806494):
        path = BASE / f"figshare_{article}.metadata.json"
        receipt = request(f"https://api.figshare.com/v2/articles/{article}", path)
        receipts.append(receipt)
        if receipt.get("status") == 200:
            data = json.loads(path.read_bytes())
            exposed = {key: data.get(key) for key in
                       ("id", "title", "doi", "url", "published_date", "references")}
            exposed["files"] = [
                {key: item.get(key) for key in ("id", "name", "size", "computed_md5")}
                for item in data.get("files", [])]
            (BASE / f"figshare_{article}.headers.json").write_text(
                json.dumps(exposed, indent=2) + "\n", encoding="utf-8")
            print(json.dumps(exposed, indent=2))
    (BASE / "REPOSITORY_METADATA_RECEIPTS.json").write_text(
        json.dumps(receipts, indent=2) + "\n", encoding="utf-8")
