"""Fetch only registry landing-page metadata/links; no chemical response table read."""
import json
from html.parser import HTMLParser

from acquire_metadata import LOG, get


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and "href" in attrs:
            self.links.append(attrs["href"])


def main():
    body, receipt = get("https://oasisconsortium.org/oasis-compounds", LOG / "sealed_source/registry_landing.html")
    parser = Links()
    parser.feed(body.decode("utf-8", errors="replace"))
    links = sorted(set(parser.links))
    (LOG / "REGISTRY_LINKS.json").write_text(json.dumps({"receipt": receipt, "links": links}, indent=2), encoding="utf-8")
    print(json.dumps({"landing_bytes": len(body), "links": links}))


if __name__ == "__main__":
    main()
