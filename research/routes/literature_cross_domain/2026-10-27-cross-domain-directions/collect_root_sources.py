"""Add inspected primary sources with the installed library tool; no model code runs."""
import subprocess
import sys

script = r'D:\CodexData\.codex\skills\lit-survey\scripts\reference_library.py'
library = r'D:\MAESTRO\reference'
sources = [
    ('arxiv-2604.27646', 'Benchmarking virtual cell models for in-the-wild perturbation response',
     '10.48550/arXiv.2604.27646', '2026-04-30',
     'https://arxiv.org/html/2604.27646v1', 'arxiv-v1',
     'Results on context transfer, unseen perturbations, cross-dataset integration; evaluation limits'),
    ('arxiv-2502.09775', 'CellFlow: Simulating Cellular Morphology Changes via Flow Matching',
     '10.48550/arXiv.2502.09775', '2025-02-13',
     'https://arxiv.org/html/2502.09775v1', 'arxiv-v1',
     'Sections 2.2,3.1-3.4 and Appendix G; generative time versus physical dynamics'),
    ('arxiv-2605.23470', 'Learning Individual Dynamics from Sparse Cross-Sectional Snapshots',
     '10.48550/arXiv.2605.23470', '2026-05-22',
     'https://arxiv.org/html/2605.23470v1', 'arxiv-v1',
     'Sections 2-5 and identifiability assumptions, observational injectivity and limitations'),
]
for pid, title, doi, date, url, version, scope in sources:
    subprocess.run([sys.executable, '-X', 'utf8', script, 'record', library, 'paper', pid,
                    'title='+title, 'doi='+doi, 'first_public_date='+date,
                    'type_status=preprint', 'landing_page='+url, 'candidate_url='+url,
                    'reading_level=P', 'reading_scope='+scope,
                    'note=2026-10-27 cross-domain direction study; partial reading, no replication'], check=True)
    subprocess.run([sys.executable, '-X', 'utf8', script, 'paper', library, pid,
                    url, '--html', '--version', version], check=True)

subprocess.run([sys.executable, '-X', 'utf8', script, 'record', library, 'paper',
                'doi-10.1038-s41592-025-02980-0',
                'title=Benchmarking algorithms for generalizable single-cell perturbation response prediction',
                'doi=10.1038/s41592-025-02980-0', 'formal_date=2025-12-11',
                'type_status=journal_article',
                'landing_page=https://www.nature.com/articles/s41592-025-02980-0',
                'download_status=restricted', 'reading_level=R',
                'reading_scope=Publisher indexed bibliographic information only; full text access failed',
                'note=Nature Methods volume 23 issue year 2026; online date 2025-12-11. Not used to infer uninspected method details.'], check=True)
