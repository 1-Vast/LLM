"""Fetch primary bibliographic sources; references never become endpoint truth."""
from __future__ import annotations

import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE / "raw"
RAW.mkdir(parents=True, exist_ok=True)

QUERIES = [
    ("biodiscoveryagent", "BioDiscoveryAgent Designing Genetic Perturbation Experiments"),
    ("llm_design_gupta", "Gupta large language models experimental design agents feedback"),
    ("virtual_cell_baselines", "gene perturbation prediction simple baselines deep learning"),
    ("state", "State predicting cellular responses perturbation across diverse contexts"),
    ("perteval", "PertEval scFM perturbation benchmark"),
    ("feedback_conformal", "Conformal prediction under feedback covariate shift for biomolecular design"),
    ("risk_control", "Conformal Risk Control Angelopoulos Bates Fisch Lei Schuster"),
    ("learn_then_test", "Learn then Test Calibrating Predictive Algorithms to Achieve Risk Control"),
    ("evsi", "Estimating expected value sample information regression Strong Oakley Brennan Breeze"),
    ("knowledge_gradient", "knowledge gradient policy correlated normal beliefs Frazier Powell Dayanik"),
    ("decision_focused", "Smart Predict then Optimize Elmachtoub Grigas"),
    ("perturb_multimodal", "Perturb Multimodal imaging single cell sequencing"),
    ("almanac", "NCI ALMANAC comprehensive screening resource detect anticancer drug pairs enhanced therapeutic activity"),
]

PRIMARY = [
    ("baseline_doi", "https://api.crossref.org/works/10.1038/s41592-025-02772-6"),
    ("lpm_doi", "https://api.crossref.org/works/10.1038/s43588-025-00870-1"),
    ("state_doi_search", "https://api.crossref.org/works?query.bibliographic=State%20S0092-8674%2826%2900921-9&rows=3"),
    ("biodiscovery_primary", "https://proceedings.iclr.cc/paper_files/paper/2025/hash/4252dc94531833029000f85dc5fac792-Abstract-Conference.html"),
    ("perteval_primary", "https://proceedings.mlr.press/v267/wenteler25a.html"),
    ("arxiv_virtual_cell_benchmark", "https://arxiv.org/abs/2604.27646"),
    ("arxiv_robotic_uncertainty", "https://arxiv.org/abs/2504.16680"),
    ("arxiv_openworld_robotics", "https://arxiv.org/abs/2607.06501"),
    ("perturb_multimodal_pmc", "https://pmc.ncbi.nlm.nih.gov/articles/PMC12324982/"),
    ("tdc_drugcombo", "https://tdcommons.ai/multi_pred_tasks/drugcombo/"),
]


def fetch(item: tuple[str, str]) -> dict:
    key, url = item
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    req = urllib.request.Request(url, headers={"User-Agent": "MAESTRO-scientific-review/1.0 (bibliographic verification)", "Accept": "application/json,text/html,*/*"})
    try:
        with urllib.request.urlopen(req, timeout=40) as resp:
            body = resp.read(8_000_000)
            status = resp.status
            content_type = resp.headers.get("Content-Type", "")
            final_url = resp.url
        suffix = ".json" if "json" in content_type else ".html"
        path = RAW / (key + suffix)
        path.write_bytes(body)
        rec = {"key": key, "url": url, "resolved_url": final_url, "retrieved_utc": stamp,
               "status": status, "content_type": content_type, "bytes": len(body),
               "sha256": hashlib.sha256(body).hexdigest(), "path": str(path.relative_to(HERE))}
        if key.startswith("crossref_"):
            payload = json.loads(body)
            rec["candidates"] = [{"title": x.get("title", [""])[0], "doi": x.get("DOI"),
                                  "year": (x.get("published", {}).get("date-parts") or [[None]])[0][0]}
                                 for x in payload["message"].get("items", [])]
        elif key.startswith("epmc_"):
            payload = json.loads(body)
            rec["hit_count"] = payload.get("hitCount")
            rec["candidates"] = [{"title": x.get("title"), "doi": x.get("doi"), "pmid": x.get("pmid"),
                                  "pmcid": x.get("pmcid"), "year": x.get("pubYear")}
                                 for x in payload.get("resultList", {}).get("result", [])]
        elif "html" in content_type:
            match = re.search(r"<title[^>]*>(.*?)</title>", body.decode("utf-8", errors="replace"), flags=re.S | re.I)
            rec["page_title"] = re.sub(r"\s+", " ", match.group(1)).strip() if match else None
        else:
            payload = json.loads(body)
            if isinstance(payload.get("message"), dict) and payload["message"].get("title"):
                rec["title"] = payload["message"]["title"][0]
                rec["doi"] = payload["message"].get("DOI")
        return rec
    except Exception as exc:
        return {"key": key, "url": url, "retrieved_utc": stamp, "status": "FAILED", "error": str(exc)}


def run() -> None:
    work = list(PRIMARY)
    for key, query in QUERIES:
        work.append(("crossref_" + key, "https://api.crossref.org/works?" + urllib.parse.urlencode({"query.bibliographic": query, "rows": 4})))
    for key, query in [
        ("adaptive_biology", '(TITLE:"active learning" OR TITLE:"experimental design") AND (ABSTRACT:"cell lines" OR ABSTRACT:"perturbation")'),
        ("perturb_multimodal", '"Perturb-Multimodal"'),
        ("biodiscoveryagent", '"BioDiscoveryAgent"'),
    ]:
        work.append(("epmc_" + key, "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urllib.parse.urlencode({"query": query, "format": "json", "resultType": "core", "pageSize": 8})))
    with ThreadPoolExecutor(max_workers=6) as pool:
        records = list(pool.map(fetch, work))
    (HERE / "retrieval_log.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    for record in records:
        visible = {k: record[k] for k in ("key", "status", "title", "doi", "page_title", "candidates", "error") if k in record}
        print(json.dumps(visible, ensure_ascii=False))


if __name__ == "__main__":
    run()
