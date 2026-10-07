"""Try qualified author-hosted copies; keep access failures explicit."""
from __future__ import annotations

import concurrent.futures
import json

from retrieve_methods import HERE, retrieve


def main():
    urls = {
        "kg_princeton.pdf": "https://www.castlelab.princeton.edu/Papers/FrazierPowell_CorrelatedKnowledgeGradient10232008.pdf",
        "kg_cornell.pdf": "https://people.orie.cornell.edu/pfrazier/Docs/CorrelatedKnowledgeGradient.pdf",
    }
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        records = list(pool.map(lambda pair: retrieve(*pair), urls.items()))
    with (HERE / "METHOD_KG_RECEIPTS.json").open("x", encoding="utf-8") as handle:
        json.dump(records, handle, indent=2); handle.write("\n")
    print(json.dumps(records, indent=2))


if __name__ == "__main__":
    main()
