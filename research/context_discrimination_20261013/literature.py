"""Retrieve source abstracts and bibliographic records; retain failures as failures."""
import concurrent.futures
import json
from pathlib import Path
import requests

HERE = Path(__file__).resolve().parent
QUERIES = {
    "PRESAGE": "PRESAGE perturbation prediction",
    "MAP": "10.1038/s42256-026-01286-w",
    "TxPert": "TxPert",
    "GeneAgent": "GeneAgent",
    "BioDiscoveryAgent": "BioDiscoveryAgent",
    "BATCHIE": "BATCHIE",
    "CellOT": "Learning single-cell perturbation responses using neural optimal transport",
    "JUMP": "JUMP Cell Painting",
    "Systema": "Systema systematic variation perturbation",
    "Active perception": "Active Perception Bajcsy",
    "Model mismatch": "Safe Model-Based Reinforcement Learning with Stability Guarantees",
    "Label shift": "Detecting and Correcting for Label Shift with Black Box Predictors",
    "Invariant phenotypes": "Learning representations for image-based profiling of perturbations",
    "Hypothesis testing": "Optimal Experimental Design for Model Discrimination",
}

def fetch(item):
    name, query = item
    url = "https://api.openalex.org/works"
    try:
        if name == "MAP":
            r = requests.get("https://api.crossref.org/works/" + query, timeout=20)
            r.raise_for_status()
            w = r.json()["message"]
            return name, {"query": query, "request_url": r.url, "records": [{
                "title": w["title"][0], "doi": "https://doi.org/" + w["DOI"],
                "abstract": w.get("abstract", ""), "year": 2026}]}
        r = requests.get(url, params={"search": query, "per-page": 3}, timeout=20)
        r.raise_for_status()
        records = []
        for w in r.json()["results"]:
            inv = w.get("abstract_inverted_index") or {}
            words = {i: word for word, positions in inv.items() for i in positions}
            records.append({"title": w["title"], "year": w["publication_year"], "doi": w.get("doi"),
                            "url": w["id"], "abstract": " ".join(words[i] for i in sorted(words))})
        return name, {"query": query, "request_url": r.url, "records": records}
    except requests.RequestException as e:
        return name, {"query": query, "error": type(e).__name__}

if __name__ == "__main__":
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        records = dict(pool.map(fetch, QUERIES.items()))
    (HERE / "literature_sources.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    for name, r in records.items():
        print(name, [(w["title"], w["doi"]) for w in r.get("records", [])], r.get("error", ""))
