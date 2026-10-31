"""Extract source prose/links without rendering raw response tables."""
import argparse
from html.parser import HTMLParser
from pathlib import Path


class Prose(HTMLParser):
    def __init__(self):
        super().__init__()
        self.skip = 0
        self.out = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "table"):
            self.skip += 1
        if tag == "a" and not self.skip:
            self.links.extend(value for key, value in attrs if key == "href")
        if tag in ("h1", "h2", "h3", "p", "li", "br", "div"):
            self.out.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "table") and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.out.append(data)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    parsed = Prose()
    parsed.feed(args.source.read_text(encoding="utf-8"))
    lines = [" ".join(line.split()) for line in "".join(parsed.out).splitlines()]
    content = "\n".join(line for line in lines if line) + "\n\nLINKS\n" + "\n".join(parsed.links)
    args.destination.write_text(content, encoding="utf-8")
    print(content)


if __name__ == "__main__":
    main()
