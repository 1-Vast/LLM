"""Central reference collection through the installed library interface."""
import subprocess
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

SCRIPT = r'D:\CodexData\.codex\skills\lit-survey\scripts\reference_library.py'
LIBRARY = r'D:\MAESTRO\reference'
ROOT = Path(__file__).resolve().parent


def run(*args):
    subprocess.run([sys.executable, '-X', 'utf8', SCRIPT, *args], check=True)


sources = [
    ('arxiv-2410.02355', 'AlphaEdit: Null-Space Constrained Knowledge Editing for Language Models',
     '2024-10-03', 'v4', '2025-04-22', 'conference_ICLR2025; first_preprint2024',
     'Sections2.2-3.3,eq7-12; fixed-key preservation and numerical null space'),
    ('arxiv-2606.26783', 'Reproducibility Study of "AlphaEdit: Null-Space Constrained Knowledge Editing for Language Models"',
     '2026-06-25', 'v2', '2026-07-07', 'preprint; acceptance_unverified',
     'Sections2.1-2.2,5.3,A.3.1-A.3.2; degradation reported, causal explanations conditional'),
    ('arxiv-2509.00178', 'Poke and Strike: Learning Task-Informed Exploration Policies',
     '2025-08-29', 'v1', '2025-08-29', 'preprint; CoRL2025 metadata not separately checked',
     'Sections4.1-4.5,5.3,6; simulator privilege, task sensitivity, misspecification'),
    ('arxiv-2505.14266', 'Sampling-Based System Identification with Active Exploration for Legged Robot Sim2Real Learning',
     '2025-05-20', 'v1', '2025-05-20', 'preprint; acceptance_unverified',
     'Sections3-4,Algorithm1,7,A.5; feasible excitation,FIM,parameter compensation'),
]
for pid, title, date, version, version_date, type_status, scope in sources:
    arxiv_id = pid.removeprefix('arxiv-')
    url = 'https://arxiv.org/html/' + arxiv_id + version
    run('record', LIBRARY, 'paper', pid, 'title='+title, 'doi=10.48550/arXiv.'+arxiv_id,
        'first_public_date='+date, 'type_status='+type_status, 'landing_page='+url,
        'candidate_url='+url, 'reading_level=P', 'reading_scope='+scope,
        'date_basis=Inspected version '+version+' dated '+version_date,
        'note=Cross-domain research 2026-10-27; partial reading, no code reproduction')
    local = ROOT / 'robotics_sources' / (pid + 'v1.html')
    if local.is_file():
        run('paper', LIBRARY, pid, '--file', str(local), '--html', '--version', 'arxiv-'+version)
    else:
        run('paper', LIBRARY, pid, url, '--html', '--version', 'arxiv-'+version)

# Keep original JATS in the episode; main-file importer supports PDF/HTML, not XML.
for pmc, doi, pid, dates, scope in [
    ('PMC13109062', '10.1093/bib/bbag199', 'doi-10.1093-bib-bbag199',
     'collection2026-03; epub2026-04-25', 'sec2a/2g/2h/2m/2r and sec3j; shared/specific combination model and splits'),
    ('PMC13587831', '10.1093/bioinformatics/btag662', 'doi-10.1093-bioinformatics-btag662',
     'PubMed2026-08-31; XML2026-09-07', 'Sections2.4-2.5,2.8-2.9,4; treated-control input,representation,phenotype limitation'),
]:
    source = ROOT / 'cv_nlp_sources' / (pmc + '.xml')
    tree = ET.parse(source)
    title = ''.join(tree.getroot().find('.//article-title').itertext()).strip()
    run('record', LIBRARY, 'paper', pid, 'title='+title, 'doi='+doi, 'type_status=journal_article',
        'date_basis='+dates, 'landing_page=https://doi.org/'+doi,
        'source_url=https://www.ebi.ac.uk/europepmc/webservices/rest/'+pmc+'/fullTextXML',
        'reading_level=P', 'reading_scope='+scope,
        'failure_reason=Main PDF/HTML not collected; original full JATS inspected and retained outside library',
        'note=Original full XML and hash at '+str(source)+'; main importer does not accept XML. No code reproduction.')

run('record', LIBRARY, 'paper', 'ssrn-7368638',
    'title=Target Identifiability from Destructive Single-cell Snapshots: Sharp Bounds for Path-dependent Cellular Quantities',
    'type_status=preprint; metadata only', 'first_public_date=2026-08-29',
    'landing_page=https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7368638',
    'download_status=restricted', 'reading_level=A',
    'reading_scope=Search-indexed primary abstract only; SSRN403, no inspected proof or method',
    'note=Closest-prior threat only, not a source for uninspected identifiability claims')
