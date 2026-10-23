"""Retain exact bounded source requests and metadata extraction."""
from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/dose_update_qualification/sources'
URLS = {
    'quota_epmc': 'https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.64898/2026.10.02.754788&format=json&resultType=core',
    'quota_biorxiv_api': 'https://api.biorxiv.org/details/biorxiv/10.64898/2026.10.02.754788',
    'quota_primary': 'https://www.biorxiv.org/content/10.64898/2026.10.02.754788v1.full',
}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--followup', action='store_true')
    parser.add_argument('--metadata', action='store_true')
    parser.add_argument('--repos', action='store_true')
    parser.add_argument('--implementation', action='store_true')
    args = parser.parse_args()
    ledger = OUT / ('FOLLOWUP_REQUESTS.json' if args.followup else 'PRIMARY_REQUESTS.json')
    if args.followup:
        URLS = {
            'statistics_primary': 'https://www.biorxiv.org/content/10.64898/2026.06.09.731197v1.full',
            'emeraldbay_metadata': 'https://huggingface.co/api/datasets/tahoebio/EmeraldBay',
            'emeraldbay_readme': 'https://huggingface.co/datasets/tahoebio/EmeraldBay/raw/main/README.md',
        }
    if args.metadata:
        ledger = OUT / 'METADATA_REQUESTS.json'
        URLS = {
            'statistics_epmc': 'https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.64898/2026.06.09.731197&format=json&resultType=core',
            'statistics_biorxiv_api': 'https://api.biorxiv.org/details/biorxiv/10.64898/2026.06.09.731197',
            'emeraldbay_repos': 'https://api.github.com/search/repositories?q=EmeraldBay+Svensson',
        }
    if args.repos:
        ledger = OUT / 'REPO_REQUESTS.json'
        URLS = {
            'rhaister_repos': 'https://api.github.com/search/repositories?q=Rhaister',
        }
    if args.implementation:
        ledger = OUT / 'IMPLEMENTATION_REQUESTS.json'
        URLS = {
            'rhaister_model': 'https://huggingface.co/api/models/tahoebio/Rhaister',
            'rhaister_readme': 'https://huggingface.co/tahoebio/Rhaister/raw/main/README.md',
            'emeraldbay_tutorial': 'https://huggingface.co/datasets/tahoebio/EmeraldBay/raw/f2a0be6b02f731553657f0115c345b20bb020ede/tutorials/loading_data.ipynb',
        }
    assert not ledger.exists()
    rows = []
    for name, url in URLS.items():
        row = dict(name=name, requested_url=url, start=datetime.now(timezone.utc).isoformat())
        try:
            response = requests.get(url, timeout=45)
            path = OUT / (name + '.body')
            path.write_bytes(response.content)
            row.update(url=response.url, status=response.status_code, bytes=len(response.content),
                sha256=hashlib.sha256(response.content).hexdigest(),
                content_type=response.headers.get('Content-Type'))
            if name.endswith('api') or name.endswith('epmc'):
                print(name + ': ' + response.text[:14500])
            else:
                print(json.dumps(row))
        except Exception as exc:
            row.update(error_type=type(exc).__name__)
            print(json.dumps(row))
        rows.append(row)
        ledger.write_text(json.dumps(rows, indent=2), encoding='utf-8')
