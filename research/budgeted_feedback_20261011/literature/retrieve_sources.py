"""Retrieve primary paper records. Run from any directory; caches raw evidence."""
from __future__ import annotations

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

import requests

HERE = Path(__file__).resolve().parent
RAW = HERE / "raw"

PRIMARY = [
    ("user_doi_crossref", "https://api.crossref.org/works/10.1038/s42256-026-01286-w"),
    ("user_doi_nature", "https://www.nature.com/articles/s42256-026-01286-w"),
    ("cv_learning_loss", "https://openaccess.thecvf.com/content_CVPR_2019/html/Yoo_Learning_Loss_for_Active_Learning_CVPR_2019_paper.html"),
    ("cv_batchbald", "https://arxiv.org/abs/1906.08158"),
    ("cv_badge", "https://arxiv.org/abs/1906.03671"),
    ("nlp_bert_al", "https://aclanthology.org/2020.emnlp-main.638/"),
    ("nlp_wanli_arxiv", "https://arxiv.org/abs/2201.05955"),
    ("robot_knowno", "https://proceedings.mlr.press/v229/ren23a.html"),
    ("robot_openx", "https://arxiv.org/abs/2310.08864"),
    ("robot_sim2real", "https://proceedings.mlr.press/v87/chebotar18a.html"),
    ("bo_multifidelity", "https://proceedings.mlr.press/v70/kandasamy17a.html"),
    ("selected_conformal", "https://arxiv.org/abs/2304.06158"),
]

QUERIES = [
    ("wanli", "WANLI Worker and AI Collaboration for Natural Language Inference Dataset Creation"),
    ("batch_sequential", "active learning batch size diminishing returns annotation cost deep learning"),
    ("selective_conformal", "conformal inference under selection false coverage rate"),
    ("robot_transfer", "Closing the Sim-to-Real Loop Adapting Simulation Randomization with Real World Experience"),
    ("kg_cell", "knowledge graph perturbation prediction data efficient cellular response"),
]


def fetch(item: tuple[str, str]) -> dict:
    key, url = item
    rec = {"key": key, "url": url, "retrieved_utc": datetime.now(timezone.utc).isoformat()}
    try:
        response = requests.get(url, timeout=40, headers={"User-Agent": "MAESTRO-literature-review/1.0"})
        suffix = ".json" if "json" in response.headers.get("content-type", "") else ".html"
        path = RAW / (key + suffix)
        path.write_bytes(response.content)
        rec.update(status=response.status_code, resolved_url=response.url,
                   content_type=response.headers.get("content-type"), path=str(path.relative_to(HERE)),
                   bytes=len(response.content), sha256=hashlib.sha256(response.content).hexdigest())
        if response.ok and suffix == ".json":
            payload = response.json().get("message", {})
            if "items" in payload:
                rec["candidates"] = [{"title": x.get("title"), "doi": x.get("DOI"), "url": x.get("URL")} for x in payload["items"]]
            else:
                rec["title"] = payload.get("title")
    except requests.RequestException as exc:
        rec.update(status="FAILED", error=str(exc))
    return rec


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    work = PRIMARY + [("query_" + key, "https://api.crossref.org/works?" + urlencode({"query.bibliographic": query, "rows": 4})) for key, query in QUERIES]
    with ThreadPoolExecutor(max_workers=6) as pool:
        records = list(pool.map(fetch, work))
    (HERE / "retrieval_log.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    for rec in records:
        print(json.dumps({k: v for k, v in rec.items() if k in {"key", "status", "title", "candidates", "error"}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
