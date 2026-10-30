"""Store only decision-changing primary sources with the installed library tool."""
import subprocess
import sys

script = r'D:\CodexData\.codex\skills\lit-survey\scripts\reference_library.py'
library = r'D:\MAESTRO\reference'
sources = [
    ('arxiv-2606.25357', 'Compositional Behavioral Semantics for State Abstraction in Reinforcement Learning',
     '2026-06-24', 'https://arxiv.org/html/2606.25357v2', 'arxiv-v2'),
    ('arxiv-2608.15645', 'Generalised Transportability via Causal Abstractions',
     '2026-08-16', 'https://arxiv.org/html/2608.15645v1', 'arxiv-v1'),
    ('arxiv-2602.18724', 'Task-Aware Exploration via a Predictive Bisimulation Metric',
     '2026-02-21', 'https://arxiv.org/html/2602.18724v1', 'arxiv-v1'),
]
for pid, title, date, url, version in sources:
    subprocess.run([sys.executable, '-X', 'utf8', script, 'record', library, 'paper', pid,
                    'title='+title, 'doi=10.48550/arXiv.'+pid.removeprefix('arxiv-'),
                    'first_public_date='+date, 'type_status=preprint',
                    'landing_page='+url, 'candidate_url='+url,
                    'reading_level=A',
                    'reading_scope=Academic API abstract inspected; method reading to be recorded separately',
                    'note=Core module design; no reproduced results or verified code yet'], check=True)
    subprocess.run([sys.executable, '-X', 'utf8', script, 'paper', library, pid,
                    url, '--html', '--version', version], check=True)

# This final block is a reading log, not evidence of a reproduction.
scopes = {
    'arxiv-2606.25357': 'Sections 4.1-4.4 and 5, exact behavior preservation versus value equivalence; proofs not read',
    'arxiv-2608.15645': 'Abstract, Introduction, 2.2 definitions and 3.1 same-variable graph intervention and known-shift assumptions; certification proofs not read',
    'arxiv-2602.18724': 'Sections 3.1-3.3, predictive reward metric equations 5-12; appendix proofs not read',
}
for pid, scope in scopes.items():
    subprocess.run([sys.executable, '-X', 'utf8', script, 'record', library, 'paper', pid,
                    'reading_level=P', 'reading_scope='+scope], check=True)
