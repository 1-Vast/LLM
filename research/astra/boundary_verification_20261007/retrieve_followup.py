"""Follow official proceedings links and public metadata for the method review."""
from __future__ import annotations

import concurrent.futures
import json
from pathlib import Path

from retrieve_methods import HERE, retrieve


def main():
    urls = {
        "kg_correlated_openalex.json": "https://api.openalex.org/works/https://doi.org/10.1287/ijoc.1080.0314",
        "kg_correlated_publisher.html": "https://pubsonline.informs.org/doi/10.1287/ijoc.1080.0314",
        "combinatorial_abstract.html": "https://proceedings.neurips.cc/paper_files/paper/2014/hash/d3ea0f3316d2da934d79b8b344eafee4-Abstract.html",
        "combinatorial_paper.pdf": "https://proceedings.neurips.cc/paper_files/paper/2014/file/d3ea0f3316d2da934d79b8b344eafee4-Paper.pdf",
    }
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(lambda pair: retrieve(*pair), urls.items()))
    with (HERE / "METHOD_FOLLOWUP_RECEIPTS.json").open("x", encoding="utf-8") as handle:
        json.dump(records, handle, indent=2); handle.write("\n")
    print(json.dumps(records, indent=2))


if __name__ == "__main__":
    main()
