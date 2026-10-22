"""Metadata/method-only audit. No expression/CEL or outcome file is opened."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/tggates_rna_feedback_pilot'


def main():
    paths = [ROOT / 'log/20261022/tggates_source_qualification/PAPER.xml',
             ROOT / 'log/20261022/tggates_source_qualification/README_e.html',
             ROOT / 'log/20261022/tggates_source_qualification/DIRECTORY.html',
             ROOT / 'log/20261022/tggates_functional_qualification/skeptic_sources/EARLY_TG_FULL.xml']
    terms = re.compile(r'normaliz|\brma\b|mas.?5|dchip|affymetrix|U133|processed|quantile|robust multi', re.I)
    results = []
    for path in paths:
        text = path.read_text(encoding='utf-8')
        try:
            tree = ET.fromstring(text)
            blocks = [' '.join(node.itertext()) for node in tree.iter() if node.tag.split('}')[-1] in ('p', 'title')]
        except ET.ParseError:
            blocks = [re.sub('<[^>]+>', ' ', block) for block in re.split(r'</(?:p|tr|li|h[1-6])>', text, flags=re.I)]
        excerpts = [re.sub(r'\s+', ' ', block).strip() for block in blocks if terms.search(block)]
        results.append({'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                        'matched_method_or_documentation_blocks': excerpts})
    packages = sorted([{'name': dist.metadata.get('Name'), 'version': dist.version}
                       for dist in importlib.metadata.distributions()
                       if any(term in (dist.metadata.get('Name') or '').lower()
                              for term in ['affy', 'biopy', 'rpy', 'numpy', 'scipy', 'pandas', 'h5', 'array', 'rma'])],
                       key=lambda row: row['name'].lower())
    rscript = shutil.which('Rscript')
    command = [rscript, '--vanilla', str(Path(__file__).with_name('mechanism_r_environment.R'))]
    proc = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace', check=False)
    payload = {'python_version': platform.python_version(), 'Rscript': rscript, 'python_packages': packages,
               'r_query': {'command': command, 'exit_code': proc.returncode, 'stdout': proc.stdout, 'stderr': proc.stderr},
               'retained_primary_method_excerpts': results, 'new_rna_numeric_access': False,
               'new_package_installations': 0, 'new_network_requests': 0}
    with (OUT / 'MECHANISM_LOCAL_AUDIT.json').open('x', encoding='utf-8') as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'r_query': payload['r_query'], 'method_block_counts': [len(row['matched_method_or_documentation_blocks'])
                                                                        for row in results]}, ensure_ascii=False))


if __name__ == '__main__':
    main()
